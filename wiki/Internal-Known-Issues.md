# Known Issues

## Active Bugs

### Two-Phase Optimizer Infinite Loop
**File:** `backend/two_phase_optimizer.py:288`
**Issue:** List mutation during iteration causes infinite loop in DE phase.
**Status:** Needs fix before profiling.
**Workaround:** None — optimizer hangs.

### Median Correction in Desktop Optimizers
**File:** `backend/optimizer_global.py`, `backend/tmm_acoustics.py:phase_cost_with_offset`
**Issue:** Uses median-corrected RMS (measures evenness) instead of absolute RMS (measures accuracy).
**Status:** Desktop needs to update after laptop merges to main.
**Fix:** Remove `np.median()` offset, use absolute RMS.

### Speed of Sound Inconsistency
**Files:** `tmm_acoustics.py` (346100), `tmm_optimizer_v2.py` (343400), `bore_optimizer.py` (343500), `losses.py` (343200)
**Issue:** Different modules use different speed of sound values.
**Status:** Needs standardization to 346100 cm/s (chalumier convention).

## Design Decisions

### No Median Correction in Benchmark
**Decision:** `benchmark_all.py` uses absolute RMS, not median-corrected RMS.
**Reason:** Median correction hides systematic errors that affect ensemble playing. See [[Internal-Optimization#Metric-Standardization]].
**Impact:** Desktop numbers are not comparable to laptop numbers.

### n_register Auto-Detection
**Decision:** `n_register = 1 if closed_top else 2` auto-detected.
**Reason:** Open-open instruments require n_register=2 for the fundamental.
**Impact:** Previously, open-open instruments were evaluated with wrong register.

### Coordinate Convention Locked
**Decision:** Position 0 = bell, Position L = reed.
**Reason:** Matches chalumier convention. All code uses this.
**Impact:** Breaking change if anyone uses the old convention.

## Tech Debt

### No Timbre Proxy in Optimizer
**Impact:** Optimizer only optimizes intonation, not timbre.
**Plan:** Add a₂/a₁ ratio as second objective (bi-objective optimization).

### No Cross-Fingering Optimization
**Impact:** Only direct (cumulative) fingerings optimized. Cross-fingerings documented but not optimized.
**Plan:** Future work — requires proper fingering chart input.

### No FEM Validation Loop
**Impact:** TMM results not validated against FEM.
**Plan:** Integrate OpenWInD for validation after optimization.

### No Physical Measurement Loop
**Impact:** No feedback from printed instruments to optimizer.
**Plan:** Phase 2 of roadmap — measure, compare, iterate.

## Resolved Issues

- ✅ closedTop convention verified (open cone = open-open pipe)
- ✅ Phase 2b DE breakthrough (fixed catastrophic gaps)
- ✅ Hole diameter co-optimization (0.2-3c improvement)
- ✅ Per-note register support
- ✅ KeefeLoss integration
- ✅ True wavelength near functions ported from chalumier
