# Architecture Audit — Current State

Generated: 2026-08-06
Branch: `opencode/main/desktop`

## Executive Summary

The repository is functional but carries significant technical debt. The test
suite mostly passes on a minimal environment, but many tests are excluded from
pytest collection, dependencies are inconsistently installed, and the codebase
has 96 pre-commit-style violations (mostly bare `except:` clauses and misplaced
files). Several real bugs remain from the Kimi K3 review that the laptop has
fixed on its branch but which are still present on `opencode/main/desktop`.

## Test Suite Status

Command: `python -m pytest tests/ -q --tb=line`

- **Passed:** 146
- **Failed:** 2 (missing `pymoo`)
- **Errors:** 3 (missing `openwind`)
- **Skipped:** 1
- **Warnings:** 3 (pytest tests returning `bool` instead of asserting)

### Failures

1. `tests/test_inverse_design.py::test_match_timbre_cost_well_conditioned`
   - `ModuleNotFoundError: No module named 'pymoo'`
2. `tests/test_server_routes.py::test_optimizer_backend_importable`
   - `ModuleNotFoundError: No module named 'pymoo'`

### Errors

1. `tests/test_openwind_solver.py` (3 tests)
   - `ImportError: OpenWInD is required. Install with: pip install openwind`

### Notes

- `pymoo` and `openwind` are declared in `pyproject.toml` but not installed in
  the current environment.
- `pytest` is configured to ignore most `test_*.py` files because they are
  ad-hoc scripts, not real pytest tests.
- `tests/test_cadquery_instrument.py` returns `bool` from test functions instead
  of using assertions.

## Deleted-Module References (Real Bugs)

Running `scripts/validate_imports.py` across the whole repo found imports from
modules that no longer exist after the reorganization:

1. `backend/benchmark_unconventional_shapes.py:22`
   - `woodwind_designer.engine.instrument_library`
2. `backend/main.py:3`
   - `woodwind_designer.engine.design_server`
3. `run.py:18`
   - `woodwind_designer.main`
4. `scripts/benchmark_chalumier_dask.py:34`
   - `woodwind_designer.engine.chalumier_wrapper`
5. `tests/test_measure.py:7`
   - `backend.bore_optimizer`
6. `tests/test_server_routes.py` (multiple lines)
   - `woodwind_designer.engine.design_server`

## Bare `except:` Clauses

56 bare except clauses remain across `backend/`, `scripts/`, and `tests/`.
Examples:

- `backend/benchmark_all.py:341, 387`
- `backend/benchmark_dask.py:58, 98, 127`
- `backend/jax_optimizer.py:92, 136`
- `backend/two_phase_optimizer.py:65, 94, 135, 195`
- `scripts/benchmark_chalumier.py:195, 200, 257, 281, 311`
- `scripts/refine_chalumier.py:116, 159, 167, 298, 333, 341`

## Hardcoded Physical / Geometric Constants

Confirmed in `backend/benchmark_all.py`:

- `pvc_flute_D`: `bore_radius=10.2`, `outer_diameter=14` → impossible wall
  (OD < 2×radius).
- `diatonic_D_chalumeau`: `bore_radius=8.0`, `outer_diameter=14` → impossible
  wall (OD < 2×radius).
- `concert_flute_C`: `bore_radius=19`, ... (context needed).
- `alto_flute_G`: `bore_radius=22`, ... (context needed).

A sanity check should assert `outer_diameter > 2 * bore_radius` for every
instrument definition.

## Fingering / Hole Mismatches

- `benchmark_all.py::INSTRUMENTS["bass_chalumeau_Bb"]` has 8 target notes and
  8-column fingerings, but `modular_components.build_bass_chalumeau_Bb()` does
  not add any tone holes to the assembly.
- The canonical schema validator catches length mismatches in `config/*.json`,
  but `benchmark_all.py` instrument definitions are not validated by it.

## File Placement Violations

- `backend/reference_instruments/*.csv` in `backend/`
- `scripts/benchmark_results/*` in `scripts/`
- `scripts/compliance_log.jsonl` in `scripts/`
- `scripts/debug_run.cmd` in `scripts/`
- `tests/README.md` in `tests/`
- `tests/*.ps1` in `tests/`
- `tests/test_payload.json` in `tests/`

## Regenerable Artifacts Still Tracked

- `chat-logs/*.txt`, `chat-logs/*.json`
- `requirements-server.txt`
- `research/*.txt`
- `test_output/unconventional/*`

## Oversized Modules (Warnings)

Not in allowlist:

- `backend/fixtures.py` — 611 lines
- `backend/jax_optimizer.py` — 510 lines
- `backend/optimizer.py` — 524 lines
- `backend/stl_verifier.py` — 572 lines
- `scripts/benchmark_timbre.py` — 685 lines
- `tests/test_sympy_validation.py` — 535 lines

## Configuration / Packaging Issues

- `pyproject.toml` only includes `woodwind_designer*` as packages. `backend/`,
  `scripts/`, and `tests/` are not installed packages, which contributes to
  import confusion.
- `tool.pytest.ini_options.python_files` only lists 14 files. The remaining
  `test_*.py` files are not collected and thus not run by CI.

## Duplicate / Dead Code

- `tests/test_stl_export.py` defines `test_stl_export` twice. The first
  definition is shadowed by the second.

## Tailscale Monitor

- New `scripts/tailscale_monitor.py` is running on desktop. The laptop has
  acknowledged and is starting its side.

## Pending Cross-Machine Threads

From `docs/REMINDERS.md`:

1. Numba wiring restore on `main` (waiting PR #62 merge).
2. PR #62 head mirror cleanup.
3. Mesh-repair gate protocol draft (`docs/TOOLS.md`).
4. build123d spike merge to `opencode/main/laptop`.
5. `cadquery-ocp` pin.
6. Config schema unification — 3 configs migrated, `baroque_clarinet.json`
   stays legacy pending multi-register decision.
7. Tailscale monitor — desktop running, laptop needs latest pull + restart.

## Recommendations

### P0 (Fix Immediately)

1. Fix deleted-module references so affected scripts/tests import correctly.
2. Add `outer_diameter > 2 * bore_radius` sanity check to `benchmark_all.py`
   instrument definitions and fix impossible ODs.
3. Fix `bass_chalumeau_Bb` so its modular builder adds the same number of holes
   as its fingering chart.

### P1 (Fix Soon)

4. Replace bare `except:` with `except Exception:` (or narrower) in production
   code (`backend/` and `scripts/`).
5. Move regenerable logs/results out of git or add them to `.gitignore`.
6. Fix file placement: move CSVs out of `backend/`, results out of `scripts/`,
   docs out of `tests/`.
7. Fix `tests/test_stl_export.py` duplicate function.
8. Fix `tests/test_cadquery_instrument.py` to assert instead of returning bool.

### P2 (Architecture)

9. Reconcile `pyproject.toml` package discovery to include `backend/` or
   document why it is intentionally excluded.
10. Decide whether ad-hoc `test_*.py` scripts should be converted to pytest
    tests or moved out of `tests/`.
11. Add `benchmark_all.py` instrument definitions to the config schema
    validator or create a dedicated validator for them.
