param prefix string
param env string
param tags object = {}

resource emailService 'Microsoft.Communication/emailServices@2023-04-01' = {
  name: 'acs-email-${prefix}-${env}'
  location: 'global'
  tags: tags
  properties: {
    dataLocation: 'Europe'
  }
}

// Azure-managed domain: no DNS setup required, sends from DoNotReply@<hash>.azurecomm.net
resource managedDomain 'Microsoft.Communication/emailServices/domains@2023-04-01' = {
  parent: emailService
  name: 'AzureManagedDomain'
  location: 'global'
  properties: {
    domainManagement: 'AzureManaged'
  }
}

resource commService 'Microsoft.Communication/communicationServices@2023-04-01' = {
  name: 'acs-${prefix}-${env}'
  location: 'global'
  tags: tags
  properties: {
    dataLocation: 'Europe'
    linkedDomains: [
      managedDomain.id
    ]
  }
}

// Connection string is treated as sensitive by ARM and redacted from deployment history.
output connectionString string = commService.listKeys().primaryConnectionString
output fromAddress string = 'DoNotReply@${managedDomain.properties.mailFromSenderDomain}'
