# Desktop Session — 2026-07-21
## Branch: option-a-tauri
## Machine: Desktop (Windows)

---

## What Was Done

### 1. Constraint Reduction (optimizer.py)
**Problem**: Optimizer converged to 400 cents RMS with pop=20, gen=15 — 22 inequality constraints (11 monotonicity + 11 smoothness) were starving NSGA-II. Even though PAVA repair guaranteed monotonicity, the 11 monotonicity constraints still counted toward NSGA-II's constraint domination principle.

**Fix**: Reduced from 22 constraints to 1 aggregated smoothness constraint:
- Removed all 11 monotonicity constraints (PAVA repair already ensures this)
- Combined 11 smoothness constraints into 1: `sum(max(0, |Δr| - max_jump))`
- `n_ieq_constr: 22 → 1`

**Expected effect**: NSGA-II spends far fewer generations on constraint satisfaction → converges to accurate solutions faster.

### 2. Shared SQLite Cache (mp_cache.py — NEW FILE)
**Problem**: With `StarmapParallelization` on Windows (`spawn`), each worker process gets its own fresh Python environment with an empty `_IMPEDANCE_CACHE` dict. The same bore profile gets evaluated N times, each paying full OpenWInD cost (~1.7s).

**Fix**: Process-safe SQLite cache in `%TEMP%/impedance_cache.sqlite`:
- `backend/mp_cache.py` — standalone module with `cache_get()`, `cache_set()`, `cache_size()`, `cache_clear()`
- Integrated into `_compute_impedance_from_bore()` — checks cache before computing, stores after
- SQLite handles concurrent read/write from multiple worker processes
- JSON serialization with numpy array → list conversion
- No extra Manager process or IPC overhead

### 3. Default pop_size increased (40 → 60)
Better exploration with the reduced constraint count.

---

## How to Pull on Laptop

```powershell
$env:Path = "C:\Program Files\Git\bin;$env:Path"
cd C:\Users\...\woodwind-designer
git checkout option-a-tauri
git pull
```

After pulling:
1. Test optimizer: `python -c "import sys; sys.path.insert(0, '.'); from backend.optimizer import BoreOptimizer; opt = BoreOptimizer([261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3], n_control_points=6, pop_size=10, n_generations=5); r = opt.run(); print(r['best_candidates'][0]['objectives'])"`
2. Test parallel with shared cache: use `n_workers=4` and verify cache hits reduce redundant evaluations
3. Run validate_optimizer.py to benchmark

---

## Next Steps (Non-Conflicting Areas)
These are areas that DON'T overlap with existing work:

- **Test scripts**: `test_parallel.py` — add cache hit ratio reporting
- **design_server.py**: add `cache_size` and `cache_clear` endpoints
- **Frontend**: ImpedancePlot tooltip showing cached vs computed evaluations
- **Documentation**: Add cache architecture to ROADMAP.md

Avoid editing `backend/optimizer.py` on both machines simultaneously to prevent merge conflicts. If you need to modify it, push first or coordinate.
