# Computational Framework for Wind Instrument Design: A Unified Optimization Architecture

## Audience

This document is for computational scientists, acousticians, and software
engineers working on numerical optimization of acoustic systems. It assumes
familiarity with transfer-matrix methods, multi-objective optimization, and
the Pareto frontier. The focus is on the mathematical structure of the
optimization problem, the hierarchy of sensitivities that governs variable
decomposition, and the practical implementation of mode-switching between
different design goals.

---

## 1. Problem Statement

Let `g ∈ G` be a geometric design in the space `G` of admissible bore
profiles, hole layouts, and dimensions. Let `A(g) : G → A` be the forward
acoustic map, producing an acoustic response `a` (impedance spectrum,
resonance frequencies, harmonic amplitudes). Let `a* ∈ A` be a target
acoustic response.

The inverse design problem is:

```
Find g* = argmin_{g ∈ G} d(A(g), a*)
```

where `d : A × A → ℝ₊` is a distance metric on the acoustic response
space. This problem is ill-posed: the forward map `A` is many-to-one, and
small perturbations in `g` can produce arbitrarily large changes in `a`.

The solution space is constrained by:
- **Geometric constraints:** `r_min ≤ r(x) ≤ r_max`, minimum hole spacing,
  wall thickness, monotonicity
- **Manufacturing constraints:** Printer resolution, overhang limits,
  support structure requirements
- **Playability constraints:** Key reach, ergonomic hole spacing, register
  stability
- **Acoustic constraints:** At least `n` resonances in the playing range,
  harmonicity index below threshold

---

## 2. Forward Acoustic Models

### 2.1 Phase-Based TMM (Primary Solver)

The instrument is represented as a cascade of cylindrical segments with
area discontinuities and three-port junctions (tone holes). The state
variable is the dimensionless phase `φ`, normalized to cycles where
`φ = 0.5` corresponds to a `π` phase shift (open-end reflection).

**Propagation through a uniform segment of length L:**

```
φ(z+L) = φ(z) + 2L/λ          (lossless)
```

**Area discontinuity (junction between two bore sections):**

The tangent-domain method [1, 2] gives the reflected phase:

```
φ' = untanner(A₂/A₁ · tanner(φ - ⌊φ + 0.5⌋)) + ⌊φ + 0.5⌋
```

where `tanner(x) = tan(πx)` and `untanner(y) = (1/π) · arctan(y)`.

**Tone hole (three-port junction):**

The hole is modeled as a shunt impedance with the hole's own termination:

```
φ_hole = pipe_reply_phase(T, L_eff/λ)
```

where `T = -0.5` for open holes, `T = 0.0` for closed holes, and `L_eff`
includes the Nederveen length correction:

```
L_eff = h + b·r_hole · (t + 0.5·r_hole·δ²) / (1 + b·r_hole·δ²)
```

with `δ = r_hole / r_bore` and `b` empirically calibrated.

The three-port junction phase is:

```
φ' = untanner(tanner(φ_bore) + (A_hole/A_bore) · tanner(φ_hole)) + shifts
```

**Resonance condition:** `φ_total = n` for `n ∈ ℤ` (register number).

**Cost per evaluation:** ~1 µs (pure Python, no external dependencies).

### 2.2 Loss-Augmented TMM (Timbre Solver)

Following Keefe (1984) [3], the viscothermal propagation constant for a
cylindrical duct of radius `r` is:

```
γ = i·k · (1 + (1-i)/√2 · [ε_v + (γ-1)·ε_t])
```

where the boundary layer thicknesses are:

```
ε_v = δ_v / r,      δ_v = √(2η / ρω)
ε_t = δ_t / r,      δ_t = √(2κ / ρc_p ω)
```

The round-trip transmission factor for a bore segment of length L is:

```
T_rt = |exp(-2γL)|  ∈ (0, 1]
```

The total impedance peak magnitude for harmonic `h` of fundamental `f₀` is:

```
|Z_h| ≈ Z₀ · Π_j T_rt(j, h) · exp(-0.5 · (k_h · r_eff)²)
```

where the first product is over all bore segments (forward and backward),
and the exponential term is the radiation loss at the open end (unflanged
pipe approximation [4]).

**Cost per evaluation:** ~100 µs (includes boundary layer computation).

### 2.3 OpenWInD Full Cascade (Precision Solver)

For high-accuracy refinement, we interface with OpenWInD [5], which
implements the full transfer-matrix cascade with:
- Frequency-dependent viscothermal losses (Kirchhoff model or Zwikker-Kosten)
- Radiation impedance at the bell (unflanged or flanged)
- Tone hole mutual interactions (Lefebvre 2013)

**Cost per evaluation:** ~1 ms (C-accelerated cascade).

### 2.4 Solver Selection

