# VM Infrastructure (swe.fm.tul.cz)

VM-level stacks that are **independent of any single app**, so the box can host several
apps (Student Projects Catalogue now, a wiki later, …) behind **one domain with
path-based routing** on **one shared PostgreSQL**.

```
infra/vm/
  edge/      # Caddy — owns :80/:443 + TLS for the whole VM, routes by URL path
  data/      # shared PostgreSQL — one database + DML role per app, not published on a host port
  spc/       # Student Projects Catalogue — PROD stack (backend + frontend), no host ports
  spc-dev/   # Student Projects Catalogue — DEV stack (isolated DB, /dev prefix, own cookies)
```

Each stack is its own Docker Compose project. They communicate over two **external**
Docker networks created once on the host:

| Network | Joined by | Purpose |
|---------|-----------|---------|
| `edge`  | Caddy + app web/api services | public traffic → apps |
| `data`  | Postgres + app **backend** services | apps → database (proxy has no DB access) |

Bring-up order: **data → edge → app stacks**.

## Prerequisites
- Docker + Docker Compose v2 (`docker compose version`).
- DNS: `swe.fm.tul.cz` → this VM's public IP (already the case: `147.230.21.225`).
- Inbound TCP **80** and **443** reachable from the internet (needed for Let's Encrypt).

## One-time host setup
```bash
docker network create edge
docker network create data
```

## 1. Bring up the shared database
Each database has its **own** owner role (DDL, for migrations) and app role (DML, for the
running backend), so prod and dev — and any future app — are fully isolated.

```bash
cd infra/vm/data
cp .env.example .env                       # superuser password (bootstrap + backups only)
cp provision.conf.example provision.conf   # per-database owner/app role passwords
docker compose up -d
docker compose ps                          # expect "healthy"
```
Verify roles and databases were created (first start only):
```bash
SU=spc_superadmin   # whatever you set as POSTGRES_USER
docker compose exec postgres psql -U "$SU" -d postgres -c '\du'   # spc_prod_owner/app + spc_dev_owner/app
docker compose exec postgres psql -U "$SU" -d postgres -c '\l'    # student_projects + _dev, correct owners
# Prove isolation — the dev app role must NOT reach the prod DB:
docker compose exec postgres psql -U spc_dev_app -d student_projects -c 'select 1'   # expect: permission denied
```
> Roles and databases are provisioned by `init/10-provision-databases.sh` from
> `provision.conf`. This runs **only on first start** (empty volume). After editing
> `.env`/`provision.conf` on an already-initialised volume, recreate with
> `docker compose down -v` (destroys data — fine before the real data import).
>
> The app stacks (added later) build their DSNs from these roles: the prod backend uses
> `spc_prod_app` (runtime) + `spc_prod_owner` (migrations) against `student_projects`; the
> dev backend uses the `spc_dev_*` pair against `student_projects_dev`.

## 2. Bring up the edge proxy
```bash
cd ../edge
docker compose up -d
docker compose logs -f caddy   # watch for "certificate obtained successfully"
```

## 3. Verify TLS (run from OFF-CAMPUS, not from the VM)
```bash
curl -svI https://swe.fm.tul.cz        # must show a valid Let's Encrypt cert
curl https://swe.fm.tul.cz/healthz     # -> ok
curl -sI http://swe.fm.tul.cz          # -> 308 redirect to https
```
If issuance fails, check `docker compose logs caddy`. The usual cause is inbound **80**
being blocked; Caddy automatically falls back to the TLS-ALPN-01 challenge on **443**, so
ensure at least one of the two ports is reachable.

> The edge routes by path: `/projects/` → prod frontend, `/api/` → prod backend,
> `/dev/projects/` → dev frontend, `/dev/api/` → dev backend, `/` → `/projects/`. These
> only respond once the app stacks below are up.

## 4. Bring up the SPC app stacks
Build locally for the first manual bring-up (CI publishes SHA-tagged images later). Run the
migration job (owner/DDL role) **before** starting the services.

```bash
# PRODUCTION
cd ../spc
cp .env.example .env          # set DSNs (spc_prod_* roles), JWT_SECRET, SMTP password
IMAGE_TAG=local docker compose build
docker compose --profile migrate run --rm spc-migrate-prod   # alembic upgrade head
docker compose up -d

# DEVELOPMENT
cd ../spc-dev
cp .env.example .env          # set DSNs (spc_dev_* roles), JWT_SECRET, SMTP password
IMAGE_TAG=local docker compose build
docker compose --profile migrate run --rm spc-migrate-dev
docker compose up -d
docker compose run --rm spc-backend-dev python seed.py        # optional dev seed data
```

Verify end-to-end over HTTPS (from a browser):
- `https://swe.fm.tul.cz/projects/` loads, OTP login works (email via `smtp.tul.cz`), and
  `/api/v1/...` calls return 200 with a `session` cookie set.
- `https://swe.fm.tul.cz/dev/projects/` loads and uses the `session_dev` cookie — logging
  into dev does **not** drop the prod session.

> Prod starts with an empty database; real data is imported from Azure in the final
> migration step (see `docs/AZURE_DB_MIGRATION.md`). Do not run `seed.py` against prod.

## Backups
`data/backup.sh` writes a compressed dump per database to `data/backups/` and prunes old
ones. Add a nightly cron entry (as the deploy user):
```
30 2 * * * cd /path/to/infra/vm/data && ./backup.sh >> backups/backup.log 2>&1
```
Restore a database (as the superuser set in `.env`):
```bash
docker exec -i data-postgres pg_restore -U spc_superadmin -d student_projects \
  --clean --if-exists -1 < backups/student_projects-YYYYmmdd-HHMMSS.dump
```

## CI/CD (automated deploys)

Deploys are driven by GitHub Actions (`.github/workflows/`), not by building on the VM.

- **`Deploy to VM (Dev)`** (`deploy-dev.yml`) — on every push to `main`, builds three
  SHA-tagged images and pushes them to GHCR:
  `ghcr.io/ljezek/tul-psi/backend:<sha>`, `frontend:<sha>-dev`, `frontend:<sha>-prod`
  (all three every push, so any SHA is promotable). It then SSHes to the VM and redeploys the
  **dev** stack: `git checkout <sha>` → `docker compose pull` → `spc-migrate-dev` →
  `up -d` → reload Caddy.
- **`Promote to Prod`** (`promote-to-prod.yml`) — **manual** `workflow_dispatch`; paste the
  green dev `sha`. Runs the E2E suite as a gate, then (if the `prod` GitHub environment has
  required reviewers, after approval) redeploys the **prod** stack from the *same* images and
  smoke-tests `https://swe.fm.tul.cz/projects/`.

### Required GitHub repo secrets
| Secret | Value |
|--------|-------|
| `VM_SSH_HOST` | `swe.fm.tul.cz` |
| `VM_SSH_USER` | deploy user on the VM |
| `VM_SSH_KEY` | that user's **private** SSH key (public key in `~/.ssh/authorized_keys`) |
| `VM_SSH_PORT` | optional, defaults to `22` |
| `VM_REPO_PATH` | path to this repo's checkout on the VM, e.g. `~/tul-psi` |

GHCR pulls on the VM use the workflow's ephemeral `GITHUB_TOKEN` (passed over SSH) — no
long-lived token to manage. Optionally create a `prod` GitHub **environment** with required
reviewers to gate promotion.

### VM prerequisites for CI deploys (one-time)
- A git checkout of this repo at `VM_REPO_PATH`, with each stack's `.env` and
  `infra/vm/data/provision.conf` already configured (these are gitignored and survive
  `git checkout`).
- The deploy user is in the `docker` group and the VM has outbound access to `ghcr.io`.

## Next steps (later)
- **Observability:** a shared `observability/` stack (Jaeger/Prometheus/Grafana) behind
  edge auth; then set `OTEL_EXPORTER_OTLP_ENDPOINT` in the app `.env` files.
- **Data migration:** import the Azure database into the shared Postgres (see
  `docs/AZURE_DB_MIGRATION.md`), then cut over and decommission Azure.
