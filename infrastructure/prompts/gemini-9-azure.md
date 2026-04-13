# 🤖 Gemini CLI Infrastructure Prompt (Refined)

Act as a Senior Azure DevOps Engineer. Implement a modular, "BigTech" grade infrastructure and CI/CD setup for the "Student Projects Catalogue (SPC)".

**Context:**
- **Frontend:** React SPA (Vite).
- **Backend:** Python FastAPI.
- **Azure Region:** polandcentral.
- **Resource Strategy:**
  1. `rg-spc-shared-pl`: Shared Infrastructure (Network, Database, Registry).
  2. `rg-spc-dev-pl`: App Stack (Compute, Per-env Monitoring).

---

### Task 1: Modular Infrastructure as Code (Bicep)

Create a modular Bicep structure in `/infrastructure`. Use **Zero-Trust** (Managed Identities/Entra ID) and **Scale-to-Zero** (minReplicas: 0).

#### 1.1 Shared Infrastructure (`shared.bicep`)
- **Networking:** VNet (`vnet-spc-shared`) with subnets: `snet-db`, `snet-dev`, `snet-prod`.
- **Registry:** Azure Container Registry (Basic SKU).
- **Database:** PostgreSQL Flexible Server with **Entra ID-only authentication**.
- **Monitoring (Shared):** LAW for VNet/DB platform logs.

#### 1.2 Environment Stack (`environment.bicep`)
A parameter-driven module for Dev/Prod isolation:
- **Monitoring (Per-Env):** Isolated LAW and Application Insights instance.
- **Compute (ACA):**
  - **Backend App Identity:** System-assigned Managed Identity with **DML-only permissions** (SELECT, INSERT, UPDATE, DELETE).
  - **Migration Job Identity:** Dedicated System-assigned Managed Identity with **DDL permissions** (Entra ID Admin on PostgreSQL) to run Alembic migrations.
  - **Backend App:** Container App with OTel sidecar and `minReplicas: 0`.
  - **Migration Job:** ACA Job to run `alembic upgrade head`. Must also run a SQL bootstrap script to ensure the Backend App Identity is registered in Postgres with correct DML-only roles.
- **Frontend (SWA):** Azure Static Web App (Free Tier).

---

### Task 2: GitHub Actions Workflows

Generate three YAML workflows in `.github/workflows/`. **All workflows must use OIDC (Azure Login) for zero-secret deployments.**

#### 2.1 `infrastructure.yml`
- Trigger: Changes to `infrastructure/` or manual (`workflow_dispatch`).
- Action: Deploy `shared.bicep` and `environment.bicep` (Dev/Prod).

#### 2.2 `frontend-dev.yml`
- Trigger: Changes to `frontend/`.
- Action: Build the Vite app. Deploy to SWA using `az staticwebapp deploy` (via OIDC/RBAC) instead of deployment tokens.

#### 2.3 `backend-dev.yml`
- Trigger: Changes to `backend/`.
- **Phase 1: Build:** Build and push the Docker image to ACR.
- **Phase 2: Migrations:** Trigger the ACA Migration Job (using its DDL Identity).
- **Phase 3: Deploy:** Update the Backend Container App with the new image tag.

---

### Implementation Requirements:
- **No Secrets:** Strictly use OIDC for GitHub and Managed Identities for all Azure-to-Azure communication.
- **Permission Split:** Ensure the Bicep templates and the Migration Job explicitly handle the distinction between DDL (Migrator) and DML (App) roles as defined in `database/README.md`.
- **Clean Code:** Use Bicep `params` and `output` to link the Shared and Environment stacks.
