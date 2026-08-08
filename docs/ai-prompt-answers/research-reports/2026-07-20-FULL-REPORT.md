# FULL SESSION REPORT — instrument-designer
## For: OpenCode on desktop machine
## Date: 2026-07-20
## Branch: option-a-tauri (GitHub: kooshikooo-lab/instrument-designer)

---

## Current State Summary

The project is a wind instrument designer web app with bore optimization. Backend:
Python/FastAPI. Frontend: Tauri (Rust + webview). Optimizer uses pymoo NSGA-II +
OpenWInD impedance solver. Currently on Windows, planning Linux migration.

---

## What Was Done This Session

### 1. Parallelization — WORKING on Windows (limited)

**Problem**: `StarmapParallelization` from pymoo was added but never tested.

**Fixes applied**:
- `test_parallel.py`: Class must be at module level for pickle on Windows `spawn`.
  Must wrap execution in `if __name__ == '__main__':` guard.
- `optimizer.py` line ~310: Pool creation + runner, pool cleanup in try/finally.
- `design_server.py`: Added `n_workers` field to `OptimizeRequest` (default None =
  auto-detect CPU count, capped at 8). Progress log shows worker count.

**Results**:
- Synthetic test (DummyProblem): 2.97x speedup with 4 workers ✓
- Real optimizer (pop=20, gen=5): 93.2s serial → 55.9s parallel (1.67x)
- Speedup limited by Windows `spawn` overhead (pickle/unpickle per generation)

**File**: `backend/optimizer.py` lines 305-335 (Pool + runner setup)

### 2. Monotonicity + Smoothness Constraints — IN PROGRESS

**Problem**: Docstring claimed monotonicity but `n_ieq_constr=0`. Bore could go
backwards. Must fix before increasing control points.

**What was added to `BoreOptimizationProblem`**:
- `n_ieq_constr = (n_cp - 1) * 2` = 22 for 12 CPs
  - First half: monotonicity — `G[i] = max(0, x[i] - x[i+1])`
  - Second half: smoothness — `G[i] = max(0, abs(x[i+1] - x[i]) - max_radius_jump)`
- `max_radius_jump` defaults to 30% of radius range (~6.6mm)
- Global pitch offset correction: median-based shift before RMS calculation
  - `raw_cents = [m[3] for m in matched]`
  - `global_offset = np.median(raw_cents)`
  - `corrected_errors = abs(raw_cents - global_offset)`
  - This removes systematic sharp/flat bias

**PAVA Repair Operator** (critical — without it, 0% feasible initial population):
- `MonotonicRepair` class extending `pymoo.core.repair.Repair`
- Uses Pool Adjacent Violators Algorithm — O(n), no scipy needed
- Applied after crossover + mutation every generation
- Verified: 5/5 random samples → monotonic True ✓
- Sort approach was WRONG (destroys bore shape — clarinet needs near-constant radius)
- scipy SLSQP approach was TOO SLOW (~5s per individual)
- PAVA is fast (~microseconds) and produces minimal modification

**Current bug**: Optimizer converges to single peak (400 cents RMS) with 20 pop × 15
gen = 300 evals. Need larger budget or different approach.

**File**: `backend/optimizer.py` lines 142-265 (BoreOptimizationProblem + PAVA)

### 3. Linux Deployment Research

**Key finding**: Linux `fork` is ~20x faster than Windows `spawn` for process startup.
- spawn: fresh Python interpreter + pickle everything (~40ms/process)
- fork: copy-on-write memory (~2ms/process)
- Python 3.14 default changes to `forkserver` (safe + fast)
- Expected speedup: 3-5x over Windows parallel (vs 1.67x measured)

**WSL2 setup**: Installed WSL2 + Virtual Machine Platform Windows features.
**BLOCKED**: BIOS virtualization (Intel VT-x / AMD-V) disabled. Requires reboot into
BIOS. Deferred due to damaged keyboard making BIOS navigation difficult.
**Alternative**: `concurrent.futures.ProcessPoolExecutor` may avoid fork/spawn issue.

**Files**:
- `ROADMAP.md` — Added Phase 4: Linux Deployment & Server Hosting
- `chat-logs/2026-07-20-linux-deployment-research.md`
- `chat-logs/2026-07-20-wsl2-setup-attempt.md`

### 4. Acoustic Simulation Evaluation

