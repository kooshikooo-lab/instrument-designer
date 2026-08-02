# Research References

> Indexed by topic. All references verified as of 2026-07-25.

---

## Acoustics — TMM & Modeling

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Debut-Kergomard-Laloë (2005) | TMM for woodwinds | Transfer matrix formalism for stepped bores | — |
| Campallotto et al. | OpenWInD | 1D FEM wind instrument acoustics | https://inria.hal.science/ |
| Chaigne & Kergomard (2016) | Acoustics of Musical Instruments | Comprehensive textbook | Springer |
| Smith (2010) | Introduction to Physical Modeling | Free online textbook | https://ccrma.stanford.edu/~jos/pasp/ |

## Acoustics — Tone Holes

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Keefe (1982) | Tone hole theory | Length correction formulas, viscothermal losses | https://doi.org/10.1121/1.388248 |
| Nederveen (1969/1998) | Woodwind acoustics | Cutoff frequency, end corrections, radiation | — |
| Lefebvre (2013) | TMMI mutual radiation | External tonehole interactions | — |
| Szwarcberg (2025) | Geometric sensitivity | 0.1mm radius → 3.4c; chimney +1mm → 4c | — |

## Acoustics — Radiation & Losses

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Dalmont et al. | Radiation impedance | End corrections for flanged/unflangled pipes | — |
| Keefe (1984) | Viscothermal losses | Bore and hole loss models | — |
| Wolfe (UNSW) | Cutoff frequency | Peak spacing → timbre brightness | https://www.phys.unsw.edu.au/jw/cutoff.html |

## Acoustics — Instrument-Specific

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Lefebvre (2010) | Saxophone bore shape | Straight cone NOT appropriate for harmonicity | — |
| Lefebvre PhD (2010) | Computational woodwind design | ±5 cents target; TMMI formulas | — |
| Benade (1976) | Fundamentals of Musical Acoustics | Woodwind bore design principles | — |
| Boehm (1871) | The Flute and Flute Playing | Modern flute scale and tone hole geometry | — |
| Fletcher & Rossing (1998) | The Physics of Musical Instruments | Comprehensive reference | — |

## Optimization — Algorithms

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Noreland et al. (2013) | Logical clarinet | 0.49c RMS via gradient opt, admitted timbre missing | https://arxiv.org/abs/1209.3637 |
| Ernoult et al. (2020) JASA | Phase-based cost | Smooth sin²(π·deviation) cost function | https://doi.org/10.1121/10.0002449 |
| Ernoult et al. (2021) Acta Acustica | Woodwind optimization | Open-open vs closed-open different approaches | — |
| Bastien et al. (2025) JASA | Recorder intonation | Intonation profile concept, relative vs absolute | https://doi.org/10.1121/2.0002181 |

## Optimization — Multi-Objective & Timbre

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Ernoult et al. (2020) JASA | Intonation-timbre tradeoff | a₂/a₁ ratio conflicts with frequency targets | https://doi.org/10.1121/10.0002449 |
| Tournemenne et al. (2019) | Brass optimization | Players accept worse intonation for better timbre | https://hal.science/hal-01504179v1 |
| Petiot et al. (2025) | Trumpet bi-objective | Pareto front (intonation vs emission) | https://doi.org/10.1121/2.0002163 |
| Poirson et al. | User-centered trumpet | GA bore optimization, Pareto frontier | https://hal.science/hal-05389711v1 |

## Measurement — Impedance & BIAS

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Widholm (1995) | BIAS system | Gold standard impedance measurement | https://www.widholm.at/wp-content/uploads/2021/01/1995_Brass_wind_instrument_quality_measured_and_evaluated_by_a_new_computer_system.pdf |
| Bertsch (1998) ISMA | Trumpet intonation | MAD in cents, inter-player SD 7-15c | https://matthias-bertsch.at/Downloads/MB-PDF/1998e_MB-ISMA-intonation.pdf |
| Kausel & Kuehnelt (2008) | Woodwind impedance | JASA, head/mouthpiece separation | https://doi.org/10.1121/1.2932620 |
| Bowen et al. (2018) | Impedance accuracy | Peak agreement better than 10 cents | http://oro.open.ac.uk/58268 |
| Grothe & Baumgart (2016) | Bassoon intonation | 4 frequency estimators compared | https://pub.dega-akustik.de/DAGA_2016/data/articles/000322.pdf |

