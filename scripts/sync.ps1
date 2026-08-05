param([int]$Interval = 0)

$repo = "C:\Users\Admin\Desktop\instrument-designer"
$chatPort = 9999
$desktopIP = "100.69.113.41"
$laptopIP = "100.100.66.117"
Set-Location $repo

$lastGitHub = [datetime]::MinValue
$lastTailscale = [datetime]::MinValue

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

function Do-Tailscale {
    Write-Host "`n=== TAILSCALE $(Get-Date -Format 'HH:mm:ss') ===" -ForegroundColor Cyan
    Write-Host "--- Ping desktop ---"
    $result = tailscale ping -c 2 $desktopIP 2>&1
    Write-Host $result

    Write-Host "`n--- Listening ports ---"
    netstat -ano | Select-String "LISTENING" | Select-String $chatPort

    Write-Host "`n--- Established connections ---"
    $estab = netstat -ano | Select-String "ESTABLISHED" | Select-String $chatPort
    if ($estab) { Write-Host $estab } else { Write-Host "  (none)" }
}

function Do-OneCycle {
    $now = [datetime]::Now

    if (($now - $lastTailscale).TotalSeconds -ge 60 -or $lastTailscale -eq [datetime]::MinValue) {
        Do-Tailscale
        $script:lastTailscale = $now
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
    Do-GitHub
}
