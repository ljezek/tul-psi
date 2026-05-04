param prefix string
param env string
param tags object = {}

var suffix = uniqueString(resourceGroup().id)

resource emailService 'Microsoft.Communication/emailServices@2023-04-01' = {
  name: 'acs-email-${prefix}-${env}-${suffix}'
  location: 'global'
  tags: tags
  properties: {
    dataLocation: 'Europe'
  }
}

// Azure-managed domain: no DNS setup required.
// ACS does not expose a sender display-name field, so we use a branded local-part.
resource managedDomain 'Microsoft.Communication/emailServices/domains@2023-04-01' = {
  parent: emailService
  name: 'AzureManagedDomain'
  location: 'global'
  properties: {
    domainManagement: 'AzureManaged'
  }
}

resource commService 'Microsoft.Communication/communicationServices@2023-04-01' = {
  name: 'acs-${prefix}-${env}-${suffix}'
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
#disable-next-line outputs-should-not-contain-secrets
output connectionString string = commService.listKeys().primaryConnectionString
output fromAddress string = 'tul-student-projects-catalogue@${managedDomain.properties.mailFromSenderDomain}'
