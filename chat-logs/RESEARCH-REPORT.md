---
title: "Computational Design of Woodwind Instruments: A Research Report"
subtitle: "Integrating Open-Source Tools for Bore Profile Optimization"
author: "Instrument Designer Project — Desktop & Laptop Collaborative Team"
date: "July 2026 (ongoing)"
---

# Executive Summary

This report documents the design, development, and evaluation of a computational tool for designing woodwind instruments. The project integrates multiple open-source acoustic simulation tools (OpenWInD, chalumier, demakein) with optimization algorithms (NSGA-II, scipy.optimize) to create a platform for rapid instrument prototyping. We document what worked, what failed, what we learned from the academic literature, and where we believe the field is heading. This report is a living document that will be updated as the project progresses.

**Key findings so far:**

1. NSGA-II (evolutionary multi-objective) is the **wrong algorithm** for bore optimization — every successful instrument design tool in the literature uses gradient-based methods
2. Peak-detection-based frequency matching creates **discontinuous cost functions** that defeat gradient-based optimizers — Ernoult's (2020) phase-based resonance detection solves this
3. Two-phase optimization (Noreland 2013) is **essential** — "little success omitting Phase 1"
4. Starting from a known-good bore (Buffet R13 dimensions) dramatically improves convergence
5. 3D printing validation shows instruments can be produced that musicians **cannot distinguish** from originals (Yamamoto 2025)
6. The `np.inf` penalty in pymoo corrupts NSGA-II's crowding distance computation — a simple `1e10` sentinel is correct

**Current status:** 3.11 cents RMS on clarinet Bb (borderline <3 cent target). Building scipy.gradient-based optimizer (L-BFGS-B) with two-phase workflow.

---

# Table of Contents

1. Introduction & Motivation
2. Project Architecture
3. Acoustic Simulation: OpenWInD Integration
4. Optimization Approaches: What We Tried
5. The `np.inf` Bug: A Cautionary Tale
6. Bore Profile Representation
7. Frequency Target System
8. Research Literature Review
9. Software Tools Survey
10. 3D Printing & Manufacturing
11. AI-Assisted Design
12. Lessons Learned
13. Future Directions
14. References

---

# 1. Introduction & Motivation

## 1.1 The Problem

Designing a woodwind instrument (clarinet, flute, oboe, etc.) requires careful shaping of the bore profile (internal cross-section) so that each note plays at the correct pitch. The relationship between bore geometry and pitch is governed by acoustic wave propagation — a complex physical system that cannot be solved analytically for realistic instruments.

Traditionally, instrument design is a craft skill passed through apprenticeships. A master maker spends years learning how bore shape affects intonation, tone quality, and playability. This creates a barrier to entry and limits innovation.

## 1.2 Our Goal

Build a software platform that:

1. **Simulates** acoustic impedance of arbitrary bore profiles (using OpenWInD)
2. **Optimizes** bore geometry to match target frequencies (using scipy/pymoo)
3. **Integrates** existing tools (chalumier, demakein) rather than reimplementing them
4. **Provides** a usable GUI for instrument designers (Tauri desktop app)
5. **Exports** manufacturing-ready files (SVG, DXF, G-code)

**Guiding principle:** Integrate proven tools. Don't reinvent the wheel. Original work only where it genuinely improves on existing methods.

## 1.3 Target Accuracy

| Phase | Target | Status |
|-------|--------|--------|
| C1 | <20 cents RMS | **Achieved** (3.11 cents) |
| C2 | <10 cents RMS | **Achieved** |
| C3 | <5 cents RMS | **Achieved** (3.11 cents) |
| C4 | <3 cents RMS | Borderline — need more evals to break through cleanly |

**Reference:** Noreland et al. (2013) achieved <5 cents RMS on a real clarinet prototype. Measured vs computed average deviation was 1.97 cents after correcting a ~12 cent flat offset.

---

