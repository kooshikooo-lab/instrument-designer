# Research — Optimization (Algorithms, Multi-Objective, Methods)

> Part of the topic-split research wiki. Hub: [[Internal-Research]].
> All references verified as of 2026-07-25.

---

## Algorithms

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Noreland et al. (2013) | Logical clarinet | 0.49c RMS via gradient opt, admitted timbre missing | https://arxiv.org/abs/1209.3637 |
| Ernoult et al. (2020) JASA | Phase-based cost | Smooth sin²(π·deviation) cost function | https://doi.org/10.1121/10.0002449 |
| Ernoult et al. (2021) Acta Acustica | Woodwind optimization | Open-open vs closed-open different approaches | — |
| Bastien et al. (2025) JASA | Recorder intonation | Intonation profile concept, relative vs absolute | https://doi.org/10.1121/2.0002181 |

## Multi-Objective & Timbre

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Ernoult et al. (2020) JASA | Intonation-timbre tradeoff | a₂/a₁ ratio conflicts with frequency targets | https://doi.org/10.1121/10.0002449 |
| Tournemenne et al. (2019) | Brass optimization | Players accept worse intonation for better timbre | https://hal.science/hal-01504179v1 |
| Petiot et al. (2025) | Trumpet bi-objective | Pareto front (intonation vs emission) | https://doi.org/10.1121/2.0002163 |
| Poirson et al. | User-centered trumpet | GA bore optimization, Pareto frontier | https://hal.science/hal-05389711v1 |

## Optimization Methods — Four Key Approaches

> Full comparison document: `C:\Users\koosh\Documents\woodwind_optimization_methods_comparison.md`

### Noreland 2012 — "The Logical Clarinet"

| Aspect | Detail |
|--------|--------|
| Instrument | Clarinet (chromatic, 37 fingerings) |
| Algorithm | SQP (fmincon), finite differences |
| Variables | ~50 (positions, radii, chimneys + bore) |
| Result | <10 cents RMS with register hole |
| Key innovation | Two-phase: tune 1st register → refine both registers |
| Strength | First systematic numerical optimization; built prototype |
| Weakness | Sensitive to initialization; frequency-only cost (no timbre) |
| URL | https://arxiv.org/abs/1209.3637 |

### WIDesigner (Patkau 2017)

| Aspect | Detail |
|--------|--------|
| Instrument | Flutes, clarinets, reed instruments (tool, not single result) |
| Algorithm | DIRECT-C (global) + BOBYQA (local), derivative-free |
| Variables | 3–20+ (user-selected: holes, bore, positions) |
| Result | ~1–5 cents (simple instruments), 5–15 cents (complex) |
| Key innovation | User-facing tool with constraint system for real makers |
| Strength | Most practical; supports iterative calibration |
| Weakness | Derivative-free is slow for high dimensions; no timbre |
| URL | https://github.com/edwardkort/WWIDesigner |

### Ernoult 2020 — Phase-Based Impedance Optimization

| Aspect | Detail |
|--------|--------|
| Instrument | Pentatonic clarinet (18 fingerings, 2 registers) |
| Algorithm | SQP (fmincon), finite differences |
| Variables | 38 (9 holes × 3 + 9 bore points + length) |
| Result | <0.025 cents (both registers); amplitude ratio within 20% |
| Key innovation | Phase-based resonance tracking (unwrapped phase of Rec) |
| Strength | Best accuracy; simultaneous frequency + amplitude |
| Weakness | Local method (needs good init); only pentatonic tested |
| URL | https://doi.org/10.1121/10.0002449 |

### Petiot 2025 — ML Surrogate + NSGA-II Pareto Front

| Aspect | Detail |
|--------|--------|
| Instrument | Trumpet leadpipe (brass, 6 variables) |
| Algorithm | Random Forest surrogate + NSGA-II |
| Variables | 6 (5 radii + length) |
| Result | Pareto front (intonation vs ease of emission) |
| Key innovation | ML surrogate eliminates expensive TMM; multi-objective Pareto |
| Strength | Fast optimization (seconds); reveals trade-offs |
| Weakness | Limited by training set size; 6 variables only |
| URL | https://doi.org/10.1121/2.0002163 |

### Cross-Method Lessons

| Lesson | Source | Relevance to Us |
|--------|--------|-----------------|
| Two-phase (simple→complex) is essential | Noreland | Our sequential optimizer does this |
| Phase-based resonance tracking > peak-tracking | Ernoult | Could replace our peak-based cost |
| Sequential greedy placement needs global re-optim | Noreland | Our DE re-optim (Phase 2b) validates this |
| Smart initialization > better global search | All | CMA-ES from random init failed; sequential placement succeeded |
| Amplitude ratios matter for playability | Ernoult, Petiot | Pareto front (intonation + timbre) needed |
| ML surrogates are complementary to gradient methods | Petiot | Use ML for global, L-BFGS-B for local refinement |

## See also

- [[Internal-AI-Research]] — JAX TMM, ML surrogates, CMA-ES, Bayesian optimization
- [[Internal-Research-Acoustics]] — TMM, tone holes, radiation
- [[Internal-Research-Measurement]] — intonation metrics used by optimizers
