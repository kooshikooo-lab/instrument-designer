# Archived README — 2026-07-23

Original project README, preserved for reference. Contains historical research
sources, initial design ideas, and project planning from early development.

---

# Bass Chalumeau / Early Clarinet Design Research Project

## Project Overview

### Goal
Develop a comprehensive design automation system for historical bass chalumeaus and early clarinets, integrating TMM acoustics, historical fingering systems, and optimization algorithms.

### Scope
- Historical replication: Authentic reconstruction of surviving instruments (Denner tenor, Kress bass)
- Modern adaptation: Functional instruments with enhanced capabilities (register key, improved tuning)
- Research and documentation: Comprehensive data collection and analysis
- Software tools: Optimization algorithms, acoustic modeling, design validation

## Research Sources

### Key Instruments Studied
- **Denner tenor chalumeau (Munich Mu 136)**: Surviving historical benchmark
- **Kress bass chalumeau (Salzburg A-Salzburg 8/1)**: Only surviving bass chalumeau
- **Historical fingerings**: Majer (1732), Eisel (1738) cross-fingerings

### Acoustic Theory References
- Keefe (1981): TMM validation, tanner/untanner derivation
- Nederveen (1998): TMM theory
- Benade (1976): Open hole physics, R=-1 reflection at phase=-0.5
- Wackernagel (2005), pp. 225-239: Tenor measurements

### TMM Theory
- tanner/untanner = normalized admittance for 1D wave equation
- junction3 = parallel admittance addition with area weighting
- -0.5 phase for open hole = perfect reflection (R=-1)
- Valid for 70-150Hz (plane-wave regime)
- f_cutoff ≈ 8kHz for 25mm bore

### Design Findings
- Register hole mechanics: 80mm position, 2.5mm dia, 3mm chimney
- Graduated diameters optimal for precision (2 extra vars)
- 12 sequential holes: Hard physics limit (~15c RMS) due to sequential fingering geometry
- Cross-fingerings necessary for chromatic expansion beyond 7 holes

### Validation Results (Early)
- 7-hole diatonic (uniform 11mm): 6.19c/9.51c RMS
- 12-hole sequential chromatic: Hard-limited to ~15c RMS
- 7-hole chalumeau: 19.61c RMS (initial guess issues)
- Cross-fingerings: 47c RMS (ad-hoc, needs proper chart)

### Research Ideas
- Museum contact: Salzburg Museum (Hagen-Walther) for Kress measurements
- Material science: 3D-printed vs. traditional wood acoustics
- Manufacturing tolerances: CNC precision requirements
- CTMM/OpenWind comparison methodology
- Co-optimization of hole positions and fingerings
