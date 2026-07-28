# Unified Theoretical Framework for Wind Instrument Design Optimization

## 1. The Inverse Problem in Acoustics

Given a desired sound (target spectrum), find the bore geometry that produces it. This is fundamentally **ill-posed**: many geometries produce acoustically similar instruments. The solution space must be constrained by physics, manufacturability, and playability.

### 1.1 The Forward Map

```
f: Geometry → Acoustics → Percept
```

| Layer | Input | Forward model | Output |
|---|---|---|---|
| Geometry | bore radii, hole positions/diameters, length | N/A | Parametric representation |
| Acoustics | Geometry + excitation | TMM phase / full TMM cascade | Impedance spectrum Z(ω) |
| Percept | Z(ω) + blowing model | Harmonic generation model | Fundamental, harmonics, envelope |

The forward map is **many-to-one**: different geometries can yield similar Z(ω), and different Z(ω) can yield similar perceived sound (within the flexibility of human embouchure/reed control).

### 1.2 The Inverse Map

```
f⁻¹: Desired Sound → {Geometry}
```

Decomposed into three independent sub-problems with a **cascaded hierarchy**:

| Tier | What it determines | Acoustics variable | Geometry variable | Solver cost |
|---|---|---|---|---|
| **Scale** | Which notes are playable | Resonance frequencies (peaks of Z) | Bore length + hole positions | Low (TMM phase, µs) |
| **Timbre** | Harmonic balance, spectral envelope | Relative impedance peak magnitudes | Bore profile (radii along length) | Medium (TMM + loss model, ms) |
| **Texture** | Per-note nuance, response | Absolute impedance + Q-factors | Hole diameters, undercuts, chamfers | High (TMM full cascade, s–min) |

The cascade is **hierarchical by sensitivity**: hole positions strongly affect frequency → optimize first. Bore radii weakly affect frequency but strongly affect timbre → optimize second. Hole diameters affect both, but can be fine-tuned last.

## 2. Comparison of Existing Methods

### 2.1 By Optimization Variables

| Method | Length | Hole positions | Hole diameters | Bore radii (6 CP) | Bore radii (full) |
|---|---|---|---|---|---|
| **Generative Agent (NSGA-II)** | Estimated, fixed | ✓ (sorted) | ✓ | ✓ | ✗ |
| **Inverse Design Tier 2** | ✓ (from sound) | ✓ (via agent) | ✓ (via agent) | Fixed | ✗ |
| **Inverse Design Tier 3** | Fixed (T2) | Fixed (T2) | Fixed (T2) | ✓ (6 CP, re-opt) | ✗ |
| **Design Desk (DE + L-BFGS-B)** | ✓ (sweep) | ✓ | ✓ | ✗ | ✗ |
| **L-BFGS-B (OpenWInD)** | ✓ (sweep) | Fixed | Fixed | ✗ | ✓ (12 CP, PAVA monotonic) |
| **Two-Phase (Noreland)** | ✓ (sweep) | ✓ | ✓ | ✓ (6 CP) | ✗ |

### 2.2 By Forward Model

| Method | Solver | Loss model | Computation | Accuracy (freq) | Accuracy (mag) |
|---|---|---|---|---|---|
| **TMM phase** | Phase walking | Keefe (optional) | ~1 µs per evaluation | ~2% | ✗ (always |R|=1) |
| **TMM full cascade** | Transfer matrix | Keefe viscothermal + radiation | ~100 µs per frequency | ~1% | ~5% (good) |
| **OpenWInD FEM** | FEM/TMM hybrid | Full viscothermal + radiation | ~1 ms per frequency | <0.5% | <2% (excellent) |

### 2.3 By Cost Function

| Method | Objective 1 | Objective 2 | Combination |
|---|---|---|---|
| **Generative Agent** | RMS cents (intonation) | Bore smoothness + hole radiation consistency (geometry proxy) | NSGA-II Pareto |
| **Inverse Design Tier 2** | RMS cents (via agent) | N/A (single objective) | Weighted sum (implicit) |
| **Inverse Design Tier 3** | RMS harmonic magnitude error | N/A | Single objective |
| **Design Desk** | RMS cents or cubic mean L3 | N/A | Single objective |
| **L-BFGS-B Phase 2** | RMS cents | Evenness + Projection + Smoothness + Inharmonicity | Weighted sum |
| **Two-Phase** | Phase cost (Phase 1) → Peak cost (Phase 2) | N/A | Two-stage |

