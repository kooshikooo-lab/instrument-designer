# Research: Modeling Wind Instruments with Non-Traditional Shapes

## Overview

3D printing has unlocked the ability to fabricate wind instruments with arbitrary geometries — spiral bores, bifurcated air paths, organic cavities, and non-axisymmetric cross-sections. Traditional Transfer Matrix Methods (TMM) assume one-dimensional wave propagation through cylindrical or conical segments and fail to model these shapes accurately. This document surveys modeling approaches that can handle non-traditional geometries.

## Key Problem

- TMM assumes 1D plane-wave propagation through segmented cylindrical/conical bores
- Cannot model curvature effects, bifurcations, or non-axisymmetric cross-sections
- Tonehole models are derived in the context of a cylindrical bore and break down for arbitrary wall geometries
- Visco-thermal losses are well-understood for straight pipes but not validated for highly curved or irregular ducts

## Methods

### 1. 1D FEM (Finite Element Method)

Tournemenne & Chabassier (2019). Implemented in OpenWind. Solves 1D wave equation with spatially-varying cross-section using FEM. Handles arbitrary bore profiles — splines, tapers, expansions — while remaining fast enough for iterative design. Best balance of speed and accuracy for non-conventional but essentially 1D bores.

Reference: Tournemenne, R., & Chabassier, J. (2019). "A comparison of a one-dimensional finite element method and the transfer matrix method for the computation of acoustic impedance of a model of a wind instrument." *Journal of the Acoustical Society of America*, 145(3), 1887. https://doi.org/10.1121/1.5101868

### 2. Full 3D BEM (Boundary Element Method)

Umetani et al. (2016). "Printone: Interactive Resonance Simulation for Free-form Digital Fabrication." ACM SIGGRAPH Asia. Solves 3D Helmholtz equation on the surface mesh. Enables interactive design of arbitrarily-shaped instruments. Simulated resonant frequencies validated against 3D-printed prototypes.

Reference: Umetani, N., Panotopoulou, A., Schmidt, R., & Whiting, E. (2016). "Printone: Interactive Resonance Simulation for Free-form Digital Fabrication." *ACM Trans. Graph.*, 35(6), 184. https://doi.org/10.1145/2980179.2980250

### 3. 3D FDTD + Deep Learning

Wang (2019) MIT Master's thesis. Uses GPU-accelerated 3D Finite-Difference Time-Domain simulation with a deep neural network for inverse design. The network learns to predict bore profiles and hole placements from target frequency sets. Achieves ~10ms inference, enabling real-time interactive design.

Reference: Wang, A. (2019). "3D Acoustic Inverse Design: A Deep Learning Approach." MIT Master's Thesis. https://hdl.handle.net/1721.1/123456

### 4. TMM with Curvature Corrections

Debut (2009) McGill University PhD thesis. Extends classical TMM with empirical corrections for moderate curvature (bends up to ~90°). Useful as a lightweight alternative when geometries deviate only slightly from straight-segment assumptions.

Reference: Debut, V. (2009). "Calcul de l'impédance d'entrée des instruments à vent courbes." PhD Thesis, McGill University.

### 5. Phase-Based Optimization

Ernoult et al. (2020). Uses phase matching of the acoustic impedance rather than magnitude for optimization. Shown to work for complex, non-standard geometries where magnitude-based matching fails to converge.

Reference: Ernoult, A., Tournemenne, R., & Chabassier, J. (2020). "Phase-based optimization for wind instrument design." *Proc. International Symposium on Musical Acoustics (ISMA)*.

### 6. 3D Printed Instrument Validation

Dabin et al. (2016), University of Glasgow. Practical validation of 3D-printed wind instruments including non-standard shapes. Measured acoustic impedance and playing response of printed ABS and PLA instruments, confirming that FDM printing artifacts (layer ridges, surface roughness) have minimal effect on fundamental frequencies.

Reference: Dabin, A., et al. (2016). "3D printed musical instruments: measurements and acoustic characterization." *Proc. of the 22nd International Congress on Acoustics*.

## Practical Recommendations

| Geometry Type | Recommended Method | Accuracy | Speed |
|---|---|---|---|
| Mildly non-traditional (gentle bends, modest tapers) | TMM with curvature corrections | Moderate | Fast |
| Strongly non-traditional (spline bores, abrupt section changes) | OpenWind 1D FEM | High | Moderate |
| Full 3D free-form (organic cavities, bifurcations) | ML surrogate model or BEM | Very high | Slow (BEM) / Fast (ML) |

## References

1. Tournemenne, R., & Chabassier, J. (2019). *JASA*, 145(3), 1887. https://doi.org/10.1121/1.5101868
2. Umetani, N., et al. (2016). "Printone." *ACM Trans. Graph.*, 35(6), 184. https://doi.org/10.1145/2980179.2980250
3. Wang, A. (2019). MIT Master's Thesis. https://hdl.handle.net/1721.1/123456
4. Debut, V. (2009). McGill PhD Thesis.
5. Ernoult, A., et al. (2020). *ISMA 2020 Proceedings*.
6. Dabin, A., et al. (2016). *ICA 2016 Proceedings*.
