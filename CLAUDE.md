# CLAUDE.md — Student Projects Catalogue (SPC)

This file gives Claude Code persistent context about infrastructure architecture, deployment
behaviour, and known gotchas. For the full project overview see [GEMINI.md](GEMINI.md); for
AI coding mandates (test/lint/style rules) see [AGENTS.md](AGENTS.md); for data model, API
contracts, and sequence diagrams see [docs/DESIGN.md](docs/DESIGN.md).

---

## ⚡ Quick-Reference Commands

| Task | Command | Directory |
|------|---------|-----------|
| Start local backend | `./start.sh --reload` | `backend/` |
| Run backend tests | `python -m pytest` | `backend/` |
| Lint + format | `ruff check . && ruff format .` | `backend/` |
| Start frontend | `npm run dev` | `frontend/` |
| Run frontend tests | `npm test` | `frontend/` |
| Generate migration | `alembic revision --autogenerate -m "..."` | `backend/` |
| Apply migrations | `alembic upgrade head` | `backend/` |
| Re-seed local DB | `python seed.py --reset` | `backend/` |
| Start local infra | `docker compose up -d` | repo root |

---

## ☁️ Cloud vs Local: Critical Differences

### `start.sh` is LOCAL ONLY
The `Dockerfile` CMD is `uvicorn main:app` directly — `start.sh` is **never called** in the
cloud container. It exists only as a local dev convenience that runs migrations and seeding
before uvicorn. Do not assume cloud behaviour mirrors it.

### Seeding in the cloud
Seeding is the responsibility of the ACA migration job (`job-spc-{env}-migrate`), whose
container command is:
```
/bin/sh -c "alembic upgrade head && python seed.py"
```
Both `DATABASE_MIGRATION_URL` and `DATABASE_URL` are set on the job so `seed.py` can connect.
`seed.py` is idempotent — it checks `SELECT COUNT(*) FROM user` and skips if data already exists.

### Scale-to-zero
`minReplicas: 0` — the backend Container App does **not** start until the first HTTP request
arrives. Do not assume the app is running just because it was deployed.

---

## 🏗️ Infrastructure Architecture

### Bicep layout

```
infrastructure/
  shared.bicep            — ACR, VNet (snet-dev/prod/db/scripts), PostgreSQL server, storage
  environment.bicep       — top-level orchestrator; passes params into modules below
  modules/
    compute.bicep         — ACA environment, backend app, migration job, pgAdmin app, SWA
    database-bootstrap.bicep — deploymentScript (ACI inside VNet) that creates DB roles
    monitoring.bicep      — Log Analytics workspace + Application Insights (per env)
    network.bicep         — subnet definitions
    database.bicep        — PostgreSQL Flexible Server config
    acr.bicep / acr-role.bicep — Container Registry + pull-role assignments
```

### DB role split (principle of least privilege)

| Role | Identity | Privileges | Used by |
|------|----------|-----------|---------|
| `id-spc-{env}-migrator` | User-assigned MI | DDL + DML (schema owner) | Migration ACA Job |
| `id-spc-{env}-app` | User-assigned MI | DML only (SELECT/INSERT/UPDATE/DELETE) | Running backend |
| `{developerEmail}` | Entra ID user | Full access | pgAdmin debugging |

DML grants for the `app` role are set via `ALTER DEFAULT PRIVILEGES FOR ROLE migrator`, so they
apply automatically to every table Alembic creates.

### Key Bicep parameters

| Parameter / Variable | Location | Purpose |
|---------------------|----------|---------|
| `deployDebugTools` | `environment.bicep` param | `true` for `dev` only; gates pgAdmin ACA |
| `deployPgadminAuth` | `compute.bicep` var | `deployDebugTools && !empty(clientId) && !empty(secret)` — EasyAuth only when both GitHub secrets are set |
| `pgadminAadClientId` | `compute.bicep` param | App Registration client ID for EasyAuth |
| `pgadminAadClientSecret` | `compute.bicep` param (`@secure`) | Client secret for EasyAuth |

---

## 🚀 CI/CD Pipeline Map

| Workflow | Trigger | What it does |
|----------|---------|--------------|
| `infrastructure.yml` | push to `infrastructure/**` or manual | Deploys shared + env Bicep |
| `backend-dev.yml` | push to `backend/**` on `main` | Build image → run migration+seed job (polls for completion) → update ACA |
| `frontend-dev.yml` | push to `frontend/**` on `main` | Deploy SPA to Azure Static Web App |

**Migration job wait pattern**: `az containerapp job start` returns an execution name; the
workflow polls `az containerapp job execution show` every 10 s (max 6 min) before updating the
backend Container App.

---

## 🔧 Fresh Environment Setup Checklist

Full commands are in [`infrastructure/README.md`](infrastructure/README.md). Summary:

1. Register `Microsoft.ContainerInstance` provider (once per subscription)
2. Create resource groups + GH service principal + role assignments
3. Create `id-spc-shared-db-setup` identity + Graph API permissions
4. Configure OIDC federated credentials for `main` branch, `dev` env, and pull requests
5. Set GitHub repo-level secrets (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, etc.)
6. Create `dev` + `prod` GitHub environments with environment-specific secrets
7. **Trigger Infrastructure (run 1)** — all Azure resources created; pgAdmin without EasyAuth
8. Run Step 6 script from infra README → creates pgAdmin App Registration → add
   `PGADMIN_AAD_CLIENT_ID` + `PGADMIN_AAD_CLIENT_SECRET` to the `dev` GitHub environment
9. **Trigger Infrastructure (run 2)** — pgAdmin EasyAuth activates
10. Trigger Backend deployment → Trigger Frontend deployment