### 2.4 By Application Domain

| Method | Best for | Weakness |
|---|---|---|
| **Generative Agent** | Novel/experimental designs, hybrid instruments | Timbre is geometric proxy, not acoustic |
| **Inverse Design** | Copying a recorded instrument's sound | Cascaded errors; Tier 3 may break T2 intonation |
| **Design Desk** | Known instrument archetypes, standard designs | No support for novel or hybrid forms |
| **L-BFGS-B (OpenWInD)** | High-accuracy optimization of existing designs | Slow (OpenWInD); no Pareto tradeoff analysis |
| **Two-Phase** | General-purpose, good balance of speed/accuracy | Phase discontinuity can trap local optima |

## 3. Theoretical Unification

### 3.1 The Fundamental Tradeoff: Intonation vs Timbre

Ernoult et al. (2020, JASA) and Petiot et al. (2025, JASA) confirm: **intonation and timbre are inherently conflicting objectives** in wind instrument design. A bore that produces perfectly tuned resonances will not produce the ideal harmonic amplitude envelope, and vice versa. This is because:

- **Frequency** is determined primarily by the **total effective length** of the bore (length + hole positions)
- **Timbre** is determined primarily by the **bore profile shape** and **radiation impedance** (radii along length, flare)

Both depend on the same geometry but through different physical mechanisms. The Pareto front is therefore the correct framework.

### 3.2 Variable Decomposition by Acoustic Effect

Let `x = [L, p_1..p_n, d_1..d_n, r_1..r_m, h_1..h_n]` be the full design vector where:
- `L` = bore length
- `p_i` = hole positions
- `d_i` = hole diameters
- `r_j` = bore radii at control points
- `h_i` = hole chimney heights

The **sensitivity matrix** S_ij = ∂f_i / ∂x_j reveals the hierarchy:

| Variable | Effect on frequency | Effect on timbre | Effect on playability |
|---|---|---|---|
| L | **Strong** (f ∝ 1/L) | Weak (via overall loss) | Strong (range) |
| p_i | **Strong** (effective length per note) | Moderate (hole radiation) | Strong (ergonomics) |
| d_i | Moderate (shunt impedance) | **Strong** (radiation efficiency) | Strong (ease of playing) |
| r_j | Weak (slight phase shift) | **Strong** (loss profile, flare) | Moderate (backpressure) |
| h_i | Weak (end correction) | Moderate | Moderate |

This confirms the **cascaded optimization hierarchy**:
1. Optimize L + p_i for intonation (Tier 2 / Generative Agent)
2. Optimize r_j for timbre (Tier 3 / L-BFGS-B Phase 2)
3. Optimize d_i + h_i for texture (fine-tuning)

### 3.3 Cost Function Unification

All cost functions in the codebase can be expressed as special cases of:

```
J(x) = Σ_k w_k · C_k(f_k(x), target_k)
```

Where:

| k | Cost component C_k | Forward model f_k | Target | Weight w_k |
|---|---|---|---|---|
| 1 | RMS cents | TMM phase: frequencies for fingerings | Scale frequencies | w_intonation |
| 2 | RMS magnitude error | TMM + Keefe: harmonic magnitudes | Harmonic envelope from sound | w_timbre |
| 3 | Bore smoothness | Geometry only: std(Δ²r) | 0 (perfectly smooth) | w_smooth |
| 4 | Radiation consistency | Geometry only: std((d/2R)²) | 0 (perfectly uniform) | w_consistent |
| 5 | Evenness | TMM impedance: peak magnitude ratios | 0 (equal peak heights) | w_even |
| 6 | Projection | TMM impedance: mean peak magnitude | ∞ (maximize) | w_project |
| 7 | Inharmonicity | TMM impedance: peak deviation from harmonic | 0 (perfectly harmonic) | w_inharm |

The **mode switching** the user suggested is simply choosing different subsets of {w_k} for different goals:

| Goal | Active weights | Notes |
|---|---|---|
| **Copy a sound exactly** | w₁, w₂ (via manual instrument) | w₂ from sound's harmonic envelope; w₁ from same tuning |
| **Design new instrument** | w₁, w₃, w₄ | Create a playable, practical instrument |
| **Scientific exploration** | w₁, w₅, w₆ | Understand acoustic limits (max brightness, evenness) |
| **Microtonal/chromatic** | w₁, w₄, w₅ | Uniform hole spacing, consistent behavior across range |
| **Experimental/hybrid** | w₁...w₇ | Full Pareto front; explore the design space |

