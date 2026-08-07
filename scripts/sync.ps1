param([int]$Interval = 0)

$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$desktopIP = "100.69.113.41"
$laptopIP = "100.100.66.117"
$servicePorts = @(8000, 8786, 9124, 9999)
$selfIP = (tailscale ip -4 2>&1 | Out-String).Trim()
if ($selfIP -match $desktopIP) { $machine = "desktop" }
elseif ($selfIP -match $laptopIP) { $machine = "laptop" }
else {
    $machine = $env:TEAM_MACHINE
    if (-not $machine) { $machine = (hostname).ToLower() }
}
$otherIP = if ($machine -match "laptop") { $desktopIP } else { $laptopIP }
Set-Location $repo

$lastGitHub = [datetime]::MinValue
$lastTailscale = [datetime]::MinValue
$lastCluster = [datetime]::MinValue

function Do-GitHub {
    Write-Host "`n=== GITHUB $(Get-Date -Format 'HH:mm:ss') ===" -ForegroundColor Cyan

    git fetch origin 2>&1 | Out-Null
    $mainBehind = git rev-list --count HEAD..origin/main 2>&1
    if ($mainBehind -gt 0) {
        Write-Host "[PULL] $mainBehind commits behind" -ForegroundColor Green
        git pull origin main 2>&1
    }

    Write-Host "`n--- OPEN ISSUES ---" -ForegroundColor Yellow
    gh issue list --state open 2>&1

    Write-Host "`n--- NEW COMMENTS ---" -ForegroundColor Yellow
    $nums = gh issue list --state open --json number --jq '.[].number' 2>&1
    foreach ($n in $nums) {
        $n = $n.Trim()
        $jq = '.comments[-1:][] | "' + $n + ' by \(.author.login): \(.body[0:300])"'
        $c = gh issue view $n --json comments --jq $jq 2>&1
        if ($LASTEXITCODE -eq 0 -and $c) { Write-Host "  $c" }
    }
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

function Do-Tailscale {
    Write-Host "`n=== TAILSCALE $(Get-Date -Format 'HH:mm:ss') ===" -ForegroundColor Cyan
    Write-Host "Local: $machine ($selfIP)   Other: $otherIP"

    Write-Host "`n--- Mesh status ---"
    $status = (tailscale status 2>&1 | Out-String)
    foreach ($ip in @($desktopIP, $laptopIP)) {
        $line = ($status -split "`r?`n") | Where-Object { $_ -match [regex]::Escape($ip) } | Select-Object -First 1
        if ($line) { Write-Host "  $($line.Trim())" } else { Write-Host "  $ip  (not in mesh / tailscale down)" -ForegroundColor Red }
    }

    Write-Host "`n--- Ping other machine ($otherIP) ---"
    $result = (& tailscale ping -c 2 $otherIP 2>&1 | ForEach-Object { $_.ToString() } | Out-String)
    if ($result -match "pong") {
        $latency = if ($result -match "in (\d+)\s*ms") { $matches[1] + "ms" } else { "?" }
        if ($result -match "DERP") { Write-Host "  REACHABLE (latency ~$latency, via DERP relay - direct path not established)" -ForegroundColor Yellow }
        else { Write-Host "  REACHABLE (latency ~$latency)" -ForegroundColor Green }
        $script:lastTailscaleOK = $true
    } else {
        Write-Host "  UNREACHABLE" -ForegroundColor Red
        $script:lastTailscaleOK = $false
    }
    Write-Host ($result.Trim())

    Write-Host "`n--- Other machine services ---"
    foreach ($p in $servicePorts) {
        $open = Test-Port $otherIP $p
        $flag = if ($open) { "OPEN" } else { "closed" }
        $color = if ($open) { "Green" } else { "DarkGray" }
        Write-Host ("  {0}:{1}  {2}" -f $otherIP, $p, $flag) -ForegroundColor $color
    }

    Write-Host "`n--- Local listening ports ---"
    $local = netstat -ano | Select-String "LISTENING" | Where-Object { $_ -match ":(8000|8786|9124|9999)\s" }
    if ($local) { Write-Host ($local -join "`n") } else { Write-Host "  (none of $($servicePorts -join ', '))" }

    Write-Host "`n--- Established connections to $otherIP ---"
    $estab = netstat -ano | Select-String "ESTABLISHED" | Where-Object { $_ -match $otherIP }
    if ($estab) { Write-Host ($estab -join "`n") } else { Write-Host "  (none)" }

    if ($script:lastTailscaleOK) {
        Write-Host "`n  TAILSCALE VERDICT: PASS" -ForegroundColor Green
    } else {
        Write-Host "`n  TAILSCALE VERDICT: FAIL (peer unreachable - git sync is the fallback)" -ForegroundColor Red
    }
}

function Do-Cluster {
    Write-Host "`n=== DASK CLUSTER $(Get-Date -Format 'HH:mm:ss') ===" -ForegroundColor Cyan
    $scheduler = "tcp://${desktopIP}:8786"
    if (-not (Test-Port $desktopIP 8786)) {
        Write-Host "  scheduler unreachable at ${desktopIP}:8786 (run scripts\start-cluster.ps1)" -ForegroundColor Red
        Write-Host "  CLUSTER VERDICT: DOWN" -ForegroundColor Red
        return
    }
    $out = (& python "$repo\scripts\cluster_health.py" --scheduler $scheduler 2>&1 | Out-String)
    try {
        $j = $out.Trim() | ConvertFrom-Json
        if ($j.reachable) {
            Write-Host "  scheduler OK ($scheduler)" -ForegroundColor Green
            if ($j.workers -gt 0) {
                Write-Host ("  workers: {0} [{1}]" -f $j.workers, ($j.addresses -join ", ")) -ForegroundColor Green
                Write-Host "  CLUSTER VERDICT: PASS" -ForegroundColor Green
            } else {
                Write-Host "  workers: 0 - laptop worker not connected" -ForegroundColor Yellow
                Write-Host "  CLUSTER VERDICT: DEGRADED" -ForegroundColor Yellow
            }
        } else {
            Write-Host "  probe error: $($j.error)" -ForegroundColor Red
            Write-Host "  CLUSTER VERDICT: DOWN" -ForegroundColor Red
        }
    } catch {
        Write-Host "  probe parse failed: $out" -ForegroundColor Red
        Write-Host "  CLUSTER VERDICT: DOWN" -ForegroundColor Red
    }
}

function Do-OneCycle {
    $now = [datetime]::Now

    if (($now - $lastTailscale).TotalSeconds -ge 60 -or $lastTailscale -eq [datetime]::MinValue) {
        Do-Tailscale
        $script:lastTailscale = $now
    }

    if (($now - $lastCluster).TotalSeconds -ge 120 -or $lastCluster -eq [datetime]::MinValue) {
        Do-Cluster
        $script:lastCluster = $now
    }

    if (($now - $lastGitHub).TotalSeconds -ge 60 -or $lastGitHub -eq [datetime]::MinValue) {
        Do-GitHub
        $script:lastGitHub = $now
    }
}

if ($Interval -gt 0) {
    Write-Host "Monitoring every ${Interval}s. Ctrl+C to stop" -ForegroundColor Magenta
    while ($true) {
        Do-OneCycle
        Start-Sleep -Seconds $Interval
    }
} else {
    Do-Tailscale
    Do-Cluster
    Do-GitHub
}

