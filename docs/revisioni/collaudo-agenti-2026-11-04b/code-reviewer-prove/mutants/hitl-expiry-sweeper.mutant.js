/**
 * C3 — Punto HITL, sweeper di scadenza (§6 "Scadenza", §9 fase 5, AC-6).
 *
 * Perimetro di questo modulo: solo lo sweeper e la lettura del TTL. Fuori perimetro: la
 * cancellazione di `arguments`/`context` dopo la retention (AC-11), il collegamento a C4, la RLS
 * (AC-7), il replay/resume.
 *
 * Tre modi in cui una riga parcheggiata "muore" oltre il TTL (C3 §6):
 *   - `pending` oltre il TTL: nessuno ha deciso -> `cancelled`;
 *   - `approved` ma mai reclamata oltre il TTL: nessun run la eseguirà -> `cancelled`;
 *   - reclamata (`claimed_at` valorizzato) senza esito oltre il TTL: lo stato della scrittura è
 *     sconosciuto -> si registra `outcome='error'`/`outcome_code='reaped'`, lo `status` RESTA
 *     `approved`. Non viene MAI rieseguita qui: il claim è ciò che rende la scrittura unica, e un
 *     reaper che la rieseguisse sarebbe un secondo writer (AC-6).
 *
 * TTL: variabile di piattaforma `hitl.request_ttl_hours` (DX-13, DA-C3-04), letta per ogni
 * azienda dal registro (ConfigRegistry). Se il valore non è leggibile o non è valido, lo sweeper
 * NON chiude nessuna riga di quell'azienda (fail-closed, DX-17) ed emette un segnale.
 */

import { randomUUID } from "node:crypto";

const DEFAULT_SIGNAL_TYPE = "config_variable_unreadable";

/**
 * @param {import('pg').Pool | import('pg').Client} db
 * @param {string} companyId
 * @param {string} signalType
 * @param {Record<string, unknown>} details
 */
async function emitSignal(db, companyId, signalType, details) {
  await db.query(
    `INSERT INTO platform_signals (id, company_id, signal_type, details) VALUES ($1, $2, $3, $4)`,
    [randomUUID(), companyId, signalType, details],
  );
}

/**
 * Chiude le righe scadute di una sola azienda. Tre UPDATE basati su predicato, ciascuno con
 * `company_id = $1` nella propria WHERE, così il passaggio di un'azienda non può mai toccare le
 * righe di un'altra.
 *
 * @param {import('pg').Pool | import('pg').Client} db
 * @param {string} companyId
 * @param {string} cutoffIso
 */
async function expireCompanyRows(db, companyId, cutoffIso) {
  const cancelPending = await db.query(
    `UPDATE hitl_requests
        SET status = 'cancelled', updated_at = now()
      WHERE company_id = $1
        AND status = 'pending'
        AND created_at < $2
      RETURNING id`,
    [companyId, cutoffIso],
  );

  const cancelUnclaimed = await db.query(
    `UPDATE hitl_requests
        SET status = 'cancelled', updated_at = now()
      WHERE company_id = $1
        AND status = 'approved'
        AND claimed_at IS NULL
        AND COALESCE(decided_at, created_at) < $2
      RETURNING id`,
    [companyId, cutoffIso],
  );

  const reaped = await db.query(
    `UPDATE hitl_requests
        SET outcome = 'error', outcome_code = 'reaped', claimed_at = NULL, status = 'approved', updated_at = now()
      WHERE company_id = $1
        AND status = 'approved'
        AND claimed_at IS NOT NULL
        AND outcome IS NULL
        AND claimed_at < $2
      RETURNING id`,
    [companyId, cutoffIso],
  );

  return {
    cancelledPending: cancelPending.rowCount,
    cancelledUnclaimed: cancelUnclaimed.rowCount,
    reaped: reaped.rowCount,
  };
}

/**
 * @param {import('pg').Pool} db
 * @param {{ now?: Date, configRegistry: import('/tmp/collaudo-s6/code-reviewer/repo/src/config-registry.js').ConfigRegistry }} options
 * @returns {Promise<{
 *   scanned: number,
 *   cancelled: number,
 *   reaped: number,
 *   blockedCompanies: string[],
 * }>}
 */
export async function sweepHitlRequests(db, { now = new Date(), configRegistry }) {
  if (!configRegistry) {
    throw new Error("sweepHitlRequests richiede un configRegistry (DX-13): niente default hardcoded");
  }

  const { rows: companies } = await db.query(
    `SELECT DISTINCT company_id FROM hitl_requests WHERE status IN ('pending', 'approved')`,
  );

  const result = { scanned: companies.length, cancelled: 0, reaped: 0, blockedCompanies: [] };

  for (const { company_id: companyId } of companies) {
    const ttl = await configRegistry.getHitlRequestTtlHours(companyId);
    if (!ttl.ok) {
      // DX-17 fail-closed: variabile mancante o non valida -> l'azione (chiudere le righe) si
      // blocca per questa azienda, e parte un segnale (qui verso la tabella di collaudo
      // `platform_signals`, in attesa di A5, ondata 2).
      result.blockedCompanies.push(companyId);
      await emitSignal(db, companyId, DEFAULT_SIGNAL_TYPE, {
        variable: "hitl.request_ttl_hours",
        reason: ttl.reason,
      });
      continue;
    }

    const cutoffIso = new Date(now.getTime() - ttl.value * 60 * 60 * 1000).toISOString();
    const { cancelledPending, cancelledUnclaimed, reaped } = await expireCompanyRows(db, companyId, cutoffIso);
    result.cancelled += cancelledPending + cancelledUnclaimed;
    result.reaped += reaped;
  }

  return result;
}
