# LIVE CHAT LOG — instrument-designer
## Last updated: 2026-07-21
## For: Both machines — pull this file before starting work
## Coordination: Push here before starting new work so we don't conflict

---

## Current Status (LATEST — desktop response)
The critical discovery is that **target frequencies were wrong** — musical scale on a clarinet (closed-open pipe = odd harmonics only). The 400 cents RMS was never about constraints or population size; it was about asking the optimizer to hit notes that can't physically exist.

Desktop applied two fixes:
1. **22→1 constraint reduction** — makes NSGA-II spend less time on constraint satisfaction
2. **Shared SQLite cache** — eliminates redundant OpenWInD calls across parallel workers

Try again with correct clarinet targets: `[261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]`  
If the optimizer still times out, the shared cache should help by not re-computing identical bore profiles.

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

## Desktop Changes (2026-07-21)

### What Was Done:
1. **Constraint reduction** (optimizer.py): 22 constraints → 1 aggregated smoothness constraint. PAVA already handles monotonicity, so the 11 monotonicity constraints were dead weight.
2. **Shared SQLite cache** (mp_cache.py — NEW): Process-safe impedance cache via SQLite. Workers share cache through `%TEMP%/impedance_cache.sqlite`. Eliminates redundant OpenWInD evaluations across spawn workers.
3. **Default pop_size**: 40 → 60

### Pull these changes on laptop:
```powershell
$env:Path = "C:\Program Files\Git\bin;$env:Path"
git checkout option-a-tauri
git pull
```

## To-Do for Laptop (Desktop is NOT handling these):
### Laptop continues:
- Optimizer accuracy tuning (correct target frequencies is the key fix!)
- Parallelization improvements
- Linux/WSL2 deployment
- Dask distributed computing

---

## Git Status
Branch: `option-a-tauri`
Latest push (desktop): Constraint reduction 22→1 + SQLite shared cache + session log
Next push: Depends on laptop — pull first, then push your changes

---

## File Reference
| File | Status | Notes |
|------|--------|-------|
| `backend/optimizer.py` | MODIFIED | 22→1 constraints (desktop) + PAVA + global offset (laptop) |
| `backend/mp_cache.py` | NEW | Shared SQLite cache for parallel workers (desktop) |
| `backend/validate_optimizer.py` | MODIFIED | Phased thresholds (laptop) |
| `woodwind_designer/engine/design_server.py` | MODIFIED | n_workers field added (laptop) |
| `ROADMAP.md` | MODIFIED | Phase 4 Linux added (laptop) |
| `chat-logs/2026-07-20-FULL-REPORT.md` | NEW | Full session report (laptop) |
| `chat-logs/2026-07-21-desktop-session.md` | NEW | Desktop session log + pull instructions |
| `chat-logs/LIVE-CHAT-LOG.md` | UPDATED | This file — both machines update |
| `web/src-tauri/capabilities/default.json` | NEEDS FIX | Missing Tauri capabilities |

---

## Coordination Check (Desktop → Laptop)
Desktop has two pending items not yet pushed:
- `backend/target_frequencies.py` — new utility for correct per-instrument harmonic targets
- Minor corrections to the above

**Before I push these, laptop:** are you currently working on target frequency generation? If yes, I'll hold off to avoid merge conflicts.

**Desktop can work on (no conflict):**
- Tauri capabilities fix in `default.json`
- README/docs updates
- Test scripts for the shared cache
- Frontend polish

**Desktop will NOT touch:**
- `backend/optimizer.py` (laptop's area)
- Parallelization internals
- Linux/WSL2 work

Reply by pushing an update to this file.

## How to Sync
1. Always pull before starting work: `git pull origin option-a-tauri`
2. After making changes: `git add -A && git commit -m "description" && git push origin option-a-tauri`
3. If push is rejected (remote has newer commits): `git pull --rebase origin option-a-tauri` then push again
4. Update this file with what you did so the other machine knows

*This file is updated frequently. Pull often.*
