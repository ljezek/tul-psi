# 🤖 Gemini CLI Infrastructure Prompt

Act as a Senior Azure DevOps Engineer. I need to implement a "BigTech" grade infrastructure and CI/CD setup for a project called "Student Projects Catalogue (SPC)". 

**Context:**
- **Frontend:** React SPA (Vite).
- **Backend:** Python FastAPI.
- **Azure Region:** polandcentral.
- **Multi-Environment Resource Groups:**
  1. `rg-spc-shared-pl` (Shared services: VNet, Private DNS, Database, Container Registry).
  2. `rg-spc-dev-pl` (Dev environment: App-specific compute and monitoring).
  3. *(Future: `rg-spc-prod-pl` follows the same pattern as Dev).*

**Task 1: Infrastructure as Code (Bicep)**
Generate three modular Bicep files in the `/infrastructure` directory. Every resource group must have its own Log Analytics Workspace (LAW) for isolation:
1. `shared.bicep` (`rg-spc-shared-pl`): 
   - VNet, Private DNS Zone, Basic ACR.
   - PostgreSQL Flexible Server (`Standard_B1ms`) with Entra ID auth.
   - Shared Log Analytics Workspace for infrastructure logs (VNet flow logs, DB diagnostics).
2. `monitoring-base.bicep` (Module):
   - Creates a Log Analytics Workspace and an Application Insights instance.
3. `dev.bicep` (`rg-spc-dev-pl`): 
   - Deploys the `monitoring-base.bicep` for isolated dev observability.
   - Container App Environment injected into the shared VNet.
   - Backend Container App (with an OTel sidecar using `otel-collector-config.yaml`).
   - Azure Static Web App for the frontend.

**Task 2: GitHub Actions Workflows**
Generate two YAML workflows in `.github/workflows/`:
1. `frontend-dev.yml`: Build the React app and deploy to Azure Static Web Apps in the Dev RG.
2. `backend-dev.yml`: 
   - Use **OIDC (Azure Login)**.
   - Build and push the Docker image to ACR.
   - **Database Migrations:** Trigger an Azure Container App Job to run `alembic upgrade head` within the VNet. The job must use Managed Identity for DB access.
   - Update the Backend Container App with the new image.

**Requirements:**
- Use **Zero-Trust** (no passwords; use Managed Identity/Entra ID).
- Every stack (Shared and Dev) must be monitored via isolated Application Insights and LAW.
- The Backend Bicep must set `minReplicas: 0` for cost saving.
- Output clean, modular code with comments explaining the BigTech architectural choices.