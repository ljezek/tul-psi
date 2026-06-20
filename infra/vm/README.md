# VM Infrastructure (swe.fm.tul.cz)

VM-level stacks that are **independent of any single app**, so the box can host several
apps (Student Projects Catalogue now, a wiki later, …) behind **one domain with
path-based routing** on **one shared PostgreSQL**.

```
infra/vm/
  edge/    # Caddy — owns :80/:443 + TLS for the whole VM, routes by URL path
  data/    # shared PostgreSQL — one database + DML role per app, not published on a host port
```

Each stack is its own Docker Compose project. They communicate over two **external**
Docker networks created once on the host:

| Network | Joined by | Purpose |
|---------|-----------|---------|
| `edge`  | Caddy + app web/api services | public traffic → apps |
| `data`  | Postgres + app **backend** services | apps → database (proxy has no DB access) |

> This is **Step 1** of the Azure→VM migration: the foundation only. There are no app
> services wired in yet — the goal here is to prove TLS issuance and a healthy database
> before adding the SPC app stacks.

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
SU=pg_superadmin   # whatever you set as POSTGRES_USER
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

## Backups
`data/backup.sh` writes a compressed dump per database to `data/backups/` and prunes old
ones. Add a nightly cron entry (as the deploy user):
```
30 2 * * * cd /path/to/infra/vm/data && ./backup.sh >> backups/backup.log 2>&1
```
Restore a database (as the superuser set in `.env`):
```bash
docker exec -i data-postgres pg_restore -U pg_superadmin -d student_projects \
  --clean --if-exists -1 < backups/student_projects-YYYYmmdd-HHMMSS.dump
```

## Next steps (later)
- Add SPC app stacks (`spc/`, `spc-dev/`) joining `edge` + `data`, exposing no host ports.
- Extend `edge/Caddyfile` with the `/api`, `/projects`, `/dev/...`, `/grafana` routes.
- Add the shared `observability/` stack (Jaeger/Prometheus/Grafana) behind auth.
