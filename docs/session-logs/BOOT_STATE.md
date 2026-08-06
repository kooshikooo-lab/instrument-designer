# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- Deliver the laptop's research task: deep research on **3D modeling/CAD software,
  AI tools, and the design-to-finished-instrument pipeline** (fabrication,
  finishing, QA/tuning) → commit to GitHub docs + wiki. **DONE, `8603240` on
  `opencode/main/laptop`.** Also **attach a laptop Dask worker to desktop's live
  cluster** (desktop request 2026-08-05T10:53Z). **DONE — 2 workers confirmed.**
- **Track C (desktop allocation #23, 2026-08-05): laptop = build123d spike
  (koncovka_C) + mesh-repair gate decision.** **DONE** — spike on
  `opencode/build123d/laptop` (`8ddfc7a`), parity confirmed vs CadQuery; mesh
  repair gate protocol landed in `docs/TOOLS.md` (`e8d6254`). Both awaiting
  desktop review before merge decision.
- Consolidate the acoustic-metamaterials research (Claude + Kimi exports + web
  research) into `docs/RESEARCH_acoustic_metamaterials.md` (reference doc) and the
  internal wiki, restructured into **one page per major topic** with the
  metamaterials page organized **by instrument category** and per specific
  instrument (low clarinets the deepest dive). **DONE, on `main`.**
- Land the numba-accelerated TMM resonance-phase fast path (laptop's
  `np.floor/arctan/tan/pi` fix) on `main` behind a feature flag. **DONE, on `main`.**
- Port the Claude metamaterial artifacts into `backend/experiments/` (user
  authorized porting when present). **DONE, on `main`** — `string_metamaterial.py`,
  `brass_scaffold.py`, `metamaterial_elements.py`, `folded_bore_elements.py`, all
  reproducing documented outputs exactly.
- Standing items from prior sessions (not this session's work): `backend/spectral`
  design awaits user approval; laptop Phase 2G surrogate work lives on
  `kalles-main-branch`.
- Standing directive: tools must be **integrated into a pipeline**, never just
  installed and forgotten (tool registry guard is live).
- User's fallback instruction: if no task is assigned, do something **safe** (no
  architecture changes, no law-breaking, no deletion, no merging).

## Constraints & Preferences

- **Step 0 protocol**: `python scripts/team_chat.py sync` at session start AND
  before stopping (Discussion #23); never relay through the human; channel is
  canonical — decisions in #23 win. `TEAM_MACHINE` identifies the machine.
- Constitution: Law 1 (no architecture damage), Law 3 (reuse existing bench
  scripts), Law 7 (canonical `346100.0` mm/s speed of sound), Law 10 (stop/ask if
  intent unclear — **don't speculate about what the user wants, just ask**).
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for commits touching
  `docs/CONSTRAINTS_AND_PREFERENCES.md`; don't commit regenerable artifacts
  (STLs, JSON dumps, benchmark logs, `bench_*.txt`).
- Direct-to-main preference, but the numba landing used a landing branch + clean
  port (laptop approved that plan explicitly).
- Tool adoption rule: install + declare (`docs/TOOLS.md`) + import + whitelisted
  test; guard = `tests/test_tool_registry.py` + `scripts/toolcheck.py`.
- Laptop's `team_chat.py` protocol fixes (cursor, watch-stale-save, sync-launch)
  are on `kalles-main-branch`, **not yet on `main`** — landing them is the
  laptop's call, do not merge unilaterally.

## Progress

### Done
- **Laptop confirmation on #23** (2026-08-03T01:41:04Z): verified desktop's
  `593e149` already contains the numba fix; laptop's holding branch
  `fix/tmm-medium-numba` obsolete and dropped; **114 passed** on laptop too;
  approved the landing plan (keep main's numba-free fallback, land feature-flagged
  wiring non-AUDIT, don't merge either copilot branch's pure-Python refactor).
- **TMM numba landing on `main`** (commit `32d4c9f`): new `backend/tmm_numba.py`
  (pure `np.*` inside `@njit`, no `import math`, no circular `Hole` import);
  3 hunks into `backend/tmm_acoustics.py` (`TMM_USE_NUMBA` env flag, lossless-only
  `_action_arrays` precompute in `__init__`, int32-mask fast path in
  `resonance_phase`); `perf = ["numba>=0.60"]` extra in `pyproject.toml`;
  `docs/TOOLS.md` declaration (toolcheck PASS); parity test
  `test_numba_resonance_phase_matches_python()` in `tests/test_tmm.py`.
  Verified on `32d4c9f`: 540 wired cases max diff **0.0**; `find_resonance`
  ~6.4x, standalone `resonance_phase` ~9.8x; full whitelisted suite **114 passed**
  (126.9s); `TMM_USE_NUMBA=0` fallback identical (2.355755).
- **Wiki restructure** (commit `5c7529f`): `wiki/Internal-Research.md` rewritten
  as a hub index; new topic pages `Internal-Research-Acoustics.md`,
  `Internal-Research-Optimization.md`, `Internal-Research-Measurement.md`,
  `Internal-Research-Perception.md`, `Internal-Research-Resources.md`,
  `Internal-Research-Metamaterials.md` (organized by instrument category:
  percussion §4, low-clarinet deep dive §5 contrabass Bb/contra-alto Eb/straight
  bass/bass-in-A/folded, guitar §6, low sax §7, bowed/piano §8, standard
  woodwinds §9, brass §10, lamellophones §11, TMM integration §12, references
  §13). Renamed `wiki/Internal-Metamaterials.md` → `wiki/Internal-Research-Metamaterials.md`;
  updated `wiki/Internal-Home.md` and `docs/WIKI-INDEX.md`.
- **Metamaterials reference doc committed** (in `5c7529f`):
  `docs/RESEARCH_acoustic_metamaterials.md` — Claude + Kimi exports merged
  (Kimi §2.4: cross-category ranking, folded-geometry advantage, within-family
  low-woodwind ranking, bore verdict, bass-clarinet-in-A timbre-revival idea)
  + web-verified references.
- **Wiki cross-link fixes** (commit `b42b5bf`, this session's safe task): 7 broken
  `[[...]]` links fixed in `Home.md`/`FAQ.md`/`Getting-Started.md`/
  `3D-Printing-Guide.md` (targets `Internal-Home`, `Internal-Branches`,
  `Internal-Optimization`, `Internal-Research-Measurement`, incl. anchor fix
   `#Metric Standardization (2026-07-25)`). Validation script: **77 links, 0 broken**
   (code-span content excluded). Pushed `32d4c9f..b42b5bf` → `main`.
- **Claude artifact ports** (this session): `string_metamaterial.py` (commit
  `91b0df8`), then `brass_scaffold.py` + `metamaterial_elements.py` +
  `folded_bore_elements.py` + doc/wiki updates + toolcheck fix (commit `cf7e625`),
  all pushed. Verified exact reproductions: string band gaps (rigid
  `(1580.0,4183.3),(4768.6,8000.0)`; local `(921.1,2925.6),(4183.8,5918.5)`);
  brass open peaks 684.5/715.6/846.2, 1-3 combo 705.5/736.1/838.3/888.4
  (838.3 Hz = −16.2c), 4cm³/24.9mm resonator → 852.2 Hz (+12.2c); folded
  low-clarinet −12.8c bass / −22.9c contra-alto / −27.8c contrabass + rigid-HR
  feasibility table (contrabass fundamental unreachable below V=100). Design
  finding: rigid HRs suit upper partials/formants; `effective_density_locally_resonant`
  liner for fundamentals. Captured in `docs/RESEARCH_acoustic_metamaterials.md`
  §7 (new) + Appendix A/B + `wiki/Internal-Research-Metamaterials.md` §5.8/§10/§12.2/§12.3.
- **toolcheck guard fix** (commit `cf7e625`): `scripts/toolcheck.py` `_is_local`
  now resolves sibling modules nested under local roots (e.g.
  `backend/experiments/brass_scaffold.py` imported bare by another experiment) —
  no longer misreported as PHANTOM. Guard PASS (29 imported, 0 phantom);
  `tests/test_tool_registry.py` passes.
- **Laptop metamaterial integration merged to `main`** (this session): pulled
  `kalles-main-branch` (`cc5b447`–`fbbd1b8`, `3d318dc`) into working tree;
  merged numba fast path from `main` (`32d4c9f`) into laptop's `tmm_acoustics.py`
  (adds `_NUMBA_ENABLED`, `_action_arrays`, numba fast path for lossless
  instruments without metamaterials). **All 114 tests pass** (incl. 74 metamaterial
  tests: `test_metamaterial.py` 13, `test_metamaterial_low_clarinets.py` 36,
  `test_metamaterial_graded.py` 11, `test_metamaterial_intonation.py` 8;
  `test_numba_resonance_phase_matches_python` passes). Toolcheck PASS (29
  imported, 0 phantom).

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
- **Kimi K3 doc fixes — B1/B2/C-phase DONE on `opencode/build123d/laptop`**
  (this session; B1 `47e1b9a`, B2 `6d67f8d`, then C1–C6 + bore_optimizer fix).
  - B1: benchmark_all impossible ODs fixed + fingering charts aligned to
    canonical build + `_validate_instruments()` guard.
  - B2: outer_diameter/closed_top/n_bore_ctrl threaded through jax and
    two_phase optimizers (`n_bore_ctrl=4` now yields 4 control points);
    dead `note_to_freq`/`SEMITONE_MAP` removed; bare excepts replaced.
  - C1 coordinates `2ea8806` (bore_length required + bounds-checked on all 6
    transforms); C2 tmm_acoustics_jax `7d9ea95` (fingering-set validation,
    raw RMS, target_radius param); C3 chromatic_flute `3737885` (import
    fallback, 3c/2f register-3 guess, hole geometry in config); C4 pareto
    `ecff35f`/`c47ff9a`/`830fb61` (per-hole local-radii interpolation,
    explicit `[L,radii,hp,hd]` design vectors, generative_agent decode);
    C5 tmm_solver `c00d48a` (compute_frequencies fixed, from_network
    rewritten); C6 instrument_library `99e36cf` (verified flag, dup record
    removed, case-insensitive filters). bore_optimizer `439537e` (final
    metrics use optimized radii; bore_radii recorded).
  - bore_optimizer/stage1 fate: multi-segment radii interpolation DEFERRED
    (Kimi-rated P1, needs shared network.py geometry work); stage1_optimizer
    reviewed, no action. Full `pytest tests/` **158 passed / 2 skipped**;
    toolcheck PASS; build123d parity at parity (xaphoon_C known non-watertight
    in BOTH paths per `test_xaphoon_export_fails_gate`). Posted to #23
    (comment-17914586).

### In Progress
- Laptop Dask worker `laptop-worker` running, attached to desktop scheduler
  `tcp://100.69.113.41:8786` (logs: `scripts/laptop_worker_stdout.log` /
  `_stderr.log`, gitignored). Leave running while benchmarks use both machines;
  desktop's `cluster_health.py` will confirm once their commits land.
- **Kimi K3 doc fixes B3 = final wrap of `opencode/build123d/laptop`**
  (this session): all C-phase files committed; D-phase verification done
  (build123d parity at parity, toolcheck PASS, 158 passed / 2 skipped);
  remaining: final BOOT_STATE/REMINDERS commit + push branch. Desktop's
  `baroque_clarinet.json` option-1/2 answer (my option-2 recommendation in
  `discussioncomment-17914412`) and Fusion 360 contract approval still pending.

### Blocked
- Standing (not this session): `backend/spectral` implementation awaits user
  approval of `docs/DESIGN_spectral.md` (3 open questions). Inverse-design Tier 2
  blocked on `generative_agent`/`instrument_knowledge`/`spline_bore` not on `main`.

## Key Decisions

- Land wired numba onto `main` as a clean **port** (landing branch from
  `origin/main`, two commits), **not** a merge of the copilot branches; the
  pure-Python path stays the authoritative fallback (Law 1); laptop confirmed the
  pure-Python refactors were ~+15–20% slower and agreed not to merge them.
- Wiki restructure: **one page per major topic** (hub + Acoustics/Optimization/
  Measurement/Perception/Resources/Metamaterials), user-selected over finer or
  coarser grouping; metamaterials page by instrument category with per-instrument
  subsections, low clarinets deepest dive (user-requested).
- Research scope: reference doc + TMM-integration evaluation, **not** code
  porting; all metamaterial implementation ideas marked future-work. Repo
  integration mapping: Helmholtz side branch via `backend/core/network.py`
  `Port`/`NodeType` (new `HELMHOLTZ` node) feeding `junction2_reply_phase`/
  `junction3_reply_phase`; band-gap metrics from `backend/tone_hole_corrections.py`
  geometry; Piva/Gower/Abrahams formulas for resonator-distribution design; numba
  fast path is lossless-only so lossy resonator elements stay pure-Python or
  extend the njit function.
- This session: user asked for a task suggestion or, if none given, a **safe**
  fallback action — chose docs-only wiki cross-link repair (no architecture
  change, no law risk, no deletion, no merge).

## Next Steps

1. **Finish B3 push of `opencode/build123d/laptop`**: commit BOOT_STATE/REMINDERS
   update (this session), then push the K3-fix branch (`47e1b9a`..`HEAD`) to origin.
2. Standing: present `backend/spectral` design (`docs/DESIGN_spectral.md`) for
   user approval when the user is available.
3. **Await desktop replies** (posted #23, comment-17914586): (a) `baroque_clarinet.json`
   option-1/2 decision (laptop recommended option 2); (b) Fusion 360 contract change
   approval (no A/B/C fusion work until approved); (c) build123d spike + mesh-repair
   gate merge decision (comment-17906678).
4. **Deferred (not P0):** interpolate `n_bore_cp` radii into a multi-segment bore
   profile in `backend/optimization/bore_optimizer.py` (Kimi P1; needs shared
   network.py/Segment profile interpolation — coordinate with desktop before
   touching shared geometry).
5. **Reconcile `kalles-main-branch` deletion** with desktop: confirm which branch
   now carries the metamaterial/topk/spectral work toward `main` (history safe on
   `opencode/main/laptop`; desktop branch lacks `3d318dc`).
6. Optional user-verification: folded/low-clarinet notes wording in
   `docs/RESEARCH_acoustic_metamaterials.md` §7 / wiki §5.8.
7. **ML optimization integration** (future): add ML-based optimization methods
   (e.g., Bayesian optimization, neural surrogates, gradient-free methods) to
   complement the existing two-phase optimizer (`backend/two_phase_optimizer.py`).
   **Progress to date:** laptop delivered the reusable gradient-free winner
   as `backend/optimization/topk_polish.py` (DE + k-elite L-BFGS-B); surrogate
   warm-start tested and rejected on the shared contract. Desktop's comparison
   runners now take explicit budget args + `verify_with_retries` (PR #62), so
   `topk_polish` slots straight in. Added a dask-parallel path for the 5th
   family (`ebc2418`); PR #62 merged the 5-family suite + dask variants.
   Timing TBD — consider whether to optimize the physics pipeline further first
   (loss models, viscothermal accuracy) or proceed in parallel.

## Critical Context

- **`main` HEAD = `c8b9fd2`** (docs-only cherry-pick of laptop's research doc
  `8603240` onto `main`, per #23 plan to avoid pulling the 55-commit laptop branch
  into main) over `d663a43` (desktop's BOOT_STATE) over `7cae468` (BOOT_STATE) …
  over `32d4c9f` (numba wiring) over `5c7529f` (wiki restructure).
  **`origin/main` = `c8b9fd2`**.
- **`origin/kalles-main-branch` = DELETED** (no longer on origin as of
  2026-08-05). Full history preserved: `b198c4c` (its tip) is an ancestor of
  `origin/opencode/main/laptop`, so no commits lost. Local refs `kalles-rebased`,
  `test/kalles-into-main` also exist. Reconcile with desktop which branch now
  carries the metamaterial/topk/spectral work for `main` — desktop's
  `opencode/main/desktop` does NOT contain `3d318dc` (metamaterial impl).
- **`origin/opencode-instrument-designer` = `7f97975`** (desktop branch, PR #62:
  ML surrogate port + intonation pass tiers + `verify_with_retries` + PR stats
  snapshot / topk-thread-resolved BOOT_STATE). Comparison runners take budget
  args. The Copilot agent that acked laptop's top-k tuning is **paused until
  2026-09-01**, so desktop's opencode agent may pick up that work.
- **`origin/opencode/main/laptop` = `1e70d01`** (BOOT_STATE update): adopted
  REMINDERS.md coordination (`c5ab7d2`) + dask-parallel topk_polish path
  (`ebc2418`) + research docs (`8603240`: `docs/RESEARCH_design_to_finished_instrument.md`,
  `docs/WIKI.md` §11, `docs/WIKI-INDEX.md`, `wiki/Internal-Research-CAD-Pipeline.md`,
  `wiki/Internal-Research.md`, `wiki/3D-Printing-Guide.md`) + BOOT_STATE (`1e70d01`).
  **123 passed / 1 skipped** on laptop.
- **`origin/opencode/build123d/laptop`** = the K3-fix branch (was `e8d6254`
  spike + mesh-repair protocol). This session added B1 `47e1b9a`, B2 `6d67f8d`,
  C1–C6 (`2ea8806`..`99e36cf`), bore_optimizer fix `439537e` (HEAD). Not yet
  pushed at last BOOT_STATE write — final wrap pushes it. Awaiting desktop review
  of the spike merge (see #23 comment-17906678); K3 fixes posted as
  comment-17914586.
- Untracked regenerable artifacts left uncommitted: `bench_main.txt`,
  `bench_perf_tmm_medium.txt`, `bench_perf_tmm_refactor.txt`, `test_output/`.
- #23 stream: laptop confirmation (01:41:04Z) + laptop's three `team_chat.py`
  bugfixes pushed to `kalles-main-branch` (`45ddcb2`, `591c384`, `827c051`).
- **Laptop's low-clarinet metamaterial batch** — initially reported as "on main"
  but actually on `kalles-main-branch` (laptop corrected 02:48Z): commits
  `cc5b447` (family + STLs), `6a260d6` (graded arrays), `a4aed67` (12th-intonation
  curve), `fbbd1b8` (subcontrabass) = 83 tests passed, now at
  `origin/kalles-main-branch` = `fbbd1b8`. Physics: L2 homogenized under-estimates
  vs L1 explicit array (43–47% rel. err. at f0/base=4, 1.4–4% at f0/base=12–20;
  tests enforce f1_L1 < f1_L2); graded arrays give 2.0x stopband vs uniform at
  same target; depth-vs-12th curve 0.95x→+2..7c … 0.80x→+83..96c … 0.75x→+143..159c.
  Desktop can now run L2-vs-L1 parity sweep against ported `folded_bore_elements.py`
  / `metamaterial_elements.py` (laptop offers to port their code to `backend/experiments/`
  or adjust structure).
- **Laptop's register-suppression + soprano demos** (04:20Z/04:34Z): two new
  deliverables on `kalles-main-branch` (`478853c` → `b0a885d`):
  1. **Register-2 squeak suppression** (bass clarinet): HR stopband over the
     12th (~212 Hz) flattens phase margin at ~1.5 across 130–250 Hz; blind spot
     at f0=squeak (zero margin); compliance tail drops f1 −300..−1700c.
  2. **Soprano-clarinet demo** (600 mm × 15 mm): same physics at higher scale,
     429 Hz squeak suppressed (L1 margin 0.428, L2 0.149); trade-off curve
     f0/squeak 0.70–0.95 → margin ~0.43, f1 shift −1120..−1650c.
  Total metamaterial test suite: **89 passed** (7 test files). L1/L2 machinery
  generalizes across the full clarinet family (subcontrabass → soprano).
- **Laptop implemented metamaterials** (`3d318dc` on `kalles-main-branch`,
  186 passed, 02:06:45Z post): L1 `MetamaterialSideBranch` (Helmholtz side
  branch via `junction3_reply_phase`), L2 `MetamaterialSegment` (Dell/Krynkin/
  Horoshenkov effective-medium stopband), `TMMInstrument` `meta_slots`/
  `metamaterial_segments` args, `tests/test_metamaterial.py` (13 tests), doc
   `chat-logs/2026-08-03-metamaterial-implementation-research.md`. Desktop acked
   (discussioncomment-17875306) and offered to run the L2-vs-L1 parity sweep.
   **Not yet on `main`** — wiki §12 implementation items marked DONE on desktop's
   port side; laptop's own implementation is on `kalles-main-branch`.
- Research anchors (web-verified): Piva/Gower/Abrahams npj Acoustics 2:10 (2026)
  random Helmholtz-resonator band gaps w/ effective-properties formulas;
  Petersen/Kergomard et al. Acta Acustica 4:13 (2020) conical tonehole-lattice
  cutoff; Bader et al. JASA 145:3086 (2019) neodymium-magnet ring drum
  (~300–800 Hz); Bader Springer https://doi.org/10.1007/978-3-031-57892-2_16;
  Lercari et al. MDPI Appl. Sci. 12:8619 (2022) guitar top-plate cavities;
  Fischer et al. JASA 155(3_Suppl):A59 (2024) magnet-loaded guitar;
  Khodabakhsh 2025 spiral-neck HR; Lucklum DAS|DAGA 2025 interconnected HR
  lattice; Meier 2025 Materials & Design tunable phononic band gaps.
- Bass-clarinet family facts (used in doc/wiki): ~150 cm bore, written Eb3 ≈
  78 Hz, contrabass Bb ≈ 3 m tube doubled twice (hybrid cylindrical/conical,
  sub-wavelength features ~10–30 cm), contra-alto Eb >1.7 m straightened (least
  standardized), low-A bari-sax bell-length compromise, subcontrabass sax ≈
  2.74 m / 28.6 kg / lowest G#0 ≈ 25.95 Hz, bass clarinet in A from Wagner's
  *Lohengrin* (1848).
- Repo canonical constants unchanged: `SPEED_OF_SOUND = 346100.0` mm/s in
  `backend/tmm_acoustics.py` (Law 7 / chalumier parity).
- Git identity `Admin <kooshikooo@gmail.com>`; `gh` authed as `kooshikooo-lab`.
- Laptop identity `big-pickle`; desktop `TEAM_MACHINE=desktop`.

## Relevant Files

- `backend/tmm_acoustics.py` — numba wiring on `main` (env-flag block,
  lossless-only `_action_arrays`, int32-mask fast path in `resonance_phase`).
- `backend/tmm_numba.py` — **new on `main`** — `np.*` inside `@njit`, no
  `import math`, no circular `Hole` import.
- `pyproject.toml` / `docs/TOOLS.md` — `perf = ["numba>=0.60"]` extra + declaration.
- `tests/test_tmm.py` — `test_numba_resonance_phase_matches_python()` parity test.
- `backend/optimization/topk_polish.py` — top-k polish engine (DE + k-elite
  L-BFGS-B), now with optional `workers` param (dask/multiprocess DE).
- `tests/comparison/dask_topk.py` — dask-parallel runner for topk_polish
  (scheduler → local cluster → serial fallback); `tests/comparison/
  test_dask_topk.py` — 5 tests (comparison/slow markers).
- `docs/RESEARCH_acoustic_metamaterials.md` — Claude + Kimi + web research
  reference doc (committed); §7 = ported-artifact numerical findings, §8 =
  language/tooling.
- `wiki/Internal-Research.md` — hub index; `wiki/Internal-Research-{Acoustics,
  Optimization, Measurement, Perception, Resources, Metamaterials}.md` — topic
  pages; `wiki/Internal-Home.md`, `docs/WIKI-INDEX.md` — updated.
- `backend/experiments/` — ported Claude artifacts: `string_metamaterial.py`,
  `brass_scaffold.py`, `metamaterial_elements.py`, `folded_bore_elements.py`
  (all on `main`, exact reproductions verified; standalone `__main__` demos).
- `scripts/toolcheck.py` — `_is_local` resolves nested sibling modules (guard fix).
- `scripts/team_chat.py` + `scripts/.team_state.json` — Discussion #23 sync;
  laptop's 3 bugfixes were on `kalles-main-branch` (now deleted; history on
  `opencode/main/laptop`).
- `backend/experiments/build123d_koncovka.py` — **new on
  `opencode/build123d/laptop`** — build123d parity spike (koncovka_C / fujara_G /
  xaphoon_C); finding: CadQuery holed STL not watertight, build123d is.
- `docs/TOOLS.md` — **mesh-repair gate decision (2026-08-05)** on
  `opencode/build123d/laptop`: check-only gate wireable now; pymeshlab/pymeshfix/
  admesh declared but not adopted (awaiting desktop review).
- `backend/core/network.py`, `backend/tone_hole_corrections.py`,
  `backend/mouthpiece_models.py`, `backend/trumpet_acoustics.py` — metamaterial
  integration points mapped in the research doc/wiki (future-work).
- Standing: `docs/DESIGN_spectral.md` (awaiting approval), `docs/TOOLS.md`
  (tool registry), `scripts/toolcheck.py`, `scripts/team_watch.ps1`.
