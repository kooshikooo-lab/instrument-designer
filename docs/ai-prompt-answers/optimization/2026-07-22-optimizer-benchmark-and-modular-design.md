# Session Log: Optimizer Benchmarking, Tone Holes & Modular Design
**Date:** 2026-07-22 (continued)
**Branch:** `experiment/tmm-improvements`
**Commits:** `122ab6f` (modular components + benchmarks)

---

## What Happened This Session

### 1. UI Design Branches (Completed)
Created 3 UI design branches for human evaluation:
- `ui/card-design` — Card-based with gradients, AI illustrations, sound player, spectrum analyzer
- `ui/magazine-design` — Editorial magazine-style layout
- `ui/wiki-design` — Minimal monospace wiki with collapsible sections
All pushed to GitHub.

### 2. Chalumeau & Bass Chalumeau Benchmark (Initial)
**Bug found:** The baseline optimizer showed "Holes: 0" — tone holes were never passed to the optimizer constructor. Fixed by adding `hole_positions`, `hole_diameters`, `hole_lengths` keyword arguments.

**Initial results (broken — holes fixed but strategy wrong):**
| Instrument | RMS (cents) | Notes |
|---|---|---|
| Chalumeau C | 198 | Notes jumping to wrong register |
| Bass chalumeau Bb | 811 | Complete chaos |
| Soprano sax Bb | 372 | |
| Alto sax Eb | 75 | Best — bore-to-frequency ratio correct |

### 3. Diatonic Scale Prototype Concept
User proposed: confirm acoustic design on diatonic instruments first, then extend to chromatic. Apply same approach across families (chalumeau → sax → clarinet). Bass chalumeau as prototype for bass clarinet.

### 4. Modular Component System (`modular_components.py`)
Built comprehensive modular instrument design system:
- **Components:** BoreSection, Bell, Neck, Extension, Joint, Mouthpiece
- **Connections:** TenonConnection with cork/friction/threaded/slip types
- **KeyHole model:** ring, plateau, spatula types with pad sizes 7-26mm
- **InstrumentAssembly:** combines components, generates TMM config
- **PVC compatibility:** Schedule 40 cross-reference (3/4" = chalumeau, 1" = bass clarinet)
- **Pre-built assemblies:** chalumeau C, bass chalumeau Bb, bass clarinet Bb, soprano sax Bb

### 5. Bass Clarinet Keywork Research
Researched and modeled bass clarinet key system:
- 22-25 keys (Boehm system), 6 rings
- Key pad sizes: 7mm (register) to 26mm (low C bell key)
- Tone hole sizes: 8-10mm (upper) to 19-21mm (bell)
- Joint splitting for 3D printing (max 200mm per piece)
- Tenon dimensions: 25.7-26.0mm OD

### 6. Research Deep Dive — TMM Optimization with Tone Holes
Comprehensive research on optimization methods:

**Key findings from literature:**

| Source | Method | Key Insight |
|---|---|---|
| Noreland 2013 | Gradient-based L-BFGS-B | Sequential 3-step: single-register → dual-register → fine-tune. 0.49 cents RMS |
| Ernoult 2020 (Bordeaux) | Phase-based resonance + SQP | Unwrapped phase of reflection coefficient — smooth, differentiable. Industrial partner: Buffet Crampon |
| Guilloteau 2020 | Simultaneous bore+holes | 38 design variables for 8-hole pentatonic clarinet |
| WWIDesigner (Kort) | DIRECT-C global + BOBYQA local | 9 separate optimizers that can be chained. Empirical mouthpiece models |
| Demakein/Chalumier | Evolutionary | Good for exploration, slow for precision |
| Bordeaux group 2025 | Analytical gradients for TMM | Szwarcberg et al. — geometric sensitivity of modal parameters |

**Critical failure modes identified:**
1. **Local minima dependency** — 20 random starts gave 2 different solution types
2. **"Oblique valleys"** in cost function — optimizer jumps side-to-side
3. **Peak detection non-smoothness** — peaks appear/disappear with geometry changes
4. **Bore length fixed** — must be free variable
5. **Too many control points** — rule of thumb: 1 bore point per 2-3 holes
6. **Bore-to-frequency mismatch** — fundamental must be correct before holes matter

**Best practices:**
- Sequential is more robust than simultaneous
- Phase-based resonance (not peak detection)
- Bore length as free variable
- 3-5 bore control points for 6-8 holes
- PVC wall thickness (3-4mm) requires 20-50% larger holes than metal