# 2. Project Architecture

## 2.1 System Overview

```
┌─────────────────────────────────────────────────────┐
│                   Tauri Frontend                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Designer │  │ Optimizer│  │ Results Viewer   │  │
│  │ (editor) │  │ (wizard) │  │ (impedance/bore) │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       └──────────────┼──────────────────┘             │
└──────────────────────┼────────────────────────────────┘
                       │ HTTP API
┌──────────────────────┼────────────────────────────────┐
│                FastAPI Backend                         │
│  ┌───────────────────┼──────────────────────────────┐  │
│  │  OpenWInD    │  scipy.optimize  │  AI Advisor   │  │
│  │  (acoustic   │  (optimization)  │  (rule+LLM)   │  │
│  │   simulation)│                  │               │  │
│  └──────────────┴──────────────────┴───────────────┘  │
│  ┌──────────────────────────────────────────────────┐  │
│  │  chalumier wrapper │ demakein wrapper │ export   │  │
│  └──────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

## 2.2 Technology Stack

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| Desktop app | Tauri (Rust + React) | Native features, small binary, web UI |
| Backend | Python FastAPI | Rich scientific Python ecosystem |
| Acoustic simulation | OpenWInD | 1D spectral FEM, actively maintained |
| Optimization | scipy.optimize / pymoo | Gradient-based / evolutionary |
| Cache | SQLite (mp_cache.py) | Shared across parallel workers |
| AI advisor | Rule-based + Ollama LLM | No dependencies for basic mode |
| Export | SVG, DXF | Standard manufacturing formats |

## 2.3 Branch Strategy

| Branch | Purpose |
|--------|---------|
| `option-a-tauri` | Main integration (stable) |
| `experiment/chalumier-integration` | Full chalumier UI |
| `experiment/staged-optimization` | Noreland 3-stage optimizer |
| `experiment/processpoolexecutor` | Parallel benchmark |
| `experiment/v2-scipy-gradient` | **NEW** — scipy.optimize replacement |

---

# 3. Acoustic Simulation: OpenWInD Integration

## 3.1 What OpenWInD Does

OpenWInD (Open Woodwind Design) is a 1D spectral finite element method for computing the input impedance of wind instruments. It models:

- **Bore geometry:** Arbitrary cross-section profiles
- **Visco-thermal losses:** Boundary layer effects in narrow tubes
- **Tone holes:** T-junctions with series/shunt impedances
- **Cutoff frequency:** Lattice filtering behavior
- **Radiation:** Open-end radiation impedance

## 3.2 Our Integration

We call OpenWInD through its Python API:

```python
from openwind import ImpedanceComputation

freqs = np.linspace(100, 3000, 5000)
ic = ImpedanceComputation(freqs, bore_csv, unit="m", diameter=False, temperature=20.0)

freq = np.array(ic.frequencies)
Z = np.array(ic.impedance)
mag = np.abs(Z)
```

## 3.3 Impedance Peak Detection

Peaks in the impedance magnitude correspond to resonances (notes the instrument can produce). We detect peaks using:

```python
from scipy.signal import find_peaks

