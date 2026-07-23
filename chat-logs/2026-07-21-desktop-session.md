# Desktop Session Restore — 2026-07-21
## Branch: option-a-tauri
## Machine: Desktop (Windows)
## Status: ACTIVE — continue from here

---

## What Happened (Summary)

### 9 Commits on Desktop (overnight sessions 4-6)
1. Optimization UI, cache stats, presets fix, README
2. experiment-staged-optimization + experiment-processpoolexecutor branches
3. Chalumier integration (JDK 17 built, 27MB JAR, D whistle test)
4. AI Design Advisor (442 lines: rule-based + Ollama LLM + SQLite memory)
5. Automated Design Agent (design_desk.py, 6 presets, multi-iteration loop)
6. SVG export, BoreProfileView component, frontend polish
7. Integration tests (32/32 pass), TypeScript clean build
8. Tauri build success (binary at .cargo-target\release\instrument-designer.exe)

### 5 Commits on Laptop (BLAS fix + code review)
1. BLAS thread oversubscription fix (OMP/MKL/OPENBLAS_NUM_THREADS=1)
2. Worker config factorization (initargs instead of pickle)
3. Batch parallelization (1.80x speedup measured)
4. PAVA O(n²) → O(n) stack-based merge
5. Code review fixes (np.inf, chunksize, missing import, dead code removal)
6. Research: surrogate models, MADS, 3D printing constraints

---

## Current Best Result
- **3.11 cents RMS** (pop=15, gen=10, serial, ~250s)
- Targets: [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6] (clarinet odd harmonics)
- Borderline C4 (<3 cents) — need pop=40/gen=50 batch test to break through

---

## Known Issues Fixed (Pull Required)
If you see ProcessPoolExecutor hangs or BLAS deadlocks:
```powershell
git pull --rebase origin option-a-tauri
```
This includes: BLAS thread fix, PAVA O(n), np.inf penalties, chunksize, INSTRUMENT_CONFIGS import fix.

---

## Quick Start
```powershell
# Pull latest
git pull --rebase origin option-a-tauri

# Smoke test
python test_batch_fix.py

# Full test
python -c "
import sys; sys.path.insert(0,'.')
from backend.mp_cache import cache_clear
cache_clear()
from backend.optimizer import BoreOptimizer
targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
opt = BoreOptimizer(targets, n_control_points=12, pop_size=40, n_generations=50, n_workers=6, parallel_mode='batch')
r = opt.run(verbose=True)
best = r['best_candidates'][0]
print('RMS:', best['objectives']['frequency_accuracy'], 'cents')
"
```

---

## What to Work On Next
1. Run pop=40/gen=50 batch test (should complete ~7-10 min)
2. Fix validate_optimizer.py (uses old musical-scale targets, needs odd harmonics)
3. Frontend polish (impedance plot tooltips, wiki content)
4. Ollama install for LLM-powered advisor
5. 3D print test instrument

---

## Architecture Notes
- OpenWInD bottleneck: ~1.7s per impedance evaluation
- BLAS thread fix: OMP/MKL/OPENBLAS_NUM_THREADS=1 prevents deadlock
- SQLite shared cache: %TEMP%/impedance_cache.sqlite (process-safe)
- PAVA: stack-based O(n) monotonicity repair
- Batch parallelization: ProcessPoolExecutor, 1.80x speedup measured
- pymoo: NSGA-II with 3 objectives (frequency accuracy, evenness, projection) + 1 constraint (smoothness)

---

## File Quick Reference
| File | Description |
|------|-------------|
| `backend/bore_optimizer.py` | Main optimizer (PAVA, batch parallel, BLAS fix) |
| `backend/ai_advisor.py` | AI advisor (rule-based + Ollama + SQLite) |
| `backend/design_desk.py` | Automated design agent (6 presets) |
| `backend/target_frequencies.py` | Per-instrument harmonic targets |
| `backend/mp_cache.py` | SQLite shared cache |
| `backend/svg_export.py` | SVG bore profile export |
| `woodwind_designer/engine/design_server.py` | FastAPI server |
| `chat-logs/LIVE-CHAT-LOG.md` | Coordination file (pull before working) |