### 7. Sequential Optimizer (Bordeaux Method)
Built `tmm_optimizer_sequential.py` implementing:
1. Phase 1: Bore length from all-closed fingering
2. Phase 2: Holes added bottom-to-top, one at a time
3. Phase 3: Simultaneous refinement

**First test result (chalumeau C): 54.5 cents RMS** — much better than 198 cents before!

### 8. Comprehensive Benchmark (Attempted)
Built `benchmark_all.py` testing Sequential vs Seq+Refine on 4 instruments.
**Problem:** Powell optimizer hangs (timeout after 10+ minutes on refinement phase).
Root cause: Powell's internal line search gets stuck in the high-dimensional space.

---

## Current State — What Needs Doing

### IMMEDIATE (Active Issues)
1. **Powell hangs on refinement** — The simultaneous refinement phase uses Powell on ~13 variables (6 bore + 7 holes) and gets stuck. Need to:
   - Use Nelder-Mead instead of Powell for refinement
   - Or reduce variables (optimize bore first, then holes, then bore again)
   - Or use differential_evolution for global search on small variable sets

2. **Sequential method gives 54.5 cents** — Good starting point but needs refinement to get below 3 cents. The refinement step is the bottleneck.

3. **Bass chalumeau not tested with sequential** — Only chalumeau C was tested. Need to run on all 4 instruments.

### MEDIUM TERM
4. **Integrate sequential optimizer into design_server.py** — Currently only the old L-BFGS-B is available via the API
5. **Add to target_frequencies.py and design_desk.py** — chalumeau, bass chalumeau presets
6. **Connect modular_components.py to TMM** — Use InstrumentAssembly.to_tmm_config() for optimization

### LONGER TERM
7. **Ernoult's phase-based resonance** — Replace peak-finding with unwrapped phase of reflection coefficient
8. **Empirical mouthpiece models** — WWIDesigner approach: separate mouthpiece from bore optimization
9. **Cross-fingering support** — Demakein-style but with better convergence
10. **3D printing validation** — Print optimized designs and measure actual intonation

---

## My Opinion on Algorithms

### What Works
1. **Sequential bore-then-holes (Bordeaux method)** — The single biggest improvement. Our initial approach (simultaneous optimization of everything) is fundamentally flawed for this problem.
2. **Powell + L-BFGS-B for bore-only** — Works well when bore length is free (1.2 cents on reedpipe).
3. **Multi-start** — Important for avoiding local minima, but expensive.

### What Doesn't Work (For Us)
1. **JAX autodiff on root-finding objectives** — `jnp.where` discontinuities break gradients. The JAX TMM forward pass is useful but not the backward pass.
2. **NSGA-II evolutionary** — Wrong algorithm for single-objective bore optimization. Every successful tool uses gradient-based.
3. **Powell on >10 variables** — Hangs or converges very slowly. Need Nelder-Mead or differential_evolution for higher dimensions.

### What We Should Try
1. **Nelder-Mead for refinement** — Simplex method, no gradients, handles moderate dimensions well
2. **differential_evolution** from scipy — Global search, parallelizable, good for 10-20 variables
3. **Trust Region Reflective** (scipy) — Best for least-squares formulation, used by Ernoult
4. **WWIDesigner's DIRECT-C + BOBYQA** — Global + local combo, proven on real instruments
5. **Empirical mouthpiece models** — Simplifies the problem by separating drive mechanism

### Key Insight from Research
The Bordeaux group's **phase-based resonance detection** (unwrapped phase of reflection coefficient) is the single most important algorithmic advance in the last decade. It replaces the non-smooth peak-detection with a smooth, differentiable function. This is what makes gradient-based optimization work reliably with tone holes. Our current resonance_phase function is close but not quite the same — we should implement their formulation.

---

## Files Created/Modified This Session
- `backend/benchmark_chalumeau.py` — Initial chalumeau benchmark (holes not passed)
- `backend/benchmark_diatonic.py` — Diatonic prototype benchmark
- `backend/benchmark_optimizers.py` — Multi-method benchmark (Powell hangs)
- `backend/benchmark_all.py` — All instruments, all methods (Powell hangs)
- `backend/test_sequential.py` — Quick sequential test (54.5 cents RMS)
- `backend/tmm_optimizer_sequential.py` — Sequential Bordeaux-method optimizer
- `backend/modular_components.py` — Modular instrument design system (1344 lines)

## Git History This Session
- `122ab6f` — feat: Diatonic prototype benchmark and modular instrument components
- UI branches: `ui/card-design`, `ui/magazine-design`, `ui/wiki-design` (all pushed)
