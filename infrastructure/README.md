# 🚀 Student Projects Catalogue (SPC) Deployment Guide

This project uses **Azure Bicep** for Infrastructure-as-Code (IaC) and **GitHub Actions** for CI/CD. All deployments use **OpenID Connect (OIDC)** for a zero-secret security model.

## Context

We have 3 GitHub workflows for deployment:
1. [Infrastructure](../.github/workflows/infrastructure.yml): creates/updates the Azure resources (but not the application code/data).
2. [Frontend](../.github/workflows/frontend-dev.yml): builds and pushes a new version of the frondent code to the Azure Static Web App.
3. [Backend](../.github/workflows/backend-dev.yml): builds backend Docker image, runs DB migrations and pushes a new version of the backend image to the created Azure Container App.

See the [Infrastructure section](../docs/DESIGN.md#️-infrastructure--deployment) in the DESIGN document for details about the created Azure resources.

## 1. Prerequisites

1.  **Azure Subscription:** An active Azure subscription.
2.  **GitHub Repository:** The code must be pushed to a GitHub repository.
3.  **Azure CLI:** Installed locally for the initial setup - we'll use it in Bash (on Windows in WSL).

---

## 2. Initial Security Setup (OIDC)

You must grant GitHub permission to access your Azure subscription without using long-lived secrets.

### Step 1: Create an Entra ID (Active Directory) App
Run this locally to create the application and service principal:

```bash
# Set your variables
SUBSCRIPTION_ID="your-subscription-id"
TENANT_ID="your-tenant-id"
APP_NAME="gh-actions-spc"

az login

# Create the app registration
az ad app create --display-name $APP_NAME

# Get IDs
APP_ID=$(az ad app list --display-name $APP_NAME --query "[0].appId" -o tsv)
APP_OBJECT_ID=$(az ad app show --id $APP_ID --query id -o tsv)

# Create the Service Principal (Identity, instance of the App registration) within the tenant
# This is CRITICAL for login and role assignment
az ad sp create --id $APP_ID
SP_OBJECT_ID=$(az ad sp show --id $APP_ID --query id -o tsv)

# Create resource groups and assign roles to the Service Principal scoped to each Resource Group.
# Note: Roles must be assigned for EACH environment (shared, dev, prod)
# Not assigning roles at Subscription level to follow the Principle of Least Privilege.

# 1. Create Resource Groups
# 2. Assign 'Contributor' and 'User Access Administrator' to the SP for each RG
# User Access Administrator is required for Bicep to create Role Assignments (e.g., AcrPull)
for rg in "rg-spc-shared-pl" "rg-spc-dev-pl" "rg-spc-prod-pl"; do
  az group create --name "$rg" --location polandcentral
  az role assignment create --role Contributor --assignee $SP_OBJECT_ID --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$rg"
  az role assignment create --role "User Access Administrator" --assignee $SP_OBJECT_ID --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$rg"
done
```

### Step 2: Configure Federated Identity Credentials
This links your GitHub repository to the Azure App. This works for `ljezek/tul-psi` repo.

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

# For Pull Requests (Required if not using environments in PRs, or for general PR triggers)
az ad app federated-credential create --id $APP_OBJECT_ID --parameters '{
  "name": "gh-actions-spc-pr",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:ljezek/tul-psi:pull_request",
  "audiences": ["api://AzureADTokenExchange"]
}'
```
### Step 3: Set GitHub Secrets & Variables
In your GitHub repository, go to **Settings > Secrets and variables > Actions**.

#### 🔑 Secrets (Encrypted)
These are sensitive values that must be kept secret.

| Name | Description | Source |
| :--- | :--- | :--- |
| `AZURE_CLIENT_ID` | The `appId` from Step 1. | Azure Portal |
| `AZURE_TENANT_ID` | Your Azure Tenant ID. | Azure Portal |
| `AZURE_SUBSCRIPTION_ID` | Your Azure Subscription ID. | Azure Portal |
| `AZURE_DB_ADMIN_ID` | Your Entra ID Object ID (Initial DB admin). | `az ad signed-in-user show` |
| `AZURE_DB_ADMIN_NAME` | Your Entra ID Display Name or Email. | `az ad signed-in-user show` |
| `GEMINI_API_KEY` | API key for Gemini AI integration (required by GH workflows). | Google AI Studio |
| `JWT_SECRET` | Secret key for signing session cookies (min 32 chars). | [backend/.env](../backend/.env.example) |
| `VITE_LOGIC_APP_FEEDBACK_URL` | The URL for your Logic App feedback. | Logic app for processing customer feedback |

### Step 3.5: Configure GitHub Environments
To manage differences between `dev` and `prod`, use **GitHub Environments**:

1.  In GitHub, go to **Settings > Environments**.
2.  Create two environments: `dev` and `prod`.
3.  Add environment-specific secrets (like `JWT_SECRET` and `VITE_LOGIC_APP_FEEDBACK_URL`) directly to these environments.
4.  The workflows are already configured to pick the right secrets automatically based on the targeted environment.

### Step 4: Use Azure Login in Workflows

Use `azure/login` [GitHub action](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure) to retrieve the Cloud access token in your GitHub workflow.

---

## 2.5 Local Validation & Testing

To avoid deployment failures due to syntax or configuration errors (like invalid CIDR notations), validate your Bicep files locally before pushing.

### 1. Static Analysis (Linting)
The Azure CLI or Bicep CLI automatically lints files during build.
```bash
# Build to ARM template (checks syntax and best practices)
# Output is redirected to ignored dist/ folder
az bicep build --file infrastructure/shared.bicep --outfile infrastructure/dist/shared.json
az bicep build --file infrastructure/environment.bicep --outfile infrastructure/dist/environment.json
```

### 2. Pre-flight Validation
This checks if the deployment would succeed without actually creating resources. It requires an active Azure session.
```bash
# Validate shared infrastructure
az deployment group validate \
  --resource-group rg-spc-shared-pl \
  --template-file infrastructure/shared.bicep \
  --parameters adminPrincipalId=$(az ad signed-in-user show --query id -o tsv) \
               adminPrincipalName=$(az ad signed-in-user show --query userPrincipalName -o tsv)

