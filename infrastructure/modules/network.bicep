param location string
param vnetName string = 'vnet-spc-shared'
param vnetAddressPrefix string = '10.0.0.0/16'

resource vnet 'Microsoft.Network/virtualNetworks@2023-09-01' = {
  name: vnetName
  location: location
  properties: {
    addressSpace: {
      addressPrefixes: [
        vnetAddressPrefix
      ]
    }
    subnets: [
      {
        name: 'snet-db'
        properties: {
          addressPrefix: '10.0.5.0/28'
          delegations: [
            {
              name: 'delegation'
              properties: {
                serviceName: 'Microsoft.DBforPostgreSQL/flexibleServers'
              }
            }
          ]
        }
      }
      {
        name: 'snet-dev'
        properties: {
          addressPrefix: '10.0.1.0/23'
          delegations: [
            {
              name: 'delegation'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
      {
        name: 'snet-prod'
        properties: {
          addressPrefix: '10.0.3.0/23'
          delegations: [
            {
              name: 'delegation'
              properties: {
                serviceName: 'Microsoft.App/environments'
              }
            }
          ]
        }
      }
    ]
  }
}

output vnetId string = vnet.id
output snetDbId string = vnet.properties.subnets[0].id
output snetDevId string = vnet.properties.subnets[1].id
output snetProdId string = vnet.properties.subnets[2].id
