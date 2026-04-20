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

### Step 0: Register Resource Providers (Subscription Level)
Resource providers must be registered once per subscription. Since GitHub only has Resource Group access, you must do this manually (in Bash):

```bash
az login
az provider register --namespace Microsoft.ContainerInstance
```

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

### Step 2: Create DB Bootstrap Identity & Grant Permissions (Required for VNet DB Access)
Because the DB is in a VNet, Bicep uses a temporary script to create roles. This identity and the DB server itself need permissions to look up other Managed Identities in Entra ID.

```bash
# 1. Create the identity in the 'shared' resource group
az identity create -g rg-spc-shared-pl -n id-spc-shared-db-setup

# 2. Get the Principal IDs for both the Setup Identity and the DB Server
SETUP_PRINCIPAL_ID=$(az identity show -g rg-spc-shared-pl -n id-spc-shared-db-setup --query principalId -o tsv)
DB_SERVER_PRINCIPAL_ID=$(az postgres flexible-server show -g rg-spc-shared-pl -n psql-spc-shared --query identity.principalId -o tsv)

# 3. Define the Granular Graph Permissions (Least Privilege)
GRAPH_ID=$(az ad sp list --filter "displayName eq 'Microsoft Graph'" --query '[0].id' -o tsv)
APPROLE_IDS=$(az ad sp show --id "$GRAPH_ID" \
  --query "appRoles[?value=='User.Read.All' || value=='GroupMember.Read.All' || value=='Application.Read.All'].id" \
  -o tsv)

# 4. Assign permissions to both identities
for PRINCIPAL_ID in $SETUP_PRINCIPAL_ID $DB_SERVER_PRINCIPAL_ID; do
  echo "Assigning permissions to Principal: $PRINCIPAL_ID"
  for ROLE_ID in $APPROLE_IDS; do
    az rest --method POST \
      --uri "https://graph.microsoft.com/v1.0/servicePrincipals/$PRINCIPAL_ID/appRoleAssignments" \
      --body "{
        \"principalId\": \"$PRINCIPAL_ID\",
        \"resourceId\": \"$GRAPH_ID\",
        \"appRoleId\": \"$ROLE_ID\"
      }"
  done
done
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
az deployment group validate --resource-group rg-spc-shared-pl --template-file infrastructure/shared.bicep

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
               idDbSetupId="/subscriptions/ca830bff-0330-40f0-8d49-a18d5db67e9c/resourceGroups/rg-spc-shared-pl/providers/Microsoft.ManagedIdentity/userAssignedIdentities/id-spc-shared-db-setup" \
               idDbSetupName="id-spc-shared-db-setup" \
               storageAccountName="stspcsharedscripts" \
               scriptsSubnetId="/subscriptions/ca830bff-0330-40f0-8d49-a18d5db67e9c/resourceGroups/rg-spc-shared-pl/providers/Microsoft.Network/virtualNetworks/vnet-spc-shared/subnets/snet-scripts" \
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

---

## 5. Troubleshooting & DB Debugging (GUI Access)

Since the PostgreSQL server is restricted to the private VNet, you cannot connect to it directly from your local machine. We deploy a **pgAdmin Azure Container App** in the `dev` environment for secure GUI access.

### Step 1: Access the pgAdmin UI
1.  Go to the Azure Portal and find the `ca-spc-dev-pgadmin` Container App.
2.  Open the Application URL.
3.  **EasyAuth:** You will be prompted to log in with your Microsoft account (`lukas.jezek@gmail.com`). This ensures only authorized developers can reach the pgAdmin login screen.

### Step 2: Connect to the Database
Once inside the pgAdmin web interface, add a new server:

1.  **General Tab:**
    *   **Name:** `spc-dev`
2.  **Connection Tab:**
    *   **Host:** `psql-spc-shared.postgres.database.azure.com`
    *   **Port:** `5432`
    *   **Maintenance Database:** `spc_dev`
    *   **Username:** `lukas.jezek@gmail.com` (or your registered identity)
    *   **Password:** An Entra ID Access Token. Generate it on your local machine:
        ```bash
        az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv
        ```
        *Note: The token is valid for 1 hour.*
3.  **SSL Tab:**
    *   **SSL Mode:** `Require`

### Step 3: Cost Management
The `pgadmin` Container App is configured to **scale to zero**. It will automatically shut down when you are not using it and start back up when you browse to its URL.