## Measurement — Intonation Metrics

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Dai & Dixon (2017) ISMIR | Singing intonation | MAPE, MAMIE metrics defined | https://archives.ismir.net/ismir2017/paper/000024.pdf |
| Dai & Dixon (2019) JASA | Intonation trajectories | Median and frame-level pitch measurement | https://webspace.eecs.qmul.ac.uk/s.e.dixon/pub/2019/DaiDixon-JASA-Quartet-AcceptedVersion.pdf |
| Weiss et al. (2019) ISMIR | Choir intonation | Adaptive reference grid removes drift | https://www.audiolabs-erlangen.de/content/05_fau/professor/00_mueller/03_publications/2019_WeissSRM_ChoirIntonation_ISMIR_PrintedVersion.pdf |
| ISO 16:1975 | Standard pitch | A4 = 440 Hz, no intonation metric standard | https://cdn.standards.iteh.ai/samples/3601/3e7b175fdcae4a2aa09f9d0db4ac099d/ISO-16-1975.pdf |

## Perception — Timbre & Intonation

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Sagepub (1987) | Timbre-intonation perception | Brighter = perceived as sharper | https://journals.sagepub.com/doi/10.2307/3345719 |
| Ely (1992) | Timbre affects intonation | Timbre affects detection of intonation problems | https://doi.org/10.2307/3345565 |
| Thompson (1979) | Reed resonance | Harmonic alignment affects tone stability | https://doi.org/10.1121/1.383448 |

## Measurement — Databases

| Database | URL | Content |
|----------|-----|---------|
| Wolfe/UNSW | https://phys.unsw.edu.au/music/flute/ | Impedance + sound + bore for baroque flute |
| Wolfe/UNSW instruments | https://www.phys.unsw.edu.au/jw/instr.html | Multiple instrument impedance measurements |
| BIAS | https://www.widholm.at/ | Brass instrument measurement system |
| MIMF | https://www.mimf.com/ | 10,000+ archived instrument discussions |

## GitHub Repos — Critical

| Repo | URL | Description |
|------|-----|-------------|
| OpenWInD | https://inria.hal.science/ | Python FEM wind instrument acoustics |
| WWIDesigner | https://github.com/edwardkort/WWIDesigner | Java TMM optimizer (47★) |
| demakein | https://github.com/garyscavone/demakein | Python TMM optimizer (55★) |
| NESS | https://github.com/Edinburgh-Acoustics-and-Audio-Group/ness | C++/CUDA physical modeling (45★) |
| build123d | https://github.com/gumyr/build123d | Python CAD (2649★) |
| acoustics | https://github.com/mailys/acoustics | Python acoustic analysis |
| acmt | https://github.com/garyscavone/acmt | MATLAB acoustic analysis |

## Books

| Book | Author | Year | Relevance |
|------|--------|------|-----------|
| Fundamentals of Musical Acoustics | Benade | 1976 | Woodwind design bible |
| The Physics of Musical Instruments | Fletcher & Rossing | 1998 | Comprehensive physics reference |
| Acoustical Aspects of Woodwind Instruments | Nederveen | 1998 | Tone hole theory, cutoff |
| Acoustics of Musical Instruments | Chaigne & Kergomard | 2016 | Modern comprehensive reference |
| Introduction to Physical Modeling Synthesis | Smith | 2010 | Free online TMM tutorial |

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

---

## AI/ML for Instrument Design

> See also: [[Internal-AI-Research]]

| Reference | Topic | Key Finding | URL |
|-----------|-------|-------------|-----|
| Petiot et al. (2025) | Yamaha trumpet ML surrogates | LassoLars 0.305c RMSE, 2min training | https://doi.org/10.1121/2.0002163 |
| Fréour et al. (2023) | Trumpet bifurcation ML | 12K samples, ~1% error, real-time | https://doi.org/10.61782/fa.2023.0281 |
| Wang (2019) | MIT wind instrument NN | FDTD + NN inverse design, 3D-printed | https://dspace.mit.edu/handle/1721.1/123116 |
| Yokota et al. (2024) | ResoNet PINN | Physics-informed NN for tube resonance | https://arxiv.org/html/2310.11804v4 |
| Qasim et al. (2024) | RL physics instrument | PPO sequential design | https://arxiv.org/abs/2412.10237 |
| OpenWInD | TMM + gradient bore reconstruction | Bore reconstruction via adjoint | https://openwind.inria.fr/ |
| j-Wave | JAX differentiable acoustics | Full differentiable acoustic sim in JAX | https://github.com/ucl-bug/jwave |
| BoTorch | Bayesian optimization | Multi-objective BO with GP surrogates | https://github.com/meta-pytorch/botorch |
| pycma | CMA-ES | State-of-the-art derivative-free optimizer | https://github.com/CMA-ES/pycma |
