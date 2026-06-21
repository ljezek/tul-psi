# Azure → VM Database Migration Guide

How to copy the production data out of the Azure-hosted PostgreSQL (inside a private VNet)
into the new self-hosted database on `swe.fm.tul.cz`.

## Target environment (read this first)

On the VM, PostgreSQL does **not** run on the host — it is the `data-postgres` container
(`infra/vm/data/docker-compose.yml`, `postgres:17-alpine`) on the internal `data` Docker
network with **no published host port**. So you cannot `pg_restore -h localhost`; restores go
through `docker exec -i data-postgres ...`.

There is also a **least-privilege role split** per database
(`infra/vm/data/provision.conf`):

| Role | Privileges | Used by |
|------|-----------|---------|
| `${POSTGRES_USER}` (superuser) | everything; owns no app data | bootstrap + backups |
| `spc_prod_owner` | DDL + DML, owns `student_projects` | Alembic migrations |
| `spc_prod_app` | DML only | the running backend |

Two consequences for the restore:
- The Azure dump references **Azure role names that don't exist here** → dump and restore with
  `--no-owner --no-privileges`, and make the objects owned by `spc_prod_owner` via
  `--role=spc_prod_owner`.
- The prod DB **already contains the empty schema + `alembic_version`** created by the initial
  migration run (`spc-migrate-prod`). The restore must clear it first (`--clean --if-exists`).

> `$POSTGRES_USER` below is the superuser from `infra/vm/data/.env`. `docker exec` connects
> over the container's local socket (`trust`), so no password is needed for these commands.

## Prerequisites
- Access to the Azure Portal; permission to create a small VM in the DB's VNet.
- Hostname, username, password for the Azure PostgreSQL instance.
- SSH access to `swe.fm.tul.cz`.

## Step 0 — Pre-flight: record Azure's Alembic version
After the restore we run `alembic upgrade head` to apply any migrations newer than Azure's.
That only works if Azure's recorded revision is one of the revisions in
`backend/migrations/versions/` (linear history, current head `f1a2b3c4d5e6`). Capture it from
the jumpbox once connectivity is up:
```bash
psql -h <AZURE_DB_HOST> -U <AZURE_USER> -d <AZURE_DB> -tAc "SELECT version_num FROM alembic_version;"
```
If the value is unknown or *ahead* of `f1a2b3c4d5e6`, **stop** and reconcile the migration
history before importing.

## Step 1 — Create a temporary jumpbox
1. In the Azure Portal create an **Ubuntu Server 22.04 LTS** VM.
2. **Networking:** same **Virtual Network** / a subnet with connectivity to the Azure
   PostgreSQL instance.
3. **Public IP + SSH (22)** so you can connect to it.

## Step 2 — Install the PostgreSQL client (on the jumpbox)
```bash
sudo apt-get update
sudo apt-get install -y postgresql-client   # client major version >= the Azure server
```

## Step 3 — Dump the Azure database
Custom-format dump, stripping Azure's role/ownership references:
```bash
pg_dump -h <AZURE_DB_HOST> -U <AZURE_USER> -d <AZURE_DB> \
  -F c --no-owner --no-privileges -f spc_prod.dump
```
*Enter the password when prompted.*

## Step 4 — Transfer the dump to the VM
```bash
scp spc_prod.dump <USER>@swe.fm.tul.cz:/home/<USER>/
```

## Step 5 — Stop the prod backend (on the VM)
Avoid writes/locks during the destructive restore. Leave Postgres running.
```bash
cd infra/vm/spc
docker compose stop spc-backend-prod
```

## Step 6 — Restore into the container
Connect as the **superuser** (so it can `--clean` and create any extensions) but use
`--role=spc_prod_owner` so every restored object ends up **owned by the owner role** —
required for future Alembic migrations to work.
```bash
docker exec -i data-postgres pg_restore \
  -U "$POSTGRES_USER" -d student_projects \
  --role=spc_prod_owner \
  --no-owner --no-privileges \
  --clean --if-exists \
  --single-transaction \
  < /home/<USER>/spc_prod.dump
```
- `--clean --if-exists` drops the empty schema the initial migration created, before restoring.
- `--single-transaction` makes the restore all-or-nothing.

**Fallback:** if the dump contains `CREATE EXTENSION` (or other superuser-only statements) that
error under `SET ROLE`, drop `--single-transaction` so the restore continues, or pre-create the
extension as the superuser first.

## Step 7 — Re-grant the app role
Default privileges only auto-grant on *future* objects created by the owner; the just-restored
objects need an explicit grant. (Same block as `grant_app_privileges()` in
`infra/vm/data/init/10-provision-databases.sh`.)
```bash
docker exec -i data-postgres psql -U "$POSTGRES_USER" -d student_projects <<'SQL'
GRANT USAGE ON SCHEMA public TO spc_prod_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO spc_prod_app;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO spc_prod_app;
SQL
```

## Step 8 — Apply any newer migrations
No-op if Azure was already at `f1a2b3c4d5e6`; otherwise applies the delta to the now-populated
DB. Do **not** run `seed.py` — that is only for an empty database.
```bash
cd infra/vm/spc
docker compose --profile migrate run --rm spc-migrate-prod
```

## Step 9 — Restart the backend
```bash
docker compose start spc-backend-prod   # or: docker compose up -d
```

## Step 10 — Verify
```bash
# Alembic at head
docker exec data-postgres psql -U "$POSTGRES_USER" -d student_projects \
  -tAc "SELECT version_num FROM alembic_version;"        # -> f1a2b3c4d5e6

# Data present
docker exec data-postgres psql -U "$POSTGRES_USER" -d student_projects \
  -c '\dt' -c 'SELECT count(*) FROM "user";'

# The APP role (not the superuser) can read — proves the grants are correct
docker exec data-postgres psql -U spc_prod_app -d student_projects \
  -c 'SELECT count(*) FROM "user";'
```
Then exercise the live app over HTTPS: open `https://swe.fm.tul.cz/projects/`, log in with a
known account (OTP email via `smtp.tul.cz`), and confirm real projects/users render. Compare a
couple of row counts against the Azure source to confirm a complete copy.

## Step 11 — Cleanup
1. Once verified, **delete the temporary Azure jumpbox VM** to stop costs.
2. Keep one final `pg_dump` archived off-box before decommissioning the Azure database.
