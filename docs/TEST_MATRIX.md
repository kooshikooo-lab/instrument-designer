# Test Matrix

Regular, broad, methodical testing across the codebase, organized by category.
Each category has a **tier** that controls when it may run (resource-aware):

| Tier | Meaning | Concurrency / resource rule |
|---|---|---|
| **low** | Fast (<2 min), low RAM | Any time; sequential |
| **medium** | A few minutes, 1–2 GB | Sequential, max 2 cores, one batch at a time |
| **heavy** | 10+ min, 2–6 GB | **On-demand only** (never auto-run); 1 JVM at a time, `-Xmx` capped |

Runner: `python scripts/run_all_tests.py --tier low|medium|heavy|all --category <name>`
A health gate (CPU load > 30% or free RAM < 4 GB or heavy process present) skips
a run unless `--force` is passed. Results go to `test_output/testing/results.json`.

Scheduled cadence (Task Scheduler): **daily 02:00 low tier**, **weekly Sunday 03:00 medium tier**. Heavy is manual only.

---

## Categories

### server — design server REST API
- **Tests:** `tests/test_server_routes.py` (6 tests) — optimize/start, status, evaluate, presets, cache endpoints.
- **Smoke:** import `woodwind_designer.engine.design_server`.
- **Tier:** low · **Pass:** all endpoint tests pass, import OK.

### tmm — TMM acoustics engine (chalumier port)
- **Tests:** `tests/test_tmm.py` (4 tests).
- **Tier:** low · **Pass:** impedance/register behavior matches expectations.

### physics — physics modules + coordinate conventions
- **Tests:** `tests/test_properties.py` (4 tests) — coordinate transforms (chalumier/internal/OpenWind), boundary mapping.
- **Tier:** low · **Pass:** all property tests pass.

### optimizer — two-phase / DE / Phase-2 cost
- **Tests:** `tests/test_phase2_objective.py` (3 tests) — sin² phase cost register-blindness, peak cost smoothness, refinement improves absolute pitch.
- **Smoke (optional, slow):** `tests/test_two_phase_quick.py` (known slow — capped timeout).
- **Tier:** medium · **Pass:** phase-2 tests pass; quick smoke completes or times out cleanly.

### openwind — OpenWind FEM vs TMM validation
- **Tests:** `tests/test_openwind_solver.py` (3 tests) — open-pipe register+1 convention, reed-pipe agreement, register vent.
- **Tier:** medium · **Pass:** all agreement checks within tolerance.

### stl — CadQuery STL export
- **Tests:** `tests/test_cadquery_instrument.py` (3 tests) — cylindrical/conical/parametric bore with holes.
- **Tier:** medium · **Pass:** all export tests pass.

### architecture — regression / structure
- **Tests:** `tests/test_architecture.py` (3 tests) — basic functionality, correct speed of sound, median-correction removal.
- **Tier:** low · **Pass:** all pass.

### instruments — instrument library save/load
- **Smoke:** `save_novel_instrument` round-trip + 82-library-entry integrity.
- **Tier:** low · **Pass:** smoke prints OK.

### chalumier — Kotlin/JVM integration
- **Availability (low):** `ChalumierDesigner.is_available()` + presets list (fast, no JVM design).
- **Design sweep (heavy, on-demand):** `scripts/benchmark_chalumier_dask.py --workers 1` — all 6 presets. Known issues (2026-08-01): 5/6 presets hit 600s wrapper timeout (timeout being raised); `d_major_flute` fails with a Clikt CLI parse error.
- **Pass:** availability True; sweep reports success/length/bore/holes per preset.

### jax — JAX optimizer
- **Smoke:** import + tiny evaluation.
- **Tier:** low · **Pass:** import OK, eval completes.

### comparison — AI/ML optimization families
- **Medium (on-demand):** `pytest tests/comparison/test_ai_methods_comparison.py -m comparison -s` (head-to-head: Bayesian, neural surrogate, RL, gradient-free).
- **Tier:** medium · **Pass:** all families converge within sanity bound; report table prints.

### unconventional — bore-shape benchmark
- **Heavy (on-demand):** `python backend/benchmark_unconventional_shapes.py` (serial) or `--dask` (remote cluster).
- **Status 2026-08-01:** ALL PASSED — 10/10 pipeline, 7/7 optimizations (0.0–15.8¢ RMS), serial + distributed (2 workers).

### pareto / full instrument suite — heavy sweeps
- **Heavy (on-demand):** `scripts/pareto_sweep_all.py`; full 11-instrument suite.
- **Pass:** all instruments under target RMS.

---

## Diagnostics (NOT automated)

`tests/diagnose_*.py`, `debug_*.py`, `compare_*.py`, `refine_*.py` are manual debugging
tools — they are **not** part of the matrix (many hang or need arguments). Use them
interactively only. `pytest` collects only the whitelisted files in `pyproject.toml`
(`[tool.pytest.ini_options] python_files`, 11 files).

## Current baseline

| Run | Result |
|---|---|
| `pytest tests/` | 114 passed (2026-08-04) |
| `run_tests.py` (5 parts) | all return codes 0 (2026-08-01) |
| Unconventional benchmark | ALL PASSED, 0.0–15.8¢ RMS (2026-08-01) |
| chalumier design sweep | 5/6 timeout, 1/6 CLI parse fail (2026-08-01) — follow-up open |
