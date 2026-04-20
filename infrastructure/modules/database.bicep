param location string
param prefix string
param env string
param subnetId string
param vnetId string
param scriptsSubnetId string
param tags object
param lawId string = ''

// --- Identity for DB Setup/Bootstrap ---
// PostgreSQL Flexible Server (Private Access) cannot be reached from the Azure Portal Query Editor
// or a local machine without a VPN/Jumpbox. We use this Managed Identity to run an 
// in-VNet Deployment Script that bootstraps the initial database roles.
resource idDbSetup 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${prefix}-${env}-db-setup'
  location: location
  tags: tags
}

// --- Storage Account for Infrastructure Scripts (Shared) ---
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: 'st${prefix}${env}scripts' 
  location: location
  tags: tags
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
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
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

resource postgres_diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(lawId)) {
  name: 'ds-${postgres.name}'
  scope: postgres
  properties: {
    workspaceId: lawId
    logs: [
      {
        category: 'PostgreSQLLogs'
        enabled: true
      }
    ]
    metrics: [
      {
        category: 'AllMetrics'
        enabled: true
      }
    ]
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
  tags: tags
}

resource privateDnsZoneLink 'Microsoft.Network/privateDnsZones/virtualNetworkLinks@2020-06-01' = {
  parent: privateDnsZone
  name: '${prefix}-${env}-link'
  location: 'global'
  tags: tags
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

output postgresId string = postgres.id
output postgresFullyQualifiedDomainName string = postgres.properties.fullyQualifiedDomainName
output idDbSetupId string = idDbSetup.id
output idDbSetupName string = idDbSetup.name
output storageAccountName string = storageAccount.name
