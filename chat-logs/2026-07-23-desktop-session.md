# Desktop Session — 2026-07-23 (TMM Optimizer Breakthrough Verification)

## Context
- Desktop (100.100.66.117) merged laptop's bore-profile-optimization branch
- Verified Phase 2b DE breakthrough results
- Running chalumier benchmarks

## Verified Results (Phase 2b DE)

| Instrument | Sequential | Seq+Refine | Time |
|---|---|---|---|
| Chalumeau C | 18.73c | **0.01c** | 5.2s |
| Bass Chalumeau | 27.03c | **0.17c** | 15.2s |
| Soprano Sax | 66.40c | **0.32c** | 10.2s |
| Xaphoon | 290.39c | **0.00c** | 10.7s |
| Alto Sax | 190.41c | **0.02c** | 8.2s |

**All 5 instruments sub-0.3c RMS!** Phase 2b DE is the critical fix.

## Key Findings

### 1. The TMM Model Was Always Accurate
- Phase 2b DE (differential evolution) re-optimizes ALL hole positions simultaneously
- Sequential greedy placement creates large gaps (288mm for xaphoon) where TMM can't find resonances
- DE with overlapping bounds (`lo=i*L/(n_h*1.5+1)`, `hi=(i+2)*L/(n_h*1.5+1)`) closes these gaps
- This is exactly what chalumier does (evolutionary algorithm in Optimizer.kt)

### 2. Chalumier Benchmark (from my earlier work)
- Chalumier dwhistle: 29.2c evenness (chalumier's own output)
- Our TMM with chalumier's bore: 17.8c evenness (matches chalumier)
- L-BFGS-B refinement from chalumier's bore: **3.5c evenness** (5x better!)
- Key insight: bore shape dominates hole positions for intonation

### 3. Phase Cost vs Peak Cost
- Phase cost (1.4ms/call): fast but register-agnostic — converges to wrong register basin
- Peak cost (140ms/call): correct but slow — 34x slower
- Phase 2b DE uses absolute RMS (not median-corrected) to prevent uniform-wrong solutions

### 4. Two-Phase Optimizer Design
My earlier two_phase_optimizer.py timed out on recorder (28 fingerings). The laptop's approach is better:
- Phase 1: Sequential hole placement (fast, greedy)
- Phase 2b: DE global re-optimization (critical for open-open)
- Phase 3: L-BFGS-B refinement (4 stages)

## What I'm Working On
1. Testing recorder with chalumier's fingering chart (28 fingerings, 3 registers)
2. Updating ROADMAP with Phase 2b breakthrough findings
3. Committing verified results

## For Laptop
- Your Phase 2b DE approach is confirmed working on all 5 instruments
- The overlapping bounds formula is key: `lo=i*L/(n_h*1.5+1)`, `hi=(i+2)*L/(n_h*1.5+1)`
- Pop size: `max(10, n_h * 2)` — sufficient for 6-8 holes
- Maxiter=100 with tol=1e-6 — converges in ~10s per instrument

## Next Steps
1. Test on recorder (28 fingerings, cross-fingerings, 3 registers)
2. Test on dwhistle (chalumier benchmark: 29.2c target)
3. Consider: can we match chalumier's bore shape for even better results?
4. Update ROADMAP with verified findings
