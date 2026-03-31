#!/usr/bin/env bash
# Creates the application DB role (tul_psi_app) with DML-only privileges.
#
# PostgreSQL executes every *.sh file found in /docker-entrypoint-initdb.d/
# exactly once, on the very first container start (when the data directory is
# empty).  This script therefore runs automatically after the admin role
# (POSTGRES_ADMIN_USER) and the database (POSTGRES_DB) have been created by
# the official entrypoint.
#
# Role summary
# ─────────────────────────────────────────────────────────────────────────────
#   POSTGRES_ADMIN_USER   (tul_psi_admin by default)
#       Full privileges including DDL.  Used by Alembic / CI/CD pipelines.
#
#   POSTGRES_APP_USER   (tul_psi_app by default)
#       DML only: SELECT, INSERT, UPDATE, DELETE on tables, plus sequence
#       usage for auto-increment PKs.  Used by the FastAPI application at
#       runtime so that a compromised app process cannot alter the schema.
# ─────────────────────────────────────────────────────────────────────────────
#
# Required environment variables (set via docker-compose env_file / environment):
#   POSTGRES_ADMIN_USER     admin role name
#   POSTGRES_DB             database name
#   POSTGRES_APP_USER       application role name
#   POSTGRES_APP_PASSWORD   application role password

set -euo pipefail

# Escape any single quotes in the password so the SQL literal is valid.
# (Single quotes are doubled per the SQL standard: ' → '')
ESCAPED_APP_PASSWORD=${POSTGRES_APP_PASSWORD//\'/\'\'}

psql -v ON_ERROR_STOP=1 \
     --username "$POSTGRES_ADMIN_USER" \
     --dbname   "$POSTGRES_DB" \
     <<SQL
-- Application role: DML only — no DDL / schema changes.
-- The DO block makes the script idempotent: re-running it on an already
-- initialised database (e.g. after a failed partial run) is safe.
DO \$\$
BEGIN
    IF NOT EXISTS (
        SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_APP_USER}'
    ) THEN
        CREATE ROLE "${POSTGRES_APP_USER}" LOGIN PASSWORD '${ESCAPED_APP_PASSWORD}';
    END IF;
END
\$\$;

-- Allow the application role to connect to the database.
GRANT CONNECT ON DATABASE "${POSTGRES_DB}" TO "${POSTGRES_APP_USER}";

-- Allow the application role to look up objects in the public schema.
GRANT USAGE ON SCHEMA public TO "${POSTGRES_APP_USER}";

-- Grant DML on all tables that exist at role-creation time.
GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public
    TO "${POSTGRES_APP_USER}";

-- Ensure DML is automatically granted on tables created by the admin role in
-- the future (e.g. after every Alembic migration).
ALTER DEFAULT PRIVILEGES FOR ROLE "${POSTGRES_ADMIN_USER}" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "${POSTGRES_APP_USER}";

-- Grant sequence access so that SERIAL / auto-increment primary keys work.
GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public
    TO "${POSTGRES_APP_USER}";

ALTER DEFAULT PRIVILEGES FOR ROLE "${POSTGRES_ADMIN_USER}" IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO "${POSTGRES_APP_USER}";
SQL
