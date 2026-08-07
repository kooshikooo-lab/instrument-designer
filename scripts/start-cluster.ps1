param(
    [switch]$LocalWorker,
    [int]$LocalWorkers = 0
)

# Repo root derived from script location (works on both machines).
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path

$desktopIP = "100.69.113.41"
$laptopIP = "100.100.66.117"

$selfIP = (tailscale ip -4 2>&1 | Out-String).Trim()
if ($selfIP -match $desktopIP) { $machine = "desktop" }
elseif ($selfIP -match $laptopIP) { $machine = "laptop" }
else {
    $machine = $env:TEAM_MACHINE
    if (-not $machine) { $machine = (hostname).ToLower() }
}

function Test-Port([string]$Target, [int]$Port, [int]$TimeoutMs = 1500) {
    try {
        $client = New-Object System.Net.Sockets.TcpClient
        $async = $client.BeginConnect($Target, $Port, $null, $null)
        $ok = $async.AsyncWaitHandle.WaitOne($TimeoutMs, $false)
        $open = $ok -and $client.Connected
        $client.Close()
        return $open
    } catch {
        return $false
    }
}

function Show-ClusterHealth {
    Write-Host "`n--- Cluster health ---"
    if (-not (Test-Port $desktopIP 8786)) {
        Write-Host "  scheduler unreachable at ${desktopIP}:8786" -ForegroundColor Red
        return
    }
    $out = (& python "$repo\scripts\cluster_health.py" --scheduler "tcp://${desktopIP}:8786" 2>&1 | Out-String)
    try {
        $j = $out.Trim() | ConvertFrom-Json
        if ($j.reachable) {
            Write-Host ("  scheduler OK, workers: {0} [{1}]" -f $j.workers, ($j.addresses -join ", ")) -ForegroundColor Green
        } else {
            Write-Host "  probe error: $($j.error)" -ForegroundColor Red
        }
    } catch {
        Write-Host "  probe parse failed: $out" -ForegroundColor Red
    }
}

if ($machine -match "laptop") {
    # Laptop role: run a worker attached to the desktop scheduler.
    $n = if ($LocalWorkers -gt 0) { $LocalWorkers } else { 1 }
    Write-Host "Machine: laptop -> starting $n worker(s) attached to desktop scheduler (${desktopIP}:8786)" -ForegroundColor Cyan
    for ($i = 1; $i -le $n; $i++) {
        & python "$repo\scripts\spawn_worker.py" "tcp://${desktopIP}:8786" "$i"
        Write-Host "  worker $i started (logs: scripts\dask_worker_$i.log)"
    }
    Start-Sleep -Seconds 8
    Show-ClusterHealth
} else {
    # Desktop role: ensure the scheduler is running, optionally local workers.
    Write-Host "Machine: desktop -> scheduler role" -ForegroundColor Cyan
    if (Test-Port $desktopIP 8786) {
        Write-Host "  scheduler already running at ${desktopIP}:8786"
    } else {
        Write-Host "  starting scheduler (python scripts\start_scheduler.py)"
        & python "$repo\scripts\start_scheduler.py" 2>&1
        Start-Sleep -Seconds 5
    }
    if ($LocalWorker -or $LocalWorkers -gt 0) {
        $n = if ($LocalWorkers -gt 0) { $LocalWorkers } else { 1 }
        Write-Host "  starting $n local worker(s)"
        for ($i = 1; $i -le $n; $i++) {
            & python "$repo\scripts\spawn_worker.py" "tcp://${desktopIP}:8786" "local$i"
        }
        Start-Sleep -Seconds 8
    }
    Show-ClusterHealth
    Write-Host "`nTip: ask the laptop to run: powershell -File scripts\start-cluster.ps1" -ForegroundColor Magenta
}