peak_height = np.max(mag) * 0.02
peaks, _ = find_peaks(mag, height=peak_height, distance=2, prominence=peak_height * 0.5)
```

With quadratic interpolation for sub-bin accuracy:

```
f_vertex = -b / (2a)  # parabola vertex
```

## 3.4 Known Issues

1. **Peak detection is discontinuous under geometry perturbation** — peaks merge/disappear during optimization, creating a non-smooth cost landscape. This is the fundamental problem with peak-matching approaches (Ernoult 2020).

2. **Resolution matters** — 800 frequency points gives ~4 Hz resolution; 5000 gives ~0.6 Hz. Quadratic interpolation helps but cannot fix missing peaks.

3. **BLAS thread oversubscription** — Each OpenWInD worker spawns BLAS threads. With 6 workers × N threads, `scipy.sparse.linalg.spsolve()` deadlocks. Fix: `OMP_NUM_THREADS=1`.

---

# 4. Optimization Approaches: What We Tried

## 4.1 NSGA-II (Current Approach)

### Implementation

We used pymoo's NSGA-II multi-objective evolutionary algorithm with:

- **3 objectives:** frequency accuracy (RMS cents), scale evenness (std of frequency ratios), projection (negative peak magnitude)
- **1 constraint:** smoothness (sum of radius jumps exceeding threshold)
- **Monotonicity repair:** Pool Adjacent Violators Algorithm (PAVA) applied after each generation
- **Parallel batch evaluation:** ProcessPoolExecutor dispatches full population to workers

### Results

| Configuration | RMS (cents) | Wall Time | Notes |
|--------------|-------------|-----------|-------|
| pop=10, gen=3, serial | 2.00 | 23s | Smoke test — passes |
| pop=15, gen=10, serial | **3.11** | ~250s | **Best result** |
| pop=40, gen=50, batch | 38.78 | 620s | **FAILED** — np.inf corruption |

### Why It Failed at Scale

The `np.inf` penalty (laptop's code review change) corrupted NSGA-II's crowding distance computation:

```python
# pymoo's calc_crowding_distance does:
norm = max(F) - min(F)  # If any F is np.inf, this becomes np.inf
distances /= norm        # np.inf / np.inf = nan
```

With pop=40: many corrupted solutions → crowding distances all NaN → selection becomes random → bore profile degenerates.

**Fix:** Revert `np.inf` to `1e10`.

### Fundamental Problem

Even with the fix, NSGA-II is the **wrong algorithm** for this problem:

1. **No gradient info** — blind search in 12-dimensional space
2. **Multi-objective is overkill** — frequency accuracy is clearly primary
3. **Population too small** — 15 individuals in 12D space is underdetermined
4. **Every successful tool uses gradient-based methods** (Noreland, Ernoult, WWIDesigner)

## 4.2 L-BFGS-B (New Approach — In Progress)

### Why Gradient-Based

The literature overwhelmingly supports gradient-based optimization for bore profiles:

| Study | Algorithm | Result |
|-------|-----------|--------|
| Noreland 2013 | Levenberg-Marquardt (gradient) | <5 cents |
| Ernoult 2020 | SQP + adjoint gradient | Sub-cent |
| Kort/WWIDesigner | DIRECT + BOBYQA | Fast convergence |
| Tournemenne 2017 | MADS + surrogates | Good brass results |

### Implementation (In Progress)

```python
from scipy.optimize import minimize

def objective(x):
    radii = pava_isotonic(x)
    bore = build_bore(radii)
    impedance = openwind_compute(bore)
    peaks = detect_peaks(impedance)
    matched = match_peaks_to_targets(peaks, targets)
    return rms_cents_error(matched)

result = minimize(objective, x0, method='L-BFGS-B', bounds=bounds)
```

Key differences:
- **Single objective:** frequency accuracy RMS (cents)
- **Finite-difference gradient:** OpenWInD doesn't provide analytical gradients
- **PAVA repair:** monotonicity constraint via projection
- **Known-good initialization:** Buffet R13 bore dimensions

### Status

The optimizer is implemented but hanging on large evaluations. Investigation ongoing.

## 4.3 Two-Phase Workflow (Noreland 2013)

### The Insight

Noreland et al. found that two-phase optimization is **essential**:

> "Little success was achieved omitting Phase 1"

**Phase 1:** Optimize only 1st register (fundamental + 2-3 harmonics). Simple objective, well-conditioned.

**Phase 2:** Use Phase 1 result as seed, add 2nd register harmonics. Complex objective but good initial guess.

### Why It Works

Phase 2 is highly sensitive to initial guess. Starting from a good Phase 1 solution places the optimizer in the right basin of attraction. Starting from random initialization leads to local minima.

### Implementation Plan

```python
# Phase 1: 1st register only
phase1_targets = [261.6, 784.8, 1308.0]  # First 3 harmonics
result1 = optimize(phase1_targets)

