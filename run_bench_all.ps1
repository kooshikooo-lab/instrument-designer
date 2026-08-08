# run_bench_all.ps1
# Runs the micro-benchmark script on three branches and saves outputs to files.
# Double-click this file or run it from PowerShell in the repo root.
$branches = @("main","perf/tmm-refactor-copilot","perf/tmm-medium-refactor-copilot")
foreach ($b in $branches) {
    Write-Host "Fetching and checking out $b ..."
    git fetch origin $b
    try {
        git checkout $b
    } catch {
        Write-Host "Failed to checkout $b"
        continue
    }
    $outfile = "bench_" + ($b -replace '/','_') + ".txt"
    Write-Host "Running bench on $b, saving to $outfile ..."
    try {
        conda run -n tmmbench python scripts/bench_tmm_micro.py | Tee-Object -FilePath $outfile
    } catch {
        Write-Host "Failed to run bench on $b"
    }
}
Write-Host "All done."
