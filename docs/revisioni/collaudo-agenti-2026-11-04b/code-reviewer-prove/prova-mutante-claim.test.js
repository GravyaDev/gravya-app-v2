/**
 * C3 — Punto HITL. AC-6: "Lo sweeper chiude il 100% delle righe oltre il TTL senza rieseguirne
 * nessuna" (C3 v1.4 §8), su Postgres reale, sul modello di gravya-app
 * `kloud-write-approvals.realpg.test.ts`.
 *
 * Perimetro: sweeper e lettura del TTL (§9 fase 5, parte necessaria ad AC-6). Fuori perimetro:
 * retention di arguments/context (AC-11), collegamento a C4, RLS (AC-7), replay/resume.
 */
import { test, before, beforeEach, after } from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { makeTestPool, applyMigration, truncateAll } from "/tmp/collaudo-s6/code-reviewer/repo/test/helpers/db.js";
import { sweepHitlRequests } from "./mutants/hitl-expiry-sweeper.mutant.js";
import { InMemoryConfigRegistry } from "/tmp/collaudo-s6/code-reviewer/repo/src/config-registry.js";

let pool;

before(async () => {
  pool = makeTestPool();
  await applyMigration(pool);
});

after(async () => {
  await pool.end();
});

beforeEach(async () => {
  await truncateAll(pool);
});

function hoursAgo(h) {
  return new Date(Date.now() - h * 3600_000).toISOString();
}

async function insertRow(overrides) {
  const row = {
    id: randomUUID(),
    companyId: randomUUID(),
    runId: "run-1",
    toolKey: "crm.create_record",
    permissionKey: "crm_records:create",
    status: "pending",
    outcome: null,
    outcomeCode: null,
    claimedAt: null,
    decidedAt: null,
    createdAt: new Date().toISOString(),
    ...overrides,
  };
  await pool.query(
    `INSERT INTO hitl_requests
       (id, company_id, run_id, tool_key, permission_key, arguments, context, status,
        outcome, outcome_code, claimed_at, decided_at, created_at, updated_at)
     VALUES ($1,$2,$3,$4,$5,'{}'::jsonb,'{}'::jsonb,$6,$7,$8,$9,$10,$11,$11)`,
    [
      row.id,
      row.companyId,
      row.runId,
      row.toolKey,
      row.permissionKey,
      row.status,
      row.outcome,
      row.outcomeCode,
      row.claimedAt,
      row.decidedAt,
      row.createdAt,
    ],
  );
  return row.id;
}

async function rowById(id) {
  const { rows } = await pool.query(
    "SELECT id, company_id, status, outcome, outcome_code FROM hitl_requests WHERE id = $1",
    [id],
  );
  return rows[0];
}

test("AC-6: chiude il 100% delle righe scadute nei tre modi previsti e non riesegue nessuna chiamata", async () => {
  const companyId = randomUUID();
  const registry = new InMemoryConfigRegistry({ perCompany: { [companyId]: 24 } });

  const expiredPending = await insertRow({ companyId, status: "pending", createdAt: hoursAgo(25) });
  const expiredUnclaimed = await insertRow({
    companyId,
    status: "approved",
    createdAt: hoursAgo(30),
    decidedAt: hoursAgo(25),
  });
  const expiredClaimedNoOutcome = await insertRow({
    companyId,
    status: "approved",
    createdAt: hoursAgo(30),
    decidedAt: hoursAgo(26),
    claimedAt: hoursAgo(25),
  });
  const freshPending = await insertRow({ companyId, status: "pending", createdAt: hoursAgo(1) });
  const freshClaimed = await insertRow({
    companyId,
    status: "approved",
    createdAt: hoursAgo(2),
    decidedAt: hoursAgo(1),
    claimedAt: hoursAgo(1),
  });

  const result = await sweepHitlRequests(pool, { configRegistry: registry });

  assert.equal(result.cancelled, 2, "le due righe pending/unclaimed scadute sono chiuse");
  assert.equal(result.reaped, 1, "la riga reclamata senza esito è segnata reaped");
  assert.deepEqual(result.blockedCompanies, []);

  assert.equal((await rowById(expiredPending)).status, "cancelled");
  assert.equal((await rowById(expiredUnclaimed)).status, "cancelled");

  const reapedRow = await rowById(expiredClaimedNoOutcome);
  assert.equal(reapedRow.status, "approved", "la riga reclamata NON cambia status: non viene rieseguita");
  assert.equal(reapedRow.outcome, "error");
  assert.equal(reapedRow.outcome_code, "reaped");

  assert.equal((await rowById(freshPending)).status, "pending", "una riga non scaduta non si tocca");
  const freshClaimedRow = await rowById(freshClaimed);
  assert.equal(freshClaimedRow.status, "approved");
  assert.equal(freshClaimedRow.outcome, null);

  const { rows: execs } = await pool.query("SELECT count(*)::int AS n FROM tool_executions");
  assert.equal(execs[0].n, 0, "nessuna esecuzione è mai stata registrata dallo sweeper");
});

