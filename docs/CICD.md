# CI/CD Pipeline Guide

This document covers the full pipeline topology, per-change-type behaviour, and operational runbooks for the Student Projects Catalogue (SPC) project.

For Azure resource architecture see [DESIGN.md](DESIGN.md). For the initial Azure setup see [infrastructure/README.md](../infrastructure/README.md).

---

## Pipeline Overview

### Trigger Chain

```
Push to main
  ├─ backend/**   → Backend Deployment (Dev)  ─┐
  ├─ frontend/**  → Frontend Deployment (Dev) ──┼─→ E2E Tests ─→ Promote to Production
  ├─ infrastructure/** → Infrastructure Deployment (dev only; prod is manual)
  └─ data/**      → Validate JSON (PR gate only)

Pull Request to main
  ├─ backend/**   → Backend Gate (pytest + ruff)
  ├─ frontend/**  → Frontend Gate (vitest + eslint) + Preview SWA deploy
  ├─ infrastructure/** → Infrastructure Gate (az bicep build)
  └─ data/**      → Validate JSON
  (no app changes: skip workflows satisfy branch-protection checks)
```

### Workflows

| Workflow file | Trigger | Target |
|---|---|---|
| `backend.yml` | PR (backend/**) | Branch protection gate — no deployment |
| `frontend.yml` | PR (frontend/**) | Branch protection gate + SWA preview |
| `infrastructure-pr.yml` | PR (infrastructure/**) | Branch protection gate (bicep build) |
| `backend-dev.yml` | Push to main (backend/**) or manual | Dev backend Container App |
| `frontend-dev.yml` | Push to main (frontend/**) or manual | Dev Static Web App |
| `infrastructure.yml` | Push to main (infrastructure/**) or manual | Dev infra (auto) / Prod infra (manual) |
| `e2e.yml` | After backend-dev or frontend-dev completes | Local docker-compose stack |
| `promote-to-prod.yml` | After E2E passes or manual | Prod backend + prod SWA |

---

## Behaviour by Change Type

| Change type | Dev auto-deploy | E2E triggered | Backend promoted to prod | Frontend promoted to prod |
|---|---|---|---|---|
| **Backend only** | `backend-dev` runs | Yes | Yes | Yes (rebuilt from same SHA — same output) |
| **Frontend only** | `frontend-dev` runs | Yes | Skipped cleanly (no ACR image for this SHA) | Yes |
| **All parts** | Both run | Yes (concurrency keeps one E2E) | Yes | Yes |
| **Infrastructure only** | `infrastructure.yml` runs for dev | No | No | No — prod infra is manual |
| **Data / other** | No | No | No | No |

### Why frontend rebuilds on backend-only changes

`VITE_API_URL` is compiled into the JavaScript bundle at build time. The dev build points at the dev backend. The promote workflow always rebuilds the frontend from source with the prod backend URL. On a backend-only change the source is identical to the previous prod frontend build, so the output is functionally the same — it is a harmless but necessary rebuild.

### Infrastructure changes and prod

Infrastructure changes are automatically deployed to dev. **Prod infrastructure is never auto-deployed.** After merging infra changes, trigger the prod deployment manually:

1. Go to **Actions → Infrastructure Deployment → Run workflow**
2. Set `environment` to `prod`
3. Monitor and verify in the Azure Portal

---

## Automatic Promotion: How It Works

After E2E tests pass on `main`, `promote-to-prod.yml` runs five jobs in sequence:

```
gate
  └── verify-dev
        ├── deploy-backend-prod  (parallel)
        └── deploy-frontend-prod (parallel)
              └── smoke-test
```

### gate
Runs without a GitHub environment (uses the main-branch OIDC credential). Performs three checks:

1. **E2E conclusion**: for `workflow_run` triggers, skips everything if E2E didn't succeed.
2. **SHA regression check**: reads the `promotedSha` Azure tag from `ca-spc-prod-backend`. Uses `git merge-base --is-ancestor` to detect if the incoming SHA is older than what is currently live. Blocks promotion silently if so.
3. **ACR image check**: verifies whether a backend Docker image exists for this SHA. Outputs `has_backend_image=false` for frontend-only commits so the backend job skips cleanly.

### verify-dev
Polls the live `ca-spc-dev-backend` `/health` endpoint. Prod promotion is blocked if dev itself is unhealthy.

### deploy-backend-prod
Promotes the same Docker image that was deployed to dev (no rebuild). Runs Alembic migrations first; if migrations fail, the Container App update is never attempted and the previous image keeps running.

### deploy-frontend-prod
Checks out the exact promoted SHA and rebuilds the frontend with the prod backend URL baked in. Deploys to `swa-spc-prod`.

### smoke-test
Polls prod `/health` with retries. On success, stamps the `promotedSha` tag on `ca-spc-prod-backend` and writes a summary to the GitHub Actions job summary page.

---

## SHA Anti-Regression

The `promotedSha` tag on `ca-spc-prod-backend` records the last SHA that successfully completed a prod smoke test. On every promotion attempt the gate checks:

```
git merge-base --is-ancestor <new-sha> <promoted-sha>
```

If this returns true, the new SHA is an ancestor (i.e. older) of what is already live → promotion is blocked with a clear log message.

**Parallel-PR scenario**: PR1 (all changes) and PR2 (frontend-only) are merged close together. PR2's pipeline is faster and promotes first, stamping its SHA. PR1's SHA is older in git history → gate blocks PR1's promotion. Prod retains PR2's (newer) frontend.

To intentionally bypass (for rollback), use `workflow_dispatch` with `force=true` — see Rollback below.

---

## Manual Operations

### Force-deploy a specific SHA to prod

Use this when you want to deploy a specific commit without waiting for the full pipeline:

1. Go to **Actions → Promote to Production → Run workflow**
2. Enter the full commit SHA in the `sha` field
3. Leave `force` unchecked (unless rolling back — see below)
4. Click **Run workflow** and monitor the run

The SHA must have a corresponding Docker image in ACR (i.e. `backend-dev.yml` must have run for it). For frontend-only SHAs, the backend deploy is skipped automatically.

### Rollback prod

> Alembic down-migrations are not used in this project. Rolling back is only safe if the old code is compatible with the current database schema (i.e. you have not dropped columns or tables). Additive migrations are always safe to roll back.

1. Find the target SHA:
   - `git log --oneline main` — shows recent commits
   - Azure Portal → `ca-spc-prod-backend` → Revisions → check image tag of the previous revision
2. Confirm the image exists in ACR:
   ```bash
   az acr repository show-tags --name <acr-name> --repository backend | grep <short-sha>
   ```
3. Go to **Actions → Promote to Production → Run workflow**
4. Enter the SHA and check **"Skip SHA regression check"** (`force: true`)
5. Click **Run workflow** and monitor

After a successful rollback, `promotedSha` is stamped with the older SHA. Future automatic promotions from E2E will be blocked until a newer commit is merged and its pipeline succeeds.

### Deploy infrastructure to prod

```bash
# Option A: GitHub Actions UI
# Actions → Infrastructure Deployment → Run workflow → environment: prod

# Option B: Azure CLI (for emergency or validation)
az deployment group create \
  --resource-group rg-spc-prod-pl \
  --template-file infrastructure/environment.bicep \
  --parameters env=prod ...
```

### Retrigger a dev deployment manually

Both `backend-dev.yml` and `frontend-dev.yml` support `workflow_dispatch`. Go to **Actions → [Backend|Frontend] Deployment (Dev) → Run workflow**.

---

## Troubleshooting

### "Promote to Production" workflow skipped immediately

**Symptom:** The workflow runs but all jobs except `gate` are skipped. Gate logs show: *"SHA X is older than currently promoted Y"*.

**Cause:** The SHA anti-regression check blocked promotion because another pipeline already promoted a newer commit.

**Fix:** No action needed in most cases — the correct version is already live. If you intended to deploy this specific SHA, use `workflow_dispatch` with `force=true`.

---

### Backend deploy skipped on a full-stack PR

**Symptom:** `deploy-backend-prod` shows as "skipped" even though both backend and frontend changed.

**Cause:** The gate's ACR check found no backend image for this SHA. This usually means `backend-dev.yml` hasn't completed yet, or it failed.

**Fix:**
1. Check whether `backend-dev.yml` completed successfully for this SHA
2. If it failed, fix the issue and re-run via `workflow_dispatch`
3. Once a backend image exists in ACR, use `workflow_dispatch` to promote the SHA manually

---

### "Verify Dev is Healthy" failed

**Symptom:** `verify-dev` exits with *"Dev backend unhealthy"*.

**Cause:** The live dev backend is not responding 200 on `/health`. This could be a bad migration, a container crash-loop, or a transient startup issue.

**Fix:**
1. Check `ca-spc-dev-backend` in the Azure Portal → Log stream
2. Check Application Insights → `ai-spc-dev` for recent exceptions
3. Fix the issue on dev (re-run `backend-dev.yml` if needed)
4. Once dev is healthy, the next E2E run will re-trigger prod promotion automatically, or use `workflow_dispatch`

---

### Migration failed in prod

**Symptom:** `Run Migrations` step fails with logs showing a SQL error.

**Cause:** An Alembic migration was incompatible with the prod database state.

**Fix:**
1. The Container App was NOT updated — the previous version is still running
2. Fix the migration in code and push a new commit
3. The new commit will go through the full pipeline: dev deploy → E2E → prod promotion
4. Do NOT manually run migrations against prod without the pipeline

---

### Smoke test failed after successful deployment

**Symptom:** Both deploy jobs succeeded but `smoke-test` fails after retries.

**Cause:** The backend was deployed but is not healthy — likely a runtime error, misconfigured environment variable, or database connectivity issue.

**Fix:**
1. The `promotedSha` tag was NOT updated (stamp only happens after smoke test passes)
2. Check `ca-spc-prod-backend` → Log stream in the Azure Portal
3. Check Application Insights → `ai-spc-prod` for exceptions
4. If needed, activate the previous Container App revision:
   ```bash
   az containerapp revision list \
     --name ca-spc-prod-backend \
     --resource-group rg-spc-prod-pl \
     --query "[].{name:name, active:properties.active, image:properties.template.containers[0].image}"
   az containerapp revision activate \
     --name ca-spc-prod-backend \
     --resource-group rg-spc-prod-pl \
     --revision <previous-revision-name>
   ```

---

### E2E tests blocked by a cancelled run

**Symptom:** E2E shows as "cancelled" — promote-to-prod was not triggered.

**Cause:** A second push to main cancelled the in-progress E2E run (concurrency: cancel-in-progress: true). Only the most recent E2E run completes.

**Fix:** Wait for the pipeline of the latest commit to complete. If both commits were on the same SHA this is a no-op. If you need to force-promote, use `workflow_dispatch`.

---

## Environment Reference

| Resource | Dev | Prod |
|---|---|---|
| Resource group | `rg-spc-dev-pl` | `rg-spc-prod-pl` |
| Backend Container App | `ca-spc-dev-backend` | `ca-spc-prod-backend` |
| Migration Job | `job-spc-dev-migrate` | `job-spc-prod-migrate` |
| Static Web App | `swa-spc-dev` | `swa-spc-prod` |
| Application Insights | `ai-spc-dev` | `ai-spc-prod` |
| pgAdmin | `ca-spc-dev-pgadmin` | Not deployed |
| Backend min replicas | 0 (scale-to-zero) | 1 (always warm) |
| Log retention | 30 days | 90 days |
| Shared ACR | `rg-spc-shared-pl` | same |
| Shared PostgreSQL | `rg-spc-shared-pl` | same |

### GitHub Environments

| Environment | OIDC subject | Secrets |
|---|---|---|
| `dev` | `repo:ljezek/tul-psi:environment:dev` | `JWT_SECRET`, `VITE_LOGIC_APP_FEEDBACK_URL`, `PGADMIN_AAD_CLIENT_ID`, `PGADMIN_AAD_CLIENT_SECRET` |
| `prod` | `repo:ljezek/tul-psi:environment:prod` | `JWT_SECRET`, `VITE_LOGIC_APP_FEEDBACK_URL` |
| *(main branch)* | `repo:ljezek/tul-psi:ref:refs/heads/main` | Repo-level: `AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`, `GEMINI_API_KEY` |

The `gate` job in `promote-to-prod.yml` uses the main-branch OIDC credential (no `environment:` tag) so it runs automatically without triggering prod environment protection rules.

---

## Adding a New GitHub Environment

When adding the `prod` environment for the first time, you also need an OIDC federated credential:

```bash
APP_OBJECT_ID=$(az ad app list --display-name gh-actions-spc --query "[0].id" -o tsv)
az ad app federated-credential create --id "$APP_OBJECT_ID" --parameters '{
  "name": "gh-actions-spc-prod",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:ljezek/tul-psi:environment:prod",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

See [infrastructure/README.md](../infrastructure/README.md) for the full initial setup checklist.
