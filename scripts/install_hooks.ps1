# Installs the governance guard git hooks for this repo.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File scripts\install_hooks.ps1
# Installs commit-msg + pre-commit hooks into .git/hooks/.

$repoRoot = git rev-parse --show-toplevel
if (-not $repoRoot) { Write-Error "Not a git repo."; exit 1 }
$hooksDir = git rev-parse --git-path hooks
$sourceDir = Join-Path $repoRoot "scripts\git-hooks"

foreach ($hook in @("commit-msg")) {
    $src = Join-Path $sourceDir $hook
    if (Test-Path $src) {
        $dst = Join-Path $hooksDir $hook
        Copy-Item -Path $src -Destination $dst -Force
        Write-Host "Installed hook: $hook"
    }
}

Write-Host "Governance guard hooks installed. Edits to docs\CONSTRAINTS_AND_PREFERENCES.md"
Write-Host "now require 'GOVERNANCE-UPDATE' in the commit message (unless no change to that file)."
