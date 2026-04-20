targetScope = 'resourceGroup'

param location string = resourceGroup().location
param prefix string = 'spc'
param env string
param subnetId string
param acrName string
param acrResourceGroup string
param dbHost string
param dbName string
param idDbSetupId string
param idDbSetupName string
param storageAccountName string
param scriptsSubnetId string
param developerIdentityEmail string = 'lukas.jezek@gmail.com'
param deployDebugTools bool = false
param containerImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
@secure()
param jwtSecret string

param pgadminAadClientId string = ''
@secure()
param pgadminAadClientSecret string = ''

param tags object = {
  project: 'spc'
  env: env
  managedBy: 'bicep'
}

// --- Monitoring (Per Environment) ---
module monitoring './modules/monitoring.bicep' = {
  name: 'monitoring-${env}-deployment'
  params: {
    location: location
    prefix: prefix
    env: env
    tags: tags
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
    deployDebugTools: deployDebugTools
    pgadminAadClientId: pgadminAadClientId
    pgadminAadClientSecret: pgadminAadClientSecret
    lawId: monitoring.outputs.workspaceId
    aiConnectionString: monitoring.outputs.connectionString
    tags: tags
  }
}

// --- Database Role Bootstrap ---
module dbBootstrap './modules/database-bootstrap.bicep' = {
  name: 'db-bootstrap-${env}-deployment'
  params: {
    location: location
    prefix: prefix
    env: env
    dbHost: dbHost
    dbName: dbName
    idDbSetupId: idDbSetupId
    dbAdminName: idDbSetupName
    storageAccountName: storageAccountName
    scriptsSubnetId: scriptsSubnetId
    developerIdentityEmail: developerIdentityEmail
    tags: tags
  }
  dependsOn: [
    compute
  ]
}

output backendUrl string = compute.outputs.backendUrl
output appPrincipalId string = compute.outputs.appPrincipalId
output migratorPrincipalId string = compute.outputs.migratorPrincipalId