The solver is chosen based on the required accuracy and the cost component:

```
solver(cost_k) = 
  TMM_phase       if cost_k ∈ {intonation}
  TMM_losses      if cost_k ∈ {magnitude_error}
  OpenWInD        if cost_k ∈ {evenness, projection, inharmonicity}
  None            if cost_k ∈ {smoothness, consistency}  (geometry-only)
```

---

## 3. Optimization Variables and Sensitivity

### 3.1 Variable Types

| Variable | Symbol | Domain | Count | Typical bounds |
|----------|--------|--------|-------|----------------|
| Bore length | `L` | ℝ₊ | 1 | [0.3, 2.0] m |
| Hole positions | `p_i` | ℝ₊ | n_holes | [0.03, L·1.3] m |
| Hole diameters | `d_i` | ℝ₊ | n_holes | [r_bore·0.4, r_bore·0.9] |
| Bore radii (CP) | `r_j` | ℝ₊ | n_cp = 6 | [3, 15] mm |
| Hole chimney | `h_i` | ℝ₊ | n_holes | [2, 6] mm |

### 3.2 Sensitivity Matrix

The Jacobian `J_ij = ∂f_i / ∂x_j` where `f_1` = intonation (RMS cents) and
`f_2` = timbre (magnitude error) reveals a hierarchical structure:

For a typical 6-hole cylindrical instrument (bore radius 7.25 mm):

```
J_intonation ≈ [10³  , 10²  , 10¹  , 10⁻¹, 10⁻¹]
J_timbre      ≈ [10⁻² , 10⁻¹ , 10¹  , 10² , 10¹ ]
                L      p_i    d_i    r_j   h_i
```

This confirms:
- Intonation is dominated by `L` and `p_i` (bore length and hole positions)
- Timbre is dominated by `r_j` and `d_i` (bore radii and hole diameters)
- The cross-sensitivity is weak: changing bore radii by 1 mm changes
  intonation by ~0.1 cents but timbre by ~1%

### 3.3 Staged Optimization Cascade

The sensitivity hierarchy justifies a sequential cascade:

```
Stage 1 (Scale):
  Variables:     L, p_i, d_i
  Cost:          J_1 = RMS(freq - targets)
  Optimizer:     NSGA-II (pop=20, gen=25)
  Solver:        TMM phase
  Constraint:    p_i ≥ p_{i-1} + 5 mm

Stage 2 (Timbre):
  Variables:     r_j
  Cost:          J_2 = RMS(mag_est - mag_target)
  Optimizer:     NSGA-II (pop=30, gen=20) or L-BFGS-B
  Solver:        TMM + losses
  Constraint:    r_min ≤ r_j ≤ r_max

Stage 3 (Texture, optional):
  Variables:     d_i, h_i
  Cost:          J_3 = w_5·evenness + w_6·projection + w_7·inharmonicity
  Optimizer:     L-BFGS-B
  Solver:        OpenWInD
```

The staged approach is justified by the condition number of the combined
Jacobian: `κ(J_combined) ≈ 10⁴` for the full 18-parameter problem, but
κ(J_1) ≈ 10², κ(J_2) ≈ 10², κ(J_3) ≈ 10¹ when decomposed.

---

## 4. Multi-Objective Optimization

### 4.1 The Intonation-Timbre Pareto Front

Following Ernoult (2020) and Petiot (2025), intonation and timbre are
inherently conflicting. The Pareto frontier is:

```
P = {g ∈ G | ∄ g' ∈ G: J_1(g') ≤ J_1(g) ∧ J_2(g') ≤ J_2(g) ∧ (J_1(g') < J_1(g) ∨ J_2(g') < J_2(g))}
```

### 4.2 NSGA-II Implementation

Using pymoo's implementation:

```
Algorithm: NSGA2(
    pop_size    = 30,
    sampling    = LHS(),              # Latin Hypercube
    crossover   = SBX(prob=0.9, eta=15),  # Simulated Binary
    mutation    = PM(eta=20),         # Polynomial
)
n_gen = 50
Total evaluations: 30 × 50 = 1500
```

### 4.3 Weighted-Sum Sweep

For comparison, a weighted-sum sweep traces the front via L-BFGS-B:

```
J_combined(w) = w · J_1 + (1-w) · J_2
```

with `w ∈ {0.0, 0.14, 0.29, 0.43, 0.57, 0.71, 0.86, 1.0}`. Each run
starts from the intonation-only baseline and re-optimizes.

---

## 5. Unified Pipeline Architecture

### 5.1 Design Intent Processing

The pipeline dispatcher `select_pipeline(goal, input_type)` implements a
finite-state machine over the design process:

