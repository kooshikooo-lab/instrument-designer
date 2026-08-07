# Instrument Designer

Computational wind-instrument design platform. Given a fingering chart and target
frequencies, the optimizer designs bore geometry and hole positions that minimize
intonation error — currently **<3 cents RMS** across 12/12 instrument families.

License: GPL-3.0 · Python ≥ 3.10 · Version 2.0.0

## What it does

- **Design**: instrument-agnostic bore + tone-hole optimization from a fingering
  chart and target frequencies.
- **Acoustics**: Transfer Matrix Method (TMM) engine with a JAX rewrite for
  automatic differentiation (~25x speedup via `vmap`).
- **Optimize**: two-phase (differential evolution + L-BFGS-B) and Pareto-front
  (intonation vs timbre) pipelines.
- **Simulate & export**: OpenWInD validation, impedance plots, CadQuery/build123d
  STL/STEP export, sliced-model prep for 3D printing.
- **Distribute**: Dask cluster parallelizes benchmark/design sweeps across machines.

## Supported instruments

- **Closed-open (chalumeau family):** Chalumeau C, Bass Chalumeau Bb, Diatonic D Chalumeau
- **Open-open cylindrical:** Concert Flute, Alto Flute, PVC Flute, Tin Whistle, Xaphoon
- **Open-open conical:** Soprano Sax, Alto Sax, Recorder
- **Chromatic:** Chromatic Flute (25 notes, 17 holes)

The library holds 42+ instrument presets and the optimizer is instrument-agnostic.

## Benchmark (RMS intonation error, cents)

| Instrument | Sequential | Seq + Refined |
|---|---|---|
| Chalumeau C | 18.73 | **0.53** |
| Bass Chalumeau Bb | 27.01 | **0.00** |
| Diatonic D Chalumeau | 26.38 | **0.62** |
| Soprano Sax Bb | 66.35 | **0.00** |
| Alto Sax Eb | 196.94 | **0.00** |
| Recorder C | 233.59 | **1.04** |
| Xaphoon C | 294.54 | **0.00** |
| Tin Whistle D | 170.74 | **0.00** |
| Concert Flute C | 182.92 | **0.00** |
| Alto Flute G | 187.41 | **0.00** |
| PVC Flute D | 381.19 | **0.00** |

## Getting started

```bash
pip install -e ".[dev]"        # base + dev/test tooling
python backend/benchmark_all.py # 12-instrument benchmark
pytest tests/                   # test suite
```

Optional extras: `jax` (differentiable solver), `cad` (build123d/CadQuery export),
`bench` (Dask), `surrogate`, `fem`, `spectral`, `freecad`, `chess`.

Dependency versions are pinned with `pip-tools` lock files. Regenerate after
changing `pyproject.toml`:

```bash
python scripts/compile_requirements.py        # regenerate
python scripts/compile_requirements.py --check # verify (CI enforces)
```

### Distributed compute (Dask)

```bash
dask worker tcp://SCHEDULER_IP:8786 --nworkers 2 --nthreads 4
python scripts/dask_benchmark.py --scheduler tcp://SCHEDULER_IP:8786
```

### Frontends

- `web/` — React + Vite + TypeScript + Three.js web frontend (FastAPI backend)
- `web/src-tauri/` — Tauri v2 desktop shell
- `woodwind_designer/` — original PySide6 desktop app + FastAPI server

## Architecture

```
├── backend/            # Core engine: TMM, JAX solver, optimizers, CAD export
├── woodwind_designer/  # GUI (PySide6) + FastAPI server
├── web/                # React/TS frontend + Tauri shell
├── tests/             # pytest suite (405 tests)
├── scripts/            # Benchmarks, Dask helpers, governance guards
├── docs/               # Constitution, architecture, research, roadmaps
├── research/           # Literature references
├── config/             # Instrument preset configs (JSON)
├── chalumier/          # Third-party Kotlin designer (integration)
└── openwind/           # Third-party FEM solver (integration)
```

## Governance

This repo is developed collaboratively by two AI-assisted machines (desktop and
laptop) under a written constitution. See:

- `AGENTS.md` — working agreement + coordination protocol
- `docs/AI_CONSTITUTION.md` — laws incl. branch governance (Law 15) and
  self-audit of enforcement (Law 16)
- `docs/CONSTRAINTS_AND_PREFERENCES.md` — full constraints
- `docs/ROADMAP.md`, `docs/ARCHITECTURE.md`, `docs/STATUS.md`

Enable the git-hook guards on a fresh clone:

```bash
powershell -ExecutionPolicy Bypass -File scripts\install_hooks.ps1
```

## Coordinate systems

When bridging tools, axes/fingering conventions must be mapped explicitly:

| Tool | 0 = | Holes indexed from | Fingering |
|---|---|---|---|
| Chalumier | bell (open) | bell | X=closed, O=open |
| OpenWInD | mouthpiece | mouthpiece | x=closed, o=open |
| TMM | mouthpiece | mouthpiece | true=closed |

Full conversion rules: `docs/ARCHITECTURE.md`.

## References

- Ernoult et al. (2020) JASA — phase-based intonation cost function
- Petiot et al. (2025) JASA — NSGA-II Pareto trumpet optimization
- Noreland et al. (2013) — sequential greedy bore optimization
- Keefe (1981) — TMM validation
- Benade (1976) — open-hole acoustics

## Contributing

1. Fork and create a feature branch per the branch-governance law.
2. Run `pytest tests/` and `ruff check .`.
3. Submit a pull request.
