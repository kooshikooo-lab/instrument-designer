# run_tests_integration.ps1
# Runs pytest for tests marked with @pytest.mark.integration and saves the output.
Write-Host "Running pytest -m integration ..."
try {
    conda run -n tmmbench pytest -q -m integration --durations=20 | Tee-Object -FilePath integration_results.txt
} catch {
    Write-Host "Failed to run integration tests. If conda run does not work, activate your env: conda activate tmmbench; pytest -q -m integration"
}
Write-Host "Saved integration_results.txt"
