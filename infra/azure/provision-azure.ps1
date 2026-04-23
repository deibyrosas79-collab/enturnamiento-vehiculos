param(
    [string]$Location = "eastus2",
    [string]$ResourceGroupName = "rg-enturnamiento-prod",
    [string]$PlanName = "plan-enturnamiento-prod",
    [string]$WebAppName = "enturnamiento-diana-d79-prod",
    [string]$StorageAccountName = "stenturnad79prod",
    [string]$PostgresServerName = "psql-entd79-prod",
    [string]$PostgresDatabaseName = "enturnamiento",
    [string]$PostgresAdminUser = "evadmin"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Set-ExecutionPolicy -Scope Process Bypass -Force
Import-Module Az.Accounts
Import-Module Az.Resources
Import-Module Az.Websites
Import-Module Az.Storage
Import-Module Az.PostgreSql

Write-Host "Iniciando sesion Azure..." -ForegroundColor Cyan
Connect-AzAccount -UseDeviceAuthentication | Out-Null

$subscription = Get-AzSubscription | Where-Object { $_.State -eq "Enabled" } | Select-Object -First 1
if (-not $subscription) {
    throw "No se encontro una suscripcion habilitada en Azure."
}

Set-AzContext -SubscriptionId $subscription.Id | Out-Null

Write-Host "Suscripcion activa: $($subscription.Name)" -ForegroundColor Green

if (-not (Get-AzResourceGroup -Name $ResourceGroupName -ErrorAction SilentlyContinue)) {
    New-AzResourceGroup -Name $ResourceGroupName -Location $Location | Out-Null
}

if (-not (Get-AzAppServicePlan -ResourceGroupName $ResourceGroupName -Name $PlanName -ErrorAction SilentlyContinue)) {
    New-AzAppServicePlan `
        -ResourceGroupName $ResourceGroupName `
        -Name $PlanName `
        -Location $Location `
        -Tier "Basic" `
        -WorkerSize "Small" `
        -NumberofWorkers 1 `
        -Linux | Out-Null
}

if (-not (Get-AzWebApp -ResourceGroupName $ResourceGroupName -Name $WebAppName -ErrorAction SilentlyContinue)) {
    New-AzWebApp `
        -ResourceGroupName $ResourceGroupName `
        -Name $WebAppName `
        -Location $Location `
        -AppServicePlan $PlanName | Out-Null
}

$webConfig = @{
    linuxFxVersion = "PYTHON|3.12"
    appCommandLine = "python server.py"
    alwaysOn = $false
    ftpsState = "Disabled"
    minTlsVersion = "1.2"
}

Set-AzResource `
    -ResourceGroupName $ResourceGroupName `
    -ResourceType "Microsoft.Web/sites/config" `
    -ResourceName "$WebAppName/web" `
    -ApiVersion "2023-12-01" `
    -PropertyObject $webConfig `
    -Force | Out-Null

if (-not (Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName -ErrorAction SilentlyContinue)) {
    New-AzStorageAccount `
        -ResourceGroupName $ResourceGroupName `
        -Name $StorageAccountName `
        -Location $Location `
        -SkuName Standard_LRS `
        -Kind StorageV2 `
        -MinimumTlsVersion TLS1_2 `
        -AllowBlobPublicAccess $false | Out-Null
}

$storage = Get-AzStorageAccount -ResourceGroupName $ResourceGroupName -Name $StorageAccountName
$ctx = $storage.Context
if (-not (Get-AzStorageContainer -Name "evidencias" -Context $ctx -ErrorAction SilentlyContinue)) {
    New-AzStorageContainer -Name "evidencias" -Context $ctx -Permission Off | Out-Null
}

$existingPg = Get-AzPostgreSqlFlexibleServer -ResourceGroupName $ResourceGroupName -Name $PostgresServerName -ErrorAction SilentlyContinue
$serverIsNew = $false

if (-not $existingPg) {
    $generatedPassword = -join ((48..57 + 65..90 + 97..122 + 33..38) | Get-Random -Count 24 | ForEach-Object { [char]$_ })
    $securePassword = ConvertTo-SecureString $generatedPassword -AsPlainText -Force
    New-AzPostgreSqlFlexibleServer `
        -Name $PostgresServerName `
        -ResourceGroupName $ResourceGroupName `
        -Location $Location `
        -AdministratorUserName $PostgresAdminUser `
        -AdministratorLoginPassword $securePassword `
        -Sku "Standard_B1ms" `
        -SkuTier "Burstable" `
        -Version 16 `
        -StorageInMb 32768 `
        -BackupRetentionDay 7 `
        -HaEnabled "Disabled" `
        -PublicAccess "0.0.0.0" | Out-Null
    $serverIsNew = $true
    Write-Host "Servidor PostgreSQL creado. Guarda la clave del resumen final." -ForegroundColor Yellow
} else {
    Write-Host "Servidor PostgreSQL ya existe. DATABASE_URL se preserva del resumen anterior." -ForegroundColor Yellow
    $generatedPassword = $null
}

if (-not (Get-AzPostgreSqlFlexibleServerDatabase -ResourceGroupName $ResourceGroupName -ServerName $PostgresServerName -Name $PostgresDatabaseName -ErrorAction SilentlyContinue)) {
    New-AzPostgreSqlFlexibleServerDatabase `
        -ResourceGroupName $ResourceGroupName `
        -ServerName $PostgresServerName `
        -Name $PostgresDatabaseName | Out-Null
}

$appSettings = @{
    HOST = "0.0.0.0"
    PORT = "8000"
    WEBSITES_PORT = "8000"
    SCM_DO_BUILD_DURING_DEPLOYMENT = "true"
    UPLOADS_DIR = "/home/site/wwwroot/data/uploads"
    AZURE_STORAGE_ACCOUNT = $StorageAccountName
    AZURE_STORAGE_CONTAINER = "evidencias"
}

if ($serverIsNew -and $generatedPassword) {
    $appSettings["DATABASE_URL"] = "postgresql://${PostgresAdminUser}:${generatedPassword}@${PostgresServerName}.postgres.database.azure.com:5432/${PostgresDatabaseName}?sslmode=require"
} else {
    # Preservar DATABASE_URL existente para no sobreescribir con valor incorrecto
    $existingSettings = (Get-AzWebApp -ResourceGroupName $ResourceGroupName -Name $WebAppName).SiteConfig.AppSettings
    $existingDbUrl = ($existingSettings | Where-Object { $_.Name -eq "DATABASE_URL" }).Value
    if ($existingDbUrl) {
        $appSettings["DATABASE_URL"] = $existingDbUrl
        Write-Host "DATABASE_URL existente preservada." -ForegroundColor Cyan
    }
}

Set-AzWebApp -ResourceGroupName $ResourceGroupName -Name $WebAppName -AppSettings $appSettings | Out-Null

$publishProfilePath = Join-Path $PSScriptRoot "azure-publish-profile.xml"
Get-AzWebAppPublishingProfile -ResourceGroupName $ResourceGroupName -Name $WebAppName -OutputFile $publishProfilePath | Out-Null

$summaryPath = Join-Path $PSScriptRoot "azure-deploy-summary.txt"
@"
Suscripcion: $($subscription.Name)
Resource Group: $ResourceGroupName
Region: $Location
Web App: $WebAppName
URL: https://$WebAppName.azurewebsites.net
Plan: $PlanName
Storage: $StorageAccountName
Contenedor: evidencias
PostgreSQL Server: $PostgresServerName
PostgreSQL DB: $PostgresDatabaseName
PostgreSQL Admin: $PostgresAdminUser
PostgreSQL Password: $(if ($generatedPassword) { $generatedPassword } else { "<ver-resumen-anterior-o-azure-portal>" })
Publish Profile: $publishProfilePath
"@ | Set-Content -Path $summaryPath -Encoding UTF8

Write-Host "Provision Azure completado." -ForegroundColor Green
Write-Host "Resumen: $summaryPath" -ForegroundColor Yellow
