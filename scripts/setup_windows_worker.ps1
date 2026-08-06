param(
    [string]$Scheduler = "tcp://100.69.113.41:8786",
    [string]$MachineName = "scrappy",
    [string]$RepoUrl = "https://github.com/kooshikooo-lab/instrument-designer.git",
    [string]$Branch = "opencode/main/desktop",
    [string]$InstallDir = "$env:USERPROFILE\instrument-designer",
    [switch]$StartWorker
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host "`n=== $Message ===" -ForegroundColor Cyan
}

function Test-Command {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

# -----------------------------------------------------------------------------
# 1. Machine identity
# -----------------------------------------------------------------------------
Write-Step "Setting TEAM_MACHINE=$MachineName"
[Environment]::SetEnvironmentVariable("TEAM_MACHINE", $MachineName, "User")
$env:TEAM_MACHINE = $MachineName

# -----------------------------------------------------------------------------
# 2. Install Python 3.12 (if missing)
# -----------------------------------------------------------------------------
if (-not (Test-Command python)) {
    Write-Step "Python not found; downloading Python 3.12"
    $pyInstaller = "$env:TEMP\python-3.12.9-amd64.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.12.9/python-3.12.9-amd64.exe" -OutFile $pyInstaller -UseBasicParsing
    Write-Host "Installing Python (this may take a minute)..."
    & $pyInstaller /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 | Out-Null
    if (-not (Test-Command python)) {
        throw "Python installation failed. Please restart this script after reopening PowerShell."
    }
}
$pyVersion = (& python --version 2>&1)
Write-Host "Python: $pyVersion"

# Upgrade pip and install pip-tools so lock files can be consumed
python -m pip install --upgrade pip pip-tools -q

# -----------------------------------------------------------------------------
# 3. Install Git (if missing)
# -----------------------------------------------------------------------------
if (-not (Test-Command git)) {
    Write-Step "Git not found; downloading Git for Windows"
    $gitInstaller = "$env:TEMP\Git-2.49.0-64-bit.exe"
    Invoke-WebRequest -Uri "https://github.com/git-for-windows/git/releases/download/v2.49.0.windows.1/Git-2.49.0-64-bit.exe" -OutFile $gitInstaller -UseBasicParsing
    Write-Host "Installing Git..."
    & $gitInstaller /VERYSILENT /NORESTART /NOCANCEL /SP- /CLOSEAPPLICATIONS /RESTARTAPPLICATIONS /COMPONENTS="icons,ext\reg\shellhere,assoc,assoc_sh" | Out-Null
    if (-not (Test-Command git)) {
        throw "Git installation failed. Please restart this script after reopening PowerShell."
    }
}
Write-Host "Git: $(git --version)"

# -----------------------------------------------------------------------------
# 4. Install Tailscale (if missing)
# -----------------------------------------------------------------------------
$tailscaleExe = "$env:ProgramFiles\Tailscale\tailscale.exe"
if (-not (Test-Path $tailscaleExe)) {
    Write-Step "Tailscale not found; downloading installer"
    $tsInstaller = "$env:TEMP\tailscale-setup.exe"
    Invoke-WebRequest -Uri "https://pkgs.tailscale.com/stable/tailscale-setup-latest-amd64.exe" -OutFile $tsInstaller -UseBasicParsing
    Write-Host "Installing Tailscale..."
    & $tsInstaller /S | Out-Null
    if (-not (Test-Path $tailscaleExe)) {
        throw "Tailscale installation failed."
    }
}
Write-Host "Tailscale installed."
Write-Host "IMPORTANT: Log in to Tailscale now by running:" -ForegroundColor Yellow
Write-Host "    & '$tailscaleExe' up" -ForegroundColor Yellow
Write-Host "Then re-run this script with -StartWorker." -ForegroundColor Yellow

# If Tailscale is not running/logged in, stop here.
$tsStatus = (& $tailscaleExe status 2>&1 | Out-String)
if ($tsStatus -match "not logged in|Log in") {
    Write-Host "Tailscale is installed but not logged in. Complete login, then re-run with -StartWorker."
    exit 0
}
$selfIP = (& $tailscaleExe ip -4 2>&1 | Out-String).Trim()
Write-Host "Tailscale IP: $selfIP"

# -----------------------------------------------------------------------------
# 5. Clone or update repo
# -----------------------------------------------------------------------------
if (-not (Test-Path $InstallDir)) {
    Write-Step "Cloning repo to $InstallDir"
    git clone $RepoUrl $InstallDir
} else {
    Write-Step "Updating existing repo at $InstallDir"
    Set-Location $InstallDir
    git fetch origin
    git checkout $Branch
    git pull origin $Branch
}
Set-Location $InstallDir

# -----------------------------------------------------------------------------
# 6. Install dependencies from lock file
# -----------------------------------------------------------------------------
Write-Step "Installing Python dependencies from requirements.txt"
python -m pip install -r "$InstallDir\requirements.txt"

# -----------------------------------------------------------------------------
# 7. Start Dask worker
# -----------------------------------------------------------------------------
if ($StartWorker) {
    Write-Step "Starting Dask worker attached to $Scheduler"
    & python "$InstallDir\scripts\spawn_worker.py" $Scheduler "$MachineName"
    Start-Sleep -Seconds 5
    & python "$InstallDir\scripts\cluster_health.py" --scheduler $Scheduler
} else {
    Write-Host "`nSetup complete. To start the worker, re-run:" -ForegroundColor Green
    Write-Host "    powershell -ExecutionPolicy Bypass -File '$PSCommandPath' -StartWorker" -ForegroundColor Green
}
