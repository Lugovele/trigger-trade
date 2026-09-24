param(
    [ValidateSet("web", "trading-worker", "scheduler")]
    [string[]] $Roles = @("web", "trading-worker", "scheduler")
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ResourceGroup = "triggertrade-rg"
$AcrName = "triggertradeacr"
$AcrLoginServer = "triggertradeacr-dcfmhtd6fmaubtac.azurecr.io"
$AcrRepository = "triggertrade-web"
$ContainerAppsEnvironment = "triggertrade-env-centralus"
$UserAssignedIdentity = "triggertrade-pull-id"
$ContainerAppsByRole = @{
    "web" = "triggertrade-web-centralus"
    "trading-worker" = "triggertrade-trading-worker-centralus"
    "scheduler" = "triggertrade-scheduler-centralus"
}
$ScaleByRole = @{
    "web" = @{ min = 2; max = 4 }
    "trading-worker" = @{ min = 1; max = 1 }
    "scheduler" = @{ min = 1; max = 1 }
}
$CommonEnvVars = @(
    "TRIGGERTRADE_RUNTIME_MODE=production",
    "TRIGGERTRADE_TRADING_MODE=paper",
    "TRIGGERTRADE_LIVE_TRADING_ENABLED=false",
    "TRIGGERTRADE_EXECUTION_VENUE=bybit_demo_futures",
    "TRIGGERTRADE_ACTIVE_EXECUTION_VENUE=bybit_demo_futures",
    "TRIGGERTRADE_TEST_EXECUTION_VENUE=local_test_simulation",
    "TRIGGERTRADE_EXCHANGE=bybit",
    "TRIGGERTRADE_MARKET=linear",
    "TRIGGERTRADE_CATEGORY=linear",
    "TRIGGERTRADE_BYBIT_ENV=demo",
    "BYBIT_BASE_URL=https://api-demo.bybit.com",
    "TRIGGERTRADE_POSTGRES_DSN=secretref:postgres-dsn",
    "TRIGGERTRADE_POSTGRES_SCHEMA=public",
    "TRIGGERTRADE_RESEARCH_DEMO_HANDOFF_ENABLED=true"
)
$HealthTimeoutSeconds = 300
$HealthPollIntervalSeconds = 10

function Invoke-CheckedCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,

        [Parameter(Mandatory = $true)]
        [string[]] $Arguments,

        [Parameter(Mandatory = $true)]
        [string] $FailureMessage
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage Exit code: $LASTEXITCODE"
    }
}

function Get-CheckedCommandOutput {
    param(
        [Parameter(Mandatory = $true)]
        [string] $FilePath,

        [Parameter(Mandatory = $true)]
        [string[]] $Arguments,

        [Parameter(Mandatory = $true)]
        [string] $FailureMessage
    )

    $output = & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "$FailureMessage Exit code: $LASTEXITCODE"
    }

    return ($output | Out-String).Trim()
}

function Test-RequiredCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name
    )

    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required CLI '$Name' was not found on PATH."
    }
}

function Wait-Healthz {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Uri,

        [Parameter(Mandatory = $true)]
        [int] $TimeoutSeconds,

        [Parameter(Mandatory = $true)]
        [int] $PollIntervalSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastError = $null

    while ((Get-Date) -lt $deadline) {
        try {
            $request = [System.Net.HttpWebRequest]::Create($Uri)
            $request.Method = "GET"
            $request.Timeout = 10000
            $request.ReadWriteTimeout = 10000

            $response = $request.GetResponse()
            try {
                $statusCode = [int] $response.StatusCode
                if ($statusCode -eq 200) {
                    return "HTTP 200"
                }

                $lastError = "HTTP $statusCode"
            }
            finally {
                $response.Close()
            }
        }
        catch [System.Net.WebException] {
            if ($_.Exception.Response -ne $null) {
                $statusCode = [int] $_.Exception.Response.StatusCode
                $lastError = "HTTP $statusCode"
                $_.Exception.Response.Close()
            }
            else {
                $lastError = $_.Exception.Message
            }
        }
        catch {
            $lastError = $_.Exception.Message
        }

        Start-Sleep -Seconds $PollIntervalSeconds
    }

    if ([string]::IsNullOrWhiteSpace($lastError)) {
        $lastError = "no response"
    }

    throw "Health check failed for $Uri after $TimeoutSeconds seconds. Last result: $lastError"
}

