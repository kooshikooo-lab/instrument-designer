# Archived Optimizers

> This document records the history of the `backend/archived_optimizers/`
> package, which was **deleted from the repository** on 2026-07-31.
>
> The optimizers below were superseded by the current precision pipeline in
> `backend/two_phase_optimizer.py` (DE global search → L-BFGS-B local
> refinement, phase-based absolute cost, ~0.5¢ RMS on the chalumeau_C
> benchmark) and by the restored NSGA-II `backend/optimizer.py`.
>
> The archived package was **broken at deletion time**: `design_desk.py`
> still imported `bore_optimizer.BoreOptimizer` from it, which produced
> all-infeasible candidates (`cv_min = 1e10`, zero best candidates), so
> auto-design jobs reported "999.00 cents RMS / 0 evaluations". That import
> now points at `backend.optimizer`.

## Inventory (pre-deletion)

| File | What it was | Why archived / broken |
| --- | --- | --- |
| `__init__.py` | Lazy package shim ("frozen, do not modify") | Eager import ran benchmarks and failed on broken siblings (see `docs/AI_FAILURE_PATTERNS.md`); irrelevant once the package is gone |
| `benchmark_optimizers.py` | Cross-method benchmark (Powell, corrected Powell, sequential Bordeaux, multi-start) over 4 instruments | Ran a benchmark **at import time**; superseded by `backend/benchmark_all.py` |
| `bore_optimizer.py` | NSGA-II (pymoo) bore optimizer + `_compute_impedance_from_bore`, `_match_peaks_to_targets` helpers | **Broken**: all candidates infeasible (`cv_min = 1e10`, empty `best_candidates`). NSGA-II survives as `backend/optimizer.py` (restored, working) |
| `optimizer_global.py` | Global fingering-chart optimizer for clarinet (DE over full fingering matrix) | Frozen; had a known hole-indexing inversion documented in `docs/PHYSICS_PRINCIPLES.md` (finding C1) |
| `staged_optimizer.py` | Noreland-style staged optimization (fundamental → harmonics → full set) | Idea lives on in `backend/two_phase_optimizer.py` |
| `tmm_optimizer.py` | `TMMBoreOptimizer` — L-BFGS-B + TMM phase acoustics (flute + clarinet) | Import never worked on main; superseded by `two_phase_optimizer` |
| `tmm_optimizer_multi.py` | Multi-start variant for global convergence | Obsolete; DE in Phase 1 covers global search better |
| `tmm_optimizer_sequential.py` | Sequential (Bordeaux method) optimizer with tone holes | **Unimportable** (relative import of missing `.tmm_acoustics`); superseded |
| `tmm_optimizer_v2.py` | `TMMBoreOptimizerJAX` — Powell Phase 1 → L-BFGS-B Phase 2 | JAX variant; superseded by `two_phase_optimizer` |
| `v2_scipy_optimizer.py` | `ScipyBoreOptimizer` — L-BFGS-B + OpenWInD, PAVA monotonicity | OpenWInD impedance path, slow (~100× slower than TMM phase); superseded |
| `validate_optimizer.py` | Ground-truth validation against known designs | Referenced deleted sibling `bore_optimizer`; obsolete |

## Ideas worth keeping (all live on in `backend/two_phase_optimizer.py`)

- **Phase-based resonance cost** (Ernoult et al., Noreland et al.): find the
  resonance by solving for the phase of the input impedance, not by scanning
  impedance magnitude. This is the core of `phase_cost`/`peak_cost_nearest`.
- **Two-phase workflow**: Phase 1 = cheap global search (now differential
  evolution), Phase 2 = L-BFGS-B local polish on the absolute RMS cost with
  fixed detected registers.
- **Sequential hole placement** (Bordeaux method): add holes bottom-to-top;
  the two-phase pipeline still sorts hole positions and fixes detected
  registers per fingering.
- **PAVA monotonicity repair**: retained in `backend/optimizer.py`
  (NSGA-II); deliberately dropped in the TMM two-phase path where the bore
  need not be monotonic.

## Deletion rationale

- The package was a maintenance trap: it held the only working copy of
  helpers that other modules imported (`design_desk.py`,
  `timbre_objectives.py`), it eagerly imported broken siblings, and its
  flagship optimizer returned entirely infeasible populations.
- The validated path forward (`backend/two_phase_optimizer.py`) already
  encodes the same acoustics and a better optimizer, so keeping ~150 KB of
  broken legacy code on main only encouraged accidental imports.

## Related files

- `docs/AI_FAILURE_PATTERNS.md` — history of the import/restore failures.
- `docs/PHYSICS_PRINCIPLES.md` — physics notes incl. finding C1.
- `docs/OPTIMIZATION_THEORY.md` — current pipeline research notes.
