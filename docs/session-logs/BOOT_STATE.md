# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- **Working branch: `opencode/main/desktop`** (HEAD `3393400`).
- **Phase 0 COMPLETE**: SoS literal cleanup, Two-Phase optimizer register freeze, bass chalumeau merge conflict resolved.
- **Phase 1 READY**: WoodwindOpenWind FEM integration, surrogate audit.
- **Standing directive**: tools must be integrated into a pipeline, never just installed and forgotten; `AUDIT:` for provisional commits; ask rather than speculate when intent is unclear.

## Constraints & Preferences

- **Step 0 protocol**: `python scripts/team_chat.py sync` at session start AND before stopping (Discussion #23); channel is canonical.
- Constitution: Law 1 (no architecture damage), Law 3 (reuse existing bench scripts), Law 7 (canonical `346100.0` mm/s speed of sound), Law 10 (stop/ask).
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for `docs/CONSTRAINTS_AND_PREFERENCES.md`; don't commit regenerable artifacts.
- Tool adoption rule: install + declare (`docs/TOOLS.md`) + import + whitelisted test.

## Progress

### Done (this session)
- **Merged PR #63**: Removed phantom `openwind` gitlink (shadowed pip package).
- **Merged PR #62**: 45-file import repair (tmm_acoustics imports moved to `archived_optimizers/`).
- **SoS Literal Cleanup COMPLETE**: 46 non-canonical speed-of-sound literals fixed across 10 files (by dependency layer: physics → optimizers → core → tone-hole → tests).
- **Two-Phase Optimizer Fixes COMPLETE**:
  - Created shared `backend/physics/register_detection.py` with frozen register detection.
  - Updated `backend/two_phase_optimizer.py` to use shared module.
  - Updated `backend/optimization/selector.py` TwoPhaseOptimizer:
    - Added configurable `outer_diameter`, `closed_top`, `bore_length_bounds`.
    - Register detection frozen once from initial geometry (Discussion #23 decision).
    - Phase 2 uses `peak_cost_nearest` with frozen registers.
    - Bass instruments (>1m) enforce `bore_length_bounds`.
- **Bass Chalumeau Merge Conflict RESOLVED**: Laptop merged desktop first (per Discussion #23 decision 4B).
- **P0 Questions RESOLVED** (Discussion #23): All 4 human decisions received (A/A/A/B).
- **ROADMAP.md completely overhauled** with Phase 0-3 plan.
- **Session log saved**: `chat-logs/2026-08-07-session-log.md` + P0 questions `chat-logs/2026-08-07-p0-questions.md`.

- **Laptop optimizer/surrogate tuning on the shared benchmark contract**
  (this session, commit `27ce1cb` on `kalles-main-branch`): per desktop's
  delegation (laptop tunes optimizer/surrogate loop against the shared
  Bb-clarinet contract from `tests/comparison/ai_methods_benchmark.py` — 6 bore
  radii, closed-top, abs RMS cents over 6 chalumeau notes).
  - Result: **DE + top-k L-BFGS-B polish wins**, 5.9–7.7c RMS vs the 9.6c
    gradient-free baseline (~30% better); surrogate warm-start (neural MLP from
    DE elites) scored 19–167c — a dead end on this contract (corroborates
    desktop's neural 34.7c vs gradient-free 9.6c).
  - Delivered `backend/optimization/topk_polish.py` (generic
    `topk_polish(objective, bounds, popsize, maxiter, n_polish, seed)`; returns
    comparison-framework metric keys), exported from
    `backend/optimization/__init__.py`, `tests/test_topk_polish.py` (3 tests).
    Pushed `3e64efc..27ce1cb` → `origin/kalles-main-branch`.
  - Laptop test state: **118 passed / 1 skipped** (numba parity skipped — wiring
    was clobbered from `tmm_acoustics.py` by the `7cae468` main merge; guarded
    import fix applied matching desktop's branch). Toolcheck PASS.
- **Branch health fixes** (commit `b198c4c` on `kalles-main-branch`): declared
  `spectral` (`librosa`) + `fem` (`gmsh`/`meshio`/`scikit-fem`) extras in
  `pyproject.toml` + `docs/TOOLS.md` (fixes tool-registry guard); guarded the
  numba parity test import (skip when wiring absent); whitelisted
  `test_topk_polish.py` in `python_files`. Pushed `012f18a..b198c4c`.
- **Posted to #23**: (a) drop-in integration recipe for `topk_polish` as a 5th
  comparison-suite family (runner + registry + budget + test case); (b) branch
  health fixes + question: restore numba wiring (`32d4c9f`, verified bit-identical
  + 6.4x) into `tmm_acoustics.py` or leave skipped until reconciliation.
  Awaiting desktop decision on both.
- **Desktop adopted topk_polish as 5th family in PR #62** (commit `25e215f`),
  byte-identical engine (blob `67e1208`); added `ai_methods_dask.py` (dask
  deep-budget variants of the surrogate families), `tune_topk_polish.py`,
  `verify_with_retries`; thread 1 (topk integration) RESOLVED on both sides.
  Laptop cross-verified: 10 passed on desktop's PR #62 head in a temp worktree.
- **Adopted REMINDERS.md coordination mechanism** (commit `c5ab7d2`):
  `docs/REMINDERS.md` + AGENTS.md branch-naming, byte-identical to desktop's
  `82bfeaa`. Standing threads 2 (numba restore via PR #62 merge) and 3 (PR #62
  head mirror) still open.
- **Dask-parallel comparison path for topk_polish** (commit `ebc2418`,
  `opencode/main/laptop`): optional `workers` param in
  `backend/optimization/topk_polish.py` (forwarded to scipy
  `differential_evolution`; default `workers=1` = serial unchanged);
  `tests/comparison/dask_topk.py` (`make_client` scheduler→local cluster→None
  serial fallback, `dask_map`, `run_topk_polish_dask`); `tests/comparison/
  test_dask_topk.py` (5 tests, comparison/slow markers: serial-fallback ==
  engine, dask == serial-deferred DE exactly, dask determinism, graceful
  dask-absent degradation). No name collision with desktop's `ai_methods_dask.py`.
  Laptop: **123 passed / 1 skipped**, toolcheck PASS, ruff clean on new files.
- **Research: 3D modeling/CAD + AI tools + design-to-finished-instrument pipeline**
  (commit `8603240`, `opencode/main/laptop`, pushed): `docs/
  RESEARCH_design_to_finished_instrument.md` (REFERENCE, no code changes);
  `docs/WIKI.md` §11; `docs/WIKI-INDEX.md` entry; `wiki/Internal-Research-CAD-
  Pipeline.md` (new topic page); `wiki/Internal-Research.md` hub row;
  `wiki/3D-Printing-Guide.md` pipeline-research section. Findings: CadQuery/
  OpenCASCADE parametric CAD is correct (Build123d the only serious alternative);
  mesh gap = no pre-slicing repair gate (pymeshlab/pymeshfix, needs docs/TOOLS.md
  protocol); ML surrogates already evaluated+rejected (topk_polish+dask won, do
  not re-open w/o changed contract); gradient-based geometry optimization
  (Szwarcberg 2025) = most promising new lever; APR bore reconstruction = strongest
  QA addition. Tests **123 passed / 1 skipped**, toolcheck PASS. Posted to #23
  (comment-17905161).
- **Laptop Dask worker attached to desktop cluster** (2026-08-05): desktop
  scheduler `tcp://100.69.113.41:8786` (Tailscale), started laptop worker via
  local `scripts/start_worker.py` (`laptop-worker`, 4 threads) since desktop's
  `start-cluster.ps1`/`cluster_health.py` are not yet on
  `origin/opencode/main/desktop` (branch still at `7f97975`, only sync.ps1).
  Verified **2 workers** (`tcp://100.100.66.117:56372` laptop +
  `tcp://100.69.113.41:60461` desktop). dask[distributed] 2026.7.1 already
  installed. Version mismatch expected (numpy 2.4.6/2.5.1, py 3.14.6/3.12.10) —
  see AI_FAILURE_PATTERNS; workers run fine, functions shipped from client.
- **Build123d spike (track C, 2026-08-05, commit `8ddfc7a` on
  `opencode/build123d/laptop`)**: `backend/experiments/build123d_koncovka.py`
  ports `cadquery_export.generate_instrument`'s cylindrical path to build123d
  0.11.1. Parity results: koncovka_C (no holes) **0.000%** volume err, identical
  mesh (504 verts/1008 faces, watertight), bbox z[0,651.5] exact after `+bore_length/2`
  translate fix; fujara_G (closed top) 0.000%, both watertight; **xaphoon_C
  (7 holes): CadQuery STL NOT watertight (2624/5264) vs build123d watertight
  (1000/2012)** — corroborates the mesh-repair-gate finding. Note: build123d
  0.11 uses `Pos(...) * part` (NOT `part @ Pos(...)`). Env fix: build123d's dep
  pulled `cadquery-ocp-novtk` which clobbered shared OCP namespace and broke
  cadquery imports — uninstalled novtk, force-reinstalled `cadquery-ocp`; both
  import cleanly now. Tests **123 passed / 1 skipped**, toolcheck PASS. Posted to
  #23 (comment-17906678).
- **Mesh-repair gate decision landed in `docs/TOOLS.md`** (commit `e8d6254` on
  `opencode/build123d/laptop`): protocol section documents the gate
  (watertight AND manifold check via `backend/stl_verifier.py`/trimesh),
  repair candidates pymeshlab (primary) / pymeshfix / admesh — **declared, NOT
  adopted** (adoption requires the full adopt-a-tool protocol); check-only gate
  (fail on non-watertight) wireable with zero new deps. Posted to #23
  (comment-17906678).

### In Progress
- Phase 1: WoodwindOpenWind FEM skeleton, surrogate audit.

### Blocked
- None.

## Key Decisions
- **SoS test expectations → 346100 mm/s** (Law 7: canonical source of truth).
- **Register detection → shared module** `backend/physics/register_detection.py` (Law 3, Law 4).
- **Two-phase optimizer: Fix, don't delete** (Law 1 — it's the default `ACCURATE` strategy).
- **WoodwindOpenWind before remaining SoS test updates** (architecture over features).

## Next Steps
1. Phase 1: Create `backend/woodwind_openwind.py` mirroring `TrumpetOpenWind`.
2. Register `REFINED` strategy for woodwinds in selector.
3. Add TMM vs FEM comparison to `run_optimizer_comparison`.
4. Surrogate audit (`backend/surrogate/`).
5. Phase 2: CT-Scan benchmarking (Issue #47), Demakein replacement (Issue #48), Monte Carlo, Surrogate.

## Critical Context
- `origin/main` = `d935287`; `opencode/main/desktop` = `3393400`.
- Test baseline: `pytest tests/` → 217 passed, 3 skipped; `python scripts/toolcheck.py` PASS.
- Pre-commit validation passes; `backend/inverse_design.py` is allowlisted as oversized.
- Merged PRs: #63 (openwind gitlink), #62 (45-file import repair).
- Laptop branch `opencode/build123d/laptop` merged desktop at `73ae792`, 288 tests passing.

## Relevant Files
- `backend/physics/bore_design.py` — analytic tone-hole physics (temp formula for SoS).
- `backend/tmm_acoustics.py` — canonical `SPEED_OF_SOUND = 346100.0`.
- `backend/physics/register_detection.py` — shared frozen register detection.
- `backend/two_phase_optimizer.py` — uses shared register detection.
- `backend/optimization/selector.py` — `TwoPhaseOptimizer` with frozen registers + bass bounds.
- `backend/modular_components.py:699` — `build_bass_chalumeau_Bb()` merge conflict resolved.
- `backend/surrogate/` — `mlp_surrogate.py`, `bi_objective_bo.py` (audit next).
- `docs/ROADMAP.md` — complete Phase 0-3 plan.
- `chat-logs/2026-08-07-session-log.md` — full session audit.

(End of file)
