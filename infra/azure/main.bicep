@description('Prefijo corto para los recursos')
param prefix string = 'enturnamiento'

@description('Ubicacion de Azure')
param location string = resourceGroup().location

@description('SKU del App Service Plan')
@allowed([
  'B1'
  'S1'
])
param appServiceSku string = 'B1'

@description('Usuario administrador de PostgreSQL')
param postgresAdminUser string

@secure()
@description('Clave del administrador de PostgreSQL')
param postgresAdminPassword string

@description('Version de PostgreSQL')
param postgresVersion string = '16'

@description('Tamano de computo de PostgreSQL')
param postgresSkuName string = 'Standard_B1ms'

@description('Tamano de almacenamiento PostgreSQL en GB')
param postgresStorageGb int = 32

@description('Nombre unico global del storage account')
param storageAccountName string

@description('Nombre del sitio web')
param webAppName string

@description('Nombre del plan App Service')
param appServicePlanName string = '${prefix}-plan'

@description('Nombre del servidor PostgreSQL')
param postgresServerName string = '${prefix}-psql'

@description('Nombre del contenedor de evidencias')
param blobContainerName string = 'evidencias'

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: appServicePlanName
  location: location
  sku: {
    name: appServiceSku
    capacity: 1
  }
  kind: 'linux'
  properties: {
    reserved: true
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    accessTier: 'Hot'
    minimumTlsVersion: 'TLS1_2'
    supportsHttpsTrafficOnly: true
    allowBlobPublicAccess: false
  }
}

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  name: '${storage.name}/default'
}

resource evidenceContainer 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  name: '${storage.name}/default/${blobContainerName}'
  properties: {
    publicAccess: 'None'
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2024-08-01' = {
  name: postgresServerName
  location: location
  sku: {
    name: postgresSkuName
    tier: 'Burstable'
  }
  properties: {
    version: postgresVersion
    administratorLogin: postgresAdminUser
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: postgresStorageGb
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

resource postgresDb 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2024-08-01' = {
  name: '${postgres.name}/enturnamiento'
}

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: webAppName
  location: location
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      alwaysOn: appServiceSku == 'S1'
      appSettings: [
        {
          name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'
          value: 'true'
        }
        {
          name: 'HOST'
          value: '0.0.0.0'
        }
        {
          name: 'PORT'
          value: '8000'
        }
        {
          name: 'WEBSITES_PORT'
          value: '8000'
        }
        {
          name: 'UPLOADS_DIR'
          value: '/home/site/wwwroot/data/uploads'
        }
        {
          name: 'DATABASE_URL'
          value: 'postgresql://${postgresAdminUser}:${postgresAdminPassword}@${postgres.name}.postgres.database.azure.com:5432/enturnamiento?sslmode=require'
        }
        {
          name: 'AZURE_STORAGE_ACCOUNT'
          value: storage.name
        }
        {
          name: 'AZURE_STORAGE_CONTAINER'
          value: blobContainerName
        }
      ]
    }
  }
}

output webAppUrl string = 'https://${webApp.properties.defaultHostName}'
output postgresHost string = '${postgres.name}.postgres.database.azure.com'
output storageName string = storage.name
