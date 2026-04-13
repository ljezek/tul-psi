param location string
param prefix string
param env string
param subnetId string
param vnetId string
param adminPrincipalId string
param adminPrincipalName string
param adminPrincipalType string = 'User'

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

resource db_prod 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-06-01-preview' = {
  parent: postgres
  name: 'spc_prod'
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

resource postgresAdmin 'Microsoft.DBforPostgreSQL/flexibleServers/administrators@2023-06-01-preview' = {
  parent: postgres
  name: adminPrincipalId
  properties: {
    principalName: adminPrincipalName
    principalType: adminPrincipalType
    tenantId: subscription().tenantId
  }
}

output postgresId string = postgres.id
output postgresFullyQualifiedDomainName string = postgres.properties.fullyQualifiedDomainName