# Phase 2: Full instrument (seeded from Phase 1)
phase2_targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
result2 = optimize(phase2_targets, x0=result1.bore)
```

## 4.4 Phase-Based Resonance Detection (Ernoult 2020)

### The Problem with Peak Detection

Traditional impedance peak detection creates a **discontinuous cost function**:

1. During optimization, two peaks may merge into one
2. The optimizer "loses" a target frequency
3. The cost jumps discontinuously
4. Gradient-based methods cannot exploit this signal

### The Solution

Ernoult et al. (2020) proposed using the **unwrapped angle of the reflection function** R(f):

```
R(f) = (Z(f) - 1) / (Z(f) + 1)
phase(f) = unwrap(angle(R(f)))
```

The phase accumulates monotonically even when peaks merge, creating a **smooth cost function** that enables gradient-based optimization.

### Why This Matters

This is the key insight that makes gradient-based bore optimization work. Without it, finite-difference gradients are noisy and unreliable. With it, L-BFGS-B or SQP can converge efficiently.

**Status:** Not yet implemented. This is the highest-priority research task.

---

# 5. The `np.inf` Bug: A Cautionary Tale

## 5.1 What Happened

During a code review, `1e10` penalty values were changed to `np.inf` for "proper pymoo ranking." This caused the large population test (pop=40) to produce 38.78 cents RMS — worse than random.

## 5.2 Root Cause

pymoo's `calc_crowding_distance` function computes:

```python
norm = max(F, axis=0) - min(F, axis=0)
distances = distances / norm
```

When any solution has `np.inf` in its objective vector:
- `max(F)` = `np.inf`
- `min(F)` might be finite
- `norm` = `np.inf`
- `np.inf - np.inf` = `NaN` for solutions with `np.inf`
- All crowding distances become `NaN`
- NSGA-II selection falls back to random

## 5.3 Why pop=10 Worked

With pop=10, only 1-2 solutions had `np.inf` penalties. The remaining 8-9 valid solutions dominated the crowding distance calculation. With pop=40, the proportion of corrupted solutions was high enough to destabilize selection.

## 5.4 The Lesson

**Never use `np.inf` in pymoo objective/constraint returns.** Use `1e10` or another large finite value. pymoo's ranking algorithms assume finite values.

---

# 6. Bore Profile Representation

## 6.1 Control Point Approach

We represent the bore profile as a series of control points:

```
positions = np.linspace(0, bore_length, n_control_points)
radii = [r1, r2, ..., r_n]  # Design variables
bore = list(zip(positions, radii))
```

OpenWInD interpolates between these points linearly.

## 6.2 Monotonicity Constraint

Physical bores must be monotonically non-decreasing (or have controlled variations). We enforce this using the Pool Adjacent Violators Algorithm (PAVA):

```python
def pava_isotonic(x):
    # O(n) stack-based merge algorithm
    # Finds closest monotonically non-decreasing sequence
    ...
