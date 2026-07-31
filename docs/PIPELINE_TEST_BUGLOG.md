# Pipeline Test Bug Log - kalles-main-branch

Branch: kalles-main-branch (73d85d6)
Date: 2026-07-31
Status: OPEN / RESOLVED / VERIFIED

## Bug #1 - design_server.py imports non-existent modules
- File: woodwind_designer/engine/design_server.py:377, 482
- Import: `from backend.tmm_optimizer_v2 import TMMBoreOptimizerJAX` and `from backend.tmm_optimizer_sequential import SequentialBoreOptimizer`
- Reality: modules live in `backend/archived_optimizers/tmm_optimizer_v2.py` and `backend/archived_optimizers/tmm_optimizer_sequential.py`
- Impact: `/optimize/tmm` and `/optimize/sequential` endpoints fail at runtime (import inside worker thread), top-level import unaffected (import is lazy)
- Live verification: `/optimize/sequential` → `No module named 'backend.tmm_optimizer_sequential'`; `/optimize/tmm` → `No module named 'backend.tmm_optimizer_v2'`
- Fix: changed imports to `backend.archived_optimizers.tmm_optimizer_*`
- Status: RESOLVED

## Bug #2 - tmm_optimizer_sequential.py broken import chain
- File: backend/archived_optimizers/tmm_optimizer_sequential.py:25-32 (same pattern in tmm_optimizer_v2.py:22-27)
- Issue: relative import `.tmm_acoustics` fails when imported as `backend.archived_optimizers.tmm_optimizer_sequential` (module not in that package); fallback `sys.path.insert(dirname(__file__))` + `from tmm_acoustics import ...` also fails because `tmm_acoustics.py` is in `backend/` (parent), not in `archived_optimizers/`
- Impact: `SequentialBoreOptimizer` cannot be imported → `/optimize/sequential` endpoint broken (on top of Bug #1)
- Note: this is the "sys.path hack" anti-pattern flagged in AI_FAILURE_PATTERNS Failure #6 — file does not conform to package-relative import convention
- Fix: replaced try/except sys.path hack with direct `from backend.tmm_acoustics import ...` + `from backend.physics.losses import KeefeLoss` (both files)
- Status: RESOLVED

## Bug #3 - Generic /optimize (BoreOptimizer legacy redirect) produces no valid designs
- File: backend/archived_optimizers/bore_optimizer.py
- Root cause 1: `BoreOptimizer.__init__` stored `max_radius_jump=None` (line ~543) instead of applying the `(max_radius - min_radius) * 0.3` default used by the other two classes → constraint `np.diff(radii) - None` → TypeError → all individuals infeasible (cv=1e10)
- Root cause 2: `_compute_impedance_from_bore` used `from .mp_cache import ...` but `mp_cache.py` is at `backend/` root, not `archived_optimizers/` → ModuleNotFoundError
- Fix: applied the default max_radius_jump (matching other classes) + changed import to `backend.mp_cache`
- Verified: now returns 3 designs, 3 best_candidates, n_evals=3 (accuracy ~345c — legacy optimizer quality is poor, but no longer crashes/empty)
- Status: RESOLVED (quality caveat noted)

## Finding #4 - two_phase_optimizer: phase 2 L-BFGS-B "degrades" phase-1 result — VERIFIED: phase 1 is garbage, not a refinement bug
- File: backend/two_phase_optimizer.py + backend/tmm_acoustics.py:phase_cost_with_offset
- Test (5-note C4-G4, 600mm bore, open-open, reg=2, 5 holes): phase1 cost=0.0007 (9s) → phase2 cost=162c (60s)
- VERIFIED root cause: Phase 1 produces DEGENERATE solutions (all notes ~178-229 Hz). The phase cost `sin²(π·(phase - n_register))` after median removal is an unreliable proxy:
  - The phase curve is nearly FLAT near the targets (phase ≈ 2.0 across 261-228 Hz), so a tiny phase deviation (d=0.008 → cost 0.00006) corresponds to a -238 CENT frequency error. The actual phase=2 crossing (the note played) is 227.8 Hz.
  - `sin²(π·d)` is 0 at ANY integer deviation → wrong-register solutions cost ~0.
  - Median removal hides global pitch errors (all-notes-same-frequency degeneracy).
  - Phase cost and peak cost DISAGREE for the same geometry: phase says "good", find_resonance says "flat by 238c".
- Phase 2 is not the problem: starting from the degenerate phase-1 solution, L-BFGS-B+peak cost honestly converges to a local min at 162c. The real issue is phase 1's starting point.
- Attempted fix (rejected): phase 1 with real cents cost (find_resonance) is 31x slower (170ms vs 5.5ms/call) → 252s for popsize=6/maxiter=6 and STILL fails because the fixed n_register=2 cannot represent notes spanning registers 2 and 3. Requires redesign (per-note register in phase-1 cost + faster resonance search), NOT a quick fix.
- This is a KNOWN issue in the repo: wiki/Internal-Known-Issues.md:14, docs/ROADMAP.md:132, chat-logs/2026-07-24-session-recovery.md ("phase_cost_with_offset hides register mismatch"), tests/test_phase_register.py ("NOT phase_cost_with_offset to prevent register mismatch").
- Status: OPEN (needs redesign: register-aware cents-based phase-1 cost; verify wavelength_near returns the closest crossing)

## Finding #5 - two_phase_optimize result not directly consumable by stl_export — RESOLVED
- File: backend/two_phase_optimizer.py vs backend/stl_export.py
- `two_phase_optimize()` returned `bore_radii`, `hole_diameters`, `hole_positions` but NO `bore_length_mm` key; `export_optimizer_result()` requires `result["bore_length_mm"]` (KeyError / empty-sample failure without it)
- Also: result contained numpy arrays → `json.dump(result)` raises TypeError (not JSON serializable) — endpoint result serialization would fail
- Fix: added `bore_length_mm` + converted all three arrays to `[float(...)]` lists
- Verified: two_phase run (popsize=6/maxiter=6) → result JSON-serializable, `export_optimizer_result` wrote 633KB STL to output/two_phase_test.stl
- Status: RESOLVED

## Bug #7 - tmm_optimizer_v2.py NameError: target_freqs not defined
- File: backend/archived_optimizers/tmm_optimizer_v2.py:85
- Code used `fundamental = min(target_freqs)` but `__init__` param is `target_frequencies` (stored as `self.target_freqs` at line 73). Only the first occurrence (auto bore_length default) was broken; `self.target_freqs` used correctly everywhere else.
- Impact: `/optimize/tmm` failed immediately with NameError after Bug #1/#2 import fixes were applied
- Fix: line 85 → `min(self.target_freqs)`
- Verified: direct run + `/optimize/tmm` via server → completed, success=True, rms=330.9c (quality poor, but functional)
- Status: RESOLVED

## Finding #8 - Legacy BoreOptimizer: misleading n_evaluations + degenerate scale_evenness
- File: backend/archived_optimizers/bore_optimizer.py
- Bug (fixed): `n_evaluations` returned `len(X)` = number of UNIQUE final population members (after MonotonicRepair + eliminate_duplicates collapse 10 → 2-4), not actual evaluations. Fix: report `res.algorithm.evaluator.n_eval` (true count, 20 for pop=10×2gen) + new `n_unique_designs` field. Verified: n_evaluations=20, n_unique_designs=4.
- Not-a-bug (design limitation): `scale_evenness=1.4e10` is the sentinel for `mean_diff <= 1e-6` / `n_peaks < n_targets` — i.e., the config (261-440 Hz single register on a 0.328m bore) has fewer distinct resonances than targets, so a scale is physically impossible. This is honest reporting for an ill-posed request, not a code defect. The legacy path was designed for wide-range multi-register targets (docstring example: 261-2877 Hz).
- Status: RESOLVED (n_evaluations reporting) / scale_evenness sentinel left as-is

## Bug #10 - Inconsistent job-status URL structure across optimize endpoints — RESOLVED (alias)
- `/optimize/start` → status at `/optimize/{job_id}/status` (3-segment); `/optimize/tmm` → `/optimize/tmm/{id}/status`; `/optimize/sequential` → `/optimize/sequential/{id}/status` (4-segment). A client POSTing to `/optimize/start` naturally tries `/optimize/start/{id}/status` → 404.
- Fix: added backward-compatible alias `GET /optimize/start/{job_id}/status` (design_server.py) delegating to the existing handler. Original route unchanged.
- Verified live: both `/optimize/{id}/status` and `/optimize/start/{id}/status` return the same job.
- Status: RESOLVED

## Live endpoint verification (server run 2026-07-31, after fixes)
- `/health` → OK v1.0.0
- `/presets` → 10 presets (reedpipe, shawm, recorder, etc.) OK
- `/optimize/presets` → 15 optimization presets OK
- `/optimize/sequential` → FAILED: `No module named 'backend.tmm_optimizer_sequential'` (Bug #1 + #2) — RETESTED AFTER FIX: completed, success=True, rms=2.07c (ABSOLUTE, honest), scale_rms=0.46c, median_offset=-2.04c, bore_length=325.4mm, 4 holes, STL=633,684 bytes (Finding #6 fixed — no more fake 1.3e-7 with hidden -176c offset)
- `/optimize/tmm` → FAILED: `No module named 'backend.tmm_optimizer_v2'` (Bug #1) — RETESTED AFTER FIX: completed, success=True, rms=546.3c (honest, was falsely 330.9c), scale_rms=332.9c, global_offset=-392.4c (Finding #6 applied to v2)
- `/optimize/start` → "completed" but EMPTY (Bug #3) — RETESTED AFTER FIX: completed, 2 designs, n_evaluations=20 (true count, was 2), n_unique_designs=1-4, bore_length=328.2mm (Finding #8: honest reporting; scale_evenness=1.4e10 sentinel remains for ill-posed single-register configs; MonotonicRepair + eliminate_duplicates can collapse pop 10 → 1 unique design — legacy limitation)
- STL export: works for `/optimize/sequential` result (633KB STL); `two_phase_optimize()` result now also consumable (bore_length_mm added + numpy→list, Finding #5 fixed — verified 633KB STL via export_optimizer_result)
- NOTE: `GET /optimize/start/{job_id}/status` alias added (Bug #10); both status routes work

## Finding #6 - SequentialBoreOptimizer reports perfect RMS but is uniformly 176c flat — RESOLVED
- File: backend/archived_optimizers/tmm_optimizer_sequential.py
- Test (5-note C4-G4 closed-top, bore 7.25mm): success=True, final_rms_cents=1.5e-07, peak=2.8e-07
- BUT matched_frequencies show every note at exactly -176.17c (e.g. target 261.63 → actual 236.32)
- Root cause: ALL objectives (lines 396-397, 484-485) AND the final metric (595-597) subtracted the median offset (`sqrt(mean((c - median)^2))`). The optimizer can then report "perfect" while the instrument is unusably flat; it also allowed a degenerate local minimum where every fingering resonates at the same frequency.
- Fix:
  - Objectives now use absolute RMS `sqrt(mean(c^2))` (no median subtraction) in `_de_hole_objective`, `_refine_objective`, and `CorrectedPowellOptimizer._objective`
  - Final metric reports TRUE `final_rms_cents`/`peak_error_cents` (absolute) plus new `scale_rms_cents` (evenness) and `median_offset_cents` (global tuning offset)
  - Final evaluation now includes `loss_model=KeefeLoss()` (was lossless → reported exact-0 errors while loss-inclusive eval showed ~2c off)
- Verified: absolute errors now -2.7..-1.4c, scale_rms=0.46c, median_offset=-2.04c — genuinely well-tuned, honest metrics
- Same pattern fixed in tmm_optimizer_v2.py (_objective + final eval)
- Status: RESOLVED

## Verified-working pipeline path (workaround until bugs fixed)
`two_phase_optimize()` (backend/two_phase_optimizer.py) runs end-to-end, then convert its result to sequential format and call `stl_export.export_optimizer_result()`. Needs an adapter for `bore_length_mm` key.

## Finding #11 - Quarantined script-style test files still reference pre-refactor import paths
- Files: tests/test_stl_export.py, tests/test_bore_profile.py, tests/test_desktop_fixes.py, tests/test_import2.py, tests/benchmark_bass_clarinet.py, tests/benchmark_diatonic.py, tests/diagnose_clustering.py, tests/diagnose_fingering_direction.py, backend/benchmark_chalumeau.py
- Bug (same root cause as Bug #1/#2): `from backend.tmm_optimizer_sequential import ...` / `from backend.tmm_optimizer_v2 import ...` — modules were moved to `backend/archived_optimizers/`. These are script-style files (top-level executable code, not pytest functions) and are deliberately EXCLUDED from pytest via `addopts --ignore` in pyproject.toml (legacy quarantine), so they did not break CI (32 collected tests all pass).
- Fix applied: updated imports to `backend.archived_optimizers.tmm_optimizer_*` in all listed files.
- Caveat: these files are still ignored by design; `tests/test_desktop_fixes.py` additionally fails at runtime with `KeyError: 'rms_cents'` (expects a result field that no longer exists) and was NOT made pytest-runnable — that one needs a real rewrite if it should rejoin the suite.
- Status: RESOLVED (import paths) — files remain excluded from pytest via addopts --ignore
