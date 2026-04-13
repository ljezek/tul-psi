param location string
param prefix string
param env string
param subnetId string
param acrName string
param dbHost string
param dbName string
param lawId string
param aiConnectionString string

// --- ACR Reference ---
resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: acrName
}

var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')

resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: last(split(lawId, '/'))
}

// --- ACA Environment ---
resource env_aca 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${prefix}-${env}'
  location: location
  properties: {
    vnetConfiguration: {
      infrastructureSubnetId: subnetId
    }
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: law.properties.customerId
        sharedKey: law.listKeys().primarySharedKey
      }
    }

  }
}

// --- App Identity ---
resource app_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${prefix}-${env}-app'
  location: location
}

resource app_acr_pull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, app_identity.id, acrPullRoleDefinitionId)
  scope: acr
  properties: {
    principalId: app_identity.properties.principalId
    roleDefinitionId: acrPullRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

// --- Migrator Identity ---
resource migrator_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${prefix}-${env}-migrator'
  location: location
}

resource migrator_acr_pull 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(acr.id, migrator_identity.id, acrPullRoleDefinitionId)
  scope: acr
  properties: {
    principalId: migrator_identity.properties.principalId
    roleDefinitionId: acrPullRoleDefinitionId
    principalType: 'ServicePrincipal'
  }
}

// --- Backend App ---
resource backend_app 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-${prefix}-${env}-backend'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${app_identity.id}': {}
    }
  }
  properties: {
    managedEnvironmentId: env_aca.id
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
      }
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: app_identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: '${acrName}.azurecr.io/backend:latest'
          env: [
            { name: 'DATABASE_URL', value: 'postgresql+asyncpg://${app_identity.name}@${dbHost}:5432/${dbName}' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: aiConnectionString }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 3
      }
    }
  }
}

// --- Migration Job ---
resource migration_job 'Microsoft.App/jobs@2023-05-01' = {
  name: 'job-${prefix}-${env}-migrate'
  location: location
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: {
      '${migrator_identity.id}': {}
    }
  }
  properties: {
    environmentId: env_aca.id
    configuration: {
      triggerType: 'Manual'
      replicaRetryLimit: 1
      replicaTimeout: 300
      registries: [
        {
          server: '${acrName}.azurecr.io'
          identity: migrator_identity.id
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'migrator'
          image: '${acrName}.azurecr.io/backend:latest'
          command: ['alembic', 'upgrade', 'head']
          env: [
            { name: 'DATABASE_URL', value: 'postgresql+asyncpg://${migrator_identity.name}@${dbHost}:5432/${dbName}' }
          ]
        }
      ]
    }
  }
}

// --- Static Web App ---
resource frontend_swa 'Microsoft.Web/staticSites@2022-09-01' = {
  name: 'swa-${prefix}-${env}'
  location: location
  sku: {
    name: 'Free'
    tier: 'Free'
  }
  properties: {}
}

output backendUrl string = backend_app.properties.configuration.ingress.fqdn
output appIdentityId string = app_identity.id
output appPrincipalId string = app_identity.properties.principalId
output migratorIdentityId string = migrator_identity.id
output migratorPrincipalId string = migrator_identity.properties.principalId
