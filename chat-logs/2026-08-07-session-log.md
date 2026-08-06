# Session Log — 2026-08-07

## Summary
Comprehensive audit and planning session. Identified all blocking issues, created prioritized execution plan, began Phase 0 execution.

## Key Decisions Made

### 1. Speed-of-Sound Literal Cleanup (Law 7)
- **Decision**: Update all 46 non-canonical SoS literals to import `SPEED_OF_SOUND = 346100.0` from `backend/tmm_acoustics.py`
- **Test expectations**: Update to 346100 mm/s (canonical) per Law 7
- **Execution**: By dependency layer (physics → optimizers → tone-hole → tests)

### 2. Two-Phase Optimizer: Fix, Don't Delete (Law 1, Law 3)
- **Decision**: Fix both implementations (selector's `TwoPhaseOptimizer` + standalone `two_phase_optimizer.py`)
- **Register detection**: Extract to shared `backend/physics/register_detection.py` (Law 3, Law 4)
- **Freeze registers**: Once from initial geometry (Discussion #23 decision)
- **Bore length bounds**: Enforce for bass instruments (>1m)
- **Hardcoded params**: Remove `outer_diameter=22.0`, `closed_top=False` → read from config

### 3. WoodwindOpenWind FEM Integration (Phase 1 Priority)
- **Decision**: Create `backend/woodwind_openwind.py` mirroring `TrumpetOpenWind`
- **Selector wiring**: Route woodwinds (CLARINET, SAXOPHONE, FLUTE, CHALUMEAU) → `REFINED` strategy
- **Validation**: Add TMM vs FEM comparison to `run_optimizer_comparison`

### 4. Backlog Priorities (Phases 2-3)
| Phase | Work | Source |
|-------|------|--------|
| 2.1 | CT-Scan Benchmarking (bassoon FT40/FT44, contra clarinets) | Issue #47 |
| 2.2 | Demakein Replacement (11 presets → TMM profiles) | Issue #48 |
| 2.3 | Monte Carlo Tolerance Budget | Tier 1 (Claude) |
| 2.4 | Surrogate Audit (mlp_surrogate.py, bi_objective_bo.py) | Tier 1 (Claude) |
| 3.1 | Reaming Allowance / Post-print Adjustability | Tier 2 (Human) |
| 3.2 | JND-Weighted Intonation Objective | Tier 2 (Human) |

## Phase 0 Progress (Today)

### ✅ Completed
- Team channel sync (no new messages)
- PR #63 merged (removed phantom openwind gitlink)
- PR #62 ready for merge (45-file import repair)

### ⏳ In Progress
- SoS Literal Cleanup (10 files, 46 sites)
- Two-Phase Optimizer Fixes
- Validation suite run

### 📋 Pending
- Post 4 P0 questions to Discussion #23
- Update BOOT_STATE.md + REMINDERS.md
- Final sync

## P0 Questions for Human (Discussion #23)

1. **Impossible outer diameters** in `benchmark_all.py` — correct wall thickness?
2. **Missing tone holes** in `build_bass_chalumeau_Bb()` — add 7-8 holes or remove benchmark target?
3. **Two-phase optimizer scope** — P0 bugs only, or include P1 import fixes?
4. **Bass chalumeau merge conflict** — desktop has tone-hole fix, laptop doesn't; verify before merge

## Architecture Audit Findings

### OpenWind/FEM Status: WORKING
- `openwind` package imports correctly (verified)
- `OpenWindSolver` + 3 passing tests (`test_openwind_solver.py`)
- `TrumpetOpenWind` fully implemented with valve modeling
- **Gap**: No `WoodwindOpenWind` — selector routes brass → OpenWind but woodwinds use TMM only

### Surrogate Directory: EXISTS
- `backend/surrogate/mlp_surrogate.py`
- `backend/surrogate/bi_objective_bo.py`
- Audit before building new (prevents duplicate `BoreSection` vs `Joint` pattern)

### Speed-of-Sound Discrepancy (Finding B1)
- Core TMM: 346100 mm/s (≈24.4°C) — canonical per Law 7
- Some modules: 343000 mm/s (20°C) — ~15.6¢ difference
- Unification deferred; tests assert consistency with temp formula

## Files to Modify (Phase 0)

### SoS Cleanup (Layer Order)
1. `backend/physics/losses.py:96` → import canonical
2. `backend/bore_optimizer_lbfgs.py:188` → use temp formula
3. `backend/optimizer.py:358` → use temp formula
4. `backend/flute_calculator.py:44` → use temp formula
5. `backend/modular_components.py:334` → import canonical
6. `backend/core/network.py:146` → import canonical
7. `backend/tone_hole_corrections.py:190,262,263,270` → import canonical
8. Tests: `test_bore_design.py`, `test_architecture.py`, `test_bore_check.py`, `test_sympy_validation.py`, `validate_flutomat.py`, `compare_optimizers.py`

### Two-Phase Fixes
- New: `backend/physics/register_detection.py` (extract from `two_phase_optimizer.py:73-97`)
- Modify: `backend/optimization/selector.py` (`TwoPhaseOptimizer.optimize()`)
- Modify: `backend/two_phase_optimizer.py` (import shared register detection)
- Add: `bore_length_bounds` enforcement for bass instruments
- Remove: hardcoded `outer_diameter=22.0`, `closed_top=False`

## Validation Commands
```bash
pytest tests/ -x -q
python scripts/toolcheck.py
python scripts/compliance_watchdog.py
```

## Next Session Start Checklist
1. `python scripts/team_chat.py sync`
2. Read `docs/session-logs/BOOT_STATE.md`
3. Read `docs/REMINDERS.md`
4. Check Discussion #23 for P0 answers
5. Continue Phase 0 or start Phase 1 based on P0 resolution

---

*End of session log — 2026-08-07*