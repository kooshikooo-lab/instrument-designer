# Architecture

> Solver-agnostic acoustic network, physics plugins, instrument builders. See [[Internal-Goals]] for project objectives.

## Design Philosophy

The architecture is **solver-agnostic** — the acoustic network, coordinate system, and physics models are independent of the solver (TMM, FEM, OpenWInD). This allows swapping solvers without changing the optimization pipeline.

## Core Components

```
backend/
├── core/
│   ├── network.py          # AcousticNetwork data model
│   └── coordinates.py      # CoordinateTransform
├── solvers/
│   ├── tmm_solver.py       # TMMSolver wrapper
│   ├── openwind_solver.py  # OpenWindSolver wrapper
│   └── external_solvers.py # chalumier + OpenWind wrappers
├── physics/
│   ├── losses.py           # KeefeLoss viscothermal model
│   ├── propagation.py      # Pipe propagation
│   ├── junction.py         # Bore junctions
│   ├── tonehole.py         # Tone hole modeling
│   ├── radiation.py        # End radiation
│   └── excitation.py       # Reed/mouthpiece
├── instruments/
│   ├── clarinet.py         # ClarinetBuilder
│   └── brass.py            # BrassBuilder
├── optimization/
│   ├── cost_functions.py   # Phase cost, peak cost
│   ├── metric.py           # RMS, MAD, SD metrics
│   └── pareto.py           # Multi-objective (planned)
├── tmm_acoustics.py        # Core TMM engine
├── tmm_optimizer_sequential.py  # Sequential + DE + L-BFGS-B
├── two_phase_optimizer.py  # DE → L-BFGS-B (Noreland approach)
├── staged_optimizer.py     # 3-stage progressive refinement
├── benchmark_all.py        # Full benchmark suite
├── cadquery_export.py      # 91 instruments, STL export
└── target_frequencies.py   # Instrument presets
```

## Data Flow

```
Instrument Config (JSON)
  → AcousticNetwork (core/network.py)
    → Solver (tmm_solver / openwind_solver)
      → Impedance Spectrum
        → Cost Function (phase_cost / peak_cost)
          → Optimizer (DE / L-BFGS-B / two-phase)
            → Optimized Bore + Holes
              → CadQuery STL Export
```

## Solver-Agnostic Network

`AcousticNetwork` is a graph of acoustic elements:
- **Nodes:** Bore segments, junctions, tone holes, boundaries
- **Edges:** Acoustic connections (series/parallel)
- **Properties:** Bore radius, hole diameter, material, temperature

Any solver can consume this network:
- **TMM:** Fast (microseconds), good for optimization
- **OpenWInD FEM:** Accurate (milliseconds), good for validation
- **chalumier:** Same TMM, different implementation (Kotlin)

## Physics Plugins

Each physics phenomenon is a separate module:
- `propagation.py` — Phase advance through pipe segments
- `junction.py` — Area step changes (bore diameter changes)
- `tonehole.py` — Tone hole modeling (open/closed, length corrections)
- `radiation.py` — End radiation impedance
- `losses.py` — Viscothermal losses (Keefe 1984)
- `excitation.py` — Reed/mouthpiece boundary conditions

Plugins can be swapped or upgraded independently.

## Coordinate System

**Position 0 = bell (open end), Position L = reed (closed end).**

This matches chalumier convention. See [[Internal-Coordinates]] for details.

## Instrument Builders

`ClarinetBuilder` and `BrassBuilder` construct `AcousticNetwork` from instrument parameters:
- Bore profile (radius array)
- Tone hole positions and diameters
- Register key position
- End conditions (bell, reed, fipple)
