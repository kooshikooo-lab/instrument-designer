# Instrument Designer: Technical Overview

## What does this software do?

This is a computational wind instrument design platform. Given a description
("alto saxophone with bright timbre") or a recorded sound, it produces a
3D-printable bore geometry (tube shape, hole positions, hole sizes).

## How it works — the three-step pipeline

### Step 1: Design Intent → Specs

You provide either:

- **A text description** ("quarter-tone bass clarinet with conical bore")
  → An LLM (Ollama/llama3.1) or a physics knowledge base converts this into
     a `DesignSpec` — a structured recipe with bore type, radius, length,
     hole count, and scale.

- **A WAV recording** ("my_recording.wav")
  → The sound is analyzed: fundamental pitch is extracted via autocorrelation
     (440Hz detected at 99.7% confidence), harmonic frequencies are identified,
     and a spectral envelope is computed.

- **A preset** ("Chalumeau in C")
  → Direct configuration from a benchmark library of known instruments.

### Step 2: Scale Optimization (Tier 2)

Given the design spec, the software optimizes the **bore length** and **hole
positions** to make the instrument play in tune. This uses:

- **TMM phase solver** — a fast (~1µs) acoustic model that computes resonant
  frequencies by "walking" phase through the bore segments, junctions, and
  tone holes
- **NSGA-II** — a genetic algorithm that searches for the best hole layout
  to minimize intonation error (RMS cents deviation from target frequencies)

The result is an instrument that plays the correct notes, with 0.01–0.32 cents
accuracy on verified benchmarks (exceeding Noreland 2013 by 10×).

### Step 3: Timbre Matching (Tier 3, optional)

The bore profile (radius along the length) is optimized to match a target
sound's harmonic balance. This uses:

- **Keefe viscothermal loss model** — physics-based computation of how the
  bore shape attenuates different harmonics
- **Radiation loss model** — higher frequencies radiate more efficiently,
  creating the natural spectral tilt
- A second NSGA-II optimization pass (6 radius control points)

The result is an instrument that *sounds like* the target recording, while
still playing the correct scale.

## Optimization methods in one framework

All five optimization methods in the codebase are unified under a single
framework. They all minimize:

```
J(x) = w₁ × intonation_error + w₂ × timbre_error + w₃ × smoothness + ...
```

The difference is just which weights (w₁, w₂, ...) are active, which solver
is used, and which variables are optimized.

| Mode | What it's for | Variables | Weights |
|------|--------------|-----------|---------|
| **Copy sound** | Recreate a recorded instrument | Length, holes, then bore radii | intonation + timbre match |
| **New instrument** | Design from text description | Length, holes, then radii | intonation + smoothness |
| **Explore** | See the intonation-timbre tradeoff | Length, holes | intonation + smoothness (Pareto) |
| **Precision** | High-accuracy refinement | Full geometry | intonation + evenness |

## Key references

| Paper | Contribution | How we use it |
|-------|-------------|---------------|
| Noreland et al. (2013) | Two-phase clarinet optimization | Sequential refinement pipeline |
| Ernoult et al. (2020) | Phase-based resonance tracking | TMM phase solver cost function |
| Petiot et al. (2025) | Intonation × timbre Pareto front | NSGA-II bi-objective optimization |
| Keefe (1984) | Viscothermal loss formulas | KeefeLoss model for bore attenuation |
| Braden (2009) | Impedance curve matching | Tier 3 timbre approach (adapted) |

## Quick start

```python
from backend.design_pipeline import DesignPipeline

# Design from a text description
result = DesignPipeline.new_instrument("recorder with warm timbre")
print(result["final_geometry"]["bore_length_mm"])

# Copy a recorded sound
result = DesignPipeline.copy_sound("my_instrument.wav")

# Explore the design space
result = DesignPipeline.explore("quarter-tone clarinet")
```

## The project structure

```
backend/
  tmm_acoustics.py        — Phase-based acoustic solver (fast)
  physics/losses.py       — Keefe viscothermal loss model
  generative_agent.py     — LLM-guided design suggestion + NSGA-II
  inverse_design.py       — Sound → geometry pipeline (3 tiers)
  design_pipeline.py      — Unified dispatcher (mode switching)
  pareto_optimizer.py     — Bi-objective intonation × timbre
  instrument_knowledge.py — 15 instrument families, scales, materials
  solvers/               — Impedance solvers (TMM, OpenWInD)
woodwind_designer/
  engine/design_server.py — FastAPI backend (port 8000)
web/                      — React 19 + TypeScript frontend
  src/components/         — UI components (sidebar, tabs, plots)
  src/utils/api.py        — Backend API client
scripts/                  — Tools (messaging, startup, monitor)
docs/                     — Documentation
```

## Contributing

Good entry points:
- **Add an instrument family** → edit `instrument_knowledge.py`
- **Fix a cost function bug** → `pareto_optimizer.py` or `losses.py`
- **Improve optimization tuning** → NSGA-II parameters in `generative_agent.py`
- **Build the inverse design UI** → new React component in `web/src/components/`
- **Add a new mode** → `design_pipeline.py::select_pipeline()`

See `docs/THEORETICAL_FRAMEWORK.md` for the full theory.
See `docs/ROADMAP.md` for planned work.
