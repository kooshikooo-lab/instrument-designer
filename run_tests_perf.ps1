# run_tests_perf.ps1
# Runs pytest for tests marked with @pytest.mark.perf and saves the output.
Write-Host "Running pytest -m perf ..."
try {
    conda run -n tmmbench pytest -q -m perf --durations=50 | Tee-Object -FilePath perf_results.txt
} catch {
    Write-Host "Failed to run perf tests. If conda run does not work, activate your env: conda activate tmmbench; pytest -q -m perf"
}
Write-Host "Saved perf_results.txt"
