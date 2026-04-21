param location string
param prefix string
param env string
param appInsightsId string
param alertsEmail string
param alertWindowDuration string = 'PT5M'
param p95LatencyThreshold int = 1000
param endpointErrorsThreshold int = 3
param tags object

resource actionGroup 'Microsoft.Insights/actionGroups@2023-01-01' = {
  name: 'ag-${prefix}-${env}-alerts'
  location: 'Global'
  tags: tags
  properties: {
    groupShortName: 'SPCAlerts'
    enabled: true
    emailReceivers: [
      {
        name: 'AlertEmail'
        emailAddress: alertsEmail
        useCommonAlertSchema: true
      }
    ]
  }
}

resource errorAlert 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = {
  name: 'sqr-${prefix}-${env}-high-errors'
  location: location
  tags: tags
  properties: {
    displayName: 'High Error Rate (5xx)'
    description: 'Alerts when a specific endpoint has ${endpointErrorsThreshold} or more 5xx errors within a ${alertWindowDuration} window.'
    enabled: true
    severity: 1
    evaluationFrequency: alertWindowDuration
    windowSize: alertWindowDuration
    scopes: [
      appInsightsId
    ]
    targetResourceTypes: [
      'Microsoft.Insights/components'
    ]
    criteria: {
      allOf: [
        {
          query: 'requests\n| where success == false and resultCode startswith "5"\n| summarize ErrorCount = count() by operation_Name'
          timeAggregation: 'Average'
          metricMeasureColumn: 'ErrorCount'
          resourceIdColumn: ''
          dimensions: [
            {
              name: 'operation_Name'
              operator: 'Include'
              values: [
                '*'
              ]
            }
          ]
          operator: 'GreaterThanOrEqual'
          threshold: endpointErrorsThreshold
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        actionGroup.id
      ]
    }
  }
}

resource latencyAlert 'Microsoft.Insights/scheduledQueryRules@2023-12-01' = {
  name: 'sqr-${prefix}-${env}-high-latency'
  location: location
  tags: tags
  properties: {
    displayName: 'High Sustained Latency (P95)'
    description: 'Alerts when an endpoint has a P95 latency > ${p95LatencyThreshold}ms over a ${alertWindowDuration} window with at least 5 requests.'
    enabled: true
    severity: 2
    evaluationFrequency: alertWindowDuration
    windowSize: alertWindowDuration
    scopes: [
      appInsightsId
    ]
    targetResourceTypes: [
      'Microsoft.Insights/components'
    ]
    criteria: {
      allOf: [
        {
          query: 'requests\n| summarize RequestCount = count(), P95 = percentile(duration, 95) by operation_Name\n| where RequestCount >= 5'
          timeAggregation: 'Average'
          metricMeasureColumn: 'P95'
          resourceIdColumn: ''
          dimensions: [
            {
              name: 'operation_Name'
              operator: 'Include'
              values: [
                '*'
              ]
            }
          ]
          operator: 'GreaterThan'
          threshold: p95LatencyThreshold
          failingPeriods: {
            numberOfEvaluationPeriods: 1
            minFailingPeriodsToAlert: 1
          }
        }
      ]
    }
    actions: {
      actionGroups: [
        actionGroup.id
      ]
    }
  }
}
