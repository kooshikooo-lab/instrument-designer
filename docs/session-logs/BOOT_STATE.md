# BOOT STATE — Current Session Snapshot (reload at session start)

> This file is the reloadable boot context. At the start of every session, read
> this file and sync the team channel (`python scripts/team_chat.py sync`).
> Update this file at the END of every session so the next session can boot from it.
> This is what survives context drops — keep it current, not historical.

---

## Goal

- **Working branch: `opencode/main/desktop`** (HEAD `73159c1`).
- **This session's focus**: Phase 0 critical bug fixes — SoS literal cleanup (46 sites), two-phase optimizer register freeze, bass chalumeau merge conflict; then Phase 1 WoodwindOpenWind FEM integration.
- **Standing directive**: tools must be integrated into a pipeline, never just installed and forgotten; `AUDIT:` for provisional commits; ask rather than speculate when intent is unclear.
- **P0 questions posted to Discussion #23** — awaiting human decisions on 4 blocking items.

## Constraints & Preferences

- **Step 0 protocol**: `python scripts/team_chat.py sync` at session start AND before stopping (Discussion #23); channel is canonical.
- Constitution: Law 1 (no architecture damage), Law 3 (reuse existing bench scripts), Law 7 (canonical `346100.0` mm/s speed of sound), Law 10 (stop/ask).
- `AUDIT:` for provisional commits; `GOVERNANCE-UPDATE` for `docs/CONSTRAINTS_AND_PREFERENCES.md`; don't commit regenerable artifacts.
- Tool adoption rule: install + declare (`docs/TOOLS.md`) + import + whitelisted test.

## Progress

### Done (this session)
- **Merged PR #63**: Removed phantom `openwind` gitlink (shadowed pip package).
- **Merged PR #62**: 45-file import repair (tmm_acoustics imports moved to `archived_optimizers/`).
- **SoS Literal Cleanup plan**: 46 non-canonical speed-of-sound literals across 10 files, organized by dependency layer (physics → optimizers → core → tone-hole → tests).
- **Two-Phase Optimizer Fix plan**: Extract shared `detect_registers()` to `backend/physics/register_detection.py`, wire into selector's `TwoPhaseOptimizer` and standalone `two_phase_optimizer.py`, add `bore_length_bounds` enforcement for bass instruments, remove hardcoded `outer_diameter=22.0`/`closed_top=False`.
- **Bass Chalumeau Merge Conflict identified**: Desktop has tone-hole fix in `build_bass_chalumeau_Bb()`; laptop doesn't. Manual diff required before merge.
- **WoodwindOpenWind FEM prioritized**: Create `backend/woodwind_openwind.py` mirroring `TrumpetOpenWind`, register `REFINED` strategy for woodwinds.
- **Backlog defined**: CT-Scan Benchmarking (Issue #47), Demakein Replacement (Issue #48), Monte Carlo Tolerance Budget, Surrogate Audit, Tier 2 items.
- **P0 Questions posted to Discussion #23**: 4 blocking decisions needed (impossible ODs, bass chalumeau holes, two-phase scope, merge conflict).
- **ROADMAP.md completely overhauled** with Phase 0-3 plan.
- **Session log saved**: `chat-logs/2026-08-07-session-log.md` + P0 questions `chat-logs/2026-08-07-p0-questions.md`.

### In Progress
- SoS Literal Cleanup (10 files, 46 sites) — not yet started
- Two-Phase Optimizer Fixes — not yet started
- Validation suite run — pending

### Blocked
- P0 fixes await human decisions on 4 questions (Discussion #23)

## Key Decisions
- **SoS test expectations → 346100 mm/s** (Law 7: canonical source of truth)
- **Register detection → shared module** `backend/physics/register_detection.py` (Law 3, Law 4)
- **Two-phase optimizer: Fix, don't delete** (Law 1 — it's the default `ACCURATE` strategy)
- **Batch work**: SoS + two-phase today; surrogate + bass diff tomorrow
- **WoodwindOpenWind before remaining SoS test updates** (architecture over features)

## Next Steps
1. Await human decisions on 4 P0 questions in Discussion #23.
2. Execute Phase 0: SoS cleanup (by layer), Two-Phase fixes, validation.
3. Phase 1: WoodwindOpenWind FEM, surrogate audit.
4. Phase 2: CT-Scan benchmarking (Issue #47), Demakein replacement (Issue #48), Monte Carlo, Surrogate.

## Critical Context
- `origin/main` = `d935287`; `opencode/main/desktop` = `73159c1`.
- Test baseline: `pytest tests/` → 217 passed, 3 skipped; `python scripts/toolcheck.py` PASS.
- Pre-commit validation passes; `backend/inverse_design.py` is allowlisted as oversized.
- Merged PRs: #63 (openwind gitlink), #62 (45-file import repair).
- Discussion #23 — P0 questions posted, awaiting feedback.

## Relevant Files
- `backend/physics/bore_design.py` — analytic tone-hole physics (temp formula for SoS).
- `backend/tmm_acoustics.py` — canonical `SPEED_OF_SOUND = 346100.0`.
- `backend/two_phase_optimizer.py:73-97` — `detect_registers()` to extract.
- `backend/optimization/selector.py` — `TwoPhaseOptimizer` class to wire.
- `backend/modular_components.py:699` — `build_bass_chalumeau_Bb()` merge conflict.
- `backend/surrogate/` — `mlp_surrogate.py`, `bi_objective_bo.py` (audit first).
- `docs/ROADMAP.md` — complete Phase 0-3 plan.
- `chat-logs/2026-08-07-session-log.md` — full session audit.
- `chat-logs/2026-08-07-p0-questions.md` — 4 blocking questions for human.

(End of file)