function Wait-ContainerAppReady {
    param(
        [Parameter(Mandatory = $true)]
        [string] $Name,

        [Parameter(Mandatory = $true)]
        [string] $ResourceGroup,

        [Parameter(Mandatory = $true)]
        [int] $TimeoutSeconds,

        [Parameter(Mandatory = $true)]
        [int] $PollIntervalSeconds
    )

    $deadline = (Get-Date).AddSeconds($TimeoutSeconds)
    $lastState = $null

    while ((Get-Date) -lt $deadline) {
        $lastState = Get-CheckedCommandOutput -FilePath "az" -Arguments @(
            "containerapp", "show",
            "--name", $Name,
            "--resource-group", $ResourceGroup,
            "--query", "properties.provisioningState",
            "--output", "tsv",
            "--only-show-errors"
        ) -FailureMessage "Unable to retrieve Azure Container App provisioning state for $Name."

        if ($lastState -eq "Succeeded") {
            return $lastState
        }

        Start-Sleep -Seconds $PollIntervalSeconds
    }

    if ([string]::IsNullOrWhiteSpace($lastState)) {
        $lastState = "unknown"
    }

    throw "Container app $Name did not become ready after $TimeoutSeconds seconds. Last provisioning state: $lastState"
}

Test-RequiredCommand -Name "docker"
Test-RequiredCommand -Name "az"
Test-RequiredCommand -Name "git"

Invoke-CheckedCommand -FilePath "az" -Arguments @("account", "show", "--only-show-errors", "--output", "none") -FailureMessage "Azure CLI authentication check failed. Run 'az login' and try again."

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

$IsInsideWorkTree = Get-CheckedCommandOutput -FilePath "git" -Arguments @("rev-parse", "--is-inside-work-tree") -FailureMessage "Unable to verify git work tree."
if ($IsInsideWorkTree -ne "true") {
    throw "Script location is not inside a git work tree: $RepoRoot"
}

$GitStatus = Get-CheckedCommandOutput -FilePath "git" -Arguments @("status", "--porcelain=v1", "--untracked-files=no") -FailureMessage "Unable to inspect git working tree."
if (-not [string]::IsNullOrWhiteSpace($GitStatus)) {
    throw "Tracked working tree is not clean. Commit or revert tracked changes before deploying so the image matches the git SHA."
}

$GitSha = Get-CheckedCommandOutput -FilePath "git" -Arguments @("rev-parse", "HEAD") -FailureMessage "Unable to determine current git SHA."
$LocalImage = "${AcrRepository}:$GitSha"
$RemoteImage = "${AcrLoginServer}/${AcrRepository}:$GitSha"

Write-Host "Building image $LocalImage from $RepoRoot"
Invoke-CheckedCommand -FilePath "docker" -Arguments @("build", "--tag", $LocalImage, ".") -FailureMessage "Docker build failed."

Write-Host "Logging in to Azure Container Registry $AcrName"
Invoke-CheckedCommand -FilePath "az" -Arguments @("acr", "login", "--name", $AcrName, "--only-show-errors") -FailureMessage "Azure Container Registry login failed."

Write-Host "Pushing image $RemoteImage"
Invoke-CheckedCommand -FilePath "docker" -Arguments @("tag", $LocalImage, $RemoteImage) -FailureMessage "Docker tag failed."
Invoke-CheckedCommand -FilePath "docker" -Arguments @("push", $RemoteImage) -FailureMessage "Docker push failed."

$UserAssignedIdentityId = Get-CheckedCommandOutput -FilePath "az" -Arguments @(
    "identity", "show",
    "--name", $UserAssignedIdentity,
    "--resource-group", $ResourceGroup,
    "--query", "id",
    "--output", "tsv",
    "--only-show-errors"
) -FailureMessage "Unable to resolve user-assigned identity $UserAssignedIdentity."