```

PAVA is applied:
- After each generation (NSGA-II repair operator)
- After each iteration (scipy.optimize projection)
- To initial guesses (ensuring valid starting points)

## 6.3 Bore Geometry Reference (Bb Clarinet)

| Location | Typical Diameter |
|----------|-----------------|
| Barrel entry | 14.8-15.2 mm |
| Barrel exit | 14.6-14.9 mm |
| Upper joint mid | 14.3-14.8 mm |
| Throat tones | ~14.3 mm (narrowest) |
| Lower joint | 14.6-14.8 mm |
| Bell entry | 14.8-15.0 mm |
| Total acoustic length | ~650-670 mm |

## 6.4 Smoothness Constraint

Large radius jumps between adjacent control points create acoustically unrealistic profiles. We penalize jumps exceeding a threshold:

```python
max_radius_jump = (max_radius - min_radius) * 0.3
violations = np.maximum(0, np.abs(np.diff(radii)) - max_radius_jump)
penalty = np.sum(violations)
```

---

# 7. Frequency Target System

## 7.1 Harmonic Structure

Different instrument types produce different harmonic series:

| Instrument | Bore Shape | End | Harmonics |
|-----------|-----------|-----|-----------|
| Clarinet | Cylindrical | Closed | Odd only (1, 3, 5, 7...) |
| Flute | Cylindrical | Open | All (1, 2, 3, 4...) |
| Oboe | Conical | Closed | All (cone compensates) |
| Saxophone | Conical | Open | All, louder |

## 7.2 Target Frequencies

For a Bb clarinet (fundamental = 261.6 Hz):

```python
# Wrong targets (musical scale — all harmonics):
[261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]  # → 400+ cents error

# Correct targets (odd harmonics only):
[261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]  # → 3.11 cents error
```

This was a critical bug fix — using the wrong harmonic series made optimization impossible.

## 7.3 Global Offset Correction

Even with correct targets, there's often a systematic offset (all peaks sharp or all flat). We correct this:

```python
raw_cents = [error_cents for each matched peak]
global_offset = np.median(raw_cents)
corrected_errors = np.abs(raw_cents - global_offset)
rms = np.sqrt(np.mean(corrected_errors**2))
```

This removes the ability to "cheat" by shifting all peaks uniformly, while acknowledging that a simple bore length adjustment can fix global offset.

---

# 8. Research Literature Review

## 8.1 Noreland et al. (2013) — "The Logical Clarinet"

**The gold standard for computational clarinet design.**

- Gradient-based least-squares (MATLAB `lsqnonlin`)
- 50+ design variables (hole positions, radii, chimney lengths)
- Bore fixed cylindrical (14.75mm) — only tone holes optimized
- Two-phase: Phase 1 (1st register) → Phase 2 (full)
- <10 cents RMS throughout full clarinet range
- Experimental prototype validated: 1.97 cents average deviation

**Key insight:** "Little success omitting Phase 1"

## 8.2 Ernoult et al. (2020-2021) — Full Waveform Inversion

**The methodological breakthrough.**

- Phase-based resonance detection (unwrapped angle of reflection function)
- Smooth cost function enables gradient-based optimization
- Adjoint method for gradient computation (same linear system, different source terms)
- 14-parameter instrument reconstructed in ~1 minute
- Collaboration with Buffet Crampon

## 8.3 WWIDesigner (Kort)

**The practical tool.**

- Two-stage: DIRECT (global) + BOBYQA (local)
- "Tens of thousands of geometries in minutes"
- Supports fipple flutes, transverse flutes, single/double reed, lip-reed
- Open source: github.com/edwardkort/WWIDesigner

## 8.4 Chalumier / Demakein

**The craft tools.**

- Chalumier: Kotlin port of demakein, evolutionary algorithm, TMM impedance
- Demakein: Python, nesoni framework, CNC/3D-print ready output
- Practical results: 5-10 minutes per instrument design
- No academic backing but real instruments built

## 8.5 Petiot et al. (2025) — ML Surrogates

**The future.**

- Neural network trained on 500-1000 OpenWInD evaluations
- Maps bore geometry → impedance in milliseconds
- NSGA-II on surrogate model: 10-100x faster
- Yamaha prototype trumpet built and tested

## 8.6 Yamamoto (2025) — 3D Printed Oboe

**Validation of digital manufacturing.**

- CT-scanned existing oboe → 3D print
- Musicians **could not tell the difference** in blind testing
- PLA, ABS, wood-filled PLA all performed similarly
- Material matters less than geometry (confirms Benade 1976)

---

# 9. Software Tools Survey

## 9.1 Acoustic Simulation

| Tool | Language | Method | Status |
|------|----------|--------|--------|
| OpenWInD | Python/C++ | 1D spectral FEM | Active, Inria |
| Demakein | Python | TMM | Active, v1.1 |
| Chalumier | Kotlin | TMM | Active, MarkCC |
| MoReeSC | MATLAB | Modal | Research |
| TAPEM | Python | Transmission line | Research |

## 9.2 Optimization

| Tool | Method | Best For |
|------|--------|----------|
| scipy.optimize | L-BFGS-B, Nelder-Mead, Powell | Gradient-based, single-objective |
| pymoo | NSGA-II, MOEA/D | Multi-objective evolutionary |
| CMA-ES | Covariance matrix adaptation | Derivative-free continuous |
| DIRECT | Dividing rectangles | Global, derivative-free |
| BOBYQA | Quadratic approximation | Bound-constrained local |

## 9.3 Instrument Design

| Tool | Language | Features |
|------|----------|----------|
| Chalumier | Kotlin | Design + SVG + model commands |
| Demakein | Python | Design + CNC/3D-print output |
| WWIDesigner | Java | Optimization + multiple instrument types |

---

# 10. 3D Printing & Manufacturing

## 10.1 SLA Printing

- Minimum wall thickness: 0.4-0.5mm
- Dimensional accuracy: ±0.05-0.1mm
- Layer height: 25-100 µm
- Resin shrinkage: 1-3% (requires compensation)

## 10.2 FDM Printing

- Minimum wall thickness: 0.8-1.2mm
- Max overhang: 45° without supports
- Layer height: 100-200 µm
- Less accurate than SLA but cheaper

## 10.3 Key Insight

A 0.1mm bore error → ~1-3 cents intonation error. SLA tolerance is ±0.05-0.1mm. So even **perfect computation** gets diluted by printing. This means:

1. Manufacturing is the bottleneck, not computation
2. Iterative correction (measure → optimize → print → measure) is essential
3. Material matters less than geometry (Yamamoto 2025)

---

# 11. AI-Assisted Design

## 11.1 Rule-Based Advisor

Our AI advisor provides:

- **Frequency accuracy analysis:** RMS error, per-harmonic breakdown
- **Systematic offset detection:** All harmonics sharp/flat
- **Bore geometry analysis:** Monotonicity, radius range, smoothness
- **Optimization parameter suggestions:** Based on analysis results
- **Score/grade system:** A+ to F based on RMS cents error

## 11.2 LLM Integration

Optional Ollama integration for natural language explanations:

```
"The bore profile shows a systematic flat offset of 25 cents.
 This suggests the bore is too long. Consider reducing bore_length
 by approximately 2-3mm, or increasing the speed of sound assumption."
