# Instrument Designer

Computational wind instrument design platform. Instrument-agnostic optimizer with TMM acoustics, JAX differentiable solver, Pareto front multi-objective optimization, and distributed computing via Dask.

## What It Does

Given a fingering chart and target frequencies, the optimizer designs bore geometry and hole positions that minimize intonation error. Currently achieves **<3 cents RMS** on 12/12 instrument families after refinement.

### Supported Instruments
- **Closed-open (chalumeau family):** Chalumeau C, Bass Chalumeau Bb, Diatonic D Chalumeau
- **Open-open cylindrical:** Concert Flute, Alto Flute, PVC Flute, Tin Whistle, Xaphoon
- **Open-open conical:** Soprano Sax, Alto Sax, Recorder
- **Chromatic:** Chromatic Flute (25 notes, 17 holes)

## Benchmark Results

| Instrument | Sequential | Seq+Refined |
|---|---|---|
| Chalumeau C | 18.73c | **0.53c** |
| Bass Chalumeau Bb | 27.01c | **0.00c** |
| Diatonic D Chalumeau | 26.38c | **0.62c** |
| Soprano Sax Bb | 66.35c | **0.00c** |
| Alto Sax Eb | 196.94c | **0.00c** |
| Recorder C | 233.59c | **1.04c** |
| Xaphoon C | 294.54c | **0.00c** |
| Tin Whistle D | 170.74c | **0.00c** |
| Concert Flute C | 182.92c | **0.00c** |
| Alto Flute G | 187.41c | **0.00c** |
| PVC Flute D | 381.19c | **0.00c** |

## Architecture

```
woodwind-designer/
├── backend/                 # Core acoustic engine
│   ├── core/                # AcousticNetwork, coordinate systems
│   ├── physics/             # Loss models, excitation, radiation
│   ├── solvers/             # TMM solver, OpenWind wrapper
│   ├── optimization/        # Optimizer stages
│   ├── tmm_acoustics.py     # Core TMM engine
│   ├── tmm_acoustics_jax.py # JAX differentiable TMM (25x speedup)
│   ├── jax_optimizer.py     # JAX two-phase optimizer
│   ├── pareto_optimizer.py  # Intonation vs timbre Pareto front
│   ├── two_phase_optimizer.py # DE + L-BFGS-B pipeline
│   ├── benchmark_all.py     # 12-instrument benchmark
│   └── cadquery_export.py   # STL/STEP 3D export (1000+ lines)
├── woodwind_designer/       # GUI (Tauri/FastAPI)
├── web/                     # Frontend (TypeScript/Vite)
├── tests/                   # Test suite (96 files)
├── scripts/                 # Benchmarks, debug, utilities
├── docs/                    # Architecture, roadmap, research
├── research/                # Literature references
├── chalumier/               # Third-party Kotlin designer
├── openwind/                # Third-party FEM solver
└── pyproject.toml
```

## Key Components

### TMM Acoustics Engine (`backend/tmm_acoustics.py`)
Transfer Matrix Method solver for 1D wave propagation in cylindrical/conical bores with tone holes. Evaluates impedance spectra and resonance frequencies.

### JAX Differentiable TMM (`backend/tmm_acoustics_jax.py`)
JAX-rewritten TMM for automatic differentiation. 25x speedup via vmap, enables gradient-based optimization.

### Pareto Optimizer (`backend/pareto_optimizer.py`)
Bi-objective optimization: intonation (RMS cents) vs timbre (bore smoothness + hole radiation consistency). Weighted-sum sweep and NSGA-II via pymoo.

### CadQuery Export (`backend/cadquery_export.py`)
STL/STEP generation from bore profiles + tone holes. Handles cylindrical and conical bores, closed tops, 12+ instrument presets.

### Chalumier Integration (`chalumier/`)
Kotlin-based instrument designer. Designs instruments and outputs JSON5 bore profiles. Wrapper in `woodwind_designer/engine/chalumier_wrapper.py`.

## Distributed Computing

Dask cluster for parallel instrument optimization across machines:

```bash
# Start workers (set PYTHONPATH first)
set PYTHONPATH=/path/to/woodwind-designer
dask worker tcp://SCHEDULER_IP:8786 --nworkers 2 --nthreads 4

# Run distributed benchmark
python scripts/dask_benchmark.py --scheduler tcp://SCHEDULER_IP:8786
```

## Getting Started

```bash
# Install dependencies
pip install numpy scipy jax jaxlib pymoo cadquery dask distributed

# Run 12-instrument benchmark
python backend/benchmark_all.py

# Run Dask-parallelized benchmark
python scripts/dask_benchmark.py --scheduler tcp://localhost:8786
```

## Dependencies

Core: `numpy`, `scipy`, `jax`, `jaxlib`
Optimization: `pymoo` (NSGA-II)
3D Export: `cadquery`
Distributed: `dask`, `distributed`
Visualization: `matplotlib`

## Coordinate Systems

When bridging tools, coordinate systems must be documented:

| Tool | 0 = | Holes indexed from | Fingering |
|---|---|---|---|
| Chalumier | bell (open) | bell | X=closed, O=open |
| OpenWind | mouthpiece | mouthpiece | x=closed, o=open |
| TMM | mouthpiece | mouthpiece | true=closed |

See `docs/ARCHITECTURE.md` for full conversion rules.

## References

- Ernoult et al. (2020) JASA: Phase-based cost function for intonation
- Petiot et al. (2025) JASA: NSGA-II Pareto optimization for trumpets
- Noreland et al. (2013): Sequential greedy bore optimization
- Tournemenne (2019): Timbre preference modeling
- Keefe (1981): TMM validation
- Benade (1976): Open hole acoustics
- See `docs/archived-readme-2026-07-23.md` for full historical sources

## Contributing

1. Fork the repository
2. Create a feature branch
3. Run tests: `pytest tests/`
4. Submit a pull request

## License

See repository for license details.
