#requires -Version 5.1
<#
.SYNOPSIS
    Launch all 7 backend services locally, each in its own PowerShell window.

.DESCRIPTION
    Reads the .env at repo root (so every service inherits the same vars) and
    starts:
      gateway          :8080
      admin-service    :8001
      search-service   :8002
      booking-service  :8003
      comments-service :8004
      notification-service :8005
      ai-agent-service :8006

    Each window stays open so you can see logs.

.EXAMPLE
    .\scripts\run_all_services.ps1
#>

$ErrorActionPreference = "Stop"

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$EnvFile  = Join-Path $RepoRoot ".env"

if (-not (Test-Path $EnvFile)) {
    Write-Error ".env not found at $EnvFile -- aborting."
    exit 1
}

$Services = @(
    @{ Name = "gateway";              Port = 8080 },
    @{ Name = "admin-service";        Port = 8001 },
    @{ Name = "search-service";       Port = 8002 },
    @{ Name = "booking-service";      Port = 8003 },
    @{ Name = "comments-service";     Port = 8004 },
    @{ Name = "notification-service"; Port = 8005 },
    @{ Name = "ai-agent-service";     Port = 8006 }
)

foreach ($svc in $Services) {
    $svcPath = Join-Path $RepoRoot "services\$($svc.Name)"
    if (-not (Test-Path $svcPath)) {
        Write-Warning "Skipping $($svc.Name) -- directory not found: $svcPath"
        continue
    }
    $title = "hbs-$($svc.Name) :$($svc.Port)"
    # Run from repo root so pydantic-settings env_file='.env' picks up the
    # repo-root .env automatically; tell uvicorn where the app module lives.
    $appDir = "services\$($svc.Name)"
    $cmd    = "cd `"$RepoRoot`"; `$env:PYTHONUNBUFFERED='1'; `$env:PYTHONPATH = `"`$PWD\$appDir;`$PWD\services\shared;`$env:PYTHONPATH`"; uvicorn app.main:app --app-dir `"$appDir`" --host 127.0.0.1 --port $($svc.Port) --reload"
    Write-Host "Starting $title"
    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-Command",
        "`$Host.UI.RawUI.WindowTitle = '$title'; $cmd"
    )
    Start-Sleep -Milliseconds 600
}

Write-Host ""
Write-Host "All services launching. After ~10s try:" -ForegroundColor Green
Write-Host "  Invoke-RestMethod http://127.0.0.1:8080/health"
Write-Host "Then run the smoke test from repo root:"
Write-Host "  python scripts/smoke_test_gateway.py"
