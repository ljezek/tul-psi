targetScope = 'resourceGroup'

param location string = resourceGroup().location
param prefix string = 'spc'

param tags object = {
  project: 'spc'
  env: 'shared'
  managedBy: 'bicep'
}

// --- Monitoring (Shared) ---
module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring-shared-deployment'
  params: {
    location: location
    prefix: prefix
    env: 'shared'
    tags: tags
  }
}

// --- Network ---
module network './modules/network.bicep' = {
  name: 'network-deployment'
  params: {
    location: location
    tags: tags
  }
}

// --- Container Registry ---
module acr './modules/acr.bicep' = {
  name: 'acr-deployment'
  params: {
    location: location
    prefix: prefix
    tags: tags
    lawId: monitoring.outputs.workspaceId
  }
}

// --- Database (Shared Host) ---
module database './modules/database.bicep' = {
  name: 'database-deployment'
  params: {
    location: location
    prefix: prefix
    env: 'shared'
    subnetId: network.outputs.snetDbId
    vnetId: network.outputs.vnetId
    scriptsSubnetId: network.outputs.snetScriptsId
    tags: tags
    lawId: monitoring.outputs.workspaceId
  }
}

output acrName string = acr.outputs.acrName
output vnetId string = network.outputs.vnetId
output snetDevId string = network.outputs.snetDevId
output snetProdId string = network.outputs.snetProdId
output dbHost string = database.outputs.postgresFullyQualifiedDomainName
output idDbSetupId string = database.outputs.idDbSetupId
output idDbSetupName string = database.outputs.idDbSetupName
output storageAccountName string = database.outputs.storageAccountName
output snetScriptsId string = network.outputs.snetScriptsId
