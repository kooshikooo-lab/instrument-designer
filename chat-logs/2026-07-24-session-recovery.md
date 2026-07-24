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

## What We Actually Know (Honest Assessment)

| Configuration | Reg1 RMS | Status |
|---|---|---|
| 7-hole diatonic, reed-first | ~75c | NOT 0.45c as claimed |
| 12-hole cross-fingered (no spacing) | 63.6c | Holes collapse |
| 12-hole cross-fingered (30mm min) | 87.4c | Best realistic result |
| 12-hole bell-first sequential | 363c | Broken in TMM model |
| 12-hole GlobalOpt (L-BFGS-B only) | 84c | Stable, no collapse |

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
1. **Fix the chart** — need systematic acoustic analysis, not ad-hoc patterns
2. **Add bell model** to TMM (220mm Bessel flare, separate task)
3. **Test with losses** — lossless model may be insufficient for cross-fingerings
4. **Validate against physical measurements** or OpenWInD FEM
5. **Consider alternative optimizer** — genetic algorithm or Bayesian optimization

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