Compared our OpenWInD solver against chalumier, demakein, Noreland, OpenWind,
Ernoult (2020). Key benchmarks:
- Noreland (2013): 0.49 cents RMS on clarinet
- Ernoult (2020): <1 cent on physical prototype
- OpenWind (Inria): <5 cents on real instruments
- Our current: 5-15 cents with old optimizer

**File**: `chat-logs/2026-07-20-acoustic-simulation-evaluation.md`

---

## Files Modified This Session

| File | What Changed |
|------|-------------|
| `backend/optimizer.py` | Added MonotonicRepair class, _pava_isotonic function, smoothness constraint, monotonicity constraint, global pitch offset, Pool + runner setup, pool cleanup |
| `backend/validate_optimizer.py` | Fixed Path(__file__) relative paths, phased thresholds (C1-C4 20/10/5/3 cents, P1-P4), comparison notes |
| `ROADMAP.md` | Rewritten Phase 1 (computation), Phase 2 (3D print), Phase 3 (integration), Added Phase 4 (Linux Deployment), Renumbered Phase 4→5 |
| `test_parallel.py` | Fixed for Windows spawn: module-level class, __main__ guard |
| `test_constraint.py` | Test script for monotonicity constraint |
| `test_pava.py` | PAVA algorithm verification (all 5 tests pass) |
| `debug_constraints.py` | Debug script for constraint debugging |

## New Files Created

| File | Purpose |
|------|---------|
| `chat-logs/2026-07-20-noreland-research.md` | Noreland clarinet + Ernoult + Lefebvre research |
| `chat-logs/2026-07-20-acoustic-simulation-evaluation.md` | Solver comparison benchmarks |
| `chat-logs/2026-07-20-linux-deployment-research.md` | Fork vs spawn, deployment options |
| `chat-logs/2026-07-20-wsl2-setup-attempt.md` | WSL2 install attempt, BIOS blocker |
| `chat-logs/2026-07-20-session-summary.md` | Session part 2 summary |

---

## What's NOT Working / Blocked

1. **Optimizer accuracy**: With constraints, converges to 400 cents (single peak).
   Need more evals or different approach. The problem is that constraints + small
   population = not enough exploration.

2. **WSL2 / Linux parallelization**: Blocked on BIOS virtualization setting.

3. **No JDK installed**: chalumier blocked.

4. **Tauri build**: Missing capabilities in `default.json`:
   - `core:event:allow-listen`
   - `core:event:allow-emit`
   - `process:allow-spawn`

5. **Dask distributed for LAN**: Researched but not implemented. Two-computer
   workload sharing needs `pip install "dask[distributed]"` on both, then:
   ```
   # Machine 1: dask scheduler --port 8786
   # Machine 2: dask worker tcp://MACHINE1_IP:8786
   ```

---

## Next Steps (Priority Order)

1. **Fix optimizer accuracy** — The monotonicity constraint + PAVA repair are in
   place but the optimizer needs more budget (pop=40, gen=50) to converge.
   Currently 300 evals not enough. With parallel working, try pop=40, gen=50.

2. **Test with larger pop/gen** — Once parallel is confirmed working, run:
   pop=40, gen=50 = 2000 evals. Serial ~56 min, parallel ~33 min (1.67x).

3. **Validate against reference instruments** — Run optimizer on clarinet_Bb,
   penny_whistle_D, recorder_soprano and compare with demakein output.

4. **Fix BIOS virtualization** — Enable Intel VT-x in BIOS to unlock WSL2
   and Linux parallel (3-5x speedup expected).

5. **Distributed computing** — After Linux works, add Dask support for
   two-computer LAN workload sharing.

6. **Tauri capabilities** — Fix the three missing entries in default.json.

---

## Key Architecture Notes for New Session

- **Backend entry**: `woodwind_designer/engine/design_server.py` (FastAPI)
- **Optimizer**: `backend/optimizer.py` — BoreOptimizer wraps BoreOptimizationProblem
- **Impedance**: OpenWInD `ImpedanceComputation` — ~1.7s per unique evaluation
- **Cache**: `_IMPEDANCE_CACHE` dict, shared across calls, max 2000 entries
- **demakein**: `woodwind_designer/engine/demakein_wrapper.py` — requires two-step
  process: `designer.run()` then `Make_flute.run()` or `Make_reed_instrument.run()`
- **chalumier**: `woodwind_designer/engine/chalumier_wrapper.py` — blocked, no JDK
- **Port**: FastAPI on localhost:8000, CORS enabled
- **Windows multiprocessing**: MUST use `if __name__ == '__main__':` guard, classes
  at module level for pickle, `spawn` is the only start method available
