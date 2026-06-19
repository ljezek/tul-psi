#!/usr/bin/env bash
# Creates additional per-app databases listed in $EXTRA_DATABASES (comma-separated) and
# grants the DML-only application role (created by 10-init-db.sh) the same privileges it
# has on the primary database.
#
# Runs once, on first container start, AFTER 10-init-db.sh (which created the app role).
# Re-running on an already-initialised volume is a no-op for existing databases.
#
# Required env (provided by docker-compose / .env):
#   POSTGRES_ADMIN_USER   admin/owner role (also the migration role)
#   POSTGRES_APP_USER     DML-only application role
#   EXTRA_DATABASES       comma-separated database names (may be empty/unset)

set -euo pipefail

EXTRA_DATABASES=${EXTRA_DATABASES:-}
if [[ -z "${EXTRA_DATABASES// /}" ]]; then
	echo "20-create-databases: EXTRA_DATABASES is empty — nothing to do."
	exit 0
fi

# psql connected to the maintenance DB as the superuser/admin.
psql_admin() { psql -v ON_ERROR_STOP=1 --username "$POSTGRES_ADMIN_USER" --dbname postgres "$@"; }

IFS=',' read -ra DBS <<< "$EXTRA_DATABASES"
for raw in "${DBS[@]}"; do
	db=$(echo "$raw" | xargs) # trim whitespace
	[[ -z "$db" ]] && continue

	# CREATE DATABASE cannot run inside a transaction block, hence a separate -c each.
	if [[ "$(psql_admin -tAc "SELECT 1 FROM pg_database WHERE datname = '${db}'")" == "1" ]]; then
		echo "20-create-databases: database '${db}' already exists — skipping create."
	else
		echo "20-create-databases: creating database '${db}'."
		psql_admin -c "CREATE DATABASE \"${db}\" OWNER \"${POSTGRES_ADMIN_USER}\";"
	fi

	echo "20-create-databases: granting DML on '${db}' to '${POSTGRES_APP_USER}'."
	psql_admin -c "GRANT CONNECT ON DATABASE \"${db}\" TO \"${POSTGRES_APP_USER}\";"

	# Schema/object grants + default privileges must be applied INSIDE the target DB.
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_ADMIN_USER" --dbname "$db" <<SQL
GRANT USAGE ON SCHEMA public TO "${POSTGRES_APP_USER}";

GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public
    TO "${POSTGRES_APP_USER}";

ALTER DEFAULT PRIVILEGES FOR ROLE "${POSTGRES_ADMIN_USER}" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "${POSTGRES_APP_USER}";

GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public
    TO "${POSTGRES_APP_USER}";

ALTER DEFAULT PRIVILEGES FOR ROLE "${POSTGRES_ADMIN_USER}" IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO "${POSTGRES_APP_USER}";
SQL
done
