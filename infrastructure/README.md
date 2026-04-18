# 🚀 Student Projects Catalogue (SPC) Deployment Guide

This project uses **Azure Bicep** for Infrastructure-as-Code (IaC) and **GitHub Actions** for CI/CD. All deployments use **OpenID Connect (OIDC)** for a zero-secret security model.

## Context

We have 3 GitHub workflows for deployment:
1. [Infrastructure](../.github/workflows/infrastructure.yml): creates/updates the Azure resources (but not the application code/data).
2. [Frontend](../.github/workflows/frontend-dev.yml): builds and pushes a new version of the frontend code to the Azure Static Web App.
3. [Backend](../.github/workflows/backend-dev.yml): builds backend Docker image, runs DB migrations and pushes a new version of the backend image to the created Azure Container App.

See the [Infrastructure section](../docs/DESIGN.md#️-infrastructure--deployment) in the DESIGN document for details about the created Azure resources.

## 1. Prerequisites

1.  **Azure Subscription:** An active Azure subscription.
2.  **GitHub Repository:** The code must be pushed to a GitHub repository.
3.  **Azure CLI:** Installed locally for the initial setup.
4.  **Admin Rights:** You must have permissions to create **Entra ID Role Assignments** (like "Directory Readers").

---

## 2. Initial Security Setup (OIDC & DB Bootstrap)

You must grant GitHub permission to access your Azure subscription and set up the identity that will bootstrap your database.

### Step 1: Create Resource Groups & GH Service Principal
Run this locally to create the core resources:

```bash
# Set your variables
SUBSCRIPTION_ID="your-subscription-id"
TENANT_ID="your-tenant-id"
APP_NAME="gh-actions-spc"

az login

# 1. Create Resource Groups
for rg in "rg-spc-shared-pl" "rg-spc-dev-pl" "rg-spc-prod-pl"; do
  az group create --name "$rg" --location polandcentral
done

# 2. Create the GH App Registration
az ad app create --display-name $APP_NAME
APP_ID=$(az ad app list --display-name $APP_NAME --query "[0].appId" -o tsv)
APP_OBJECT_ID=$(az ad app show --id $APP_ID --query id -o tsv)

# 3. Create the Service Principal
az ad sp create --id $APP_ID
SP_OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)

# 4. Assign roles to the SP for each RG
for rg in "rg-spc-shared-pl" "rg-spc-dev-pl" "rg-spc-prod-pl"; do
  az role assignment create --role Contributor --assignee $SP_OBJECT_ID --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$rg"
  az role assignment create --role "User Access Administrator" --assignee $SP_OBJECT_ID --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$rg"
done
```

### Step 2: Create DB Bootstrap Identity (Required for VNet DB Access)
Because the DB is in a VNet, Bicep uses a temporary script to create roles. This identity needs "Directory Readers" to look up other Managed Identities.

```bash
# 1. Create the identity in the 'shared' resource group
az identity create -g rg-spc-shared-pl -n id-spc-shared-db-setup

# 2. Get its IDs
SETUP_CLIENT_ID=$(az identity show -g rg-spc-shared-pl -n id-spc-shared-db-setup --query clientId -o tsv)
SETUP_SP_OBJECT_ID=$(az ad sp show --id $SETUP_CLIENT_ID --query id -o tsv)

# 3. Assign 'Directory Readers' role (Scope: Subscription or Tenant)
# This allows the identity to find 'id-spc-dev-migrator' etc. during DB setup.
az ad role assignment create --role "Directory Readers" --assignee-object-id $SETUP_SP_OBJECT_ID --scope "/"
```

### Step 3: Configure Federated Identity Credentials
Links your GitHub repository to the Azure App. Replace `ljezek/tul-psi` with your actual repo path.

```bash
# For the main branch (Required for Infrastructure & Backend workflows)
az ad app federated-credential create --id $APP_OBJECT_ID --parameters '{
  "name": "gh-actions-spc-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:ljezek/tul-psi:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'

# For the 'dev' environment (Required for Frontend & Environment-specific workflows)
az ad app federated-credential create --id $APP_OBJECT_ID --parameters '{
  "name": "gh-actions-spc-dev",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:ljezek/tul-psi:environment:dev",
  "audiences": ["api://AzureADTokenExchange"]
}'

# For Pull Requests
az ad app federated-credential create --id $APP_OBJECT_ID --parameters '{
  "name": "gh-actions-spc-pr",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:ljezek/tul-psi:pull_request",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

### Step 4: Set GitHub Secrets & Variables
In your GitHub repository, go to **Settings > Secrets and variables > Actions**.

| Name | Description | Source |
| :--- | :--- | :--- |
| `AZURE_CLIENT_ID` | The `appId` from Step 1. | Azure Portal |
| `AZURE_TENANT_ID` | Your Azure Tenant ID. | Azure Portal |
| `AZURE_SUBSCRIPTION_ID` | Your Azure Subscription ID. | Azure Portal |
| `GEMINI_API_KEY` | API key for Gemini AI integration. | Google AI Studio |
| `JWT_SECRET` | Secret key for signing session cookies. | [backend/.env](../backend/.env.example) |
| `VITE_LOGIC_APP_FEEDBACK_URL` | The URL for your Logic App feedback. | Azure Portal |

### Step 5: Configure GitHub Environments
To manage differences between `dev` and `prod`:
1.  Go to **Settings > Environments**.
2.  Create two environments: `dev` and `prod`.
3.  Add environment-specific secrets (like `JWT_SECRET` and `VITE_LOGIC_APP_FEEDBACK_URL`) directly to these environments.

---

## 2.5 Local Validation & Testing

Validate your Bicep files locally before pushing to avoid deployment failures.

### 1. Static Analysis (Linting)
```bash
az bicep build --file infrastructure/shared.bicep --outfile infrastructure/dist/shared.json
az bicep build --file infrastructure/environment.bicep --outfile infrastructure/dist/environment.json
```

### 2. Pre-flight Validation
```bash
# Validate shared infrastructure
az deployment group validate \
  --resource-group rg-spc-shared-pl \
  --template-file infrastructure/shared.bicep

# Validate environment-specific infrastructure (e.g., dev)
# Note: Get the full subnetId from the outputs of your 'shared' deployment
az deployment group validate \
  --resource-group rg-spc-dev-pl \
  --template-file infrastructure/environment.bicep \
  --parameters env=dev \
               subnetId="/subscriptions/ca830bff-0330-40f0-8d49-a18d5db67e9c/resourceGroups/rg-spc-shared-pl/providers/Microsoft.Network/virtualNetworks/vnet-spc-shared/subnets/snet-dev" \
               acrName="acrtulspc" \
               acrResourceGroup="rg-spc-shared-pl" \
               dbHost="psql-spc-shared.postgres.database.azure.com" \
               dbName="spc_dev" \
               jwtSecret="not-a-secret-just-for-validation-purposes"
```

---

## 3. Deployment Sequence

The first deployment follows an automated sequence.

1.  **Trigger Infrastructure:** Go to **Actions > Infrastructure Deployment** and run it for `dev`. 
    *   Bicep will adopt the `id-spc-shared-db-setup` identity created in Section 2.
    *   The `deploymentScript` will automatically create the DB roles for `dev` inside the VNet.
2.  **Trigger Backend:** Go to **Actions > Backend Deployment (Dev)**.
3.  **Trigger Frontend:** Go to **Actions > Frontend Deployment (Dev)**.

---

## 4. Architecture Notes

- **Zero-Trust:** All services use **Managed Identities**.
- **Automated Bootstrap:** A Bicep `deploymentScript` handles initial PostgreSQL role creation (`id-spc-dev-migrator` and `id-spc-dev-app`) within the private VNet.
- **Scale-to-Zero:** The backend is configured with `minReplicas: 0` to minimize costs.
- **Permission Split:** The Migrator identity has DDL rights (Alembic), while the App identity is restricted to DML operations.