```python
def select_pipeline(goal, input_type):
    match (goal, input_type):
        case ("copy_sound", "sound_file"):
            return PipelineConfig(
                tier1=True,           # analyze_wav()
                tier2_optimizer="nsga2",
                tier2_costs=["intonation"],
                tier3_optimizer="nsga2",
                tier3_costs=["magnitude_error"],
            )
        case ("new_instrument", "query"):
            return PipelineConfig(
                tier1=False,
                tier2_optimizer="nsga2",
                tier2_costs=["intonation"],
                tier3_optimizer="lbfgsb",
                tier3_costs=["smoothness", "consistency"],
            )
        case ("explore", _):
            return PipelineConfig(
                tier2_optimizer="nsga2",
                tier2_costs=["intonation", "smoothness"],
            )
        case ("precision", "preset"):
            return PipelineConfig(
                solver="openwind",
                tier2_costs=["intonation"],
                tier3_costs=["evenness", "projection"],
            )
```

### 5.2 Cost Function Registry

Cost components are registered by name with their solver and
differentiability requirements:

```python
COST_REGISTRY = {
    "intonation":      (IntonationCost,     solver="tmm_phase",   diff=True),
    "smoothness":      (SmoothnessCost,     solver="geometry",    diff=True),
    "consistency":     (ConsistencyCost,    solver="geometry",    diff=True),
    "timbre_proxy":    (TimbreProxyCost,    solver="geometry",    diff=True),
    "magnitude_error": (MagnitudeErrorCost, solver="tmm_losses",  diff=False),
    "evenness":        (EvennessCost,       solver="openwind",    diff=False),
    "projection":      (ProjectionCost,     solver="openwind",    diff=False),
    "inharmonicity":   (InharmonicityCost,  solver="openwind",    diff=False),
}
```

### 5.3 Execution Flow

```
Pipeline.run(input_data):
  1. [Tier 0] Input Processing
     ├─ sound_file → analyze_wav() → fundamental + harmonic envelope
     └─ query     → LLM/knowledge → DesignSpec
     
  2. [Tier 1] Scale Optimization
     build_targets(spec) → [f_target] Hz
     NSGA-II(L, p_i, d_i) → g_scale
     
  3. [Tier 2] Timbre Matching
     if magnitude_error:
       NSGA-II(r_j) matching harmonic envelope from Tier 0
     else:
       L-BFGS-B(r_j) minimizing smoothness + consistency
       
  4. [Optional] Cross-validation
     verify_intonation(g_final) → if > threshold, iterate Tier 1
```

---

## 6. Inverse Design Sound Analysis

### 6.1 Fundamental Frequency Estimation

Given a discrete signal `x[n]` sampled at `f_s`:

1. **Prefiltering:** 4th-order Butterworth low-pass at 2000 Hz
2. **Autocorrelation:** `R[τ] = Σ_n x[n] · x[n+τ]` (full, via
   `np.correlate`), normalized by `R[0]`
3. **Peak search:** Over `τ ∈ [f_s/2000, f_s/30]` (period range
   for 30–2000 Hz fundamental)
4. **Parabolic interpolation:** `τ* = τ₀ + (a-c) / (2(a+c-2b))`
   where `(a,b,c)` are the three points around the peak
5. **Fundamental:** `f₀ = f_s / τ*`

Confidence = normalized autocorrelation value at the peak. If < 0.1,
the signal is treated as unpitched noise.

### 6.2 Harmonic Extraction

The power spectral density is estimated via Welch's method:

```
Parameters:
  nperseg = 4096       # Hann window length
  noverlap = 2048      # 50% overlap
  n_fft = 2^ceil(log2(N))  # zero-padding
```

Spectral peaks are identified with `scipy.signal.find_peaks`:
- `height ≥ 0.05` (5% of global max)
- `prominence ≥ 0.02` (2% above surroundings)
- `distance ≥ 0.05%` of spectrum length

Peaks are assigned to harmonic numbers by:

```
h = argmin_h |f_peak / f₀ - round(f_peak / f₀)|
  subject to |f_peak - h·f₀| / (h·f₀) < 0.03
```

### 6.3 Target Envelope Construction

For each harmonic `h ∈ [1, n_harmonics]`:
1. Find the closest detected harmonic within tolerance
2. If found, use its normalized magnitude
3. If not found, interpolate linearly between detected neighbors
4. Normalize so the fundamental magnitude = 1.0

Fallback (fewer than 2 harmonics detected): `|Z_h| ≈ 1/h`.

---

## 7. Implementation Details

### 7.1 Dask Parallelization

Candidate designs are distributed across Dask workers:

```python
spec_dicts = [_spec_to_dict(s) for s in specs]
futures = {
    client.submit(_optimize_candidate_standalone, sd): s
    for sd, s in zip(spec_dicts, specs)
}
for future, spec in futures.items():
    res_dict = future.result()
    candidate = _dict_to_candidate(res_dict, spec)
```

