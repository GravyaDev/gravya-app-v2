from __future__ import annotations

import os

from alembic import context
from sqlalchemy import engine_from_config, pool, text

config = context.config

database_url = os.environ.get("DATABASE_URL")
if not database_url:
    raise RuntimeError(
        "DATABASE_URL non impostata: la migrazione non parte su un database di default "
        "(DX-22, giro 2 CR minore). Esempio: "
        "DATABASE_URL=postgresql+psycopg://<utente>@<host>/<db> alembic upgrade head"
    )
config.set_main_option("sqlalchemy.url", database_url)

# Criterio di fine 2 (giro 3): verifica che le migrazioni girino con un
# ruolo proprietario non superuser. MIGRATION_ROLE, se impostata, fa
# eseguire `SET ROLE` subito dopo la connessione: chi lancia la migrazione
# si autentica (per esempio come il superuser di sviluppo locale) ma tutte
# le istruzioni della migrazione girano con i privilegi del ruolo indicato
# (lo stesso meccanismo di `db.writer_transaction`, non un nuovo modo di
# autenticarsi). Il nome del ruolo e' un valore fisso dell'ambiente di
# deploy, non un parametro esterno: non e' parametrizzabile in `SET ROLE`.
migration_role = os.environ.get("MIGRATION_ROLE")


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        if migration_role:
            connection.execute(text(f"SET ROLE {migration_role}"))
            connection.commit()
        context.configure(connection=connection)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
