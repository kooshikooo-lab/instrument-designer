# Session Summary (2026-07-20) — Part 2

## What We Did

### 1. Parallelization Test (Windows)
- Fixed `test_parallel.py` — class must be at module level for pickle on Windows
- Added `if __name__ == '__main__':` guard for Windows `spawn` multiprocessing
- **Result**: `StarmapParallelization` works — 2.97x speedup with 4 workers on synthetic problem

### 2. Real Optimizer Parallel Test
- Ran real optimizer with `n_workers=4` vs `n_workers=1`
- **Serial (pop=10, gen=3)**: 30.5s
- **Parallel (pop=10, gen=3, 4 workers)**: 26.2s → 1.16x speedup
- **Serial (pop=20, gen=5)**: 93.2s
- **Parallel (pop=20, gen=5, 6 workers)**: 55.9s → **1.67x speedup**
- Speedup limited by Windows `spawn` overhead (pickle/unpickle per generation)

### 3. Linux Deployment Research
- Documented `fork` vs `spawn` vs `forkserver` differences
- Fork is ~20x faster at process startup (2ms vs 40ms)
- No pickle overhead with fork (copy-on-write memory)
- Python 3.14 changes Linux default to `forkserver` (safe + fast)
- **Estimated Linux speedup: 3-5x** (vs 1.67x on Windows)
- Saved research to `chat-logs/2026-07-20-linux-deployment-research.md`

### 4. Roadmap Update
- Added **Phase 4: Linux Deployment & Server Hosting** to ROADMAP.md
  - 4a: WSL2 local testing
  - 4b: Native Linux install (optional)
  - 4c: Server deployment (Docker + FastAPI)
  - 4d: Python 3.14 migration
- Renumbered old Phase 4 → Phase 5

### 5. WSL2 Setup Attempt
- Installed WSL2 + Virtual Machine Platform (Windows features)
- **BLOCKED**: BIOS virtualization (Intel VT-x / AMD-V) must be enabled
- Requires reboot into BIOS → enable → reboot back
- Saved attempt log to `chat-logs/2026-07-20-wsl2-setup-attempt.md`

## Current Blockers
1. **BIOS virtualization disabled** — need to enable Intel VT-x/AMD-V before WSL2 can start
2. No JDK installed — chalumier still blocked
3. Tauri missing capabilities in `default.json`

## Files Modified
- `test_parallel.py` — fixed for Windows spawn (module-level class + `__main__` guard)
- `ROADMAP.md` — added Phase 4 (Linux Deployment), renumbered old Phase 4→5
- New: `chat-logs/2026-07-20-acoustic-simulation-evaluation.md`
- New: `chat-logs/2026-07-20-linux-deployment-research.md`
- New: `chat-logs/2026-07-20-wsl2-setup-attempt.md`

## Next Steps (After BIOS Fix)
1. `wsl --install -d Ubuntu`
2. Set up Python env in WSL
3. Benchmark fork-based parallelization
4. Compare with Windows 1.67x baseline