### 3.4 Algorithm Selection by Design Phase

| Phase | Goal | Algorithm | Why |
|---|---|---|---|
| **Exploration** | Find feasible region | Differential Evolution (global) or NSGA-II (Pareto) | Robust to multi-modal landscapes; no gradients needed |
| **Refinement** | Converge to optimum | L-BFGS-B (gradient-based) | Fast local convergence; needs good starting point |
| **Trade-off analysis** | Understand Pareto front | NSGA-II with dense population | Single run gives full frontier |
| **Sound copying** | Match recorded sound | Cascaded: NSGA-II (scale) → NSGA-II (timbre) | Different variables at each stage; different cost functions |

## 4. The Unified Optimization Pipeline

### 4.1 Architecture

```
User Input (query / sound file / preset)
    │
    ▼
┌─────────────────────────────────────────────────────┐
│                 DESIGN ORCHESTRATOR                  │
│  Selects optimization strategy based on:             │
│  - User goal (new design / copy sound / explore)     │
│  - Available compute (Dask / local)                  │
│  - Required accuracy (fast draft / final)            │
│  - Instrument type (known / hybrid / experimental)   │
└──────────┬──────────────────────────────────────────┘
           │
    ┌──────┴──────┐
    ▼              ▼
┌─────────┐  ┌──────────┐
│   LLM   │  │  Sound   │
│ Suggestion│  │ Analysis  │
└────┬────┘  └────┬─────┘
     │             │
     └──────┬──────┘
            ▼
┌─────────────────────┐
│    LEVEL 1 OPT      │  ← Optimize: L, p_i
│  (Scale/Fingering)   │    Cost: RMS cents (w₁)
│  Algorithm: NSGA-II  │    Target: scale frequencies
│  Solver: TMM phase   │    Variables: 1 + 2n_holes
└──────────┬──────────┘
           │ (passes fixed L, p_i, d_i)
           ▼
┌─────────────────────┐
│    LEVEL 2 OPT      │  ← Optimize: r_j (bore radii)
│  (Timbre/Envelope)   │    Cost: RMS mag error (w₂)
│  Algorithm: NSGA-II  │    Target: harmonic envelope
│  Solver: TMM + loss  │    OR: smoothness + consistency (w₃, w₄)
│  model               │    Variables: 6–12 CPs
└──────────┬──────────┘
           │ (passes fixed bore profile)
           ▼
┌─────────────────────┐
│    LEVEL 3 OPT      │  ← Optimize: d_i, h_i
│  (Texture/Response)  │    Cost: evenness + projection (w₅, w₆)
│  Algorithm: L-BFGS-B │    OR: inharmonicity (w₇)
│  Solver: OpenWInD     │    Variables: 2n_holes
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  FINAL DESIGN       │
│  Geometry + Z(ω)    │
│  + Fingering chart  │
│  + 3D model         │
└─────────────────────┘
```

### 4.2 Mode Switching Logic

```python
def select_pipeline(goal: str, input_type: str, instrument_type: str) -> PipelineConfig:
    if goal == "copy_sound":
        # Full 3-tier with sound analysis
        return PipelineConfig(
            tier1=True,                    # Sound analysis
            tier2_optimizer="nsga2",       # Scale from fundamental
            tier2_cost=["intonation"],     # w₁ only
            tier3_optimizer="nsga2",       # Timbre from envelope
            tier3_cost=["magnitude_error"],# w₂ from sound
            tier4=False,                   # Skip texture (can't measure from recording)
        )
    elif goal == "new_instrument" and instrument_type in KNOWN_FAMILIES:
        # Standard 2-level: scale + smoothness
        return PipelineConfig(
            tier1=False,
            tier2_optimizer="nsga2",
            tier2_cost=["intonation", "smoothness", "consistency"],
            tier3=False,
            tier4=False,
        )
    elif goal == "explore" or instrument_type == "hybrid":
        # Full Pareto exploration
        return PipelineConfig(
            tier1=False,
            tier2_optimizer="nsga2",
            tier2_cost=["intonation", "smoothness"],
            tier3_optimizer="lbfgsb",
            tier3_cost=["evenness", "projection"],
            tier4=False,
        )
    elif goal == "precision":
        # High-accuracy: replace TMM with OpenWInD
        return PipelineConfig(
            solver="openwind",
            ...
        )
```

### 4.3 Cost Function Selection

The cost function is assembled from components at runtime:

