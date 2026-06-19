#!/usr/bin/env bash
# Nightly backup of every application database in the shared Postgres container.
#
# Produces a compressed custom-format dump per database (restorable with pg_restore) and
# prunes dumps older than $RETENTION_DAYS. Intended to be run from the host via cron.
#
# Example crontab line (run as the deploy user, 02:30 daily):
#   30 2 * * * cd /opt/stacks/data && ./backup.sh >> backups/backup.log 2>&1
#
# Restore (see infra/vm/README.md):
#   docker exec -i data-postgres pg_restore -U <admin> -d <db> --clean --if-exists -1 < dump

set -euo pipefail

cd "$(dirname "$0")"

# shellcheck disable=SC1091
set -a; [[ -f .env ]] && . ./.env; set +a

CONTAINER=${BACKUP_CONTAINER:-data-postgres}
RETENTION_DAYS=${RETENTION_DAYS:-14}
OUT_DIR="$(dirname "$0")/backups"
TS=$(date +%Y%m%d-%H%M%S)

mkdir -p "$OUT_DIR"

# All app databases = primary + extras.
DATABASES="${POSTGRES_DB}"
if [[ -n "${EXTRA_DATABASES:-}" ]]; then
	IFS=',' read -ra EXTRA <<< "$EXTRA_DATABASES"
	for d in "${EXTRA[@]}"; do DATABASES="$DATABASES $(echo "$d" | xargs)"; done
fi

for db in $DATABASES; do
	out="$OUT_DIR/${db}-${TS}.dump"
	echo "$(date -Is) backing up '${db}' -> ${out}"
	docker exec "$CONTAINER" pg_dump -U "$POSTGRES_ADMIN_USER" -d "$db" -F c > "$out"
done

echo "$(date -Is) pruning dumps older than ${RETENTION_DAYS} days"
find "$OUT_DIR" -name '*.dump' -type f -mtime "+${RETENTION_DAYS}" -delete

echo "$(date -Is) backup complete"
