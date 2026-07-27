# Woodwind Design Automation

Computational design platform for woodwind instruments using TMM acoustics, optimization algorithms, and 3D printing.

## Status

| Metric | Value |
|--------|-------|
| Instruments supported | 12 (chalumeau, bass clarinet, soprano/alto/tenor/baritone sax, flute, clarinet, etc.) |
| TMM accuracy | <2c RMS on open-open pipe (vs theoretical) |
| Optimization | Sequential placement + DE + L-BFGS-B pipeline |
| Best result | 12/12 instruments <3c RMS |
| JAX speedup | 25x (0.053ms vs 1.31ms per eval) |

## Architecture

```
woodwind-designer/
├── backend/                    # Core physics + optimization
│   ├── core/                   # Acoustic network, coordinates, types
│   ├── physics/                # Loss models, junctions, radiation
│   ├── solvers/                # TMM, OpenWInD, external
│   ├── optimization/           # Bore optimizers
│   ├── instruments/            # Instrument definitions
│   ├── benchmarks/             # Validation benchmarks
│   ├── archived_optimizers/    # Deprecated optimizer modules
│   ├── scratch/                # One-off test/debug scripts
│   └── tests/                  # Core test suite
├── woodwind_designer/          # GUI application (PySide6)
├── tests/                      # Integration tests
├── scripts/                    # Utility scripts, benchmarks
├── config/                     # Instrument configurations
├── docs/                       # Documentation
├── research/                   # Research documents
├── wiki/                       # Wiki pages
├── chat-logs/                  # Session logs
├── designs/                    # Exported instrument designs
├── chalumier/                  # Reference implementation (submodule)
├── openwind/                   # FEM solver (submodule)
└── web/                        # Frontend (Tauri + React)
```

## Quick Start

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest tests/ backend/tests/ -v

# Run benchmarks
python scripts/benchmark_all.py

# Start design server
python -m woodwind_designer.engine.design_server
```

## Instruments

All instruments use the same acoustic graph abstraction. The solver sees only:
- Bore profile (radii at positions)
- Tonehole positions, radii, and states (open/closed)
- Bell geometry
- Reed/mouthpiece model

### Supported Instruments
- Chalumeau in C (6 holes)
- Bass clarinet in Bb (8-14 holes)
- Soprano saxophone in Bb (7 holes)
- Alto saxophone in Eb (7 holes)
- Tenor saxophone in Bb (7 holes)
- Baritone saxophone in Eb (7 holes)
- Bass saxophone in Bb (7 holes)
- Contrabass saxophone in Eb (7 holes)
- Sopranino saxophone in Eb (7 holes)
- Chromatic flute in C (17 holes)
- D whistle (6 holes)
- Bb clarinet (17 holes)

## Optimization Pipeline

1. **Sequential placement**: Place holes one at a time, optimizing each position
2. **Differential Evolution**: Global re-optimization of all parameters
3. **L-BFGS-B refinement**: 4-stage local optimization (bore → radii → holes → all)

### Key Results
- Chalumeau: 233.6c → 25.0c RMS (recorder, physics-limited)
- Chalumeau: 18.7c → 0.5c RMS (approaches Noreland's 0.49c)
- All 12 instruments: <3c RMS with full pipeline

## Branching Strategy

- `main` = verified production code only
- `experiment/*` = disposable experiment branches
- `fix/*` = bug fixes (merge to main)
- `feature/*` = new features (merge to main)

## AI/ML Research

See `wiki/Internal-AI-Research.md` for the full research plan.

### Tier 1 (Active)
- JAX-differentiable TMM: 25x speedup confirmed
- CMA-ES: 9x fewer evaluations than DE
- MLP surrogate: BLOCKED (PyTorch/AppLocker)

### Tier 2 (Planned)
- BoTorch Bayesian optimization
- OpenWInD high-fidelity validation

### Tier 3 (Aspirational)
- RL hole placement
- LLM-assisted design
- VAE bore profiles

## References

- Noreland 2013: 0.49c clarinet optimization
- Ernoult 2020: Phase-based cost function
- Petiot 2025: Pareto frontier for intonation + timbre
- Tournemenne 2019: Timbre preference modeling
- Keefe 1981: Boundary layer corrections

## License

GPL-3.0

---

*Last updated: 2026-07-28*