foreach ($Role in $Roles) {
    $ContainerAppName = $ContainerAppsByRole[$Role]
    $Scale = $ScaleByRole[$Role]
    if ([string]::IsNullOrWhiteSpace($ContainerAppName)) {
        throw "No Azure Container App is configured for role $Role."
    }
    if ($null -eq $Scale) {
        throw "No scaling policy is configured for role $Role."
    }

    $RoleEnvVars = @($CommonEnvVars + "TRIGGERTRADE_PROCESS_ROLE=$Role")
    if ($Role -eq "trading-worker") {
        $RoleEnvVars += @(
            "TRIGGERTRADE_WORKER_ID=centralus-trading-worker-1",
            "BYBIT_API_KEY=secretref:bybit-api-key",
            "BYBIT_API_SECRET=secretref:bybit-api-secret"
        )
    }

    Write-Host "Updating Azure Container App $ContainerAppName for role $Role to $RemoteImage"
    Invoke-CheckedCommand -FilePath "az" -Arguments @(
        "containerapp", "identity", "assign",
        "--name", $ContainerAppName,
        "--resource-group", $ResourceGroup,
        "--user-assigned", $UserAssignedIdentityId,
        "--only-show-errors",
        "--output", "none"
    ) -FailureMessage "Azure Container App identity assignment failed for role $Role."

    Invoke-CheckedCommand -FilePath "az" -Arguments @(
        "containerapp", "update",
        "--name", $ContainerAppName,
        "--resource-group", $ResourceGroup,
        "--image", $RemoteImage,
        "--min-replicas", [string] $Scale.min,
        "--max-replicas", [string] $Scale.max,
        "--set-env-vars"
    ) + $RoleEnvVars + @(
        "--only-show-errors",
        "--output", "none"
    ) -FailureMessage "Azure Container App update failed for role $Role."

    $RevisionName = Get-CheckedCommandOutput -FilePath "az" -Arguments @(
        "containerapp", "show",
        "--name", $ContainerAppName,
        "--resource-group", $ResourceGroup,
        "--query", "properties.latestRevisionName",
        "--output", "tsv",
        "--only-show-errors"
    ) -FailureMessage "Unable to retrieve latest Azure Container App revision name for $Role."

    if ([string]::IsNullOrWhiteSpace($RevisionName)) {
        throw "Azure Container App latest revision name was empty for role $Role."
    }

    $RoleHealthResult = Wait-ContainerAppReady -Name $ContainerAppName -ResourceGroup $ResourceGroup -TimeoutSeconds $HealthTimeoutSeconds -PollIntervalSeconds $HealthPollIntervalSeconds
    Write-Host "$Role role provisioning: $RoleHealthResult"

    if ($Role -eq "web") {
        $AzureFqdn = Get-CheckedCommandOutput -FilePath "az" -Arguments @(
            "containerapp", "show",
            "--name", $ContainerAppName,
            "--resource-group", $ResourceGroup,
            "--query", "properties.configuration.ingress.fqdn",
            "--output", "tsv",
            "--only-show-errors"
        ) -FailureMessage "Unable to retrieve latest Azure Container App FQDN for web role."

        if ([string]::IsNullOrWhiteSpace($AzureFqdn)) {
            throw "Azure Container App FQDN was empty for web role."
        }

        $AzureHealthUri = "https://$AzureFqdn/healthz"
        Write-Host "Polling $AzureHealthUri"
        $AzureHealthResult = Wait-Healthz -Uri $AzureHealthUri -TimeoutSeconds $HealthTimeoutSeconds -PollIntervalSeconds $HealthPollIntervalSeconds

        Write-Host "Web Azure health: $AzureHealthResult"
    }
}

Write-Host ""
Write-Host "Deployment summary"
Write-Host "Git SHA: $GitSha"
Write-Host "Image: $RemoteImage"
Write-Host "Container Apps environment: $ContainerAppsEnvironment"
Write-Host "User-assigned identity: $UserAssignedIdentity"
Write-Host "Roles: $($Roles -join ', ')"
Write-Host "Custom domain and DNS cutover are intentionally not modified by this script."
