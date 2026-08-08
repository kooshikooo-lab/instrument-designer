# Benchmark Audit Report — 2026-07-25

## Executive Summary

The sub-0.1c RMS results are **technically correct for the TMM model** but misleading. Two root causes:
1. **Self-evaluation bias** — optimizing against the same simplified model we measure with
2. **Over-parameterization** — 19+ design variables for 6 frequency constraints

Real instruments with the same geometry would have **5-15c RMS error** due to manufacturing tolerances, tone hole interactions, and nonlinear effects the TMM model omits.

---

## CRITICAL BUGS FOUND

### BUG #1: Median Correction = Measures Evenness, Not Absolute Error
**Files:** `tmm_optimizer_sequential.py:395-403`, `two_phase_optimizer.py:62-76`

Multiple code paths subtract a **median offset** before computing RMS:
```python
med = np.median(ca)
return float(np.sqrt(np.mean((ca - med) ** 2)))  # EVENNESS, not absolute error
```

An instrument that is **uniformly flat by 50 cents** would report "0.00c RMS".

**Note:** `benchmark_all.py` does NOT do this — it uses absolute RMS. So `benchmark_all.py` results are correct, but `two_phase_optimizer.py` results are misleading.

### BUG #2: Two-Phase Optimizer Mutates Input List
**File:** `backend/two_phase_optimizer.py:283-292`

```python
for f in fingerings:
    fl = [...]
    fingerings.append(fl[:len(hole_lens)])  # BUG: appends to list being iterated!
```
Infinite loop / doubled fingerings. The `two_phase_optimize()` function is broken.

### BUG #3: Chromatic Flute Import Path
**File:** `backend/chromatic_flute.py:41-43`

Bare import `from tmm_acoustics import ...` fails when loaded via `benchmark_all.py` as `from backend.chromatic_flute import ...`. Chromatic flute benchmark silently fails.

---

## DESIGN ISSUES (Not Bugs, But Misleading)

### Issue #1: Results Measure Model Self-Consistency, Not Real Accuracy
The TMM model omits:
- Tone hole mutual interaction (TMMI, Lefebvre 2013)
- Frequency-dependent bore losses (uses constant approximation)
- Manufacturing tolerances
- Reed nonlinearity
- Embouchure effects

0.00c means "the model's predicted frequencies match ET targets perfectly" — not that a physical instrument would be this accurate.

### Issue #2: Degrees of Freedom vs Constraints
For a 6-hole chalumeau:
- 6 hole positions + 6 diameters + 6 bore radii + 1 bore length = **19 variables**
- **6 frequency constraints**
- Ratio: 3.25:1

With this many DOFs, sub-1c RMS is trivially achievable. It's not evidence of a breakthrough.

### Issue #3: Speed of Sound Inconsistency
Four different values across modules:
| Module | Value (mm/s) | Temperature |
|--------|-------------|-------------|
| tmm_acoustics.py | 346100 | ~25°C |
| tmm_optimizer_v2.py | 343400 | 20°C |
| bore_optimizer.py | 343500 | 20°C |
| losses.py | 343200 | ~20°C |

The benchmark pipeline uses 346100 (internally consistent), but other pipelines have ~0.7% systematic error.

### Issue #4: Cost Function ≠ Reported Metric
- Phase 1 optimizes `sin^2(π × deviation)` (phase cost)
- Phase 2 optimizes median-corrected RMSE (evenness)
- Final report uses absolute RMSE
- None of these are the same metric

### Issue #5: Register Detection Can Mask Errors
`detect_registers()` searches registers 1-5 and picks the "least wrong" one. Creates artificial error floor independent of actual intonation quality.

---

## What's Actually Correct

1. **`benchmark_all.py` pipeline** — Uses absolute RMSE throughout, no median correction. Results are honest for the TMM model.
2. **TMM engine physics** — Phase math, pipe_reply_phase, junction models match chalumier. Core physics is correct.
3. **Resonance finding** — `find_resonance()` correctly locates impedance peaks.
4. **Coordinate conventions** — All fixed, consistent across 9 files.

---

## Action Items

### Must Fix
1. Fix `two_phase_optimizer.py` infinite loop (list mutation)
2. Fix `chromatic_flute.py` import path
3. Remove median correction from `two_phase_optimizer.py` — use absolute RMSE
4. Standardize speed of sound to 346100 across all modules

### Should Do
5. Add a "validation against real instrument" test — compare TMM predictions against Wolfe impedance data
6. Report both absolute RMSE AND evenness (median-corrected RMSE) separately
7. Add DOF/constraint ratio to benchmark output
8. Fix `phase_cost_with_offset` to use cents-based metric or document the mapping

### Nice to Have
9. Add noise/uncertainty to target frequencies to simulate measurement error
10. Test optimizer with constrained DOFs (e.g., fix bore profile, only optimize holes)
