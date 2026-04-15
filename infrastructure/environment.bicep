targetScope = 'resourceGroup'

param location string = resourceGroup().location
param prefix string = 'spc'
param env string
param subnetId string
param acrName string
param acrResourceGroup string
param dbHost string
param dbName string
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
@secure()
param jwtSecret string

// --- Monitoring (Per Environment) ---
module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring-${env}-deployment'
  params: {
    location: location
    prefix: prefix
    env: env
  }
}

// --- Compute (ACA + SWA) ---
module compute './modules/compute.bicep' = {
  name: 'compute-${env}-deployment'
  params: {
    location: location
    prefix: prefix
    env: env
    subnetId: subnetId
    acrName: acrName
    acrResourceGroup: acrResourceGroup
    dbHost: dbHost
    dbName: dbName
    containerImage: containerImage
    jwtSecret: jwtSecret
    lawId: monitoring.outputs.workspaceId
    aiConnectionString: monitoring.outputs.connectionString
  }
}

output backendUrl string = compute.outputs.backendUrl
output appPrincipalId string = compute.outputs.appPrincipalId
output migratorPrincipalId string = compute.outputs.migratorPrincipalId
