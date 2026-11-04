// Prova RIL-1 e RIL-2 (DX-17 / AC-12): registro non leggibile (eccezione) e valore non validato dallo sweeper.
import { test, before, beforeEach, after } from "node:test";
import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { makeTestPool, applyMigration, truncateAll } from "/tmp/collaudo-s6/code-reviewer/repo/test/helpers/db.js";
import { sweepHitlRequests } from "/tmp/collaudo-s6/code-reviewer/repo/src/hitl-expiry-sweeper.js";
import { ConfigRegistry } from "/tmp/collaudo-s6/code-reviewer/repo/src/config-registry.js";

let pool;
before(async () => { pool = makeTestPool(); await applyMigration(pool); });
after(async () => { await pool.end(); });
beforeEach(async () => { await truncateAll(pool); });
const hoursAgo = (h) => new Date(Date.now() - h * 3600_000).toISOString();
async function insertPending(companyId, createdAt) {
  const id = randomUUID();
  await pool.query(
    `INSERT INTO hitl_requests (id, company_id, run_id, tool_key, permission_key, arguments, status, created_at)
     VALUES ($1,$2,'r','t','p','{}'::jsonb,'pending',$3)`, [id, companyId, createdAt]);
  return id;
}
const status = async (id) => (await pool.query("SELECT status FROM hitl_requests WHERE id=$1", [id])).rows[0].status;

test("RIL-1: registro non disponibile (getHitlRequestTtlHours lancia) -> nessun segnale e il giro si interrompe per tutte le aziende", async () => {
  const a = randomUUID(), b = randomUUID();
  const ra = await insertPending(a, hoursAgo(48));
  const rb = await insertPending(b, hoursAgo(48));
  let calls = 0;
  class Down extends ConfigRegistry {
    async getHitlRequestTtlHours(companyId) {
      calls++;
      if (calls === 1) throw new Error("registry unavailable"); // prima azienda: registro giu'
      return { ok: true, value: 24, version: "v1" };            // la seconda sarebbe valida
    }
  }
  await assert.rejects(sweepHitlRequests(pool, { configRegistry: new Down() }), /registry unavailable/);
  const { rows: signals } = await pool.query("SELECT * FROM platform_signals");
  assert.equal(signals.length, 0, "NESSUN segnale emesso (AC-12/DX-17 lo richiedono)");
  // l'azienda con TTL valido e riga scaduta da 48h non e' stata processata: sweep abortito
  assert.equal(calls, 1, "il ciclo si e' fermato alla prima azienda");
  const states = [await status(ra), await status(rb)];
  assert.deepEqual(states, ["pending", "pending"], "righe scadute da 48h restano pending per tutte");
});

test("RIL-2: lo sweeper non valida il valore: un registro che restituisce ok con value=0 chiude righe fresche", async () => {
  const c = randomUUID();
  const fresh = await insertPending(c, hoursAgo(0.01)); // ~36 s fa
  class Zero extends ConfigRegistry {
    async getHitlRequestTtlHours() { return { ok: true, value: 0, version: "v1" }; }
  }
  const res = await sweepHitlRequests(pool, { configRegistry: new Zero() });
  assert.equal(res.cancelled, 1, "TTL=0 (fuori dall'intervallo 1-168 di DA-C3-04) accettato: riga di 36 s cancellata");
  assert.equal(await status(fresh), "cancelled");
});

test("RIL-2b: value=NaN -> RangeError non gestito, nessun segnale", async () => {
  const c = randomUUID();
  await insertPending(c, hoursAgo(48));
  class Nan extends ConfigRegistry {
    async getHitlRequestTtlHours() { return { ok: true, value: NaN, version: "v1" }; }
  }
  await assert.rejects(sweepHitlRequests(pool, { configRegistry: new Nan() }), RangeError);
  assert.equal((await pool.query("SELECT 1 FROM platform_signals")).rowCount, 0);
});
