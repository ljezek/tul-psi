param location string
param prefix string
param tags object
param lawId string = ''

resource acr 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' = {
  name: 'acrtul${replace(prefix, '-', '')}'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: false
  }
}

resource acr_diagnostics 'Microsoft.Insights/diagnosticSettings@2021-05-01-preview' = if (!empty(lawId)) {
  name: 'ds-${acr.name}'
  scope: acr
  properties: {
    workspaceId: lawId
    logs: [
      {
        category: 'ContainerRegistryRepositoryEvents'
        enabled: true
      }
      {
        category: 'ContainerRegistryLoginEvents'
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

output acrId string = acr.id
output acrName string = acr.name
output acrLoginServer string = acr.properties.loginServer
