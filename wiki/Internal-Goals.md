# Project Goals

## Core Objectives

1. **Build a fast, accurate acoustic simulator** using TMM for woodwinds
2. **Achieve <3 cents RMS** intonation accuracy through multi-stage optimization
3. **Optimize for BOTH intonation AND timbre** — the two are inherently coupled
4. **Support 91+ instruments** across 10 families
5. **Democratize instrument design** via Tauri desktop app and web browser
6. **Produce 3D-printable STL files** with SLA-compatible tolerances

## The Timbre-Intonation Goal

**Intonation and timbre are fundamentally at odds.** Ernoult et al. (2020) proved this: optimizing both impedance peak frequencies (intonation) and peak amplitude ratios (timbre proxy) produces a Pareto frontier — you cannot improve one without degrading the other.

### What This Means

| Metric | What It Measures | Optimizer Behavior |
|--------|-----------------|-------------------|
| Absolute RMS | Pitch accuracy (vs A=440 ET) | Pushes toward exact frequencies |
| Median-corrected RMS | Scale evenness (relative spacing) | Pushes toward harmonic alignment |
| a₂/a₁ ratio | Register stability / brightness | Pushes toward consistent tone color |

**Current state:** Optimizer uses absolute RMS (accuracy). Evenness reported separately. Timbre proxy not yet integrated.

**Target state:** Bi-objective optimization with Pareto front between intonation and timbre. User chooses position on the front.

### Key References

| Paper | Finding | URL |
|-------|---------|-----|
| Ernoult et al. (2020) JASA | Intonation + timbre tradeoff proven | https://doi.org/10.1121/10.0002449 |
| Noreland et al. (2013) | Intonation-only optimization is incomplete | https://arxiv.org/abs/1209.3637 |
| Petiot et al. (2025) | Pareto front (intonation vs emission) | https://doi.org/10.1121/2.0002163 |
| Tournemenne et al. (2019) | Players accept worse intonation for better timbre | https://hal.science/hal-01504179v1 |

## Roadmap Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Computational accuracy & speed | **Current** |
| Phase 2 | 3D print accuracy | After Phase 1 |
| Phase 3 | Integration & polish | After Phase 2 |
| Phase 4 | Linux deployment & server hosting | After Phase 3 |
| Phase 5 | Desktop app | After Phase 3 |

See `ROADMAP.md` for full details.

## Success Metrics

| Metric | Target | Current Best |
|--------|--------|-------------|
| Computational accuracy | <3 cents RMS | 0.00-0.32 cents |
| Optimization speed | <60 seconds | 5-180 seconds |
| Instrument library | 91+ instruments | 91 instruments |
| 3D print accuracy | <10 cents | ~15 cents (unvalidated) |
| Timbre consistency | a₂/a₁ ratio uniform across range | Not yet measured |
