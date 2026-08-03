# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- Benchmark the two copilot TMM perf branches (`perf/tmm-refactor-copilot`,
  `perf/tmm-medium-refactor-copilot`) against `main`, then land a real speedup.
- **Status: numba fast path is wired into `backend/tmm_acoustics.py` on branch
  `perf/tmm-medium-refactor-copilot` and gives ~6.4x on `find_resonance`
  (bit-identical output). Wiring is local/uncommitted — coordinate a commit with
  the laptop via #23 (laptop fixed the numba import bug and its fix is also
  uncommitted on the same branch).**

## Constraints & Preferences

- Repo mandatory boot sequence: read AGENTS.md + `docs/AI_CONSTITUTION.md` +
  `docs/CONSTRAINTS_AND_PREFERENCES.md`; **Step 0 = `python scripts/team_chat.py sync`**
  (Discussion #23); never relay machine-to-machine messages through the human.
- **Direct-to-main only**, no PRs (user correction). Copilot perf branches exist
  as work vehicles; do not merge the slower pure-Python refactors (see below).
- `AUDIT:` prefix for provisional commits; `GOVERNANCE-UPDATE` for commits
  touching `docs/CONSTRAINTS_AND_PREFERENCES.md`.
- Don't commit regenerable artifacts (`*_benchmark_results.json`, bench txt logs).
- **Tool adoption rule**: any third-party import must be declared in
  `pyproject.toml` + `docs/TOOLS.md` (guard: `tests/test_tool_registry.py`).
- Numba fast path is **opt-in via `TMM_USE_NUMBA` env (default ON when
  available), lossless-only** (`loss_model is None`) — pure-Python path stays
  authoritative; no architectural invention (Constitution Law 1).

## Progress

### Done
- Cloned `kooshikooo-lab/instrument-designer` to
  `C:\Users\Admin\AppData\Local\Temp\opencode\instrument-designer`; authed as
  `kooshikooo-lab`; on branch `perf/tmm-medium-refactor-copilot`.
- Boot sequence run (sync, AI Constitution, CONSTRAINTS, BOOT_STATE).
- Micro-benchmark `scripts/bench_tmm_micro.py` (identical across branches; extracted
  via `git show` for main baseline), 3 repeats:
  - main: find_resonance **0.495s**, resonance_phase **0.117s**
  - perf/tmm-refactor-copilot: 0.586s (+18.5%) / 0.136s (+15.6%) — slower
  - perf/tmm-medium-refactor-copilot: 0.589s (+19.1%) / 0.141s (+19.9%) — slower
- Parity check: refactor branch **bit-identical** to main (max diff 0.0) —
  regression is genuine, not behavioral.
- Numba import crash root-caused (`IMPORT_NAME` opcode, numba 0.66.0/Py3.14,
  `backend/tmm_numba.py`); posted to #23 (17874716).
- Laptop replied: confirmed both slowdowns, fixed numba by `math.*` → `np.*`
  inside `@njit`; verified 480 cases bit-identical; clean timing ~5.5–6.3x;
  earlier "0.94x" was a measurement artifact.
- Applied laptop's numba fix locally; 480 cases max abs diff **0.0**; standalone
  `resonance_phase` **9.8x** (6.74us vs 65.82us).
- Wired numba into `backend/tmm_acoustics.py`:
  - `_USE_NUMBA`/`_NUMBA_ENABLED` module flags (respects tmm_numba's own guard);
  - `self._action_arrays` precomputed in `__init__` (numba on + lossless);
  - fast path at top of `resonance_phase` (int32 fingering mask);
  - removed `from backend.tmm_acoustics import Hole` from tmm_numba.py (circular import).
- Wired-path parity: 540 cases numba vs pure-Python max abs diff **0.0**;
  `find_resonance` **6.42x** (447us vs 2870us).
- Declared `numba` in `pyproject.toml` (`perf` extra) + `docs/TOOLS.md`;
  `tests/test_tool_registry.py` green.
- Added `test_numba_resonance_phase_matches_python()` to `tests/test_tmm.py`
  (parity: numba vs pure-Python, bit-identical).
- Full whitelisted suite: **114 passed, 0 failed** (46.9s). `TMM_USE_NUMBA=0`
  fallback verified OK.

### In Progress
- **Uncommitted local edits** on `perf/tmm-medium-refactor-copilot`:
  `backend/tmm_acoustics.py`, `backend/tmm_numba.py`, `tests/test_tmm.py`,
  `pyproject.toml`, `docs/TOOLS.md`. Bench txt artifacts (`bench_*.txt`)
  untracked — do NOT commit. Decision on commit/merge coordination pending #23.

### Blocked
- Merging the copilot perf branches as-is: both are **pure-Python regressions**
  (+15–20%). The numba fast path supersedes their point. Do not merge the
  branch refactors; land the numba wiring (likely onto main) instead.
- Full-suite collection is limited to whitelisted `python_files` in
  `pyproject.toml`; many `tests/*.py` are ad-hoc scripts that `raise SystemExit`
  at import (quarantined, ignored by collection).

## Key Decisions

- Primary compared branch: `perf/tmm-refactor-copilot` (most recent, `3ba475b`).
- `bench_tmm_micro.py` is identical on both copilot branches → apples-to-apples.
- Numba adoption: feature-flagged, default ON, **lossless-only**, pure-Python
  fallback preserved — respects Law 1/no invention.
- Both machines confirmed the two copilot branches are slower in pure Python;
  laptop root-caused + fixed numba; desktop verified + wired it.
- Laptop's numba fix and desktop's wiring are both **uncommitted**; commit
  coordination happens on #23.

## Next Steps

1. Post this status + wiring summary to #23 (team_chat.py), confirm laptop's
   numba fix is same-as-desktop's; decide where to land (proposal: AUDIT: commit
   on the copilot branch, then cherry-pick/merge numba wiring onto main).
2. Consider committing as `AUDIT:` on `perf/tmm-medium-refactor-copilot` if
   laptop confirms; then reconcile to main per direct-to-main policy.
3. Re-run `python scripts/toolcheck.py` (must stay PHANTOM-empty after numba).
4. If pursuing further speedup beyond numba: revisit the slower branch refactors
   (deque/lambda in refactor, numpy Profile in medium) — likely drop them.

## Critical Context

- Machine: **desktop** (`TEAM_MACHINE=desktop`), Windows; system Python 3.14.6;
  numpy 2.4.6; numba 0.66.0; pytest 9.1.1; dask 2026.7.1; jax 0.11.0. `conda`
  NOT on PATH (no `tmmbench` env) — run via `python` with `PYTHONPATH=<repo>`.
- Channel: GitHub Discussion #23 (GraphQL `D_kwDOTOg0Rs4AoFZO`);
  `python scripts/team_chat.py sync` / `post --file`. Watcher runs in background.
- Repo governance: AI Constitution boot sequence; direct-to-main; AUDIT:/
  GOVERNANCE-UPDATE commit prefixes; install_hooks.ps1 guard for
  CONSTRAINTS_AND_PREFERENCES.md.
- Profile of hot path (`resonance_phase`): `junction2_reply_phase` (0.843s),
  `tanner`, `untanner`, `math.tan/atan/floor` — per-action Python helper-call
  overhead is the bottleneck (fixed by numba).
- Refactor branch change vs main: `deque` in `wavelength_near` + precomputed
  `_loss_phase_delta` lambda — lambda costs ~7% even in lossless path.
- Medium branch change: numpy-backed `Profile` + vectorized `as_stepped` —
  pure-Python regression confirmed by both machines.

## Relevant Files

- `backend/tmm_acoustics.py` — hot path (`resonance_phase`, `find_resonance`);
  numba wiring added (env flag block after `FOUR_PI`, `_action_arrays` in
  `__init__`, fast path at top of `resonance_phase`).
- `backend/tmm_numba.py` — fixed `math` → `np` inside `@njit`; removed
  `from backend.tmm_acoustics import Hole` (circular import).
- `scripts/bench_tmm_micro.py`, `scripts/compare_bench.py`,
  `scripts/test_numba.py`, `scripts/bench_tmm_dask.py`.
- `tests/test_tmm.py` — includes new `test_numba_resonance_phase_matches_python`.
- `tests/test_tool_registry.py` + `scripts/toolcheck.py` — tool guard.
- `pyproject.toml` — `perf = ["numba>=0.60"]` extra added; whitelisted
  `python_files` for pytest collection.
- `docs/TOOLS.md` — numba declared under `perf` extra.
- `docs/AI_CONSTITUTION.md`, `docs/CONSTRAINTS_AND_PREFERENCES.md`,
  `docs/session-logs/BOOT_STATE.md` — governance/boot sequence.
