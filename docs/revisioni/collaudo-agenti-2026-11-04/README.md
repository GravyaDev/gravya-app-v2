# Collaudo degli agenti di governance — 2026-11-04 (sessione 5)

Collaudo dei quattro agenti la cui configurazione sulla piattaforma coincide con `.claude/agents/` (verifica di `list_agents` all'avvio): registrar, code-reader, implementer, regulatory-researcher. Code-reviewer, compliance-auditor, doc-writer e plan-auditor avevano sulla piattaforma la descrizione precedente e non sono stati collaudati.

Impronte md5 di `docs/` e `.claude/` prima e dopo: cambiano solo `docs/index.md` (registrar), `docs/norme-di-riferimento.md` (nuovo) e questa cartella. gravya-app e gravya-app-kloudify: HEAD e stato di lavoro invariati.

| Agente | Configurazione | Prova | Esito del coordinator | Problemi verificati |
|---|---|---|---|---|
| registrar | Haiku, medium | Reale: `regulatory-researcher` nella riga agenti di `docs/index.md` (commit 89029b1) | OK | Minore: nota informativa scritta in `conflitti_da_riportare` |
| code-reader | Haiku, medium | Sandbox (sola lettura): TTL e sweeper HITL di gravya-app@349118b1, una domanda di sintesi, una domanda trappola | Sufficiente sulle domande precise; sintesi da verificare | `kloud-resume.ts:173-178` citato per un file di 41 righe (corretto: :28, :32); "gravya-hitl non montato in app.ts" falso (`app.ts:439` lo monta) |
| implementer | Sonnet, medium sulla piattaforma (il file dice high) | Sandbox: C3 AC-6 su repo git finto con Postgres 16 reale | Buono | Intervallo 1-168 h come costanti nel codice (DA-C3-04: lo fissa il superadmin, quindi DX-22); non ha segnalato la tensione DX-17 / C3 AC-12 |
| regulatory-researcher | Sonnet, medium | Reale in sandbox, poi portato in `docs/norme-di-riferimento.md` | Buono | Nessun errore trovato nelle verifiche a campione (Reg. 2026/1744, provv. Garante 284/2026, d.lgs. 179/2026, aperti sulle fonti ufficiali dal coordinator) |

| File | Contenuto |
|---|---|
| `code-reader-hitl-ttl.md` | Report del code-reader (contiene i due errori sopra: non usarlo come fonte senza le correzioni) |
| `implementer-report-c3-ac6.md` | Report dell'implementer |
| `implementer-c3-ac6.patch` | Commit della sandbox (`git format-patch`); codice di collaudo, non di v2 |
