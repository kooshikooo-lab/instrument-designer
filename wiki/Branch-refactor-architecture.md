# Branch: refactor/architecture-redesign

> Solver-agnostic architecture. Synced with laptop — all core files identical.

## Purpose

Modular architecture with:
- Solver-agnostic acoustic network (`core/network.py`)
- Physics plugins (propagation, junction, tonehole, radiation, losses, excitation)
- Instrument builders (ClarinetBuilder, BrassBuilder)
- OpenWInD FEM solver plugin
- Coordinate transform module

## What It Has

| Feature | Status |
|---------|--------|
| `core/network.py` (AcousticNetwork) | ✅ |
| `core/coordinates.py` (CoordinateTransform) | ✅ |
| `solvers/tmm_solver.py` (TMMSolver) | ✅ |
| `solvers/openwind_solver.py` (OpenWindSolver) | ✅ |
| `physics/*.py` (plugins) | ✅ |
| `instruments/*.py` (builders) | ✅ |
| `optimization/*.py` (framework) | ✅ |
| `tests/test_properties.py` | ✅ (4/4 pass) |

## Status

**Fully synced with laptop.** All core architecture files are identical between this branch and laptop. This branch is dead — all work has been integrated.

## When to Use

- As a reference for architecture decisions
- When adding new solvers or physics plugins
- When modifying the acoustic network data model
