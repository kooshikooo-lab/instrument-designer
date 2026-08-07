# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- **Working branch: `opencode/build123d/laptop`** (laptop).
- **Desktop branch `opencode/main/desktop`** now at `9fb1c0b` (Phase 0 complete).
- **Phase 0 COMPLETE (desktop)**: SoS literal cleanup, Two-Phase optimizer register freeze, bass chalumeau merge conflict resolved — merged into laptop.
- **Laptop merge RECONSTRUCTED + caught up to desktop Phase 0**: broken single-parent merge `73ae792` replaced by proper 2-parent merge `e794979` (parents `56cad29` + `962b3f9`), then merged desktop `9fb1c0b` (Phase 0) on top.
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

### In Progress
- Laptop: Phase 1 tasks per work separation — desktop owns WoodwindOpenWind FEM skeleton + surrogate audit (per REMINDERS threads 17-19). Laptop resumes its Phase 0/1 queue (SoS cleanup folded into desktop's; Fusion 360 Phase 2b CAM probe cursor from laptop BOOT_STATE).
- Laptop cursor (pre-merge): P0-2b CAM-activation probe (Fusion 360 Phase 2b) — trigger/result/progress constants added, `_delayed_phase2b` + `_run_phase2b()` NOT yet implemented.

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
- `origin/main` = `d935287`; `opencode/main/desktop` = `9fb1c0b` (was `962b3f9` at merge time).
- Laptop branch `opencode/build123d/laptop`: HEAD after reconstructing merge + merging desktop Phase 0.
- Test baseline (desktop): `pytest tests/` → 217 passed, 3 skipped; laptop full suite on merge content → **288 passed, 3 skipped** (pre-Phase-0-merge); re-run pending after Phase 0 merge.
- Pre-commit validation passes; `backend/inverse_design.py` is allowlisted as oversized.
- Merged PRs: #63 (openwind gitlink), #62 (45-file import repair).
- Original broken merge `73ae792` (single-parent, partial) was force-replaced with `e794979` (proper 2-parent merge). Desktop notified via #23 comments 17927394 + 17927522.

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