# Validate environment-specific infrastructure (e.g., dev)
# Note: Get the full subnetId from the outputs of your 'shared' deployment:
# az deployment group show -g rg-spc-shared-pl -n network-deployment --query properties.outputs.snetDevId.value -o tsv

az deployment group validate \
  --resource-group rg-spc-dev-pl \
  --template-file infrastructure/environment.bicep \
  --parameters env=dev \
               subnetId="/subscriptions/ca830bff-0330-40f0-8d49-a18d5db67e9c/resourceGroups/rg-spc-shared-pl/providers/Microsoft.Network/virtualNetworks/vnet-spc-shared/subnets/snet-dev" \
               acrName="acrtulspc" \
               acrResourceGroup="rg-spc-shared-pl" \
               dbHost="psql-spc-shared.postgres.database.azure.com" \
               dbName="spc_dev"
```

The validations are only partial, to actually run the deployments locally use `create` instead of the `validate` in the commands above.

### 3. What-If Analysis
See exactly what changes will be applied to your environment.
```bash
az deployment group what-if \
  --resource-group rg-spc-dev \
  --template-file infrastructure/environment.bicep \
  --parameters ...
```

---

## 3. First Deployment Sequence

The first deployment must follow a specific order because components depend on each other.

1.  **Trigger Infrastructure:** Go to **Actions > Infrastructure Deployment** and run it manually (for `dev`). This creates the VNet, ACR, and the Database.
2.  **Create DB Users:** Bicep cannot reach inside the PostgreSQL engine to run GRANT statements. Manually create the roles for the app and migrator managed identities. See [database/init-db.sh](../database/init-db.sh).
3.  **Trigger Backend:** Go to **Actions > Backend Deployment (Dev)**. This will:
    - Build the Docker image.
    - Push it to the new ACR.
    - Run the Migration Job to set up the DB schema.
    - Update the Container App.
4.  **Trigger Frontend:** Go to **Actions > Frontend Deployment (Dev)**. This will build and deploy the React app to Azure Static Web Apps.

---

## 4. Architecture Notes

- **Zero-Trust:** No passwords or secrets are stored in GitHub or Azure Key Vault. All services use **Managed Identities**.
- **Initial Deployment:** The first infrastructure deployment uses a public "hello-world" image (`mcr.microsoft.com/azuredocs/containerapps-helloworld:latest`) because the ACR is initially empty. Furtehr deployments should pass `containerImage=acrtulspc.azurecr.io/backend:latest` to Bicep.
- **Scale-to-Zero:** The backend (Azure Container Apps) is configured with `minReplicas: 0`. It costs $0 when not in use.
- **Permission Split:** 
    - The `job-spc-dev-migrate` uses a **DDL Identity** (PostgreSQL Admin) for schema changes.
    - The `ca-spc-dev-backend` uses an **App Identity** (DML only) for runtime operations.
- **Monitoring:** Every environment (`dev`, `prod`) has its own **Application Insights** instance for complete isolation.
