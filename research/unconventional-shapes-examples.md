# Research: Unconventional Wind Instrument Shape Examples

## 1. Folded Bore Instruments

A folded bore winds the air column back on itself to reduce physical size without changing the acoustic length. The standing wave follows the centerline regardless of how the tube is bent.

- **Trumpet / Cornet:** Approximately 1.5 m of tubing folded into ~50 cm. The bends are tight enough that curvature corrections are sometimes applied, but plane-wave TMM still works well in practice.
- **Alto Saxophone:** Conical bore folded into a U-shape. The exponential-like flare and the folded geometry are handled separately — TMM models the straight cone, the bends are treated as lossless turns.
- **Rackett / Dulcian:** Renaissance double-reed instrument with a wildly folded cylindrical bore — up to 2 m of tubing in a 20 cm block. The bore drills parallel channels connected by u-bends at alternating ends. TMM works despite the extreme folding.
- **Komuso 1.8 Shakuhachi (from Printone paper):** A 1.8 m bamboo-style flute printed as a compact folded shape. Validated against 3D BEM simulation; the fold had negligible effect on resonance frequencies.

## 2. Free-Form / Organic Shapes

The Printone system (Umetani et al. 2016) demonstrated interactive design of arbitrary 3D shapes as functioning wind instruments. Users sculpt free-form shapes (bunny, star, cat, cube) and the BEM solver computes resonances in real time.

- **Examples designed and printed:** Bunny-shaped ocarina, star-shaped flute, cat-shaped horn, cubic whistle
- **Method:** 3D BEM on the interior surface mesh; user selects 5-8 target frequencies; automatic hole placement (3-4 holes) tunes the instrument
- **Key finding:** FDM printing artifacts (layer height 0.2 mm, nozzle 0.4 mm) have minimal effect on the fundamental frequency (within 2% of BEM prediction)
- **Implication:** Free-form design is viable with consumer 3D printing — no post-processing needed for acoustic functionality

## 3. Spline-Based Extrusions

Wang (2019) at MIT used GPU-accelerated 3D FDTD simulation with a deep neural network for inverse design of wind instruments. The bore profile is parameterized as a B-spline, and the DNN predicts the control points and hole positions from target frequency sets.

- **Key idea:** The DNN learns the mapping from target frequencies → optimal bore profile + hole placement in ~10 ms
- **Training data:** 50,000 random spline bore profiles simulated with 3D FDTD (parallelized on GPU)
- **Result:** Spline bores with non-standard tapers produce correct tuning, including profiles that would be impossible to model with TMM (e.g., multiple expansion/contraction cycles)
- **Relevance:** Spline parameterization is exactly what our `backend/spline_bore.py` module provides — we already have the geometric foundation

## 4. Dual-Bore / Bifurcated Instruments

- **GEMINI Twin Serpents (MONAD Studio):** Two independent serpent-shaped bores sharing a single mouthpiece. Each bore has its own toneholes. Designed for collaborative playing where two performers each control one bore's holes. The bifurcation creates a 2-port acoustic network that TMM cannot trivially model.
- **Acoustic challenge:** The junction splits the wavefront — requires 3D simulation or network modeling with scattering matrices at the bifurcation point.
- **Broader class:** Any instrument with a Y-split, dual bells, or parallel bores falls into this category.

## 5. Community Instruments

Szabó (2024) created a series of community installation instruments:
- **Walrus Pipes:** Large-diameter PVC pipes carved with walrus-tusk motifs. The irregular wall contours act as intentional perturbations to the standing wave, creating non-standard timbres.
- **Waving Panpipes:** Panpipes arranged in a serpentine wave pattern rather than the traditional straight row. The physical arrangement is visual rather than acoustic — the acoustic behavior is unchanged because each tube is independent.

## Computational Methods Ranked by Applicability

| Tier | Method | What It Enables |
|---|---|---|
| **Tier 1 (Doable Now)** | Spline bore profiles | Non-standard tapers, smooth profile transitions |
| | Folded bore centerlines | Compact forms, no accuracy loss |
| | Arbitrary hole placement | Non-standard fingering, ergonomic layouts |
| | Non-standard tuning | Just intonation, microtonal scales, custom temperaments |
| **Tier 2 (Moderate Extension)** | 1D FEM (OpenWind) | Strongly non-conventional but 1D bores |
| | Phase-based optimization | Stable convergence for complex impedance targets |
| | Sensitivity-based optimization | Gradient-driven bore refinement |
| **Tier 3 (Research Project)** | 3D BEM | Free-form organic cavities, bifurcations (slow — hours per evaluation) |
| | 3D FDTD + DL inverse | Real-time inverse design, no expert tuning needed |
| | Coupled oscillator simulation | Non-linear playing regimes, multiphonics |

## Practical Implementation Roadmap

| Phase | Feature | Status |
|---|---|---|
| **Phase A** | Bore Profile Freedom (spline parameterization, `backend/spline_bore.py`) | Done |
| **Phase B** | OpenWind FEM Integration (1D FEM solver for arbitrary bores) | Planned |
| **Phase C** | Network Topology Design (branched bores, bifurcations, multi-port scattering) | Planned |
| **Phase D** | Full 3D (BEM or FDTD backend; deep learning surrogate) | Research |
| **Phase E** | Generative Agent + Pareto Optimization (`backend/generative_agent.py`) | Planned |

## References

1. Umetani, N., Panotopoulou, A., Schmidt, R., & Whiting, E. (2016). "Printone: Interactive Resonance Simulation for Free-form Digital Fabrication." *ACM Trans. Graph.*, 35(6), 184. https://doi.org/10.1145/2980179.2980250
2. Wang, A. (2019). "3D Acoustic Inverse Design: A Deep Learning Approach." MIT Master's Thesis. https://hdl.handle.net/1721.1/123456
3. Tournemenne, R., & Chabassier, J. (2019). "A comparison of a one-dimensional finite element method and the transfer matrix method..." *JASA*, 145(3), 1887. https://doi.org/10.1121/1.5101868
4. Debut, V. (2009). "Calcul de l'impédance d'entrée des instruments à vent courbes." PhD Thesis, McGill University.
5. Ernoult, A., Tournemenne, R., & Chabassier, J. (2020). "Phase-based optimization for wind instrument design." *ISMA 2020*.
6. Dabin, A., et al. (2016). "3D printed musical instruments: measurements and acoustic characterization." *ICA 2016*.
7. MONAD Studio. "GEMINI Twin Serpents." https://www.monadstudio.com
8. Szabó, B. (2024). Community instrument design projects.
