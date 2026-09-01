// Minimal Azure Container Apps deployment for the Portfolio Risk Studio.
// This is scaffolding, not a production-hardened template: it deploys a
// single container app pulling from an Azure Container Registry image,
// with the Groq key passed as a secret. Adjust SKU/scale/ingress
// settings as needed once you're ready to go beyond a demo deployment.
//
// Usage (after building & pushing the image -- see DEPLOY.md):
//   az deployment group create \
//     --resource-group <your-resource-group> \
//     --template-file deployment/azure/container-app.bicep \
//     --parameters acrLoginServer=<your-acr>.azurecr.io imageName=risk-studio:latest groqApiKey=<key>

@description('Name for the Container App')
param containerAppName string = 'portfolio-risk-studio'

@description('Location for all resources')
param location string = resourceGroup().location

@description('Login server of your Azure Container Registry, e.g. myacr.azurecr.io')
param acrLoginServer string

@description('Image name and tag, e.g. risk-studio:latest')
param imageName string

@secure()
@description('Groq API key for the AI Analyst feature')
param groqApiKey string

resource env 'Microsoft.App/managedEnvironments@2023-05-01' = {
  name: '${containerAppName}-env'
  location: location
  properties: {}
}

resource containerApp 'Microsoft.App/containerApps@2023-05-01' = {
  name: containerAppName
  location: location
  properties: {
    managedEnvironmentId: env.id
    configuration: {
      ingress: {
        external: true
        targetPort: 8000
      }
      secrets: [
        {
          name: 'groq-api-key'
          value: groqApiKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: containerAppName
          image: '${acrLoginServer}/${imageName}'
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'GROQ_API_KEY'
              secretRef: 'groq-api-key'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output appUrl string = 'https://${containerApp.properties.configuration.ingress.fqdn}'
