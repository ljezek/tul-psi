#Requires -Version 7
<#
.SYNOPSIS
  Run the full E2E suite locally: Docker backend + Vite frontend + Playwright.

.PARAMETER NoBuild
  Skip rebuilding the Docker image (use when only test code changed).

.PARAMETER NoDown
  Keep the Docker stack running after the suite (useful for debugging).

.PARAMETER Spec
  Run a single spec file, e.g. tests/student/student-home.spec.ts

.PARAMETER Headed
  Run Playwright with a visible browser window.
#>
param(
    [switch]$NoBuild,
    [switch]$NoDown,
    [string]$Spec,
    [switch]$Headed
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$RepoRoot = Split-Path $PSScriptRoot -Parent
$FrontendDir = Join-Path $RepoRoot 'frontend'
$E2eDir = $PSScriptRoot

function Write-Step([string]$msg) { Write-Host "`n==> $msg" -ForegroundColor Cyan }
function Fail([string]$msg) { Write-Host "ERROR: $msg" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
# 1. Start backend stack
# ---------------------------------------------------------------------------
Write-Step "Starting Docker Compose backend stack"
$composeFile = Join-Path $RepoRoot 'docker-compose.e2e.yaml'
if ($NoBuild) {
    docker compose -f $composeFile up -d --wait
} else {
    docker compose -f $composeFile up -d --wait --build
}
if ($LASTEXITCODE -ne 0) { Fail "docker compose up failed" }

$viteProcess = $null
$pwExit = 0
try {
    # -----------------------------------------------------------------------
    # 2. Free port 3000 if something is already listening
    # -----------------------------------------------------------------------
    Write-Step "Checking port 3000"
    $owner = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue |
             Select-Object -ExpandProperty OwningProcess -First 1
    if ($owner) {
        Write-Host "  Killing PID $owner that holds port 3000"
        Stop-Process -Id $owner -Force
        Start-Sleep -Milliseconds 500
    }

    # -----------------------------------------------------------------------
    # 3. Build frontend and start Vite preview in the background
    # -----------------------------------------------------------------------
    Write-Step "Building frontend"
    Push-Location $FrontendDir
    try {
        npm install
        if ($LASTEXITCODE -ne 0) { Fail "npm install failed" }

        $env:VITE_API_URL = 'http://localhost:8001'
        npm run build
        if ($LASTEXITCODE -ne 0) { Fail "npm run build failed" }

        Write-Step "Starting Vite preview on port 3000 (background)"
        $viteLog = Join-Path $E2eDir 'vite-preview.log'
        $viteProcess = Start-Process `
            -FilePath 'cmd.exe' `
            -ArgumentList '/c', 'npx vite preview --port 3000 --strictPort' `
            -WorkingDirectory $FrontendDir `
            -NoNewWindow `
            -RedirectStandardOutput $viteLog `
            -RedirectStandardError "$viteLog.err" `
            -PassThru
        Write-Host "  Vite output → $viteLog"
    } finally {
        Pop-Location
    }

    # Wait for Vite to be ready via TCP (avoids proxy issues with Invoke-WebRequest)
    Write-Host "  Waiting for port 3000 ..."
    $deadline = (Get-Date).AddSeconds(30)
    $ready = $false
    while ((Get-Date) -lt $deadline) {
        try {
            $tcp = New-Object System.Net.Sockets.TcpClient
            $tcp.Connect('127.0.0.1', 3000)
            $tcp.Close()
            $ready = $true; break
        } catch { }
        Start-Sleep -Milliseconds 500
    }
    if (-not $ready) { Fail "Vite preview did not become ready within 30 s" }
    Write-Host "  Frontend is ready." -ForegroundColor Green

    # -----------------------------------------------------------------------
    # 4. Install Playwright deps and run tests
    # -----------------------------------------------------------------------
    Write-Step "Installing Playwright dependencies"
    Push-Location $E2eDir
    try {
        npm ci
        if ($LASTEXITCODE -ne 0) { Fail "npm ci failed in e2e/" }

        npx playwright install chromium
        if ($LASTEXITCODE -ne 0) { Fail "playwright install chromium failed" }

        Write-Step "Running Playwright tests"
        if ($Headed -and $Spec) {
            npx playwright test --headed $Spec
        } elseif ($Headed) {
            npx playwright test --headed
        } elseif ($Spec) {
            npx playwright test $Spec
        } else {
            npx playwright test
        }
        $pwExit = $LASTEXITCODE
    } finally {
        Pop-Location
    }

} finally {
    # -----------------------------------------------------------------------
    # 5. Stop Vite preview
    # -----------------------------------------------------------------------
    if ($viteProcess -and -not $viteProcess.HasExited) {
        Write-Step "Stopping Vite preview (PID $($viteProcess.Id))"
        Stop-Process -Id $viteProcess.Id -Force -ErrorAction SilentlyContinue
    }

    # -----------------------------------------------------------------------
    # 6. Tear down Docker stack (unless --NoDown)
    # -----------------------------------------------------------------------
    if (-not $NoDown) {
        Write-Step "Tearing down Docker stack and removing volumes"
        docker compose -f (Join-Path $RepoRoot 'docker-compose.e2e.yaml') down -v
    } else {
        Write-Host "`nDocker stack left running (--NoDown). Stop with:" -ForegroundColor Yellow
        Write-Host "  docker compose -f docker-compose.e2e.yaml down -v"
    }
}

# ---------------------------------------------------------------------------
# 7. Final result
# ---------------------------------------------------------------------------
Write-Host ""
if ($pwExit -ne 0) {
    Write-Host "================================================" -ForegroundColor Red
    Write-Host "  E2E FAILED  (exit code $pwExit)" -ForegroundColor Red
    Write-Host "================================================" -ForegroundColor Red
    Write-Step "Opening Playwright HTML report"
    Push-Location $E2eDir
    npx playwright show-report
    Pop-Location
    exit $pwExit
}

Write-Host "================================================" -ForegroundColor Green
Write-Host "  E2E PASSED" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
