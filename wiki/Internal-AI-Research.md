# AI/ML Research for Instrument Designer

> Created: 2026-07-26 | Issue: #21

---

## Overview

Research on applying AI/ML to accelerate acoustic simulation, enable generative design, and optimize intonation+timbre. Our project uses TMM (Transfer Matrix Method) for bore acoustics, CadQuery for STL export, and Dask for distributed compute.

---

## Tier 1: Highest Impact, Ready to Implement

### 1. JAX-Differentiable TMM

Rewrite `tmm_acoustics.py` in JAX. Same math, different runtime.

| Aspect | Current (Python TMM) | JAX TMM |
|--------|---------------------|---------|
| Speed | ~1ms/eval | ~10-50μs/eval (10-50x faster) |
| Gradients | Manual finite differences | `jax.grad` (automatic) |
| GPU | No | Yes (via XLA) |
| Accuracy | Exact | Exact (same math) |

**Key insight**: TMM involves matrix multiplications and exponentials — all naturally differentiable. Gradients flow from intonation RMS → bore parameters directly.

**References**:
- [j-Wave](https://github.com/ucl-bug/jwave) — JAX differentiable acoustics framework
- [OpenWInD](https://openwind.inria.fr/) — TMM + adjoint-based bore reconstruction
- [jaxdiffmodal](https://github.com/rodrigodzf/jaxdiffmodal) — Differentiable modal simulation

### 2. MLP Surrogate Model

Train neural network on TMM data: geometry → resonant frequencies.

| Aspect | TMM Solver | MLP Surrogate |
|--------|-----------|---------------|
| Inference | ~1ms | <1μs (1000x faster) |
| Training | N/A | 10K-50K TMM samples (~30s) |
| Accuracy | Exact | ~1% error (Fréour et al.) |
| Gradient | Not available | Through NN weights |

**Architecture**: 2-3 hidden layers, 128-512 neurons, ReLU/tanh.

**Training data**: Latin Hypercube Sampling of design space, generate via Dask.

**References**:
- Fréour et al. (2023) — 12K trumpet bifurcation diagrams, ~1% error
- Petiot et al. (2025) — Yamaha/IRCAM, LassoLars 0.305c RMSE
- DeepVocalTube (2025) — Tube geometry → formant prediction

### 3. CMA-ES

Replace differential evolution with CMA-ES ([pycma](https://github.com/CMA-ES/pycma)).

| Aspect | DE (current) | CMA-ES |
|--------|-------------|--------|
| Covariance | Diagonal only | Full learned |
| Convergence | ~50K evals | ~5-10K evals |
| Correlated params | Poor | Excellent |
| Step size | Fixed/tuned manually | Auto-tuned |

**Why it works**: Bore parameters are correlated (adjacent sections affect each other). CMA-ES learns this correlation structure.

---

## Tier 2: Medium-term

### 4. Bayesian Optimization (BoTorch)

Gaussian Process surrogate + acquisition functions for smart sampling.

- 10-50x fewer evals than random/grid search
- Multi-objective: simultaneously optimize intonation + timbre via qNEHVI
- Dask-parallel batch acquisition maps to cluster
- Reference: [BoTorch](https://github.com/meta-pytorch/botorch), [Ax Platform](https://ax.dev/)

### 5. Inverse Design Network

Train NN: desired impedance curve → bore parameters. Inverts the forward problem.

- Reference: Wang (2019 MIT thesis) — FDTD + NN, audio→shape, 3D-printed prototype
- Your TMM generates training data; NN learns the inverse mapping

### 6. OpenWInD Integration

- `pip install openwind` — GPL, Python, TMM + gradient bore reconstruction
- Validation tool + alternative forward model
- Gradient-based bore reconstruction as baseline

---

## Tier 3: Research Directions

### 7. RL for Hole Placement (PPO)

Sequential decision: place hole (yes/no) + diameter. Reward = -intonation RMS.

- Reference: Qasim et al. (2024) — RL beats gradient-based for sequential physics design

### 8. LLM-Assisted Design

GPT-4/Claude generates CadQuery from natural language instrument descriptions.

- No CadQuery-specific generative work exists — we'd be first
- Use case: "a clarinet bore tapering from 15mm to 12mm over 60cm" → parametric CadQuery

### 9. VAE for Bore Profiles

Train on successful bores (sub-3c intonation). Latent space = smooth manifold of good designs.

---

## Key Papers

| # | Paper | Technique | Relevance |
|---|-------|-----------|-----------|
| 1 | Petiot et al. (2025) — Yamaha trumpet ML surrogates | LassoLars regression, 0.305c error | **Direct blueprint** |
| 2 | Fréour et al. (2023) — Trumpet bifurcation ML | 12K samples, ~1% error, real-time | Very High |
| 3 | Wang (2019) — MIT wind instrument NN | FDTD + NN inverse design | Very High |
| 4 | Yokota et al. (2024) — ResoNet PINN | Physics-informed NN for tube resonance | High |
| 5 | Qasim et al. (2024) — RL physics instrument | PPO sequential design | High |
| 6 | OpenWInD (Ernoult et al.) | TMM + gradient bore reconstruction | High |
| 7 | j-Wave (Stanziola et al.) | JAX differentiable acoustics | High |

---

## Gap Analysis — Where We Lead

- **No one combines TMM + NN surrogates** for woodwind optimization (MIT used FDTD)
- **No diffusion models for bore profiles** — 1D radius is a natural candidate
- **No intonation-specific optimization** — our sub-3c RMS target is novel
- **No CadQuery + LLM generative work** — we'd be first

---

## Implementation Plan

### Phase 1: Tier 1 testing
- [ ] Benchmark JAX TMM — port `tmm_acoustics.py`, compare speed/accuracy
- [ ] Generate 10K training samples via Dask
- [ ] Train MLP surrogate, measure speed vs accuracy
- [ ] Swap DE for CMA-ES, compare convergence

### Phase 2: Integration
- [ ] Add BoTorch for multi-objective Pareto (intonation + timbre)
- [ ] Integrate MLP surrogate into two-phase optimizer
- [ ] Build inverse design network prototype

### Phase 3: Research
- [ ] RL hole placement with PPO
- [ ] LLM-assisted CadQuery generation
- [ ] VAE bore profile manifold

---

## Expected Speedup

| Approach | Current (L-BFGS-B + DE) | With ML Integration |
|---|---|---|
| Evaluations to converge | 50K-100K TMM | 2K-5K TMM + NN |
| Multi-objective | Weighted sum | True Pareto (10-20 designs) |
| New instrument family | Full reoptimization | 5-10 evals with transfer |
| Timbre optimization | Not included | Integrated perceptual model |

---

## Integration Architecture

```
Dask Cluster
├── Workers: TMM forward model (existing)
├── Workers: GP surrogate evaluation (BoTorch, GPU-optional)
├── Worker: NN surrogate (PyTorch, GPU)
└── Central: BoTorch acquisition optimization
    ├── qNEHVI for Pareto
    ├── CMA-ES for local refinement
    └── Active learning uncertainty sampling
```

---

## Key Libraries

| Library | Purpose | Install |
|---------|---------|---------|
| JAX | Differentiable TMM | `pip install jax` |
| BoTorch | Bayesian optimization | `pip install botorch` |
| pycma | CMA-ES | `pip install cma` |
| GPyTorch | Scalable GPs | `pip install gpytorch` |
| Ax Platform | Experiment management | `pip install ax-platform` |
| PyTorch | NN surrogates | `pip install torch` |
