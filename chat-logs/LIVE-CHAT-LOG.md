# LIVE CHAT LOG — instrument-designer
## Last updated: 2026-07-20 (session ongoing)
## For: OpenCode on desktop machine — pull this file for latest status

---

## Current Status (LATEST)
The optimizer test with correct clarinet harmonic targets timed out at 5 minutes.
The PAVA repair + constraints are too slow with the current impedance computation.
Each evaluation is ~1.7s, and with 20 pop × 15 gen = 300 evals, minimum time is
~8.5 minutes just for impedance. The repair adds overhead too.

**Next action**: Need to either:
1. Reduce the problem (fewer CPs, smaller freq range)
2. Use concurrent.futures instead of pymoo StarmapParallelization (faster on Windows)
3. Wait for Linux/WSL2 for proper fork-based parallel

---

## CRITICAL DISCOVERY: Target Frequencies Were Wrong
The optimizer was using musical scale targets (261-523 Hz) for a clarinet bore.
A clarinet (closed-open pipe) only produces ODD HARMONICS: f, 3f, 5f, 7f...

For a 328mm cylindrical bore at 262Hz fundamental:
- Actual peaks: 270, 775, 1288, 1803, 2319, 2835 Hz
- Musical scale targets (261-523): only 2 peaks in range → physically impossible (423 cents)
- Odd harmonic targets: 6 peaks match → 32.79 cents RMS on simple bore

**Correct clarinet targets**: [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
**NOT**: [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]

This explains why the optimizer was stuck at 400 cents — it was trying to match
targets that don't exist in the bore's impedance spectrum.

---

## What Changed Since Last Push
1. Fixed PAVA repair operator (was buggy, now 5/5 tests pass)
2. Added monotonicity + smoothness constraints to BoreOptimizationProblem
3. Added global pitch offset correction (median-based)
4. Verified impedance solver finds 6 peaks for cylindrical bore
5. Discovered target frequency issue (musical scale vs odd harmonics)
6. Added MonotonicRepair class to optimizer.py

---

## To-Do for Desktop Computer
When you pull this repo, these are things you can work on:

### Immediate (can start now):
1. Review `backend/optimizer.py` — understand the new constraint system
2. Check `chat-logs/2026-07-20-FULL-REPORT.md` for full context
3. Test optimizer with correct clarinet targets on your machine
4. Fix Tauri capabilities in `web/src-tauri/capabilities/default.json`:
   - Add `"core:event:allow-listen"`
   - Add `"core:event:allow-emit"`
   - Add `"process:allow-spawn"`

### If you have time:
5. Research proper target frequency generation for different instrument types
6. Look at demakein's target generation approach
7. Test demakein STL generation (should work)

### NOT to work on (I'm handling):
- Optimizer accuracy tuning
- Parallelization improvements
- Linux/WSL2 deployment
- Dask distributed computing

---

## Git Status
Branch: `option-a-tauri`
Latest push: Monotonicity constraints, PAVA repair, parallelization, Linux research
Next push will include: Correct clarinet targets, accuracy improvements

---

## File Reference
| File | Status | Notes |
|------|--------|-------|
| `backend/optimizer.py` | MODIFIED | Has constraints + PAVA + global offset |
| `backend/validate_optimizer.py` | MODIFIED | Phased thresholds |
| `woodwind_designer/engine/design_server.py` | MODIFIED | n_workers field added |
| `ROADMAP.md` | MODIFIED | Phase 4 Linux added |
| `chat-logs/2026-07-20-FULL-REPORT.md` | NEW | Full session report |
| `web/src-tauri/capabilities/default.json` | NEEDS FIX | Missing Tauri capabilities |

---

*This file is updated frequently. Pull often.*
