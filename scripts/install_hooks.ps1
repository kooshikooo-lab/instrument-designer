# Installs the governance guard git hooks for this repo.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File scripts\install_hooks.ps1
#
# Uses git's core.hooksPath to point at scripts/git-hooks INSIDE the repo, so the
# hooks are version-controlled and merged to every machine. Nothing is copied into
# .git/hooks. Idempotent — safe to run on every pull.

$repoRoot = git rev-parse --show-toplevel
if (-not $repoRoot) { Write-Error "Not a git repo."; exit 1 }

$hooksPath = git rev-parse --show-toplevel
$hooksDir = Join-Path $hooksPath "scripts\git-hooks"

if (-not (Test-Path (Join-Path $hooksDir "commit-msg"))) {
    Write-Error "Hook source missing: $hooksDir\commit-msg"
    exit 1
}
if (-not (Test-Path (Join-Path $hooksDir "pre-push"))) {
    Write-Error "Hook source missing: $hooksDir\pre-push"
    exit 1
}

# Set core.hooksPath to the versioned hooks directory (forward slashes for git).
$rel = "scripts/git-hooks"
git config core.hooksPath $rel
if ($LASTEXITCODE -ne 0) { Write-Error "git config core.hooksPath failed"; exit 1 }

Write-Host "Governance guard hooks ACTIVE via core.hooksPath=$rel"
Write-Host "Edits to docs\CONSTRAINTS_AND_PREFERENCES.md (or other governance files)"
Write-Host "now require 'GOVERNANCE-UPDATE' in the commit message (unless the file is unchanged)."
Write-Host "Hooks installed: pre-commit, commit-msg, pre-push (Law 15/16)."
Write-Host "Verify the whole system with: python scripts\system_audit.py"
Write-Host ""
Write-Host "To verify:  git config --get core.hooksPath"
