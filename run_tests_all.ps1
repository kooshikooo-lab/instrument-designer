# run_tests_all.ps1
# Runs all pytest tests and saves the output. Useful to run full test suite locally.
Write-Host "Running full pytest suite ..."
try {
    conda run -n tmmbench pytest -q --durations=50 | Tee-Object -FilePath all_tests_results.txt
} catch {
    Write-Host "Failed to run full test suite. If conda run does not work, activate your env: conda activate tmmbench; pytest -q"
}
Write-Host "Saved all_tests_results.txt"