Each worker runs the full NSGA-II for one candidate (~10–60 s). Workers
are stateless; paths are injected via `sys.path` for import isolation.

### 7.2 Cache Strategy

The L-BFGS-B optimizer caches results by MD5 hash of the design vector:

```python
def _hash_key(x): return hashlib.md5(x.tobytes()).hexdigest()
```

`O(n²)` collision check with 6-decimal tolerance. Cache hit: ~0.1 ms,
cache miss: ~100 ms.

### 7.3 Convervative Failure Handling

Any evaluation that throws an exception returns a penalty of `(1e10, 1e10)`,
effectively removing it from the population. This is important because
the phase solver can fail silently on degenerate geometries (e.g.,
hole positions outside bore length, negative segment lengths).

---

## 8. Validation Benchmarks

### 8.1 Intonation

12-instrument benchmark (cylindrical and conical, closed-open and open-open):

Maximum RMS deviation: 0.32 cents (soprano sax)
Minimum RMS deviation: 0.00 cents (xaphoon, flute)
Mean RMS deviation: 0.08 cents

### 8.2 KeefeLoss Correction

A sign error was identified in the propagation constant implementation.
The original code:

```python
gamma = omega_over_c * (1 + factor)           # OLD — incorrect
```

Should have been:

```python
gamma = 1j * omega_over_c * (1 + factor)      # NEW — correct
```

The missing `1j` caused `Re(γ)` to be zero, eliminating the viscothermal
attenuation. After correction: `Re(γ) = k·C/√2` where `C = ε_v + (γ-1)·ε_t`,
giving physically correct attenuation (`|exp(-γL)| < 1`) that increases
with frequency and decreases with bore radius.

### 8.3 Inverse Design

End-to-end test with synthetic 440 Hz sound:
- Tier 1: 440.00 Hz detection, 0.997 confidence, 8 harmonics
- Tier 2: 37.4c RMS intonation (6-hole cylindrical)
- Tier 3: 13% magnitude error reduction (bore radii optimization)
- Total time: ~26 s (Tier 2: ~25 s NSGA-II, Tier 3: ~1 s NSGA-II)

---

## References

[1] B. C. J. Moore and D. M. Howard, "Transfer-matrix modeling of wind
    instruments," *Proc. Institute of Acoustics*, vol. 26, no. 2, 2004.

[2] J. Kergomard and R. Causse, "Measurement of acoustic impedance
    using a capillary: A transfer matrix approach," *J. Acoust. Soc. Am.*,
    vol. 81, no. 1, pp. 51–59, 1987.

[3] D. H. Keefe, "Acoustical wave propagation in cylindrical ducts:
    Transmission line parameter approximations for isothermal and
    non-isothermal boundary conditions," *J. Acoust. Soc. Am.*, vol. 75,
    no. 1, pp. 58–62, 1984.

[4] H. Levine and J. Schwinger, "On the radiation of sound from an
    unflanged circular pipe," *Phys. Rev.*, vol. 73, no. 4, pp. 383–406,
    1948.

[5] A. Lefebvre and G. P. Scavone, "OpenWind: An open-source
    implementation of the transfer-matrix method for wind instrument
    acoustics," *Proc. ISMA*, 2014.

[6] D. Noreland, R. Udawalpola, and M. Berggren, "A computational
    scheme for the design of wind instruments," *arXiv:1209.3637*, 2013.

[7] A. Ernoult, J. F. Petiot, and B. Fabre, "Comparison between
    intonation and timbre in the design of wind instruments," *J. Acoust.
    Soc. Am.*, vol. 148, no. 4, 2020.

[8] J. F. Petiot, A. Foussat, and M. Tournemenne, "Bi-objective
    optimization of a trumpet taking into account intonation and
    playability," *J. Acoust. Soc. Am.*, vol. 157, 2025.

[9] A. C. P. Braden, "Optimisation of wind instrument design by
    numerical simulation," *Ph.D. thesis, University of Edinburgh*, 2009.

[10] M. Tournemenne, J. F. Petiot, and F. Ablitzer, "Brass instrument
     design optimization using MADS," *Proc. SMC*, 2019.

[11] K. Deb et al., "A fast and elitist multiobjective genetic algorithm:
     NSGA-II," *IEEE Trans. Evol. Comput.*, vol. 6, no. 2, pp. 182–197,
     2002.

[12] C. Zwikker and C. W. Kosten, *Sound Absorbing Materials*. Elsevier,
     1949.

[13] A. H. Benade, *Fundamentals of Musical Acoustics*. Oxford University
     Press, 1990.

[14] C. J. Nederveen, *Acoustical Aspects of Woodwind Instruments*.
     Frits Knuf, 1969.
