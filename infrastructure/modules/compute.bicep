param location string
param prefix string
param env string
param subnetId string
param acrName string
param acrResourceGroup string
param dbHost string
param dbName string
param lawId string
param aiConnectionString string
param containerImage string
param deployDebugTools bool = false
param developerIdentityEmail string = 'lukas.jezek@gmail.com'
@secure()
param jwtSecret string

param pgadminAadClientId string = ''
@secure()
param pgadminAadClientSecret string = ''

@secure()
param acsConnectionString string
param acsFromAddress string

param tags object

var acrPullRoleDefinitionId = subscriptionResourceId('Microsoft.Authorization/roleDefinitions', '7f951dda-4ed3-4680-a7ca-43fe172d538d')
var deployPgadminAuth = deployDebugTools && !empty(pgadminAadClientId) && !empty(pgadminAadClientSecret)

resource law 'Microsoft.OperationalInsights/workspaces@2022-10-01' existing = {
  name: last(split(lawId, '/'))
}

// --- ACA Environment ---
resource env_aca 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: 'cae-${prefix}-${env}'
  location: location
  tags: tags
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
  tags: tags
}

module app_acr_pull './acr-role.bicep' = {
  name: 'app-acr-pull-${env}'
  scope: resourceGroup(acrResourceGroup)
  params: {
    principalId: app_identity.properties.principalId
    roleDefinitionId: acrPullRoleDefinitionId
    acrName: acrName
  }
}

// --- Migrator Identity ---
resource migrator_identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2023-01-31' = {
  name: 'id-${prefix}-${env}-migrator'
  location: location
  tags: tags
}

module migrator_acr_pull './acr-role.bicep' = {
  name: 'migrator-acr-pull-${env}'
  scope: resourceGroup(acrResourceGroup)
  params: {
    principalId: migrator_identity.properties.principalId
    roleDefinitionId: acrPullRoleDefinitionId
    acrName: acrName
  }
}

// --- Backend App ---
resource backend_app 'Microsoft.App/containerApps@2023-05-01' = {
  name: 'ca-${prefix}-${env}-backend'
  location: location
  tags: tags
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
      secrets: [
        {
          name: 'acs-connection-string'
          value: acsConnectionString
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: containerImage
          env: [
            { name: 'DATABASE_URL', value: 'postgresql+asyncpg://${app_identity.name}@${dbHost}:5432/${dbName}' }
            { name: 'APPLICATIONINSIGHTS_CONNECTION_STRING', value: aiConnectionString }
            { name: 'JWT_SECRET', value: jwtSecret }
            { name: 'APP_ENV', value: env }
            { name: 'ALLOWED_ORIGINS', value: 'https://${frontend_swa.properties.defaultHostname}' }
            { name: 'FRONTEND_URL', value: 'https://${frontend_swa.properties.defaultHostname}' }
            { name: 'AZURE_MANAGED_IDENTITY_ENABLED', value: 'true' }
            { name: 'AZURE_CLIENT_ID', value: app_identity.properties.clientId }
            { name: 'OTEL_EXPORTER_OTLP_ENDPOINT', value: 'http://localhost:4318' }
            { name: 'ACS_CONNECTION_STRING', secretRef: 'acs-connection-string' }
            { name: 'ACS_FROM_ADDRESS', value: acsFromAddress }
          ]
          probes: [
            {
              type: 'Liveness'
              httpGet: {
                path: '/health'
                port: 8000
              }
              periodSeconds: 30
              failureThreshold: 3
            }
          ]
          resources: {
            cpu: json('0.5')
            memory: '1Gi'
          }
        }
        {
          name: 'otel-collector'
          image: 'otel/opentelemetry-collector-contrib:0.111.0'
          args: [
            '--config=env:OTEL_CONFIG_CONTENT'
          ]
          env: [
            {
              name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
              value: aiConnectionString
            }
            {
              name: 'OTEL_CONFIG_CONTENT'
              value: loadTextContent('../monitoring/otel-collector-config.azure.yaml')
            }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
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
  tags: tags
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
          image: containerImage
          command: ['/bin/sh', '-c', 'alembic upgrade head && python seed.py']
          env: [
            { name: 'DATABASE_MIGRATION_URL', value: 'postgresql+asyncpg://${migrator_identity.name}@${dbHost}:5432/${dbName}' }
            { name: 'DATABASE_URL', value: 'postgresql+asyncpg://${migrator_identity.name}@${dbHost}:5432/${dbName}' }
            { name: 'AZURE_MANAGED_IDENTITY_ENABLED', value: 'true' }
            { name: 'AZURE_CLIENT_ID', value: migrator_identity.properties.clientId }
            { name: 'APP_ENV', value: env }
            { name: 'JWT_SECRET', value: jwtSecret }
          ]
        }
      ]
    }
  }
}

// --- Debugging Tools (Conditional) ---
resource pgadmin 'Microsoft.App/containerApps@2023-05-01' = if (deployDebugTools) {
  name: 'ca-${prefix}-${env}-pgadmin'
  location: location
  tags: tags
  properties: {
    managedEnvironmentId: env_aca.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8080
        transport: 'auto'
      }
      secrets: deployPgadminAuth ? [
        {
          name: 'aad-client-secret'
          value: pgadminAadClientSecret
        }
      ] : []
    }
    template: {
      containers: [
        {
          name: 'pgadmin'
          image: 'dpage/pgadmin4'
          env: [
            { name: 'PGADMIN_DEFAULT_EMAIL', value: developerIdentityEmail }
            { name: 'PGADMIN_DEFAULT_PASSWORD', value: 'this-is-not-used-with-easyauth-123' }
            { name: 'PGADMIN_CONFIG_ENHANCED_COOKIE_PROTECTION', value: 'True' }
            { name: 'PGADMIN_CONFIG_CONSOLE_LOG_LEVEL', value: '10' }
            { name: 'PGADMIN_LISTEN_PORT', value: '8080' }
            { name: 'PGADMIN_LISTEN_ADDRESS', value: '0.0.0.0' }
          ]
          resources: {
            cpu: json('0.25')
            memory: '0.5Gi'
          }
        }
      ]
      scale: {
        minReplicas: 0
        maxReplicas: 1
      }
    }
  }
}

resource pgadmin_auth 'Microsoft.App/containerApps/authConfigs@2023-05-01' = if (deployPgadminAuth) {
  parent: pgadmin
  name: 'current'
  properties: {
    platform: {
      enabled: true
    }
    globalValidation: {
      unauthenticatedClientAction: 'RedirectToLoginPage'
      redirectToProvider: 'azureactivedirectory'
    }
    identityProviders: {
      azureActiveDirectory: {
        enabled: true
        registration: {
          clientId: pgadminAadClientId
          clientSecretSettingName: 'aad-client-secret'
          openIdIssuer: '${environment().authentication.loginEndpoint}${subscription().tenantId}/v2.0'
        }
        validation: {
          allowedAudiences: [
            'api://${pgadminAadClientId}'
            pgadminAadClientId
          ]
        }
      }
    }
  }
}

// --- Static Web App ---
resource frontend_swa 'Microsoft.Web/staticSites@2022-09-01' = {
  name: 'swa-${prefix}-${env}'
  // Static Web Apps is a globally distributed service not available in all regions.
  // Therefore we hardcode the location to westeurope (it's only used for metadata storage).
  location: 'westeurope'
  tags: tags
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
