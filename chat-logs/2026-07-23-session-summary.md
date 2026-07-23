# Session Summary — 2026-07-23

## Context
- Previous session deleted; user requested full work recovery
- Research redone on key topics
- Cross-machine cooperation established via Tailscale

## Key Findings from Research Update

### OpenWInD (v0.13)
- FEM+TMM with `optimization` submodule for impedance-based bore reconstruction
- v0.12.3 has TMM-only with bug fixes
- Installation: `pip install openwind`

### WWIDesigner (v2.4.0)
- Validation tool for woodwind bore design
- Available for cross-validation of our TMM results

### ML Surrogates (2025)
- **Petiot 2025**: Random forest surrogate for trumpet bore — biobjective optimization (intonation + ease of emission)
- **Szwarcberg 2024**: Neural surrogate achieves <2.5% error in 1/6th time vs physical model

### 3D Printing Validation
- **Yamamoto 2025**: MuseScore museum case study
- **Fritz 2025**: Hotteterre traverso reproduction
- Musicians cannot distinguish 3D-printed from original instruments

### Existing Decisions (Confirmed)
- Two-phase optimizer: Powell → L-BFGS-B (0.00 cents RMS in ~10s)
- Phase-based resonance detection (Ernoult 2020) over peak-based
- JAX V2 TMM: 1.0ms forward, 6.9ms gradient

## Work Delegation Plan

### Laptop (100.100.66.117) — `experiment/flute-pvc`
- **Task**: OpenWInD v0.13 integration testing
- Install openwind, test FEM+TMM optimization
- Validate against our TMM results for known-good bores

### Desktop (this machine) — `experiment/tmm-improvements`
- **Task**: Tone-hole TMM extension
- Extend TMM to handle open/closed tone holes
- Test with clarinet/saxophone fingerings