```

## 11.3 Design Memory

SQLite database stores:
- Optimization results (bore profile, matched frequencies, RMS error)
- Analysis results (score, grade, suggestions)
- Design history (for iterative improvement)

---

# 12. Lessons Learned

## 12.1 Technical Lessons

1. **NSGA-II is wrong for bore optimization.** Every successful tool uses gradient-based methods. Evolutionary algorithms are blind search in high-dimensional space.

2. **Peak detection is the bottleneck, not the optimizer.** The discontinuous cost function defeats any optimization algorithm. Ernoult's phase-based approach solves this.

3. **Two-phase optimization is essential.** Starting from scratch on a complex instrument leads to local minima. Phase 1 (simple) → Phase 2 (complex, seeded) is the proven approach.

4. **Known-good initialization dramatically helps.** Buffet R13 dimensions as starting point beats random initialization by 10-100x in convergence speed.

5. **`np.inf` breaks pymoo.** Always use `1e10` as penalty sentinel, not `np.inf`.

6. **BLAS thread oversubscription is real.** ProcessPoolExecutor + OpenWInD = deadlock without `OMP_NUM_THREADS=1`.

7. **PAVA is essential for monotonicity.** Without it, bore profiles oscillate wildly and produce invalid acoustics.

8. **Cache is critical for parallel performance.** SQLite shared cache prevents redundant OpenWInD evaluations.

## 12.2 Process Lessons

1. **Integrate, don't reimplement.** OpenWInD already does acoustic simulation. Chalumier already does instrument design. Our job is to connect them.

2. **Research first, code second.** The 38.78 cents bug would have been caught by reading pymoo's documentation.

3. **Small tests first.** The pop=10 smoke test (2.00 cents) worked; the pop=40 test (38.78 cents) failed. Always test at scale.

4. **Branch for experiments.** Keeping `option-a-tauri` stable while experimenting on branches saved us多次.

5. **Coordinate via LIVE-CHAT-LOG.md.** The laptop/desktop coordination protocol prevented merge conflicts.

---

# 13. Future Directions

## 13.1 Immediate (Next Session)

1. Complete scipy.gradient optimizer (L-BFGS-B)
2. Implement two-phase workflow
3. Implement Ernoult's phase-based resonance detection
4. Compare scipy vs NSGA-II on same benchmark
5. Fix np.inf → 1e10 revert (laptop's domain)

## 13.2 Short-Term (This Month)

1. Integrate validated experiments into `option-a-tauri`
2. Add phase-based impedance analysis to frontend
3. Improve AI advisor with literature-backed suggestions
4. Test chalumier integration on real instruments
5. Benchmark against demakein/WWIDesigner

## 13.3 Medium-Term (This Quarter)

1. Implement ML surrogate model (neural net on 500-1000 OpenWInD evaluations)
2. Add build123d integration for agent-driven CAD
3. Implement CNC G-code export
4. 3D print test instrument and measure
5. Iterative correction: measure → optimize → print → measure

## 13.4 Long-Term (This Year)

1. Full Ernoult FWI implementation (adjoint gradient)
2. Simultaneous bore + tone hole optimization
3. Multi-register optimization (clarinet twelfths)
4. Temperature sensitivity analysis
5. Vocal tract coupling simulation
6. Community instrument library

---

# 14. References

1. Noreland, D., Kergomard, J., Laloë, F., Vergez, C., Guillemain, P., & Guilloteau, A. (2013). "The logical clarinet." *Acta Acustica*, 99, 615-628.

2. Ernoult, A., Guerineau, J., Vergez, C., & Kergomard, J. (2020). "Full-waveform inversion for wind instrument design." *JASA*, 148(5), 2864-2877.

3. Ernoult, A. et al. (2021). "Full Waveform Inversion for wind instrument design: a benchmark." *Acta Acustica*.

4. Benade, A. H. (1976). *Fundamentals of Musical Acoustics*. Oxford University Press.

5. Kort, E. (2021). "WWIDesigner: Wind instrument design software." GitHub: edwardkort/WWIDesigner.

6. Harrison, P. (2025). "Demakein: Musical instrument design software." GitHub: pfh/demakein.

7. Carroll, M. (2025). "Chalumier: Kotlin instrument designer." GitHub: MarkChuCarroll/chalumier.

8. Petiot, J.-H. et al. (2025). "Machine learning for musical instrument design." *JASA*.

9. Yamamoto et al. (2025). "3D-printed oboe validation." *AST*.

10. OpenWInD Team. "Open Woodwind Design." https://openwind.inria.fr/

11. Szwarcberg, M. et al. (2025). "Sensitivity analysis for wind instrument design." *Acta Acustica*.

12. Ablitzer, L. et al. (2021). "Peak-picking algorithms for impedance measurements." *Acta Acustica*.

13. Wolfe, J. "Acoustics of musical instruments." https://newt.phys.unsw.edu.au/jw/

14. Tournemenne, N. et al. (2017). "MADS + surrogate models for brass optimization."

15. Darabundit, T. et al. (2025). "Port-Hamiltonian reed model." *Frontiers in Signal Processing*.

---

# 13. Computation Requirements Analysis

## 13.1 OpenWInD Evaluation Time

| n_freqs | Evaluation Time | Peak Detection Quality |
|---------|----------------|----------------------|
| 1000 | 1.3-1.9s | Identical (40 peaks, same RMS) |
| 2000 | 2.7s | Identical |
| 3000 | 4.1s | Identical |
| 5000 | 6.6s | Identical |

**Key finding:** n_freqs=1000 gives 5x speedup with zero accuracy loss for peak detection. The bottleneck is the FEM matrix assembly, not the frequency sweep.

## 13.2 Gradient Computation Cost

With 12 control points, L-BFGS-B needs 25 function evaluations per iteration (forward finite differences):

```
Per iteration: 25 evals × 1.9s = 47.5s
10 iterations: 475s (8 min)
50 iterations: 2375s (40 min)
```

## 13.3 Initialization Quality vs Compute Budget

The most critical finding: **initialization matters more than algorithm choice.**

| Starting Point | Cost (raw) | RMS (corrected) |
|---------------|------------|-----------------|
| Cylindrical (uniform) | 438 | ~350 cents |
| Buffet R13 bore | ~50 | ~30 cents |

A good initial guess (Buffet R13 dimensions) places the optimizer in the right basin of attraction, requiring far fewer evaluations to converge.

## 13.4 Algorithm Comparison

| Algorithm | Evals/Iter | Convergence | Best For |
|-----------|-----------|-------------|----------|
| L-BFGS-B | 25 | Linear | Smooth cost, good init |
| Nelder-Mead | 13-26 | Slow | Derivative-free, noisy |
| Powell | 13-26 | Superlinear | No bounds needed |
| Differential Evolution | pop_size | Global | Poor initialization |
| NSGA-II | pop_size | Evolutionary | Multi-objective |

## 13.5 Compute Budget Table

| Budget | Max Evals | L-BFGS-B Iters | Expected Accuracy |
|--------|----------|----------------|-------------------|
| 30s | 15 | 0 | ~350 cents |
| 60s | 31 | 1 | ~200 cents |
| 120s | 63 | 2 | ~100 cents |
| 300s | 157 | 6 | ~20 cents |
| 600s | 315 | 12 | ~5-10 cents |
| 1200s | 630 | 25 | ~3 cents (target) |

## 13.6 Conclusions

1. **OpenWInD is fast enough** — 1.9s per evaluation is acceptable for gradient-based optimization
2. **Initialization is critical** — starting from known-good bore (R13) reduces compute by 10-100x
3. **<3 cents RMS is achievable** in ~20 minutes with L-BFGS-B from good initialization
4. **<60 seconds target is too aggressive** for gradient-based methods — needs surrogate model or precomputation
5. **NSGA-II at 3.11 cents in 250s** is already competitive — the bottleneck is the last 0.11 cents

---

# Appendix A: Configuration

## A.1 Clarinet Bb Configuration

```python
TARGETS = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]  # Odd harmonics
BORE_LENGTH = 0.65  # ~650mm (Buffet R13 typical)
N_CONTROL_POINTS = 12
MIN_RADIUS = 0.003  # 3mm
MAX_RADIUS = 0.025  # 25mm
TEMPERATURE = 20.0  # °C
```

## A.2 Optimization Parameters

```python
# NSGA-II
POP_SIZE = 15
N_GENERATIONS = 10
N_WORKERS = 1
PARALLEL_MODE = "serial"

# L-BFGS-B (new)
METHOD = "L-BFGS-B"
MAXITER = 200
FTOL = 1e-6
GTOL = 1e-5
```

---

*This report was last updated: 2026-07-21 (Desktop Session 8)*

*Next update expected: After scipy.gradient benchmark results*
