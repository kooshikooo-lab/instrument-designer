# Known Issues

> Updated 2026-07-25 after laptop → main merge.

## Active Bugs

### Two-Phase Optimizer Infinite Loop
**File:** `backend/two_phase_optimizer.py:288`
**Issue:** List mutation during iteration causes infinite loop in DE phase.
**Status:** Needs fix before profiling.
**Workaround:** None — optimizer hangs.

### Median Correction in Cost Functions
**Files:** `phase_cost_with_offset` in tmm_acoustics.py, `bore_optimizer.py`
**Issue:** Uses median-corrected RMS (measures evenness) instead of absolute RMS (measures accuracy).
**Status:** All pipelines affected. Needs systematic fix.
**Fix:** Remove `np.median()` offset, use absolute RMS everywhere.

### Speed of Sound Inconsistency
**Files:** `tmm_acoustics.py` (346100), `tmm_optimizer_v2.py` (343400), `bore_optimizer.py` (343500), `losses.py` (343200)
**Issue:** Different modules use different speed of sound values.
**Status:** Needs standardization to 346100 cm/s (chalumier convention).

### No Timbre Proxy in TMM Pipeline
**Impact:** Optimizer only optimizes intonation, not timbre.
**Plan:** Add inharmonicity + phase-slope sharpness (no external reference needed).
**Reference:** Ernoult et al. (2020) proved Pareto frontier exists between intonation and timbre.

## Design Decisions

### n_register Auto-Detection
**Decision:** `n_register = 1 if closed_top else 2` auto-detected.
**Reason:** Open-open instruments require n_register=2 for the fundamental.

### Coordinate Convention Locked
**Decision:** Position 0 = bell, Position L = reed.
**Reason:** Matches chalumier convention. All code uses this.

### Main Branch Quality Gate
**Decision:** `main` only contains verified working code.
**Reason:** Prevent bugs from propagating. All imports and smoke tests must pass before merge.

## Tech Debt

### 8 Optimizer Files (should be 2-3)
**Files:** `tmm_optimizer.py`, `tmm_optimizer_v2.py`, `tmm_optimizer_sequential.py`, `tmm_optimizer_multi.py`, `two_phase_optimizer.py`, `v2_scipy_optimizer.py`, `staged_optimizer.py`, `optimizer_global.py`
**Plan:** Consolidate to: two_phase_optimizer (primary), staged_optimizer (Noreland), optimizer_global (desktop variant).

### Flat Files Alongside Architecture
**Issue:** 30 production files in root `backend/` alongside `core/`, `physics/`, `solvers/`, `instruments/`, `optimization/` directories.
**Plan:** Move remaining files into architecture directories.

### No Cross-Fingering Optimization
**Impact:** Only direct (cumulative) fingerings optimized.
**Plan:** Future work — requires proper fingering chart input.

### No FEM Validation Loop
**Impact:** TMM results not validated against FEM.
**Plan:** Integrate OpenWInD for validation after optimization.

## Resolved Issues

- ✅ closedTop convention verified (open cone = open-open pipe)
- ✅ Phase 2b DE breakthrough (fixed catastrophic gaps)
- ✅ Hole diameter co-optimization (0.2-3c improvement)
- ✅ Per-note register support
- ✅ KeefeLoss integration
- ✅ True wavelength near functions ported from chalumier
- ✅ Architecture directories created (core/, physics/, solvers/, instruments/, optimization/)
- ✅ Scratch/benchmark files organized
- ✅ 17 dead remote branches deleted
- ✅ Tailscale connectivity verified (4ms latency)
