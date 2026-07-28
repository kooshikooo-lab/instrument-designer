<#
.SYNOPSIS
    Start all Desktop session services.
.DESCRIPTION
    Starts: Dask scheduler, Dask workers, GitHub monitor, HTTP messaging server.
    Run this at the beginning of each session.
#>
$ProjectRoot = "C:\Users\Admin\.copilot\repos\instrument-designer"
$Python = "python"

Write-Host "=== Starting Desktop Session Services ===" -ForegroundColor Cyan
Write-Host "Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host ""

# Kill any leftover python processes from previous session
Write-Host "[1/4] Cleaning up old processes..." -ForegroundColor Yellow
Get-Process -Name python -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep 2

Set-Location $ProjectRoot

# 1. Dask Scheduler (port 9797, dashboard 9798)
Write-Host "[2/4] Starting Dask scheduler on port 9797..." -ForegroundColor Yellow
$schedJob = Start-Process -WindowStyle Hidden -FilePath $Python -ArgumentList @(
    "-m", "distributed.cli.dask_scheduler",
    "--port", "9797",
    "--dashboard-address", ":9798"
) -PassThru -NoNewWindow
Start-Sleep 3

# 2. Dask Workers (2 workers, 8 threads each)
Write-Host "      Starting 2 Dask workers (8 threads each)..." -ForegroundColor Yellow
$workerJob = Start-Process -WindowStyle Hidden -FilePath $Python -ArgumentList @(
    "-m", "distributed.cli.dask_worker",
    "tcp://100.69.113.41:9797",
    "--nworkers", "2",
    "--nthreads", "8"
) -PassThru -NoNewWindow
Start-Sleep 2

# 3. GitHub Monitor (polls Discussion #23, PRs, issues, commits every 60s)
Write-Host "[3/4] Starting GitHub monitor..." -ForegroundColor Yellow
$monJob = Start-Process -WindowStyle Hidden -FilePath $Python -ArgumentList @(
    "$ProjectRoot\scripts\github_monitor.py"
) -PassThru -NoNewWindow

# 4. HTTP Messaging Server (port 9124 - reachable via Tailscale)
Write-Host "[4/4] Starting HTTP messaging server on port 9124..." -ForegroundColor Yellow
$msgJob = Start-Process -WindowStyle Hidden -FilePath $Python -ArgumentList @(
    "$ProjectRoot\scripts\lan_msg.py", "server", "9124"
) -PassThru -NoNewWindow

Start-Sleep 1

Write-Host ""
Write-Host "=== Session Services Running ===" -ForegroundColor Green
Write-Host "  Dask Scheduler:   tcp://100.69.113.41:9797"
Write-Host "  Dask Dashboard:   http://100.69.113.41:9798/status"
Write-Host "  Dask Workers:     2 workers, 16 threads total"
Write-Host "  GitHub Monitor:   polls Discussion #23 every 60s"
Write-Host "  HTTP Messaging:   port 9124"
Write-Host ""

# Run final check
Write-Host "=== Running verification ===" -ForegroundColor Cyan
& $Python "$ProjectRoot\scripts\startup_check.py" --verbose
