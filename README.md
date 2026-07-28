# Instrument Designer

Computational wind instrument design platform. Instrument-agnostic optimizer with TMM acoustics, JAX differentiable solver, Pareto front multi-objective optimization, and distributed computing via Dask.

## What It Does

Given a fingering chart and target frequencies, the optimizer designs bore geometry and hole positions that minimize intonation error. Currently achieves **<1 cent RMS** on 11 instrument families after Pareto optimization (w_int=0.9).

### Supported Instruments
- **Closed-open (chalumeau family):** Chalumeau C, Diatonic D Chalumeau
- **Open-open cylindrical:** Concert Flute, Alto Flute, PVC Flute, Tin Whistle, Xaphoon
- **Open-open conical:** Soprano Sax, Alto Sax, Recorder
- **Chromatic:** Chromatic Flute (25 notes, 17 holes)

## Benchmark Results

All 11 instruments achieve <1c RMS with w_int=0.9 (mean 0.17c, max 0.82c). See `backend/benchmark_all.py` or run:

```bash
python backend/benchmark_all.py
```

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

### Generative Agent (`backend/generative_agent.py`)
LLM-guided + physics-based novel instrument design. Generates design specs from text queries, then runs Pareto optimization. Supports hybrid instruments, random instruments, and quarter-tone variants. Parallel candidate optimization via Dask.

### Chalumier Integration (`chalumier/`)
Kotlin-based instrument designer. Designs instruments and outputs JSON5 bore profiles. Wrapper in `woodwind_designer/engine/chalumier_wrapper.py`.

## Distributed Computing

Dask cluster for parallel instrument optimization across machines:

```bash
# Start scheduler on desktop (Twitchy)
dask-scheduler --port 9797 --dashboard-address 9798

# Start worker on laptop (Kalle)
set PYTHONPATH=/path/to/instrument-designer
dask worker tcp://100.69.113.41:9797 --nworkers 2 --nthreads 4

# Run distributed benchmark
python scripts/dask_benchmark.py --scheduler tcp://100.69.113.41:9797
```

The generative agent automatically uses Dask when the scheduler is available, dispatching candidate optimizations in parallel.

## Getting Started

```bash
# Install dependencies
pip install numpy scipy jax jaxlib pymoo cadquery dask distributed

# Run 11-instrument benchmark
python backend/benchmark_all.py

# Run Dask-parallelized benchmark
python scripts/dask_benchmark.py --scheduler tcp://localhost:9797

# Generative agent (single-machine, no Dask)
python -c "from backend.generative_agent import generate; print(generate('recorder', n_candidates=2))"
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
