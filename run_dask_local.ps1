# run_dask_local.ps1
# Run the Dask LocalCluster benchmark (local multi-process) with defaults.
param(
    [int]$tasks = 1000,
    [int]$chunk = 5,
    [int]$nworkers = 16
)

Write-Host "Running dask local benchmark (tasks=$tasks chunk=$chunk nworkers=$nworkers)"
$env:OMP_NUM_THREADS = "1"
$env:MKL_NUM_THREADS = "1"
$outfile = "bench_dask_local.txt"
try {
    conda run -n tmmbench python scripts/bench_tmm_dask.py --local --tasks $tasks --chunk $chunk --nworkers $nworkers | Tee-Object -FilePath $outfile
} catch {
    Write-Host "Failed to run dask benchmark"
}
Write-Host "Saved to $outfile"
