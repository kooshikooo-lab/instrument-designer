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
| [Research References](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research) | Hub — topic pages below |
| [Research — Acoustics](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research-Acoustics) | TMM, tone holes, radiation, instrument-specific |
| [Research — Optimization](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research-Optimization) | Algorithms, multi-objective, four key methods |
| [Research — Measurement](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research-Measurement) | Impedance/BIAS, intonation metrics, databases |
| [Research — Perception](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research-Perception) | Timbre & intonation perception |
| [Research — Resources](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research-Resources) | GitHub repos, books |
| [Research — Metamaterials](https://github.com/kooshikooo-lab/instrument-designer/wiki/Internal-Research-Metamaterials) | Acoustic metamaterials in instruments |
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

### Governance
| Page | Content |
|------|---------|
| [Governance-Boot-Sequence](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Boot-Sequence) | AI boot sequence (CONSTRAINTS_AND_PREFERENCES.md) |
| [Governance-Constitution](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Constitution) | 10 non-negotiable laws (AI_CONSTITUTION.md) |
| [Governance-ADRs](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-ADRs) | Architecture Decision Records (ARCHITECTURE_DECISIONS.md) |
| [Governance-Checklist](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Checklist) | Pre-flight/pre-commit checklist (ARCHITECTURE_CHECKLIST.md) |
| [Governance-Compliance](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Compliance) | Compliance triggers (COMPLIANCE_CHECK.md) |
| [Governance-Failure-Patterns](https://github.com/kooshikooo-lab/instrument-designer/wiki/Governance-Failure-Patterns) | Failure pattern log (AI_FAILURE_PATTERNS.md) |

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
