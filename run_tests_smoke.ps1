# run_tests_smoke.ps1
# Runs pytest for quick smoke tests marked with @pytest.mark.smoke and saves the output.
Write-Host "Running pytest -m smoke ..."
try {
    conda run -n tmmbench pytest -q -m smoke | Tee-Object -FilePath smoke_results.txt
} catch {
    Write-Host "Failed to run smoke tests. If conda run does not work, activate your env: conda activate tmmbench; pytest -q -m smoke"
}
Write-Host "Saved smoke_results.txt"
