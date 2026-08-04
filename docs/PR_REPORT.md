# PR Report — 2026-08-04

Status of all open PRs on `kooshikooo-lab/instrument-designer`, with per-PR
rationale, code-map, and verification. Written by the opencode agent
(`opencode-instrument-designer` branch) so other agents (desktop, laptop,
reviewer) can understand each PR without re-reading the full diff.

---

## Open PRs at a glance

| PR | Head branch | Title | State | Mergeable | Commits | ± |
|----|-------------|-------|-------|-----------|---------|---|
| [#62](https://github.com/kooshikooo-lab/instrument-designer/pull/62) | `opencode-instrument-designer` | fix: repair broken `tmm_acoustics` imports across 45 files + numba test guard | OPEN | MERGEABLE | 5 | +2609/−75 |
| [#61](https://github.com/kooshikooo-lab/instrument-designer/pull/61) | `mai-code-1-flash-test-branch` | refactor: shared optimization problem metrics | OPEN | MERGEABLE | 1 | +102/−29 |
| [#58](https://github.com/kooshikooo-lab/instrument-designer/pull/58) | `feature/dask-jvm-chalumier-compliance` | feat: chalumier JVM heap cap + Dask distributed design scripts | OPEN | UNKNOWN* | 1 | +357/−4 |
| [#33](https://github.com/kooshikooo-lab/instrument-designer/pull/33) | `experiment/unconventional-shapes` | fix: resolve 12 compliance violations per AI Constitution | OPEN | UNKNOWN* | 9 | +7954/−272 |

\* `UNKNOWN` = GitHub has not finished computing mergeability (needs a refresh
on the PR page / pending checks); the PRs are not known-conflicting.

---

## PR #62 — opencode-instrument-designer → main  (OWNED BY THIS AGENT)

**Purpose.** The `opencode-instrument-designer` branch is the opencode agent's
permanent working branch (user directive, 2026-08-04), based on this lineage's
`origin/main` (`d663a43`). This PR lands the branch's fixes onto `main`:
repair the import breakage left by prior merges, restore the dropped numba fast
path, and port the ML-surrogate / AI-family comparison work so both machines
converge on one implementation.

### Commit 1 — `56d0ec9` fix: repair broken `tmm_acoustics` imports across 45 files

**What.** 50 files (`backend/`, `scripts/`, `tests/`) imported `tmm_acoustics`
and `import tmm_acoustics` as a top-level package, but the module lives at
`backend/tmm_acoustics.py`. All were corrected to `backend.tmm_acoustics`.

**Why.** The audit (`python -m compileall`) showed the tree did not even
import — every module that reached for the TMM engine crashed at import time.
No logic was changed; this is mechanical import repair.

**Code-map.** Representative fixes: `backend/chromatic_flute.py`,
`backend/fingering_reference.py`, `backend/trumpet_acoustics.py`,
`backend/solvers/tmm_solver.py`, plus 45 in `scripts/`/`tests/`.

**Verified.** `from backend.chromatic_flute import ChromaticFluteModel` and
`from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND`
both import; whole tree compiles.

### Commit 2 — `0b6e9ad` fix: make numba parity test skip when wiring absent

**What.** `test_numba_resonance_phase_matches_python` imports
`_NUMBA_ENABLED` from `backend.tmm_acoustics`. The `7cae468` metamaterial merge
overwrote that module and dropped the numba wiring from `32d4c9f`, so the test
failed on a pre-existing branch (`d663a43`). The test's own skip-guard was
robusted to skip cleanly when the wiring is absent.

**Why.** The failure predates this branch; the numba wiring itself was restored
in commit 4 below. This commit made the test honest about its precondition in
the interim.

### Commit 3 — `9e58f39` docs: BOOT_STATE — branch + PR #62; numba restore follow-up

**What.** Session-state snapshot pointing at the new branch/PR and tracking the
numba restore as a follow-up. Docs only.

### Commit 4 — `da8e8fc` perf: wire numba-accelerated resonance phase into TMM

**What.** Re-applied the `32d4c9f` fast path that `7cae468`'s metamaterial merge
dropped. `backend/tmm_numba.py` was intact — only the wiring in
`backend/tmm_acoustics.py` was missing.

**The wiring (code-map).**
- `TMM_USE_NUMBA` env flag (default ON when available); `_NUMBA_ENABLED` module
  flag; `numba_resonance_phase` bound from `backend.tmm_numba` when available
  (`backend/tmm_acoustics.py:44-53`).
- `_action_arrays` precomputed in `_prepare_phase()` (`tmm_acoustics.py:614`),
  **not** `__init__` — so metamaterial `meta_slots`/`metamaterial_segments`
  wired *after* construction are picked up (the two metamaterial tests that
  failed in the interim failed exactly because the precompute lived in
  `__init__` and missed post-construction wiring).
- Fast path gated on: `_NUMBA_ENABLED` **and** `loss_model is None` **and** no
  `pipe_meta`/`meta_branch` actions (`tmm_acoustics.py:707`). Metamaterial
  instruments always use the Python walk.
- Fast path calls `numba_resonance_phase(*self._action_arrays, mask,
  wavelength, closed_top=self.closed_top)` with an int32 fingering mask
  (`[1 if f == Hole.OPEN else 0]`) (`tmm_acoustics.py:732`).

**Why.** ~6.7× `find_resonance` speedup, bit-identical results — pure-Python
remains the authoritative fallback (Law 1). The numba module is already in the
numba-0.66/Python-3.14-safe form (pure `np.*` inside `@njit`, no `import math`).

**Verified.** 540 wired cases max diff **0.0**; benchmark ~8.5 µs vs 56.7 µs
per `resonance_phase` call = 6.66×; `TMM_USE_NUMBA=0` → `_NUMBA_ENABLED=False`
confirmed; new test `test_meta_disables_numba_fast_path` added.

### Commit 5 — `6870fde` feat: port ML surrogate optimizers + AI/ML family comparison suite

**What.** Ported the desktop's uncommitted ML-surrogate pile so both machines
share one implementation.

**Why.** Two repos, no shared history — the desktop had developed this work in
an uncommitted working tree. Porting to the opencode branch (the permanent
working branch) puts it under version control and on `main` via this PR.

**Code-map.**
- `backend/ml_surrogate_optimizer.py` — two-phase bore optimizer. Phase 1:
  `differential_evolution` global search on `inst.phase_cost_with_offset(...)`
  (fast, register-agnostic). Phase 2: `L-BFGS-B` polish on
  `peak_cost_nearest(...)` (register-aware). Builds on `backend.tmm_acoustics`
  `tmm_instrument_from_radii` + `backend.two_phase_optimizer`
  (`peak_cost_nearest`, `detect_registers`).
- `backend/ml_optimizer_splitted.py` — alternate single-call harness
  (`ml_surrogate_optimize`) around the same two-phase pattern. Fixed two latent
  desktop bugs so the module actually imports: missing `import time` (used
  `time.time()` at runtime) and an invalid dict-key literal
  (`n_bore_ctrl=n_bore_ctrl` → `'n_bore_ctrl': n_bore_ctrl`).
- `tests/comparison/` — shared framework + suite:
  - `comparison_framework.py` — already present on opencode and byte-identical
    to desktop's (verified); `AlgorithmResult` dataclass + `AlgorithmComparator`.
  - `ai_methods_benchmark.py` — four AI/ML families on the canonical
    `chalumeau_C` TMM task (fixed skeleton, 6 bore radii as decision vars,
    absolute RMS cents objective via `backend.jax_optimizer.eval_all`):
    Bayesian (botorch `SingleTaskGP` + `qLogExpectedImprovement`), neural
    surrogate (PyTorch MLP + `differential_evolution`), RL (REINFORCE over
    sequential radius decisions), gradient-free (CMA-ES/PSO/DE).
  - `ai_methods_dask.py` — Dask-parallel, deep-budget variants; every runner
    accepts a batch evaluator and falls back to serial when Dask is absent.
  - `test_ai_methods_comparison.py` — marked `comparison`/`slow`; each family
    must converge under `SANE_RMS_CENTS = 150.0`; prints the report table.
  - `test_ml_surrogate_optimizer.py` — 7 tests for the two-phase optimizer
    (build instrument, phase 1, phase 2, full run, low-clarinet + folded-bore
    configs).
- `backend/experiments/` — `bore_builder.py` (segment + insertion bore
  composer, tonehole shunt matrices), `benchmark_and_optimize.py` (intonation/
  peak-quality metrics + scipy two-phase demo), `jax_resonator_sketch.py`
  (JAX-autodiff Helmholtz shunt element, `UNTESTED`-flagged sketch). Ported
  alongside the existing `brass_scaffold.py`/`metamaterial_elements.py`/
  `folded_bore_elements.py` siblings (desktop's root-level `folded_bore_elements.py`
  verified byte-identical to opencode's experiments copy).
- `pyproject.toml` — added `test_ml_surrogate_optimizer.py` to the pytest
  collection whitelist.
- `scripts/run_all_tests.py` + `docs/TEST_MATRIX.md` — new `comparison` medium
  tier category.

**Verified.** 7 ML-surrogate tests pass (5.5 s). 6 comparison tests pass
(47.7 s): Bayesian 64.9¢ / neural 34.7¢ / RL 26.2¢ / gradient-free 9.6¢ RMS on
the shared Bb-clarinet task. Full default pytest collection: **121 passed**.

### PR-level audit (all 5 commits)

- `python -m compileall backend scripts tests woodwind_designer` — OK
- `scripts/run_all_tests.py --tier low --force` — all PASS
- `scripts/run_all_tests.py --tier medium --force` — all PASS
- Default `pytest tests/` — **121 passed** (66.8 s)
- Governance guard hooks active; no protected governance file touched
- `test_output/testing/` left untracked (regenerable artifact)

---

## PR #61 — mai-code-1-flash-test-branch → main

**Purpose.** Consolidate the optimizer stack's metric contract. The optimizer
pipeline had drifted across entry points, each defining its own cents
conversion and metric interpretation.

**Changes.**
- New shared optimization-problem module with canonical metric summaries.
- Bore optimizer moved onto the shared absolute-RMS metric path.
- Two-phase and Pareto optimizers wired to the same cents-to-metrics helper.
- Regression test locking the absolute-RMS contract.

**Why.** Single canonical semantics so objectives/benchmarks compare against the
same contract; removes duplicated metric logic; keeps metric interpretation
separate from solver logic (physics boundary preserved).

**Verified.** `pytest -q tests/test_optimization_problem.py` — 1 passed.

---

## PR #58 — feature/dask-jvm-chalumier-compliance → main

**Purpose.** Second batch of pre-existing desktop work (after PR #55's
metric/import remediation). Fixes chalumier JVM timeouts/RAM saturation and
adds the Dask distributed design tooling used for the chalumier sweep.

**Changes.**
- `woodwind_designer/engine/chalumier_wrapper.py` — cap JVM heap `-Xmx2g`
  (3 uncapped JVMs saturated RAM and caused Dask sweep timeouts); design
  timeout 600 s → 1800 s. Result: `d_major_flute` now fails fast with an
  upstream chalumier `AssertionException` (balance validation in
  `examples/dmajor-folk-flute.chal`) instead of a wrapper timeout.
- New scripts: `scripts/start_desktop_cluster.py` (desktop Dask workers
  `6x2` threads, `2.5GB` each, reconnect loop for scheduler downtime/Tailscale
  blips), `scripts/chalumier_design_remote.py` (remote Dask runs, ships the
  fixed wrapper to workers at runtime, never modifies the remote repo).
- PS1 wrappers: `run_dask_sweep.ps1`, `run_dask_scheduler.ps1`,
  `run_remote_design.ps1`, `run_test_sweep.ps1`, `start_desktop_cluster.ps1`,
  `compliance_sweep.ps1` (resource tiers).
- Logs/docs: `scripts/compliance_log.jsonl` (recurring ComplianceCheck results);
  `docs/TEST_MATRIX.md` (chalumier section updated); `docs/AI_FAILURE_PATTERNS.md`
  (Failure #11: compliance check skipped before edit, then defended — root cause
  manual trigger, fix recurring Task Scheduler task).

**Verified.** All new Python scripts pass `--help` + AST parse; all PS1 pass
PowerShell parser; `chalumier_wrapper.py` imports, `-Xmx2g` present; deps
available (`distributed 2026.7.1`, Python 3.14.6); compliance watchdog shows
only the 44 pre-existing backend violations (scripts live outside scanned
`backend` dirs).

**Out of scope.** `chalumier` gitlink build artifacts (`gradle/`,
`test-output/`) left uncommitted.

---

## PR #33 — experiment/unconventional-shapes → main

**Purpose.** Fix 12 compliance violations across 15 files to satisfy the AI
Constitution (Laws 4, 5, 7, 9, 10) and the pre-commit checklist.

**Changes.**
- **Governance:** add 6 docs (`AI_CONSTITUTION.md`, `CONSTRAINTS_AND_PREFERENCES.md`,
  `COMPLIANCE_CHECK.md`, `AI_FAILURE_PATTERNS.md`, `ARCHITECTURE_DECISIONS.md`,
  `ARCHITECTURE_CHECKLIST.md`).
- **Law 7 (No Code Duplication):** delete `backend/scale_definitions.py` (pure
  re-export of `instrument_knowledge.py`, nothing imported it); dedup
  `SPEED_OF_SOUND` in `tmm_acoustics_jax.py` (import from canonical
  `tmm_acoustics.py`).
- **Law 9 (No Module-Level Mutable State):** `_agent: GenerativeAgent | None`
  module global → `get_agent._cache` function attribute.
- **Law 10 (No Hardcoded Secrets/Addresses):** hardcoded Dask scheduler IP →
  `DASK_SCHEDULER_URL` env var; hardcoded `OLLAMA_URLS` → comma-separated
  `OLLAMA_HOSTS` env var.
- **Law 4/5 (Physics Separation / Thin Orchestrators):** extract bore shape
  generators, `DesignSpec`/`CandidateResult` dataclasses, `build_targets`,
  `suggest_from_knowledge`, `optimize_candidate_standalone` into
  `backend/physics/pipeline_utils.py`; narrow `generative_agent.py` from 1111 →
  512 lines; `spline_bore.py` `SPEED_OF_SOUND` moved to local import inside
  `validate()`.
- **Pre-commit checklist:** fix bare `except:` in `two_phase_optimizer.py`,
  `benchmark_all.py`, `benchmark_dask.py`, `jax_optimizer.py`; fix bug in
  `two_phase_optimizer.py` (`targets = np.array(hole_lens)` clobbered frequency
  targets with hole lengths); dedupe the try/except import block in
  `two_phase_optimizer.py`.

**Verified.** All modified files pass `py_compile`; full import chain verified
(`from backend.generative_agent import *`).

**Note for other agents.** This branch is a large cumulative experiment branch
(9 commits, +7954/−272) and includes the governance docs that later PRs
(including #62's process) reference. Its mergeable state is pending a GitHub
recompute; it is not known-conflicting.

---

## How this PR #62 interacts with the others

- **#62 vs #61:** different concerns (import repair + numba + ML port vs. metric
  contract). #61 touches `two_phase_optimizer.py`-adjacent metric helpers; #62
  adds modules that *call* `two_phase_optimizer` functions but does not modify
  them, so conflicts are unlikely.
- **#62 vs #58:** #58 is scripts + chalumier wrapper; #62 does not touch those
  files.
- **#62 vs #33:** #33 modifies `two_phase_optimizer.py`, `jax_optimizer.py`,
  `benchmark_all.py` and adds `backend/physics/pipeline_utils.py`. #62's
  ported tests call `backend.jax_optimizer.eval_all` and
  `backend.two_phase_optimizer` — if #33 merges first, re-run the comparison
  suite against the merged `main` to confirm the metric semantics match (both
  converge on absolute-RMS / cents contracts, which is mutually consistent).
