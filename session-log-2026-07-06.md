# Session Log — 2026-07-06

## Summary
Major refocus: abandoning Python scipy optimizer prototype, switching to Kotlin/Chalumier as the foundation for instrument design engine. Forked Chalumier, started build toolchain setup.

## Accomplished

### 1. Research & Discovery
- Found **Chalumier** — Kotlin port of demakein by MarkChuCarroll (github.com/MarkChuCarroll/chalumier)
  - 4x-400x faster than demakein (5 min vs 20 min simple flute, 10 min vs 3 days complex)
  - Complete toolchain: design optimizer + STL generation + SVG diagram + OpenSCAD export
  - Uses same evolutionary algorithm but without Python multiprocessing fragility
  - Written in Kotlin/JVM — no PyInstaller crashes, no legion workers

- Found **Openwind** (INRIA, France) — open-source Python library for wind instrument acoustic simulation
  - Web demo: demo-openwind.inria.fr
  - 1D finite element method for impedance calculation
  - Could add acoustic simulation layer later

- Found **WIAT** (McGill University) — Wind Instrument Acoustic Toolkit (2008, Python 2.5)
- Found **NESS** (University of Edinburgh) — Physical modelling synthesis (C++/CUDA)

### 2. Git Operations
- **instrument-designer** repo:
  - `main` branch at `a6e4136` — all 8 bug fixes pushed to GitHub
  - `scipy-prototype` branch at `34bf13c` — V2 numpy ES optimizer committed and pushed
    - Kept as backup/dead branch on GitHub in case we need the Python approach

- **chalumier** repo forked to `kooshikooo-lab/chalumier`

### 3. Scipy Optimizer V2 (scipy-prototype branch)
Implemented `ScipyDesignerV2` with pure-numpy evolution strategy:
- Replicates demakein's weighted-recombination ES without legion multiprocessing
- Key finding: demakein's optimizer needs 3000+ iterations to find valid geometry
- Our V1 (DE + basinhopping) gave up at 500 iterations
- V2 still needs debugging — the ES needs to match demakein's exact algorithm

### 4. Chalumier Setup
- Forked to `kooshikooo-lab/chalumier`
- Cloned locally to `C:\Users\Admin\Desktop\Woodwind design automation\chalumier`
- Downloaded JDK 17 (Temurin-17.0.19) to `C:\Users\Admin\Desktop\Woodwind design automation\tools\jdk17`
- Fixed gradle wrapper (downloaded missing gradle-wrapper.jar)
- **Build fails** — missing dependencies:
  - `ProgressMonitor` / `MakerState` — part of `chalumier/make` package, not yet implemented
  - `BoundedTranscript` — from mordant library API mismatch
  - These are compilation errors in unreferenced code paths

## Next Steps
1. Fix Chalumier build errors (missing classes in `make/`, `cli/`)
2. Build shadowJar to get executable JAR
3. Test design command with `flute.chal` spec
4. Design Python-Chalumier bridge (Python GUI calls JAR as subprocess)
5. Create how-to guides and documentation
6. Explore Discord bot for community support

## Project Vision (per user)
Democratized, low-cost access to musical instruments for everyone regardless of income. Non-technical users should be able to access digital instrument design through an easy-to-use GUI that combines tools, provides how-to guides, and abstracts away the complexity.

## Key Decisions
- Switch from Python/demakein to Kotlin/Chalumier as design engine
- Keep Python PySide6 GUI as frontend/launcher (calls Chalumier JAR)
- Keep `scipy-prototype` branch as backup reference (may be abandoned)
- Fork Chalumier rather than building from scratch

## Files Modified
- `woodwind_designer/engine/scipy_optimizer.py` — Rewritten with V2 numpy ES

## Repos
- Original: `github.com/kooshikooo-lab/instrument-designer`
  - `main` — production Python GUI + demakein wrapper
  - `scipy-prototype` — backup, possibly dead
- New: `github.com/kooshikooo-lab/chalumier`
  - Fork of MarkChuCarroll/chalumier
  - Kotlin-based design engine

## Build Issues
Chalumier build fails with:
1. Missing `ProgressMonitor`, `MakerState` in `cli/Make.kt`
2. Missing `BoundedTranscript` in `optimize/ProgressDisplay.kt`
These are incomplete modules in the upstream repo that need to be stubbed or completed.
