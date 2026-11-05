"""Giro 4: revoca l'appartenenza temporanea a `gravya_e1_so_owner`, errori visibili, policy dei segnali sul GUC.

- **G3-02.** 0005 concedeva `gravya_e1_so_owner`/`gravya_migrator` a
  `current_user` (serve per `ALTER FUNCTION ... OWNER TO`, quando le
  migrazioni girano con un proprietario non superuser) ma non revocava mai
  quella appartenenza: chi esegue le migrazioni restava permanentemente
  membro di `gravya_e1_so_owner` (`BYPASSRLS`), potendo leggere
  `gravya_traces` di ogni tenant con `SET ROLE`, fuori dal regime di accesso
  applicativo. Qui si revoca `gravya_e1_so_owner FROM gravya_migrator` (il
  caso tipico di deploy: migrazioni con `MIGRATION_ROLE=gravya_migrator`).
  **Revocare richiede chi l'ha concessa (o un superuser)**: se questa
  migrazione gira sotto `gravya_migrator` stesso (senza `ADMIN OPTION` sulla
  concessione fatta da un superuser esterno, vedi
  `scripts/test-non-superuser.sh`), la REVOKE fallisce per privilegio
  insufficiente; non viene piu' inghiottita (nessun `EXCEPTION WHEN OTHERS
  THEN NULL`): un `RAISE WARNING` la rende visibile, e la pulizia reale
  resta affidata al deploy esterno (la stessa sessione superuser che ha
  fatto la concessione temporanea, subito dopo le migrazioni: vedi lo
  script). Il requisito di deploy - il ruolo di migrazione non e' mai il
  ruolo applicativo e non ha accesso ai dati a runtime - va dichiarato nella
  procedura di deploy (vedi report, sezione "Giro 4").
- **Rilievo V-07/correzione 7 del giro 5 (testo corretto).** Il punto
  precedente di questo docstring diceva che il `GRANT CREATE ON SCHEMA
  public TO gravya_e1_so_owner` era stato tolto dallo script perche' "non
  serve": **non e' vero, verificato con `psql` diretto** (due database di
  prova, un ruolo che crea una funzione e un altro a cui provare a
  trasferirne la proprieta'): PostgreSQL richiede che il NUOVO proprietario
  di una funzione abbia `CREATE` sullo schema che la contiene, altrimenti
  `ALTER FUNCTION ... OWNER TO` fallisce con "permission denied for schema
  public". `scripts/test-non-superuser.sh` concede quel `CREATE` (passo 2,
  temporaneo) e lo revoca subito dopo le migrazioni (passo 5), insieme
  all'appartenenza a `gravya_e1_so_owner`: e' un requisito di deploy (due
  concessioni temporanee, due revoche obbligatorie dopo), non qualcosa che
  questa migrazione tolga o revochi da sola. Vedi report, sezione "Giro 5".
- **Task correzione 5 (CR minore).** La policy di RLS della tabella
  provvisoria dei segnali torna ad avere un `WITH CHECK` sul tenant del GUC
  (`tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id')`):
  il writer non puo' piu' inserire un segnale a nome di un tenant diverso da
  quello della propria sessione (o senza tenant). `PostgresSignalSink.emit`
  imposta il GUC nella propria transazione prima dell'INSERT
  (`signals.py`). `USING` resta `true`: la riservatezza in lettura dipende
  dal privilegio (nessun `SELECT` per il writer, G15/G15b), non da questa
  policy.

Revision ID: 0006
Revises: 0005
Create Date: 2026-11-05
"""
from __future__ import annotations

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # G3-02: revoca l'appartenenza temporanea (best-effort: fallisce con un
    # avviso visibile se chi esegue la migrazione non ha l'ADMIN OPTION
    # necessaria per revocare, invece di restare silenziosa).
    op.execute(
        """
        DO $$
        BEGIN
            REVOKE gravya_e1_so_owner FROM gravya_migrator;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'impossibile revocare gravya_e1_so_owner da gravya_migrator qui (%); '
                'va fatto dalla sessione superuser di deploy subito dopo le migrazioni (vedi scripts/test-non-superuser.sh)', SQLERRM;
        END
        $$;
        """
    )

    # Task correzione 5: policy dei segnali con WITH CHECK sul tenant del GUC.
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON gravya_signals_min_audit;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON gravya_signals_min_audit
        FOR ALL
        USING (true)
        WITH CHECK (tenant_id IS NULL OR tenant_id = current_setting('app.tenant_id', true)::uuid);
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tenant_isolation ON gravya_signals_min_audit;")
    op.execute(
        """
        CREATE POLICY tenant_isolation ON gravya_signals_min_audit
        FOR ALL
        USING (true)
        WITH CHECK (true);
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            GRANT gravya_e1_so_owner TO gravya_migrator;
        EXCEPTION WHEN OTHERS THEN
            RAISE WARNING 'impossibile ri-concedere gravya_e1_so_owner a gravya_migrator qui (%)', SQLERRM;
        END
        $$;
        """
    )