test("AC-6: idempotenza — un secondo giro non rielabora le righe già chiuse", async () => {
  const companyId = randomUUID();
  const registry = new InMemoryConfigRegistry({ perCompany: { [companyId]: 24 } });
  const id = await insertRow({ companyId, status: "pending", createdAt: hoursAgo(25) });

  const first = await sweepHitlRequests(pool, { configRegistry: registry });
  assert.equal(first.cancelled, 1);

  const second = await sweepHitlRequests(pool, { configRegistry: registry });
  assert.equal(second.cancelled, 0, "la riga già cancellata non viene più contata (status non più pending/approved)");
  assert.equal((await rowById(id)).status, "cancelled");
});

test("AC-6: soglia netta sul TTL — appena sotto resta aperta, appena sopra viene chiusa", async () => {
  const companyId = randomUUID();
  const registry = new InMemoryConfigRegistry({ perCompany: { [companyId]: 24 } });

  const justBelow = await insertRow({ companyId, status: "pending", createdAt: hoursAgo(23.98) }); // ~23h59
  const justAbove = await insertRow({ companyId, status: "pending", createdAt: hoursAgo(24.02) }); // ~24h01

  await sweepHitlRequests(pool, { configRegistry: registry });

  assert.equal((await rowById(justBelow)).status, "pending", "sotto il TTL: resta pending");
  assert.equal((await rowById(justAbove)).status, "cancelled", "sopra il TTL: viene chiuso");
});

test("AC-6 / DX-17: TTL mancante o fuori intervallo blocca la chiusura solo per l'azienda interessata, con segnale", async () => {
  const companyMissing = randomUUID(); // nessun valore nel registro
  const companyInvalid = randomUUID(); // valore fuori dall'intervallo 1-168h (DA-C3-04)
  const companyValid = randomUUID();

  const registry = new InMemoryConfigRegistry({
    perCompany: { [companyInvalid]: 500, [companyValid]: 24 },
  });

  const rowMissing = await insertRow({ companyId: companyMissing, status: "pending", createdAt: hoursAgo(48) });
  const rowInvalid = await insertRow({ companyId: companyInvalid, status: "pending", createdAt: hoursAgo(48) });
  const rowValid = await insertRow({ companyId: companyValid, status: "pending", createdAt: hoursAgo(48) });

  const result = await sweepHitlRequests(pool, { configRegistry: registry });

  assert.deepEqual(result.blockedCompanies.sort(), [companyInvalid, companyMissing].sort());
  assert.equal((await rowById(rowMissing)).status, "pending", "senza TTL leggibile, nessuna chiusura (fail-closed)");
  assert.equal((await rowById(rowInvalid)).status, "pending", "con TTL fuori intervallo, nessuna chiusura (fail-closed)");
  assert.equal((await rowById(rowValid)).status, "cancelled", "l'azienda con TTL valido viene comunque processata");

  const { rows: signals } = await pool.query(
    "SELECT company_id, signal_type, details FROM platform_signals ORDER BY company_id",
  );
  assert.equal(signals.length, 2, "un segnale per ciascuna azienda bloccata");
  const byCompany = Object.fromEntries(signals.map((s) => [s.company_id, s]));
  assert.equal(byCompany[companyMissing].details.reason, "missing");
  assert.equal(byCompany[companyInvalid].details.reason, "out_of_range");
});

test("AC-6: isolamento — il TTL e la chiusura di un'azienda non toccano le righe scadute di un'altra azienda con TTL diverso", async () => {
  const companyA = randomUUID();
  const companyB = randomUUID();
  const registry = new InMemoryConfigRegistry({ perCompany: { [companyA]: 24, [companyB]: 48 } });

  // Scaduta per A (TTL 24h) ma NON per B (TTL 48h), stessa età: 30h.
  const rowA = await insertRow({ companyId: companyA, status: "pending", createdAt: hoursAgo(30) });
  const rowB = await insertRow({ companyId: companyB, status: "pending", createdAt: hoursAgo(30) });

  await sweepHitlRequests(pool, { configRegistry: registry });

  assert.equal((await rowById(rowA)).status, "cancelled", "A è scaduta secondo il proprio TTL");
  assert.equal((await rowById(rowB)).status, "pending", "B non è scaduta secondo il proprio TTL, nonostante la stessa età di A");
});
