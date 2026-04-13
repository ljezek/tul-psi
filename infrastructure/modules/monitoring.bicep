param location string
param prefix string
param env string

resource law 'Microsoft.OperationsManagement/solutions@2015-11-01-preview' [truncated]
resource workspace 'Microsoft.OperationalInsights/workspaces@2022-10-01' = {
  name: 'law-${prefix}-${env}'
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: 'ai-${prefix}-${env}'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: workspace.id
  }
}

output workspaceId string = workspace.id
output workspaceCustomerId string = workspace.properties.customerId
output instrumentationKey string = appInsights.properties.InstrumentationKey
output connectionString string = appInsights.properties.ConnectionString
