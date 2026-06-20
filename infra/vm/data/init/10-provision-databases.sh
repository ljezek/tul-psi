#!/usr/bin/env bash
# Generic multi-tenant provisioner for the shared Postgres server.
#
# Reads /provision.conf (mounted) and, for each database row, creates an isolated pair of
# login roles and a database owned by the owner role:
#   owner_user  — owns the database, full DDL+DML (used by Alembic migrations)
#   app_user    — DML only on the public schema (used by the running backend)
#
# DML on tables created LATER by the owner is auto-granted to the app role via
# ALTER DEFAULT PRIVILEGES FOR ROLE <owner> (same technique as database/init-db.sh).
#
# Runs once, on first container start (empty data dir), as the superuser ($POSTGRES_USER).
# Idempotent: existing roles/databases are skipped, grants are re-applied safely.
#
# provision.conf format — one row per database, whitespace-separated, '#' comments:
#   db   owner_user   owner_password   app_user   app_password

set -euo pipefail

CONF=${PROVISION_CONF:-/provision.conf}
if [[ ! -f "$CONF" ]]; then
	echo "10-provision: $CONF not found — nothing to provision." >&2
	exit 1
fi

# psql connected to the maintenance DB as the bootstrap superuser.
psql_super() { psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres "$@"; }

# Double single quotes so a value is a safe SQL string literal ('  ->  '').
sql_lit() { printf "%s" "${1//\'/\'\'}"; }

# Create a LOGIN role if it does not already exist, then (re)set its password.
ensure_role() {
	local role=$1 password=$2
	local role_lit pw_lit
	role_lit=$(sql_lit "$role"); pw_lit=$(sql_lit "$password")
	psql_super <<SQL
DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${role_lit}') THEN
        CREATE ROLE "${role}" LOGIN PASSWORD '${pw_lit}';
    ELSE
        ALTER ROLE "${role}" WITH LOGIN PASSWORD '${pw_lit}';
    END IF;
END
\$\$;
SQL
}

ensure_database() {
	local db=$1 owner=$2
	local db_lit
	db_lit=$(sql_lit "$db")
	if [[ "$(psql_super -tAc "SELECT 1 FROM pg_database WHERE datname = '${db_lit}'")" == "1" ]]; then
		echo "10-provision: database '${db}' already exists — skipping create."
	else
		echo "10-provision: creating database '${db}' owned by '${owner}'."
		psql_super -c "CREATE DATABASE \"${db}\" OWNER \"${owner}\";"
	fi
}

grant_app_privileges() {
	local db=$1 owner=$2 app=$3
	psql_super -c "GRANT CONNECT ON DATABASE \"${db}\" TO \"${app}\";"
	# Schema/object grants and default privileges must be applied INSIDE the target DB.
	psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$db" <<SQL
GRANT USAGE ON SCHEMA public TO "${app}";

GRANT SELECT, INSERT, UPDATE, DELETE
    ON ALL TABLES IN SCHEMA public TO "${app}";
ALTER DEFAULT PRIVILEGES FOR ROLE "${owner}" IN SCHEMA public
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "${app}";

GRANT USAGE, SELECT
    ON ALL SEQUENCES IN SCHEMA public TO "${app}";
ALTER DEFAULT PRIVILEGES FOR ROLE "${owner}" IN SCHEMA public
    GRANT USAGE, SELECT ON SEQUENCES TO "${app}";
SQL
}

# Read the config, skipping comments and blank lines.
while read -r db owner owner_pw app app_pw _rest; do
	[[ -z "${db:-}" || "${db:0:1}" == "#" ]] && continue
	if [[ -z "${owner:-}" || -z "${owner_pw:-}" || -z "${app:-}" || -z "${app_pw:-}" ]]; then
		echo "10-provision: malformed row for db '${db}' (need 5 columns) — skipping." >&2
		continue
	fi
	echo "10-provision: provisioning '${db}' (owner=${owner}, app=${app})."
	ensure_role "$owner" "$owner_pw"
	ensure_role "$app" "$app_pw"
	ensure_database "$db" "$owner"
	grant_app_privileges "$db" "$owner" "$app"
done < "$CONF"

echo "10-provision: done."