```python
cost_functions = {
    "intonation":       IntonationCost(scale_targets, TMMPhaseSolver()),
    "magnitude_error":  MagnitudeErrorCost(harmonic_envelope, TMMLossSolver()),
    "smoothness":       BoreSmoothnessCost(),
    "consistency":      RadiationConsistencyCost(),
    "evenness":         PeakEvennessCost(full_impedance_solver),
    "projection":       PeakProjectionCost(full_impedance_solver),
    "inharmonicity":    InharmonicityCost(full_impedance_solver),
}
```

Each cost function has:
- **Solver requirement**: TMM phase / TMM + loss / OpenWInD / geometry-only
- **Scaling**: Normalized to [0, 1] for Pareto comparability
- **Differentiability**: For gradient-based optimization where applicable
- **Pareto axis**: Which tradeoffs it participates in

## 5. Relationship to Existing Literature

| Paper | Method | Our analog | Difference |
|---|---|---|---|
| **Ernoult 2020** | Phase-based resonance + Pareto intonation/timbre | Generative agent NSGA-II | Their timbre cost uses actual impedance magnitudes (via measurement); ours uses geometry proxy |
| **Ernoult 2021** | Full Waveform Inversion (adjoint) | L-BFGS-B Phase 2 | FWI needs differentiable solver (our TMM phase is not differentiable); they use FEM |
| **Braden 2009** | Windowed impedance matching + Rosenbrock | L-BFGS-B Phase 1 | Braden works on brass (no tone holes); our TMM handles holes via junction3 |
| **Noreland 2013** | Two-phase: DE + L-BFGS-B | Two-Phase Optimizer | Direct port of the same approach |
| **Petiot 2025** | Pareto intonation × timbre via NSGA-II | Generative Agent + Inverse Design | Petiot proves the tradeoff exists; our architecture implements it |
| **Logie 2015** | TMM optimization for Scottish smallpipes | Chalumier solver | Same phase-based TMM, same application domain |
| **Zwikker & Kosten 1949** | Visothermal boundary layer theory | KeefeLoss | Fundamental physics; our implementation is correct per Keefe 1984 |

## 6. Concrete Recommendations

### 6.1 What to Unify Now

1. **Cost function registry**: All cost components (w₁...w₇) live in one module with a uniform interface, selectable at runtime.
2. **Variable registry**: All variable types (L, p_i, d_i, r_j, h_i) have known bounds, sensitivities, and solver dependencies.
3. **Pipeline dispatcher**: A single entry point that assembles the optimizer pipeline from the user's goal + input type.

### 6.2 What to Keep Separate

1. **Solvers** (TMM phase, TMM full cascade, OpenWInD) — each has different accuracy/cost tradeoffs.
2. **Optimizers** (NSGA-II, DE, L-BFGS-B) — each suitable for different phases (global vs local, Pareto vs single).
3. **Input processors** (sound analysis, LLM suggestion, preset lookup) — different sources of design intent.

### 6.3 What to Add

1. **A Tier 0 "design intent" processor** that takes a user query and maps it to a pipeline config (mode switch).
2. **A `compute_impedance` cascade** in the TMM solver that produces correct magnitudes (currently, only OpenWInD does this).
3. **Cross-validation**: After Tier 3, verify that intonation hasn't degraded (if so, re-run Tier 2 with updated bore profile).

### 6.4 The Correct Default Pipeline

For the **general case** (user says "design me an instrument"), the correct pipeline is:

```
1. Intent → LLM suggests DesignSpec (family, scale, hole count)
2. Level 1 (Scale): NSGA-II on L + p_i + d_i → minimize intonation RMS
3. Level 2 (Timbre): NSGA-II on r_j → minimize harmonic envelope error from:
   a. [If sound provided]: Difference from target envelope
   b. [If no sound]: Bore smoothness + hole radiation consistency (geometry proxy)
4. [Optional] Level 3 (Texture): L-BFGS-B on d_i + h_i → maximize evenness
5. [If sound provided] Validate: Check intonation didn't degrade; iterate if needed
```

For the **inverse design case** (user says "make an instrument that sounds like this.wav"):

```
1. Sound → analyze_wav → fundamental + harmonic envelope
2. Level 1 (Scale): NSGA-II on L + p_i + d_i using fundamental as scale root
3. Level 2 (Timbre): NSGA-II on r_j matching sound's harmonic envelope
4. Cross-validate: recompute intonation with new radii
```

This is essentially what `inverse_design.py` already does, confirming the architecture is correct.
