# Internal Documentation

> Developer documentation for the Instrument Designer project. Architecture, algorithms, code conventions, and research references.

## Navigation

### Core
- [[Internal-Goals]] — Project goals, roadmap, the timbre+intonation optimization objective
- [[Internal-Architecture]] — Solver-agnostic network, physics plugins, instrument builders
- [[Internal-Acoustic-Engine]] — TMM, KeefeLoss, losses, radiation models
- [[Internal-Optimization]] — Cost functions, metrics, Pareto front, two-phase optimizer
- [[Internal-Coordinates]] — Coordinate systems, fingering conventions

### Reference
- [[Internal-Instruments]] — 91 instruments, naming conventions, benchmark results
- [[Internal-Branches]] — Branch comparison, algorithms, merge status
- [[Internal-Research]] — Research hub (topic pages: Acoustics, Optimization, Measurement, Perception, Resources, Metamaterials, AI)
- [[Internal-Conventions]] — Code style, testing, commit messages
- [[Internal-Known-Issues]] — Bugs, design decisions, tech debt

### Quick Reference

| What | Where |
|------|-------|
| TMM engine | `backend/tmm_acoustics.py` |
| Losses | `backend/physics/losses.py` |
| Sequential optimizer | `backend/tmm_optimizer_sequential.py` |
| Two-phase optimizer | `backend/two_phase_optimizer.py` |
| Staged optimizer | `backend/staged_optimizer.py` |
| Benchmark | `backend/benchmark_all.py` |
| Instrument library | `backend/cadquery_export.py` |
| Server | `woodwind_designer/engine/design_server.py` |
| Frontend | `web/src/` |
| Tauri | `web/src-tauri/` |
