# Wiki Index

> Two wikis: **User** (for people using the tool) and **Internal** (for developers/researchers).

## User Wiki

| Page | Content |
|------|---------|
| [Home](https://github.com/kooshikooo-lab/instrument-designer/wiki/Home) | Overview, quick start |
| [Getting Started](https://github.com/kooshikooo-lab/instrument-designer/wiki/Getting-Started) | Installation, first design |
| [Instrument Library](https://github.com/kooshikooo-lab/instrument-designer/wiki/Instrument-Library) | 91 instruments, 10 families |
| [3D Printing Guide](https://github.com/kooshikooo-lab/instrument-designer/wiki/3D-Printing-Guide) | Print settings, materials |
| [FAQ](https://github.com/kooshikooo-lab/instrument-designer/wiki/FAQ) | Common questions |

## Internal Wiki

### Core
| Page | Content |
|------|---------|
| [Home](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Home) | Index of all internal docs |
| [Project Goals](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Goals) | Core objectives, timbre+intonation goal |
| [Architecture](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Architecture) | Solver-agnostic network, plugins |
| [Acoustic Engine](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Acoustic-Engine) | TMM, KeefeLoss, losses |
| [Optimization](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Optimization) | Cost functions, metrics, Pareto front |
| [Coordinate Systems](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Coordinates) | Position 0 = bell, position L = reed |

### Reference
| Page | Content |
|------|---------|
| [Instrument Library](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Instruments) | 91 instruments, benchmark results |
| [Branch Comparison](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Branches) | All branches, merge/keep/discard |
| [Research References](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research) | Papers, books, repos (indexed by topic) |
| [Code Conventions](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Conventions) | Style, testing, commit messages |
| [Known Issues](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Known-Issues) | Bugs, design decisions, tech debt |

### Branch Pages
| Page | Content |
|------|---------|
| [laptop](https://github.com/kooshikooo-lab/instrument-designer/wiki/Branch-laptop) | Active development branch |
| [main](https://github.com/kooshikooo-lab/instrument-designer/wiki/Branch-main) | Stable shared branch |
| [option-a-tauri](https://github.com/kooshikooo-lab/instrument-designer/wiki/Branch-option-a-tauri) | Tauri UI (desktop decides) |
| [experiment/trumpet](https://github.com/kooshikooo-lab/instrument-designer/wiki/Branch-experiment-trumpet) | Trumpet model |
| [refactor/architecture](https://github.com/kooshikooo-lab/instrument-designer/wiki/Branch-refactor-architecture) | Architecture redesign |

## Quick Reference

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
| Roadmap | `ROADMAP.md` |
| Technical reference | `WIKI.md` |
