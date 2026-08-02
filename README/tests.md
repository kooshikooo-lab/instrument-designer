# Tests — how to run and organize

This document explains the convenient, reproducible ways to run tests in this repository, how they are grouped, and the helper scripts available in the repo so you can run tests with a double‑click or from VS Code.

Quick prerequisites
- Python environment: we recommend using the `tmmbench` conda environment.
  - Create it (one-time):
    conda create -n tmmbench python=3.10 -y
    conda activate tmmbench
    conda install -c conda-forge numpy dask distributed numba pytest -y
- Open the repository root folder in VS Code (recommended) or use PowerShell in the repo root.

Overview of test groups (markers)
- smoke: very fast, basic checks you can run frequently.
- integration: multi-component tests (moderate runtime).
- perf: heavyweight performance / benchmark tests (run occasionally).

pytest.ini
- The repository includes `pytest.ini` registering the markers and enabling strict markers. Use `@pytest.mark.smoke`, `@pytest.mark.integration`, `@pytest.mark.perf` in tests to place them in groups.

Helper scripts (Windows)
These scripts are placed in the repo root and can be double-clicked in Explorer or run from VS Code integrated terminal.
- run_tests_smoke.bat / run_tests_smoke.ps1
  - Runs tests marked `smoke`. Saves `smoke_results.txt`.
- run_tests_integration.bat / run_tests_integration.ps1
  - Runs tests marked `integration`. Saves `integration_results.txt`. Also prints the slowest tests via `--durations=20`.
- run_tests_perf.bat / run_tests_perf.ps1
  - Runs tests marked `perf`. Saves `perf_results.txt`.
- run_tests_all.bat / run_tests_all.ps1
  - Runs the entire test suite and saves `all_tests_results.txt`.

Bench & numba helpers
- run_bench_all.ps1 / .bat — runs the micro-bench across branches (main + perf branches) and saves outputs.
- run_dask_local.ps1 — run the distributed LocalCluster benchmark locally (useful for throughput testing).
- run_numba_test.ps1 + scripts/test_numba.py — small parity/timing test comparing Python vs numba compiled path.
- scripts/compare_bench.py — comparator script to compare JSON summary outputs from bench runs.

How to run (easy ways)
A) Double-click (Windows)
- In the repo folder, double-click one of the `.bat` files (e.g., `run_tests_integration.bat`). The terminal will run and pause so you can read results. Output files are saved to the repo root.

B) From VS Code (recommended)
1. Open the repo folder in VS Code.
2. Open Terminal (Ctrl+`).
3. Activate the conda env (if not using `conda run` inside scripts):
   conda activate tmmbench
4. Run a script:
   .\run_tests_smoke.ps1
   .\run_tests_integration.ps1
   .\run_tests_perf.ps1
   .\run_tests_all.ps1

C) Run pytest directly (more control)
- Run smoke tests:
  pytest -q -m smoke | Tee-Object -FilePath smoke_results.txt   (PowerShell)
- Run integration tests:
  pytest -q -m integration --durations=20 | Tee-Object -FilePath integration_results.txt
- Run perf tests:
  pytest -q -m perf --durations=50 | Tee-Object -FilePath perf_results.txt
- Run a single file:
  pytest -q tests/bass_clarinet_full_test.py
- Run a single test function:
  pytest tests/file.py::test_function_name
- Run tests by substring:
  pytest -k "clarinet"

Finding slow tests (helpful when deciding markers)
- Run:
  pytest --durations=20
- This prints the slowest 20 tests so you can decide which to mark `integration` or `perf`.

Marking tests
- Add a marker decorator above test functions or classes. Example:

```python
import pytest

@pytest.mark.integration
def test_bass_clarinet_final_configuration():
    ...
```

- The registered markers are declared in `pytest.ini`. Using unknown markers will raise a warning (strict markers enabled).

Using the VS Code Test UI
- The Python extension discovers pytest tests and exposes them in the Test (beaker) sidebar.
- Configure pytest args in `.vscode/settings.json` if needed. Example:

```json
{
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests"],
  "python.testing.unittestEnabled": false
}
```

Troubleshooting & tips
- If a script fails with `conda run` errors, try activating the environment first:
  conda activate tmmbench
  pytest -q -m integration
- If PowerShell blocks `.ps1` execution, allow local scripts once:
  Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
- If `git checkout` fails in `run_bench_all.ps1`, commit or stash your changes first:
  git stash --include-untracked
- Numba helper:
  - Install numba via conda for best compatibility: `conda install -c conda-forge numba`
  - `scripts/test_numba.py` shows a simple parity/timing check and is run by `run_numba_test.ps1`.

Recommended workflows
- Quick check (daily): run smoke tests.
- Pre-merge checks: run integration (and perf if you changed heavy code).
- Performance comparisons: run `run_bench_all.ps1` to collect micro-bench outputs across branches and use `scripts/compare_bench.py` to compute improvements.

If you want help with any of these now
- I can run a scan (locally) to list the slowest tests and suggest which to mark as `integration`/`perf`.
- Or I can add a short `README/tests.md` (this file) to other branches if you prefer. Tell me which branch to push to or I can push to the current perf branch.

