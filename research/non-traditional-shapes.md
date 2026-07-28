# Research: Modeling Wind Instruments with Non-Traditional Shapes

## Overview

Traditional wind instruments use cylindrical or conical bores with simple tone holes. Modern additive manufacturing (3D printing) enables arbitrary geometries — spiral bores, bifurcated paths, organic cavities, variable cross-sections. This document summarizes computational methods for modeling and optimizing such instruments.

## Key Problem

Standard TMM (Transfer Matrix Method) assumes 1D wave propagation through cylindrical or conical segments. For arbitrary shapes:
- TMM cannot handle curvature, bifurcations, or non-axisymmetric cross-sections
- Viscothermal loss formulas are only exact for cylinders (approximate for cones, wrong for arbitrary shapes)
- Tonehole models assume cylindrical bore context

## Methods

### 1. 1D FEM (Finite Element Method) — Best balance of speed and accuracy

**Paper:** Tournemenne & Chabassier (2019), Acta Acustica
**Tool:** OpenWind (open-source Python)

Solves the same wave equations as TMM but discretizes using 1D finite elements instead of analytical transfer matrices.

**Advantages over TMM:**
- Handles arbitrary bore profiles (no equivalent radius approximation needed)
- Viscothermal losses computed correctly for any shape
- Frequency-domain formulation naturally handles discontinuities
- Pressure and volume flow available along entire bore axis

**Performance:** Slightly slower than TMM for simple geometries, but more efficient for a given accuracy target on realistic instruments (e.g., trumpet with 33 conical sections).

**Relevance to us:** We already use OpenWind. This confirms 1D FEM is the right path for non-cylindrical bores.

### 2. Full 3D BEM (Boundary Element Method) — Interactive free-form design

**Paper:** Umetani et al. (2016), "Printone" — ACM SIGGRAPH

Models instruments as passive 3D acoustic resonators. Uses boundary element method to compute resonance frequencies.

**Key innovations:**
- Resonance formulated as nonlinear minimum eigenvalue problem
- Generalized eigenvalue problem for fast approximate resonance estimation
- Sensitivity-based first-order estimation for real-time feedback (>30 FPS)
- AutoTune: automatic hole size optimization via Newton-Raphson

**Demonstrated on:** Star-shaped instruments, bunny-shaped instruments, cube instruments — all playable after 3D printing.

**Limitation:** Only optimizes fundamental frequency, not timbre/harmonics. Interactive, not automated optimization.

**Relevance to us:** Shows full 3D simulation is feasible for interactive design. Could complement our TMM optimizer for truly free-form shapes.

### 3. 3D FDTD + Deep Learning — Full 3D with ML inverse design

**Paper:** Wang (2019), MIT thesis

GPU-accelerated 3D Finite Difference Time Domain simulation of wind instruments.

**Key innovations:**
- CUDA-accelerated 3D FDTD for real-time acoustic simulation
- Deep learning solves the inverse problem: desired sound → 3D shape
- Automatic pitch hole placement for any bore geometry
- Optimizes for fundamental frequency AND overtone series

**Performance:** ~3 sounds/second on 4x GTX 1080 Ti GPUs. Training data generated via random spline bore profiles.

**Demonstrated on:** Spline-based extrusions, pentatonic scale instruments.

**Limitation:** 1D design domain (spline extrusions only). Doesn't exploit full 3D freedom.

**Relevance to us:** Shows ML can solve the inverse design problem. Could train a surrogate model on our TMM data.

### 4. TMM with Curvature Corrections — Extended classical approach

**Source:** McGill thesis (Debut, 2009), multiple papers

Investigates how bore curvature affects acoustics:
- Rayleigh (1945): Curved tube ≈ straight tube of same center-line length
- Nederveen (1998): Curved tube appears shorter and wider
- FEM shows curvature effect is frequency-dependent and more complex than simplified theories predict

**Key finding:** For moderate curvature, TMM with length corrections works. For strong curvature, full 2D/3D simulation required.

**Relevance to us:** Our TMM can handle mildly curved bores with corrections. Strongly curved bores need FEM.

### 5. Phase-Based Optimization for Complex Geometries

**Paper:** Ernoult et al. (2020), JASA

Uses unwrapped phase of the reflection function instead of peak detection for resonance identification.

**Advantage:** Phase is smooth and continuous, unlike peak-based metrics which are discontinuous. This enables gradient-based optimization even for complex impedance profiles with secondary resonances.

**Demonstrated on:** Key-less pentatonic clarinet with 38 design variables.

**Relevance to us:** We already use phase_cost(). This confirms the approach works for complex geometries.

### 6. 3D Printed Instruments — Practical validation

**Papers:**
- Dabin et al. (2016): Microtonal flutes via 3D printing (FDM + Polyjet)
- Titanium flute study (2020): Ti-AM for wind instruments, "richer" sound
- Glasgow University: 3D printed clarinet for 19-TET

**Key findings:**
- FDM insufficient for fine acoustic features (layer resolution 0.254mm)
- Polyjet/EBM much better (0.016mm resolution, gas-tit walls)
- Material affects timbre: titanium produces "richer" harmonics than polymer
- Surface finish matters: polishing inner bore improves acoustics

**Relevance to us:** CadQuery export already produces STL. Need to consider printer resolution in constraint scoring.

## Practical Recommendations for Our Platform

### For mildly non-traditional shapes (stepped bores, variable taper,弯曲):
- **Use our existing TMM** with 1D FEM fallback (OpenWind)
- Add curvature correction factors from Nederveen
- Phase-based optimization (already implemented)

### For strongly non-traditional shapes (bifurcations, organic cavities):
- **Use OpenWind 1D FEM** as primary solver
- For truly 3D shapes: integrate BEM solver (like Printone's approach)
- Consider GPU-accelerated FDTD for validation

### For full 3D free-form design:
- **ML surrogate model** trained on TMM/FEM data for fast evaluation
- BEM for interactive design feedback
- FDTD for final validation

### For inverse design (sound → shape):
- **Deep learning approach** from Wang (2019)
- Train on our 12-instrument benchmark data
- Output: bore profile + hole positions for arbitrary target spectra

## References

1. Tournemenne & Chabassier (2019). "A comparison of a 1D FEM and TMM for wind instrument impedance." Acta Acustica. https://doi.org/10.3813/aaa.919364
2. Umetani et al. (2016). "Printone: Interactive Resonance Simulation for Free-form Print-wind Instrument Design." ACM SIGGRAPH. https://doi.org/10.1145/2980179.2980250
3. Wang (2019). "Algorithmic design of wind instrument shape via 3D FDTD and deep learning." MIT. https://hdl.handle.net/1721.1/123116
4. Debut (2009). "Comparing Theory and Measurements of Woodwind-Like Instrument Acoustic Radiation." McGill. https://escholarship.mcgill.ca/concern/theses/sf268697f
5. Ernoult et al. (2020). "Woodwind instrument design optimization based on impedance characteristics with geometric constraints." HAL. https://hal.science/hal-02479433v1
6. Szwarcberg (2025). "Geometric sensitivity of modal parameters in wind instrument design." Acta Acustica. https://acta-acustica.edpsciences.org/articles/aacus/full_html/2025/01/aacus250082/aacus250082.html
7. Dabin et al. (2016). "3D Modelling and Printing of Microtonal Flutes." Zenodo. https://doi.org/10.5281/zenodo.1176013
8. Titanium 3D-printed flute (2020). Academia. https://www.academia.edu/110186125/
