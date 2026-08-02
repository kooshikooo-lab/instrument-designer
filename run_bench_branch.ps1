# run_bench_branch.ps1
# Run the micro-benchmark on the current git branch and save output.
$branch = (& git rev-parse --abbrev-ref HEAD).Trim()
$outfile = "bench_" + ($branch -replace '/','_') + ".txt"
Write-Host "On branch $branch, running micro-bench and saving to $outfile"
try {
    conda run -n tmmbench python scripts/bench_tmm_micro.py | Tee-Object -FilePath $outfile
} catch {
    Write-Host "Failed to run bench"
}
Write-Host "Done."
