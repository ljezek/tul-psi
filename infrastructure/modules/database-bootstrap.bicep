param location string
param prefix string
param env string
param scriptsSubnetId string
param storageAccountName string
param dbHost string
param dbAdminName string
param dbName string
param idDbSetupId string
param developerIdentityEmail string

// A timestamp to ensure the script runs on every deployment
param forceUpdateTag string = utcNow()

// --- Deployment Script (The "Ad-hoc Setup Job") ---
// This resource executes SQL commands inside the VNet using the Setup Identity.
resource dbBootstrap 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'ds-${prefix}-${env}-bootstrap'
  location: location
  kind: 'AzureCLI'
  tags: tags
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${idDbSetupId}': {}
    }
  }
  properties: {
    forceUpdateTag: forceUpdateTag
    azCliVersion: '2.50.0'
    containerSettings: {
      containerGroupName: 'cg-${prefix}-${env}-db-bootstrap'
      subnetIds: [
        {
          id: scriptsSubnetId
        }
      ]
    }
    storageAccountSettings: {
      storageAccountName: storageAccountName
    }
    environmentVariables: [
      { name: 'DB_HOST', value: dbHost }
      { name: 'DB_ADMIN', value: dbAdminName }
      { name: 'DB_NAME', value: dbName }
      { name: 'ENV', value: env }
      { name: 'DEV_EMAIL', value: developerIdentityEmail }
    ]
    scriptContent: '''
set -e

echo "Waiting for DNS propagation..."
sleep 30

# Install psql (alpine-based azure-cli container needs it)
apk update && apk add postgresql-client

# Get token for PostgreSQL Entra ID authentication
export PGPASSWORD=$(az account get-access-token --resource https://ossrdbms-aad.${environment().suffixes.sqlServerHostname} -o tsv --query accessToken)

echo "--- Debugging: Available Functions ---"
psql "host=${DB_HOST} user=${DB_ADMIN} dbname=postgres sslmode=require" -c "\df *pgaad*" || echo "Failed to list functions"

echo "--- Step 1: Create Global Roles (Connecting to 'postgres' database) ---"
psql "host=${DB_HOST} user=${DB_ADMIN} dbname=postgres sslmode=require" <<EOF
  DO \$$
  BEGIN
    -- Create roles for Managed Identities
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'id-spc-${ENV}-migrator') THEN
      PERFORM pgaadauth_create_principal('id-spc-${ENV}-migrator', false, false);
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'id-spc-${ENV}-app') THEN
      PERFORM pgaadauth_create_principal('id-spc-${ENV}-app', false, false);
    END IF;
    -- Create role for the developer identity
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DEV_EMAIL}') THEN
      PERFORM pgaadauth_create_principal('${DEV_EMAIL}', false, false);
    END IF;
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Notice: Principal creation failed or not supported: %', SQLERRM;
  END \$$;
EOF

echo "--- Step 2: Grant Permissions (Connecting to '$DB_NAME' database) ---"
psql "host=${DB_HOST} user=${DB_ADMIN} dbname=${DB_NAME} sslmode=require" <<EOF
  -- Ensure roles exist locally (fallback for environments where pgaadauth isn't active yet)
  DO \$$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'id-spc-${ENV}-migrator') THEN
       CREATE ROLE "id-spc-${ENV}-migrator" WITH LOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'id-spc-${ENV}-app') THEN
       CREATE ROLE "id-spc-${ENV}-app" WITH LOGIN;
    END IF;
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${DEV_EMAIL}') THEN
       CREATE ROLE "${DEV_EMAIL}" WITH LOGIN;
    END IF;
  EXCEPTION WHEN OTHERS THEN
    RAISE NOTICE 'Notice: Manual role creation fallback failed: %', SQLERRM;
  END \$$;

  -- Grant Permissions
  ALTER SCHEMA public OWNER TO "id-spc-${ENV}-migrator";
  GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO "id-spc-${ENV}-migrator";
  GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO "${DEV_EMAIL}";
  GRANT CONNECT ON DATABASE ${DB_NAME} TO "id-spc-${ENV}-app";
  GRANT USAGE ON SCHEMA public TO "id-spc-${ENV}-app";
  
  ALTER DEFAULT PRIVILEGES FOR ROLE "id-spc-${ENV}-migrator" IN SCHEMA public 
  GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "id-spc-${ENV}-app";
  
  ALTER DEFAULT PRIVILEGES FOR ROLE "id-spc-${ENV}-migrator" IN SCHEMA public 
  GRANT USAGE, SELECT ON SEQUENCES TO "id-spc-${ENV}-app";
EOF

echo "Verifying that Managed Identity roles exist..."
MISSING_ROLES=$(psql "host=${DB_HOST} user=${DB_ADMIN} dbname=${DB_NAME} sslmode=require" -t -A <<EOF
  SELECT rolname FROM (VALUES ('id-spc-${ENV}-migrator'), ('id-spc-${ENV}-app'), ('${DEV_EMAIL}')) AS t(rolname)
  EXCEPT
  SELECT rolname FROM pg_roles;
EOF
)

if [ -n "$MISSING_ROLES" ]; then
  echo "ERROR: Missing roles: $MISSING_ROLES"
  exit 1
fi

echo "SUCCESS: Database bootstrap complete for $ENV."
'''
    retentionInterval: 'P1D'
    cleanupPreference: 'OnSuccess'
  }
}

}
