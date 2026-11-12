param([int]$Port = 5393, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
$taskUrl = "http://127.0.0.1:$Port/"
# The packaged studio carries the checked athlete-manifest.json (docs/ATHLETE_MANIFEST.md); the
# legacy manifest.json is no longer part of a studio build.
$taskManifestPath = Join-Path $PSScriptRoot 'studio\athlete-assets\athlete-manifest.json'
if (-not (Test-Path -LiteralPath $taskManifestPath)) { throw 'The packaged studio folder, or its athlete-manifest.json, is missing beside this launcher.' }

function Get-ModelHash($manifest) {
    $model = @($manifest.files.PSObject.Properties | Where-Object { $_.Value.role -eq 'model' })
    if ($model.Count -ne 1) { return $null }
    return $model[0].Value.sha256
}

$taskHash = Get-ModelHash (Get-Content -LiteralPath $taskManifestPath -Raw | ConvertFrom-Json)
if (-not $taskHash) { throw 'The packaged athlete-manifest.json names no single model.' }

function Read-ServedAthleteHash {
    try {
        return Get-ModelHash (Invoke-RestMethod -Uri ($taskUrl + 'athlete-assets/athlete-manifest.json') -TimeoutSec 2)
    } catch { return $null }
}

$taskExisting = Read-ServedAthleteHash
if ($taskExisting -and $taskExisting -ne $taskHash) { throw "Port $Port serves a different athlete build. Choose another -Port." }
if (-not $taskExisting) {
    $taskPython = (Get-Command python -ErrorAction Stop).Source
    $taskProcess = Start-Process -FilePath $taskPython -ArgumentList @('serve.py', '--root', 'studio', '--port', "$Port") -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $PSScriptRoot 'studio-server.log') -RedirectStandardError (Join-Path $PSScriptRoot 'studio-server-error.log')
    for ($taskAttempt = 0; $taskAttempt -lt 20; $taskAttempt++) {
        if ((Read-ServedAthleteHash) -eq $taskHash) { break }
        if ($taskProcess.HasExited) { throw 'The studio server exited. Check studio-server-error.log or choose another -Port.' }
        Start-Sleep -Milliseconds 250
    }
    if ((Read-ServedAthleteHash) -ne $taskHash) { throw 'The studio did not become ready.' }
    Set-Content -LiteralPath (Join-Path $PSScriptRoot 'studio-server.pid') -Value $taskProcess.Id
}
Write-Output "Athlete studio is ready: $taskUrl"
if (-not $NoBrowser) { Start-Process $taskUrl }
