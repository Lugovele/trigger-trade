Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ResourceGroup = "triggertrade-rg"
$AcrName = "triggertradeacr"
$AcrLoginServer = "triggertradeacr-dcfmhtd6fmaubtac.azurecr.io"
$AcrRepository = "triggertrade-web"
$ContainerAppName = "triggertrade-web"
$CustomDomain = "tt.lugovele.com"
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

Test-RequiredCommand -Name "docker"
Test-RequiredCommand -Name "az"
Test-RequiredCommand -Name "git"

Invoke-CheckedCommand -FilePath "az" -Arguments @("account", "show", "--only-show-errors", "--output", "none") -FailureMessage "Azure CLI authentication check failed. Run 'az login' and try again."

$RepoRoot = Get-CheckedCommandOutput -FilePath "git" -Arguments @("rev-parse", "--show-toplevel") -FailureMessage "Unable to determine repository root."
Set-Location $RepoRoot

$GitStatus = Get-CheckedCommandOutput -FilePath "git" -Arguments @("status", "--porcelain=v1") -FailureMessage "Unable to inspect git working tree."
if (-not [string]::IsNullOrWhiteSpace($GitStatus)) {
    throw "Working tree is not clean. Commit, stash, or remove local changes before deploying so the image matches the git SHA."
}

$GitSha = Get-CheckedCommandOutput -FilePath "git" -Arguments @("rev-parse", "--short", "HEAD") -FailureMessage "Unable to determine current git SHA."
$LocalImage = "${AcrRepository}:$GitSha"
$RemoteImage = "${AcrLoginServer}/${AcrRepository}:$GitSha"

Write-Host "Building image $LocalImage from $RepoRoot"
Invoke-CheckedCommand -FilePath "docker" -Arguments @("build", "--tag", $LocalImage, ".") -FailureMessage "Docker build failed."

Write-Host "Logging in to Azure Container Registry $AcrName"
Invoke-CheckedCommand -FilePath "az" -Arguments @("acr", "login", "--name", $AcrName, "--only-show-errors") -FailureMessage "Azure Container Registry login failed."

Write-Host "Pushing image $RemoteImage"
Invoke-CheckedCommand -FilePath "docker" -Arguments @("tag", $LocalImage, $RemoteImage) -FailureMessage "Docker tag failed."
Invoke-CheckedCommand -FilePath "docker" -Arguments @("push", $RemoteImage) -FailureMessage "Docker push failed."

Write-Host "Updating Azure Container App $ContainerAppName to $RemoteImage"
Invoke-CheckedCommand -FilePath "az" -Arguments @(
    "containerapp", "update",
    "--name", $ContainerAppName,
    "--resource-group", $ResourceGroup,
    "--image", $RemoteImage,
    "--only-show-errors",
    "--output", "none"
) -FailureMessage "Azure Container App update failed."

$RevisionName = Get-CheckedCommandOutput -FilePath "az" -Arguments @(
    "containerapp", "show",
    "--name", $ContainerAppName,
    "--resource-group", $ResourceGroup,
    "--query", "properties.latestRevisionName",
    "--output", "tsv",
    "--only-show-errors"
) -FailureMessage "Unable to retrieve latest Azure Container App revision name."

$AzureFqdn = Get-CheckedCommandOutput -FilePath "az" -Arguments @(
    "containerapp", "show",
    "--name", $ContainerAppName,
    "--resource-group", $ResourceGroup,
    "--query", "properties.configuration.ingress.fqdn",
    "--output", "tsv",
    "--only-show-errors"
) -FailureMessage "Unable to retrieve Azure Container App FQDN."

if ([string]::IsNullOrWhiteSpace($RevisionName)) {
    throw "Azure Container App latest revision name was empty."
}

if ([string]::IsNullOrWhiteSpace($AzureFqdn)) {
    throw "Azure Container App FQDN was empty."
}

$AzureHealthUri = "https://$AzureFqdn/healthz"
$CustomDomainHealthUri = "https://$CustomDomain/healthz"

Write-Host "Polling $AzureHealthUri"
$AzureHealthResult = Wait-Healthz -Uri $AzureHealthUri -TimeoutSeconds $HealthTimeoutSeconds -PollIntervalSeconds $HealthPollIntervalSeconds

Write-Host "Polling $CustomDomainHealthUri"
$CustomDomainHealthResult = Wait-Healthz -Uri $CustomDomainHealthUri -TimeoutSeconds $HealthTimeoutSeconds -PollIntervalSeconds $HealthPollIntervalSeconds

Write-Host ""
Write-Host "Deployment summary"
Write-Host "Git SHA: $GitSha"
Write-Host "Image: $RemoteImage"
Write-Host "Azure revision: $RevisionName"
Write-Host "Azure FQDN: $AzureFqdn"
Write-Host "Azure health: $AzureHealthResult"
Write-Host "Custom-domain health: $CustomDomainHealthResult"
