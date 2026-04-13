# 🚀 Student Projects Catalogue (SPC) Deployment Guide

This project uses **Azure Bicep** for Infrastructure-as-Code (IaC) and **GitHub Actions** for CI/CD. All deployments use **OpenID Connect (OIDC)** for a zero-secret security model.

## 1. Prerequisites

1.  **Azure Subscription:** An active Azure subscription.
2.  **GitHub Repository:** The code must be pushed to a GitHub repository.
3.  **Azure CLI:** Installed locally for the initial setup.

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

# Create the app and service principal
az ad app create --display-name $APP_NAME
# Note the appId (Client ID) from the output

# Get the Object ID of the service principal
APP_ID=$(az ad app list --display-name $APP_NAME --query "[0].appId" -o tsv)
OBJECT_ID=$(az ad app show --id $APP_ID --query id -o tsv)

# Assign 'Contributor' role to the subscription
az role assignment create --role Contributor --assignee $OBJECT_ID --scope "/subscriptions/$SUBSCRIPTION_ID"
```

### Step 2: Configure Federated Identity Credentials
This links your GitHub repository to the Azure App. This works for `ljezek/tul-psi` repo.

```bash
# For the main branch
az ad app federated-credential create --id $OBJECT_ID --parameters '{
  "name": "gh-actions-spc-main",
  "issuer": "https://token.actions.githubusercontent.com",
  "subject": "repo:ljezek/tul-psi:ref:refs/heads/main",
  "audiences": ["api://AzureADTokenExchange"]
}'
```

### Step 3: Set GitHub Secrets
In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add the following:

- `AZURE_CLIENT_ID`: The `appId` from Step 1.
- `AZURE_TENANT_ID`: Your Azure Tenant ID.
- `AZURE_SUBSCRIPTION_ID`: Your Azure Subscription ID.
- `AZURE_DB_ADMIN_ID`: Your personal Entra ID Object ID (to be the initial DB admin).
- `AZURE_DB_ADMIN_NAME`: Your personal Entra ID Display Name or Email.

### Step 4: Use Azure Login in Workflows
Use `azure/login` [GitHub action](https://docs.github.com/en/actions/how-tos/secure-your-work/security-harden-deployments/oidc-in-azure) to retrieve the Cloud access token in your GitHub workflow.

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
- **Scale-to-Zero:** The backend (Azure Container Apps) is configured with `minReplicas: 0`. It costs $0 when not in use.
- **Permission Split:** 
    - The `job-spc-dev-migrate` uses a **DDL Identity** (PostgreSQL Admin) for schema changes.
    - The `ca-spc-dev-backend` uses an **App Identity** (DML only) for runtime operations.
- **Monitoring:** Every environment (`dev`, `prod`) has its own **Application Insights** instance for complete isolation.
