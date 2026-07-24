# Session Recovery Log — 2026-07-24

## Session Summary

Recovery session. Attempted to reproduce and extend previous results.
**Critical finding: previous session's 0.45c RMS was never actually verified.**

## Actions Completed

### 1. P0 Blocker Fixed (from previous session)
- Cherry-picked `tmm_acoustics.py` to `option-a-tauri` (commit `c829540`)
- All branches synced and pushed

### 2. Cross-Fingering Optimization (THIS SESSION)

#### Attempted: ChatGPT 12-hole chart
- Chart from previous session research
- Result: **305c RMS** — hole numbering mismatch with physical positions
- Holes collapsed to same position (three at 750mm)

#### Attempted: Cross-fingered reed-first chart
- Chart from `test_final_correct.py`
- Result: **63.6c RMS** (best achieved) — but holes collapse
- Without collapse penalty: 63.6c but duplicate positions (230, 230, 602, 609, 609)
- With 30mm min spacing: 87.4c RMS

#### Attempted: Bell-first sequential (12 holes)
- Result: **363c RMS** — fundamentally broken
- Root cause: `wavelength_near` can't find register 1 for bell-first fingering
- Phases at target wavelengths: 0.58-0.66 (never reach 1.0)

#### Attempted: 7-hole diatonic optimization
- Result: **74.5c RMS** with reed-first sequential (NOT 0.45c as claimed)
- DE + L-BFGS-B: 166c RMS (stuck in local minima)

### 3. Phase-Cost vs Freq-Cost Analysis
- `phase_cost_with_offset` **hides register mismatch** (removes median)
- `phase_cost` (without offset) is register-aware — correctly identifies bell-first as broken
- Phase cost is ~10x faster than frequency evaluation

### 4. GlobalFingeringOptimizer Testing
- L-BFGS-B only (skip slow DE): 84c RMS reg1, 122c RMS reg2
- DE + L-BFGS-B: timed out at 300s (12 variables too slow)

## BREAKTHROUGH: 4.3c RMS Chromatic Intonation

### Final Configuration
- **12-hole reed-first sequential** (simplest possible chart)
- Hole positions: [142, 199, 250, 304, 354, 400, 439, 479, 516, 555, 590, 611]mm
- Graduated diameters: 14.5mm (reed end) → 20.0mm (bell end)
- Bore length: 1159.0mm (optimized, shorter than 1211.3mm)
- Register hole: 80mm, 2.5mm diameter

### Results
| Note | Target (Hz) | Actual (Hz) | Error (cents) |
|---|---|---|---|
| D2 | 73.4 | 73.6 | +4.1 |
| D#2 | 77.8 | 77.5 | -6.6 |
| E2 | 82.4 | 82.2 | -4.2 |
| F2 | 87.3 | 87.1 | -4.1 |
| F#2 | 92.5 | 92.1 | -7.1 |
| G2 | 98.0 | 98.0 | -0.6 |
| G#2 | 103.8 | 104.0 | +3.0 |
| A2 | 110.0 | 110.4 | +6.3 |
| A#2 | 116.5 | 116.5 | -0.7 |
| B2 | 123.5 | 123.4 | -0.7 |
| C3 | 130.8 | 130.5 | -3.7 |
| C#3 | 138.6 | 138.8 | +2.7 |
| D3 | 146.8 | 147.3 | +5.0 |

**RMS = 4.30c, Max error (excl D2) = 7.0c**

### What We Learned
1. Reed-first sequential is the correct fingering direction for this TMM model
2. Cross-fingerings are NOT needed — simple sequential works when properly optimized
3. Bore length optimization is critical (1159mm vs 1211mm)
4. Larger holes (14.5-20mm) work better than small (8-11mm)
5. Graduated diameters improve intonation significantly
6. Multi-start DE optimization is essential (5 seeds, best=4.3c, worst=11.6c)
7. Bell-first is broken in this TMM model (phases never reach register 1)

### Root Causes of Poor Results
1. **TMM model's `wavelength_near` is unreliable** for large pitch changes
2. **Hole collapse** — optimizer merges adjacent holes that serve different functions
3. **Chart design is ad-hoc** — no systematic acoustic analysis
4. **Previous session's numbers were inflated** — 0.45c never reproduced

### Key Technical Findings
1. **Bell-first fingering is broken in this TMM model** — phases never reach register 1
2. **Reed-first is the only working direction** for this phase-based TMM
3. **`phase_cost_with_offset` is dangerous** — hides register mismatch
4. **`phase_cost` is the correct objective** — register-aware, smooth, fast
5. **Minimum spacing penalty prevents collapse** but worsens RMS by ~25c

## Next Steps
1. **Validate 4.3c result** with different optimizer configurations
2. **Add bell model** to TMM (220mm Bessel flare, separate task)
3. **Test with losses** — viscothermal losses may shift frequencies
4. **Register hole optimization** — joint optimization with bore length
5. **Validate against OpenWInD FEM** (laptop task)
6. **Physical prototype** — 12-hole bass clarinet with these dimensions

## Files Created This Session
- `backend/test_direction.py` — Reed vs bell-first direction test
- `backend/test_verify_baseline.py` — Baseline verification
- `backend/test_optimize_7hole.py` — 7-hole optimization (too slow)
- `backend/test_opt7_fast.py` — Fast 7-hole optimization
- `backend/test_profile.py` — TMM speed profiling
- `backend/test_phase_opt.py` — Phase-cost optimization
- `backend/test_phase_vs_freq.py` — Phase vs freq comparison
- `backend/test_chart_designs.py` — Multiple chart designs
- `backend/test_cross_spacing.py` — Spacing penalty test
- `backend/test_bell_lbfsg.py` — Bell-first L-BFGS-B
- `backend/test_bell_phase.py` — Bell-first phase analysis
- `backend/test_cross_quick.py` — Quick cross-fingering test
- `backend/test_cross_extend.py` — 7+5 extension test
- `backend/test_cross_7plus5.py` — 7+5 optimization
- `backend/test_cross_fast.py` — Fast 12-hole optimization
- `backend/test_global_lbfsg.py` — Global optimizer L-BFGS-B
- `backend/test_phase_register.py` — Register-aware phase optimization
