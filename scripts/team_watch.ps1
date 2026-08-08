param(
    [int]$PollSeconds = 3,
    [switch]$NoToast,
    [switch]$NoSound,
    [string]$LogFile = "scripts\.team_watch.log"
)

$ErrorActionPreference = "Continue"

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir
$stateFile = Join-Path $scriptDir ".team_state.json"
$logPath = Join-Path $repoRoot $LogFile
$inboxPath = Join-Path $scriptDir ".team_inbox.md"

function Write-Log {
    param([string]$Line)
    $stamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    try {
        Add-Content -LiteralPath $logPath -Value "[$stamp] $Line" -Encoding UTF8
    } catch { }
}

function Show-Notify {
    param([string]$Title, [string]$Body)
    if (-not $NoSound) {
        try { [System.Media.SystemSounds]::Exclamation.Play() } catch { }
    }
    if (-not $NoToast) {
        try {
            Add-Type -AssemblyName System.Windows.Forms
            Add-Type -AssemblyName System.Drawing
            $icon = New-Object System.Windows.Forms.NotifyIcon
            $icon.Icon = [System.Drawing.SystemIcons]::Exclamation
            $icon.Visible = $true
            $icon.BalloonTipTitle = $Title
            $icon.BalloonTipText = $Body
            $icon.BalloonTipIcon = [System.Windows.Forms.ToolTipIcon]::Info
            $icon.ShowBalloonTip(10000)
            Start-Sleep -Milliseconds 100
            $icon.Dispose()
        } catch {
            Write-Log "toast failed: $_"
        }
    }
}

Write-Log "team_watch started (poll ${PollSeconds}s, toast=$( -not $NoToast), sound=$( -not $NoSound))"

while ($true) {
    try {
        $json = & python (Join-Path $scriptDir "team_chat.py") sync --json 2>&1 | Out-String
        $obj = $json | ConvertFrom-Json
    } catch {
        Write-Log "sync error: $_"
        Start-Sleep -Seconds $PollSeconds
        continue
    }

    foreach ($m in $obj.messages) {
        if ($null -ne $m.other -and -not $m.other) { continue }
        $body = [string]$m.body
        $snippet = ($body -replace "\s+", " ").Trim()
        if ($snippet.Length -gt 160) { $snippet = $snippet.Substring(0, 157) + "..." }
        Write-Log "NEW from $($m.user): $snippet"
        try {
            Add-Content -LiteralPath $inboxPath -Value ("`n---`n[{0}] {1}:" -f $m.date, $m.user) -Encoding UTF8
            Add-Content -LiteralPath $inboxPath -Value $body -Encoding UTF8
        } catch { Write-Log "inbox write failed: $_" }
        Show-Notify -Title "Team message from $($m.user)" -Body $snippet
    }
    Start-Sleep -Seconds $PollSeconds
}
