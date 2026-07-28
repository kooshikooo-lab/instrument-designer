# Project Goals

## Core Objectives

1. **Build a fast, accurate acoustic simulator** using TMM for woodwinds
2. **Produce professional-quality instruments** with intonation, timbre, and playability optimized simultaneously
3. **Support 91+ instruments** across 10 families
4. **Democratize instrument design** via Tauri desktop app and web browser
5. **Produce 3D-printable STL files** with SLA-compatible tolerances

## The Quality-First Philosophy

**Instrument quality is multi-dimensional.** Intonation (pitch accuracy) is one important sub-goal, but it cannot be optimized in isolation without degrading timbre (tone color) and playability (ease of blowing).

### Intonation as a Sub-Goal

Professional instruments typically achieve 5–10 cents/note. Our <3c computational target exceeds most professional standards, but perfect intonation alone does not guarantee a good instrument.

| Metric | What It Measures | Professional Target | Our Target |
|--------|-----------------|-------------------|------------|
| Absolute RMS | Pitch accuracy (vs A=440 ET) | 5–10 cents | <3 cents (computational) |
| Median-corrected RMS | Scale evenness (relative spacing) | — | <2 cents |
| a₂/a₁ ratio | Register stability / brightness | Varies by instrument | Uniform across range |
| Max deviation | Worst note | <15 cents | <5 cents |

### The Pareto Front Concept

Ernoult et al. (2020) proved that intonation and timbre are fundamentally at odds. Optimizing both impedance peak frequencies (intonation) and peak amplitude ratios (timbre proxy) produces a **Pareto frontier** — you cannot improve one without degrading the other.

**What this means for our project:**
- We optimize intonation first (it's measurable and verifiable)
- We then build timbre proxy (a₂/a₁ ratios) into the optimizer
- The Pareto front gives users a set of optimal trade-offs to choose from
- Professional makers already make these trade-offs (e.g., Buffet R-13 vs RC clarinets)

### Key References

| Paper | Finding | URL |
|-------|---------|-----|
| Ernoult et al. (2020) JASA | Intonation + timbre tradeoff proven | https://doi.org/10.1121/10.0002449 |
| Noreland et al. (2013) | Intonation-only optimization is incomplete | https://arxiv.org/abs/1209.3637 |
| Petiot et al. (2025) | Pareto front (intonation vs emission) | https://doi.org/10.1121/2.0002163 |
| Tournemenne et al. (2019) | Players accept worse intonation for better timbre | https://hal.science/hal-01504179v1 |
| Bastien et al. (2025) | Intonation profile concept, relative vs absolute | https://doi.org/10.1121/2.0002181 |

## Roadmap Phases

| Phase | Focus | Status |
|-------|-------|--------|
| Phase 1 | Computational accuracy & speed | **DONE** (0.00-0.82c RMS, all 11 instruments <1c) |
| Phase 2 | 3D print accuracy | After Phase 1 |
| Phase 3 | Integration & polish | After Phase 2 |
| Phase 4 | Linux deployment & server hosting | After Phase 3 |
| Phase 5 | Desktop app | After Phase 3 |

See `ROADMAP.md` for full details.

## Success Metrics

| Metric | Target | Current Best |
|--------|--------|-------------|
| Computational accuracy | <3 cents RMS | **0.00–0.82 cents** (all 11 instruments, w_int=0.9) |
| Optimization speed | <60 seconds | 2.5–30.5 seconds |
| Instrument library | 91+ instruments | 91 instruments |
| 3D print accuracy | <10 cents | ~15 cents (unvalidated) |
| Timbre consistency | a₂/a₁ ratio uniform across range | Bore-geometry proxy (smoothness + radiation) |
| Pareto front | Trade-off curve available | Weighted-sum sweep + NSGA-II |
