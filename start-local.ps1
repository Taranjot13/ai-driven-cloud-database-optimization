$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$venvPython = Join-Path $root ".venv\Scripts\python.exe"
$frontendDir = Join-Path $root "frontend"
$npmCmd = (Get-Command npm -ErrorAction Stop).Source
$backendUrl = "http://127.0.0.1:8000/api/health"
$siteUrl = "http://localhost:5173"

if (-not (Test-Path $venvPython)) {
    Write-Error "Python virtual environment not found at $venvPython. Run: python -m venv .venv"
    exit 1
}

if (-not (Test-Path $frontendDir)) {
    Write-Error "Frontend directory not found at $frontendDir"
    exit 1
}

if (-not (Test-Path (Join-Path $frontendDir "node_modules"))) {
    Write-Host "Installing frontend dependencies..."
    Push-Location $frontendDir
    npm install
    Pop-Location
}

Write-Host "Starting API on $backendUrl"
Start-Process -FilePath $venvPython -ArgumentList @(
    "-m",
    "uvicorn",
    "src.api:app",
    "--host",
    "127.0.0.1",
    "--port",
    "8000"
) -WorkingDirectory $root -WindowStyle Minimized

Start-Sleep -Seconds 3

Write-Host "Starting frontend on $siteUrl"
Start-Process -FilePath $npmCmd -ArgumentList @(
    "run",
    "dev",
    "--",
    "--host",
    "0.0.0.0",
    "--port",
    "5173"
) -WorkingDirectory $frontendDir -WindowStyle Minimized

Start-Sleep -Seconds 2
Start-Process $siteUrl

Write-Host ""
Write-Host "Open the site here: $siteUrl"
Write-Host "API health: $backendUrl"
Write-Host ""
Write-Host "The API and frontend are running in separate background processes."
Write-Host "Close the terminal or terminate those processes when you are done."
