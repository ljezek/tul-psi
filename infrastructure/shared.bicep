targetScope = 'resourceGroup'

param location string = resourceGroup().location
param prefix string = 'spc'

// --- Network ---
module network './modules/network.bicep' = {
  name: 'network-deployment'
  params: {
    location: location
  }
}

// --- Container Registry ---
module acr './modules/acr.bicep' = {
  name: 'acr-deployment'
  params: {
    location: location
    prefix: prefix
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
  }
}

// --- Monitoring (Shared) ---
module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring-shared-deployment'
  params: {
    location: location
    prefix: prefix
    env: 'shared'
  }
}

// --- Debugging (Bastion Developer) ---
resource bastion 'Microsoft.Network/bastionHosts@2023-11-01' = {
  name: 'bastion-${prefix}-shared'
  location: location
  sku: {
    name: 'Developer'
  }
  properties: {
    virtualNetwork: {
      id: network.outputs.vnetId
    }
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
