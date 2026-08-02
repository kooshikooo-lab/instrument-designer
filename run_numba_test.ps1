# run_numba_test.ps1
# Run a small numba parity/timing test. Ensure you are on the perf/tmm-medium-refactor-copilot branch
# (which contains backend/tmm_numba.py) and that your tmmbench conda env has numba installed.
$branch = (& git rev-parse --abbrev-ref HEAD).Trim()
Write-Host "Current branch: $branch"
$outfile = "numba_test_" + ($branch -replace '/','_') + ".txt"
try {
    conda run -n tmmbench python scripts/test_numba.py | Tee-Object -FilePath $outfile
} catch {
    Write-Host "Failed to run numba test. Ensure backend/tmm_numba.py exists on this branch and numba is installed in the tmmbench env."
}
Write-Host "Saved to $outfile"
