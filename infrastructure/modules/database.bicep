param location string
param prefix string
param env string
param subnetId string
param vnetId string
param scriptsSubnetId string

// --- Identity for DB Setup/Bootstrap ---
// PostgreSQL Flexible Server (Private Access) cannot be reached from the Azure Portal Query Editor
// or a local machine without a VPN/Jumpbox. We use this Managed Identity to run an 
// in-VNet Deployment Script that bootstraps the initial database roles.
resource idDbSetup 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${prefix}-${env}-db-setup'
  location: location
}

// --- Storage Account for Infrastructure Scripts (Shared) ---
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'st${prefix}${env}scripts' 
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    networkAcls: {
      bypass: 'AzureServices'
      defaultAction: 'Deny'
      virtualNetworkRules: [
        {
          id: scriptsSubnetId
          action: 'Allow'
        }
      ]
    }
  }
}

// RBAC: The setup identity needs to manage the storage account and files
resource storageContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, idDbSetup.id, 'StorageAccountContributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '17d1049b-9a84-46fb-8f53-869881c3d3ab')
    principalId: idDbSetup.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource blobContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, idDbSetup.id, 'BlobDataContributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', 'ba92f5b4-2d11-453d-a403-e96b0029c9fe')
    principalId: idDbSetup.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource filePrivilegedContributor 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(storageAccount.id, idDbSetup.id, 'FilePrivilegedContributor')
  scope: storageAccount
  properties: {
    roleDefinitionId: subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '69566ab7-960f-475b-8e7c-b3118f30c6bd')
    principalId: idDbSetup.properties.principalId
    principalType: 'ServicePrincipal'
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-06-01-preview' = {
  name: 'psql-${prefix}-${env}'
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '15'
    storage: {
      storageSizeGB: 32
    }
    network: {
      delegatedSubnetResourceId: subnetId
      privateDnsZoneArmResourceId: privateDnsZone.id
    }
    authConfig: {
      activeDirectoryAuth: 'Enabled'
      passwordAuth: 'Disabled'
    }
  }
}

// Databases are required as resources in Flexible Server Bicep
resource db_dev 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: 'spc_dev'
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource privateDnsZone 'Microsoft.Network/privateDnsZones@2020-06-01' = {
  name: '${prefix}-${env}.postgres.database.azure.com'
  location: 'global'
}

resource privateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZone
  name: '${prefix}-${env}-link'
  location: 'global'
  properties: {
    registrationEnabled: false
    virtualNetwork: {
      id: vnetId
    }
  }
}

// --- PostgreSQL Administrator ---
// We set the Setup Identity as the DB Admin to allow it to create other roles.
// CRITICAL: This identity MUST be granted the "Directory Readers" role in Entra ID 
// to successfully run 'pgaadauth_create_principal'.
module postgresAdmin './database-admin.bicep' = {
  name: 'postgres-admin-assignment'
  params: {
    postgresName: postgres.name
    principalId: idDbSetup.properties.principalId
    principalName: idDbSetup.name
    tenantId: subscription().tenantId
  }
}

// --- Deployment Script (The "Ad-hoc Setup Job") ---
// This resource executes SQL commands inside the VNet using the Setup Identity.
resource dbBootstrap 'Microsoft.Resources/deploymentScripts@2023-08-01' = {
  name: 'ds-${prefix}-${env}-bootstrap'
  location: location
  kind: 'AzureCLI'
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${idDbSetup.id}': {}
    }
  }
  dependsOn: [
    postgresAdmin
    db_dev
    storageContributor
    blobContributor
    filePrivilegedContributor
  ]
  properties: {
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
      storageAccountName: storageAccount.name
    }
    environmentVariables: [
      { name: 'DB_HOST', value: postgres.properties.fullyQualifiedDomainName }
      { name: 'DB_ADMIN', value: idDbSetup.name }
    ]
    scriptContent: '''
      echo "Waiting for DNS to propagate..."
      sleep 30
      
      # Install psql (alpine-based azure-cli container needs it)
      apk update && apk add postgresql-client
      
      # Get token for PostgreSQL Entra ID authentication
      export PGPASSWORD=$(az account get-access-token --resource-type oss-rdbms --query accessToken -o tsv)
      
      bootstrap_db() {
        local dbname=$1
        local environment=$2
        echo "Bootstrapping $dbname for $environment..."
        psql "host=${DB_HOST} user=${DB_ADMIN} dbname=${dbname} sslmode=require" <<EOF
          -- 1. Create Roles for Managed Identities
          -- Note: pgaadauth_create_principal is a custom Azure PG extension function
          DO \$$
          BEGIN
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'id-spc-${environment}-migrator') THEN
              PERFORM pgaadauth_create_principal('id-spc-${environment}-migrator', false, false);
            END IF;
            IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'id-spc-${environment}-app') THEN
              PERFORM pgaadauth_create_principal('id-spc-${environment}-app', false, false);
            END IF;
          END \$$;


          -- 2. Grant Permissions
          -- The migrator needs to manage schema (DDL)
          ALTER SCHEMA public OWNER TO "id-spc-${environment}-migrator";
          GRANT ALL PRIVILEGES ON DATABASE ${dbname} TO "id-spc-${environment}-migrator";
          
          -- The app needs to manage data (DML)
          GRANT CONNECT ON DATABASE ${dbname} TO "id-spc-${environment}-app";
          GRANT USAGE ON SCHEMA public TO "id-spc-${environment}-app";
          
          -- Automatically grant permissions on tables created by the migrator in the future
          ALTER DEFAULT PRIVILEGES FOR ROLE "id-spc-${environment}-migrator" IN SCHEMA public 
          GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO "id-spc-${environment}-app";
          
          ALTER DEFAULT PRIVILEGES FOR ROLE "id-spc-${environment}-migrator" IN SCHEMA public 
          GRANT USAGE, SELECT ON SEQUENCES TO "id-spc-${environment}-app";
EOF
      }

      # Currently only bootstrapping the 'dev' environment roles
      bootstrap_db "spc_dev" "dev"
    '''
    retentionInterval: 'P1D'
    cleanupPreference: 'OnSuccess'
  }
}

output postgresId string = postgres.id
output postgresFullyQualifiedDomainName string = postgres.properties.fullyQualifiedDomainName
