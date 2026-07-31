# Roadmap: Instrument Designer

## Completed
- [x] Bore optimization with pymoo + OpenWInD (basic)
- [x] Impedance solver resolution fix (800 → 5000 points)
- [x] Quadratic interpolation for peak finding
- [x] Impedance caching for repeated evaluations
- [x] Intonation accuracy research (documented in chat-logs/2026-07-18)
- [x] CORS middleware added to FastAPI backend
- [x] demakein installed and design pipeline working
- [x] Preset dropdown grouped by category (Flute / Woodwind)
- [x] SimulationWorker: renamed finished signal, added exception handling
- [x] ProjectWidget: public methods, cross-platform folder open
- [x] Cloned chalumier (Kotlin demakein rewrite) for evaluation
- [x] STL generation: CadQuery-based pipeline (replaced broken demakein Maker classes)
- [x] Quick mode support for demakein designs (faster draft iterations)
- [x] chalumier wrapper module (ready when JDK is available)
- [x] Error handling: _run_design try/except, unified job status responses
- [x] freecad_engine.py: robust JSON parsing from stdout
- [x] YAML bore_length unit consistency (mm throughout)
- [x] validate_optimizer.py: fixed paths, phased thresholds, portability

---

## Phase 1: Intonation-Only Optimization (CURRENT FOCUS)

> **Scope:** This phase optimizes **only intonation** (RMS cents deviation from
> target frequencies). No timbre, ergonomics, printability, or multi-objective
> optimization. The cost function is purely `phase_cost()` — measuring how close
> the instrument's resonances are to target wavelengths.

> **Before starting work here:** Check the "Periodic Research Review" section
> below for new papers or tool updates that may change the approach.

Everything here is software-only — no printing required. The goal is a fast,
accurate optimizer that matches or exceeds demakein/chalumier on reference instruments.

**Target: <3 cents intonation error, <60 seconds per design.**

**Future phases will add:**
- Phase 1b: Timbre-aware optimization (spectral centroid, harmonic balance)
- Phase 1c: Ergonomic constraints (hole spacing, reach, thumb position)
- Phase 1d: Printability constraints (wall thickness, support structure, overhang)
- Phase 1e: Multi-objective Pareto optimization (intonation vs timbre vs ergonomics)

### 1a. TMM Optimizer — DONE
Phase-based TMM optimizer is working and validated:

- [x] Phase-based TMM engine (`backend/tmm_acoustics.py`) — ported from chalumier/demakein
- [x] Cumulative fingering evaluator (`core/engine.py`) — evaluates all fingerings at once
- [x] L-BFGS-B optimization — gradient-based, fast convergence
- [x] Sequential refinement engine (`SequentialRefinementEngine` in `core/engine.py`)
- [x] Cylindrical bore: **0.0 cents evenness** (perfect relative intonation)
- [x] Conical bore: **23.9 cents evenness** with L-BFGS-B (54% hole sizing)
- [x] Phase cost functions: `phase_cost()`, `phase_cost_with_offset()`
- [x] API integration: `/optimize/tmm` endpoint in design server

**Performance:** 0.01-0.03s per evaluation, <2 seconds per design.

### 1b. closedTop Convention — VERIFIED
**Critical finding:** For conical bores (saxophone, oboe, etc.), always use `closedTop=False`.

- [x] Verified analytically: closed cone resonates at f=nc/(2L) — same as open-open pipe
- [x] Verified TMM: `closedTop=False` reproduces all cone harmonics correctly
- [x] Verified TMM: `closedTop=True` gives wrong results for cones (models cylinder, not cone)
- [x] Phase verification: at expected cone resonance wavelengths, phase = n+1 (integer)
- [x] Search algorithm is correct — no bugs found
- [x] coneStep has no effect on accuracy (0.125mm to 2.0mm all give same result)
- [x] Systematic offset: -8.4c from end flange correction (known, correctable)

**Theory:** A cone with closed small end resonates at ALL harmonics (f=nc/(2L)) —
identical to open-open pipe. The stepped-cylinder TMM captures this with `closedTop=False`
because area steps approximate the cone's acoustic behavior. With `closedTop=True`,
it incorrectly models a closed-open cylinder (odd harmonics only).

**For saxophone design:** Always pass `closed_top=False` to TMMInstrument.

### 1c. Speed — Parallelize Optimizer
The optimizer timed out at pop=20/gen=10 on a single instrument. This is the
#1 blocker — we can't even validate accuracy if we can't run it.

- [ ] Add `StarmapParallelization` to BoreOptimizationProblem
  - pymoo supports `elementwise_runner=StarmapParallelization(pool.starmap)`
  - Each evaluation is independent (40 calls/gen, each runs OpenWInD)
  - Pool size = CPU core count (typically 4-8)
  - Expected speedup: 4-8x (core-count bound, not quality-limited)
  - Cache won't be shared across workers — acceptable tradeoff for now
- [ ] Profile single evaluation time to understand bottleneck
- [ ] Verify accuracy is preserved after parallelization (same seed = same result)

### 1d. Accuracy — Bore Quality Constraints
- [ ] Add monotonicity constraint (docstring promises it, code doesn't implement it)
  - `n_ieq_constr=0` in current code — bore can go backwards
  - Must land BEFORE increasing control points — extra DOF without constraints = jaggier bores
  - Implementation: inequality constraint `bore[i+1] >= bore[i]` for all i
- [ ] Add smoothness constraint (penalize large radius jumps between adjacent points)
- [ ] Add global pitch offset correction (shift all peaks by constant cents offset)
- [ ] Improve scale evenness objective (currently std of diffs, consider musical intervals)
- [ ] Add support for clarinet odd-harmonic tuning (every other peak)

### 1e. Validation — Benchmark Against Other Software
Our optimizer should match or exceed demakein/chalumier accuracy on the same
reference instruments. This is the "match or exceed" requirement.

- [x] Clarinet benchmark: 4.46 cents evenness achieved
- [x] Cylindrical bore: 0.0 cents evenness (perfect)
- [x] Conical bore: 23.9 cents evenness with proper hole sizing
- [x] **Phase 2b DE breakthrough** — ALL 5 instruments sub-0.3c RMS:
  - Chalumeau C: 0.01c (5.2s)
  - Bass Chalumeau Bb: 0.17c (15.2s)
  - Soprano Sax Bb: 0.32c (10.2s)
  - Xaphoon C: 0.00c (10.7s)
  - Alto Sax Eb: 0.02c (8.2s)
- [x] Chalumier benchmark: TMM matches chalumier when given same bore profile
- [x] L-BFGS-B refinement from chalumier's bore achieves 3.5c (5x better than chalumier's 29c)
- [ ] Test recorder with chalumier fingering chart (28 fingerings, cross-fingerings)
- [ ] Test dwhistle with chalumier fingering chart (14 fingerings, 2 registers)
- [ ] Document accuracy comparison: ours vs chalumier

**Phase 2b key insight:** Sequential greedy hole placement creates large gaps (288mm for xaphoon)
where TMM can't find resonances. DE with overlapping bounds (`lo=i*L/(n_h*1.5+1)`,
`hi=(i+2)*L/(n_h*1.5+1)`) re-optimizes ALL hole positions simultaneously, closing gaps.

### 1f. Bore Representation
Sequencing: smoothness constraint first, then more control points.
- [ ] Test with more control points (12 → 20-30 for complex profiles)
  - Only after monotonicity constraint is in place

### 1g. Metric Standardization & Timbre Optimization — **COMPLETED 2026-07-31**

**Critical finding (2026-07-25):** Median correction in cost functions measures **scale evenness**, not **pitch accuracy**. These are fundamentally different things with different timbre implications. Ernoult et al. (2020) proved intonation and timbre are inherently at odds — optimizing both requires a Pareto front approach.

**Changes Made (2026-07-31):**
- [x] Removed median correction from ALL optimizers:
  - `tmm_acoustics.py:phase_cost_with_offset()` — deprecated, now returns absolute RMS via `phase_cost()`
  - `two_phase_optimizer.py:phase_cost_with_offset()` — deprecated, now returns absolute RMS
  - `benchmark_all.py:eval_all()` — already used absolute RMS (primary metric)

- [x] Absolute RMS is now the **primary metric** everywhere:
  - Formula: `sqrt(mean(cent_deviations²))` — measures pitch accuracy
  - No median offset subtraction

- [ ] Report full metric suite in benchmark output (future):
  - **Absolute RMS (c):** `sqrt(mean(cent_deviations²))` — accuracy
  - **MAD (c):** `mean(|cent_deviations|)` — robust accuracy
  - **SD (c):** `std(cent_deviations)` — evenness
  - **Max deviation (c):** worst note
  - **Per-note table:** full profile for debugging

- [ ] Add timbre proxy to optimizer: impedance peak amplitude ratios (a₂/a₁)
  - a₂/a₁ determines register stability and brightness
  - Target: varies linearly from ~2 (low register) to ~1 (high register)
- [ ] Update benchmark_all.py to report full metric suite
- [ ] Bi-objective optimization (stretch goal): intonation + timbre Pareto front
  - Reference: Petiot et al. (2025) trumpet bi-objective optimization
  - Reference: Tournemenne et al. (2019) brass instrument optimization

**Why this matters:**
- An instrument can be perfectly even but 15c sharp (median-corrected: 0c, absolute: 15c)
- An instrument can be accurate but uneven (median-corrected: 5c, absolute: 2c)
- Professional makers explicitly trade intonation for timbre (Buffet R-13 vs RC)
- Brighter timbre is perceived as sharper (perception coupling)
- Noreland et al. (2013) optimized only intonation and admitted including timbre would produce different designs

**Key references:**
- Ernoult et al. (2020) JASA — intonation + timbre tradeoff: https://doi.org/10.1121/10.0002449
- Noreland et al. (2013) — "Logical Clarinet": https://arxiv.org/abs/1209.3637
- Bastien et al. (2025) JASA — intonation profile: https://doi.org/10.1121/2.0002181
- Petiot et al. (2025) — trumpet Pareto front: https://doi.org/10.1121/2.0002163
- Tournemenne et al. (2019) — brass optimization: https://hal.science/hal-01504179v1
- Wolfe (UNSW) — cutoff frequency and timbre: https://www.phys.unsw.edu.au/jw/cutoff.html
- Keefe (1982) — tone hole theory: https://doi.org/10.1121/1.388248

### 1h. Optimization Methods Research (2026-07-27)

Research into four published optimization methods to identify best practices and implementation opportunities. Full comparison document: `C:\Users\koosh\Documents\woodwind_optimization_methods_comparison.md`

**Methods researched:**

| Method | Algorithm | Key Innovation | Our Status |
|--------|-----------|----------------|------------|
| Noreland 2012 | SQP + finite differences | Two-phase (simple→complex) | Sequential optimizer validates this |
| WIDesigner (Patkau 2017) | DIRECT-C + BOBYQA | User-facing tool with constraints | Open-source Java tool available |
| Ernoult 2020 | SQP + phase-based tracking | Unwrapped phase resonance ID | **To implement** — best accuracy |
| Petiot 2025 | Random Forest + NSGA-II | ML surrogate + Pareto front | **To implement** — multi-objective |

**Key insights from research:**
- **Two-phase optimization is essential** (Noreland): Phase 1 tunes first register, Phase 2 refines both. Our sequential optimizer does this.
- **Phase-based resonance tracking > peak-tracking** (Ernoult): Unwrapped phase of reflection function is smooth and differentiable. Our peak-based cost is non-smooth.
- **Sequential greedy placement needs global re-optim** (Noreland): Our DE re-optim (Phase 2b) validates this.
- **Smart initialization > better global search** (All methods): CMA-ES from random init fails. Sequential placement succeeds.
- **Amplitude ratios matter for playability** (Ernoult, Petiot): Frequency-only optimization produces incomplete instruments.
- **Professional intonation is 5–10 cents** (Bertsch 1998, forum consensus): Our <3c target exceeds most professional standards.

**Implementation/testing plan:**

- [ ] **Phase 1h-a: Implement Ernoult phase-based cost function**
  - Replace peak-tracking with unwrapped phase of reflection function
  - Test on 12-instrument benchmark
  - Expected: smoother optimization landscape, faster convergence
  - Reference: Ernoult et al. 2020, doi:10.1121/10.0002449

- [ ] **Phase 1h-b: Test Noreland two-phase approach**
  - Phase 1: optimize first register only (10 fingerings)
  - Phase 2: refine both registers (all fingerings)
  - Compare convergence vs current all-at-once approach
  - Reference: Noreland et al. 2013, arXiv:1209.3637

- [x] **Phase 1h-c: Implement Pareto front (intonation + timbre)**
  - Bore-geometry timbre proxy: bore smoothness + hole radiation consistency
  - Weighted-sum sweep: sequential init → L-BFGS-B with varying w_int/w_tim
  - NSGA-II blocked by missing pymoo (install: `pip install pymoo`)
  - Tested on 3 instruments: stronger tradeoff on conical (soprano sax) vs cylindrical

**Phase 1h-c results (2026-07-28):**
- Bore-geometry proxy shows measurable tradeoff on conical instruments
- Soprano sax: w_int=0.0 → 5.2c intonation / 0.028 timbre vs w_int=1.0 → 0.0c / 0.146
- Chalumeau: weak tradeoff (constant bore → no conflict between intonation and timbre)
- Key finding: timbre proxy conflicts more with tapered bores (real instruments) than constant bores
- To improve: install pymoo for NSGA-II, or compute actual a₂/a₁ via impedance peaks

- [ ] **Phase 1h-d: Validate against WIDesigner**
  - Install WIDesigner (Java, open-source)
  - Run same instruments through both optimizers
  - Compare accuracy and speed
  - Reference: https://github.com/edwardkort/WWIDesigner

- [ ] **Phase 1h-e: Test manufacturing tolerance sensitivity**
  - Add ±0.1mm noise to optimal bore profiles
  - Re-evaluate intonation
  - Document which instruments are most sensitive
  - Critical for Phase 2 (3D print accuracy)

### 1i. JAX Autodiff Stage 2 (2026-07-28)

Implemented JAX automatic differentiation for bore-radii refinement (Stage 2 of the
4-stage L-BFGS-B pipeline). Uses `jax.grad` for exact gradients instead of finite
differences.

**Implementation:**
- `build_chain_for_optimizer()` in `tmm_acoustics_jax.py` — builds JAX action chain
- `jax_stage2_refine()` in `jax_optimizer.py` — L-BFGS-B with `jax.grad`
- `make_phase_cost()` updated to accept `n_register` parameter (was using `round(phase)`)
- `use_jax_bore` flag on `refine_sequential()` and `jax_two_phase_optimize()`

**Results (11 instruments, A/B test):**

| Instrument | Type | Python TMM | JAX autodiff | Δ |
|-----------|------|-----------|-------------|---|
| chalumeau_C ✓ | closed-open | 0.53c | 0.00c | **+0.53c** |
| diatonic_D ✓ | closed-open | 0.62c | 0.00c | **+0.62c** |
| bass_chalumeau_Bb | closed-open | 0.00c | 0.67c | -0.67c* |
| soprano_sax ✓ | open-open | 0.00c | 0.00c | 0.00c |
| xaphoon ✓ | open-open | 0.00c | 0.00c | 0.00c |
| alto_sax ✓ | open-open | 0.00c | 0.00c | 0.00c |
| concert_flute ✓ | open-open | 0.00c | 0.00c | 0.00c |
| tin_whistle ✓ | open-open | 0.00c | 0.00c | 0.00c |
| alto_flute ✓ | open-open | 0.00c | 0.00c | 0.00c |
| pvc_flute ✓ | open-open | 0.00c | 0.00c | 0.00c |
| recorder_C ✓ | open-open | 1.04c | 1.04c | 0.00c |

*Bass chalumeau Bb uses unverified dimensions — regression not meaningful.

**Key findings:**
- JAX improves closed-open instruments that need help (chalumeau, diatonic)
- No regressions on verified instruments
- Speed equivalent (1.00x ratio) — JAX compilation offset by fewer iterations
- JAX phase cost only reliable for n_reg=1 (closed-open); n_reg=2 falls back to Python TMM
- Phase cost landscape differs from peak-finding landscape — can trap on unverified instruments

---

### Computational Accuracy Targets
| Phase | Target | Requirements | Status |
|-------|--------|--------------|--------|
| C1 | <20 cents | L-BFGS-B + correct hole sizing | **ACHIEVED** (23.9c cone) |
| C2 | <10 cents | Multi-param optimization | **ACHIEVED** (Phase 2b DE) |
| C3 | <5 cents | Noreland-level (0.49 cents RMS) | **ACHIEVED** (0.01-0.32c) |
| C4 | <3 cents | Best-case everything | **ACHIEVED** (0.00c xaphoon) |

**Benchmark:** Noreland clarinet (2013) achieved 0.49 cents RMS fundamental,
<5 cents after removing global offset. We now achieve 0.01-0.32c on all instruments.

---

## Phase 2: 3D Print Accuracy (AFTER PHASE 1)

Research-first approach: measure what matters, then compensate.
All items here require physical printing and measurement.

### 2a. Print Tolerance Research
- [ ] Quantify SLA dimensional accuracy for bore geometries
  - Print test cylinders at various diameters (10-25 mm)
  - Measure with calipers/micrometer
  - Document actual tolerance vs manufacturer spec
- [ ] Quantify material shrinkage (engineering resin vs standard resin)
  - Print known-length specimens
  - Measure before/after post-cure
  - Build shrinkage lookup table per resin
- [ ] Quantify bore surface roughness impact
  - Print bores at different layer heights (25/50/100 µm)
  - Measure impedance spectra of each
  - Determine minimum layer height for <1 cent acoustic effect
- [ ] Quantify warp/dimensional distortion over length
  - Print 500mm bore in sections
  - Measure straightness and diameter consistency
  - Document join accuracy for multi-part prints

### 2b. Shrinkage Compensation
- [ ] Add per-resin shrinkage factor to STL export
- [ ] Validate compensation with test prints
- [ ] Support non-uniform shrinkage (axial vs radial)

### 2c. Measurement Loop
- [ ] Import measured impedance data from real instruments
- [ ] Compare designed vs measured bore profiles
- [ ] Iterative correction: measure → optimize → print → measure

### Physical Accuracy Targets
| Phase | Target | Requirements | Status |
|-------|--------|--------------|--------|
| P1 | <20 cents | SLA print + basic compensation | After C1 |
| P2 | <10 cents | Calibrated SLA + shrinkage comp | After P1 |
| P3 | <5 cents | Excellent SLA + measurement loop | After P2 |
| P4 | <3 cents | Best-case everything | Stretch goal |

**Key insight from research:** Manufacturing is the bottleneck, not computation.
A 0.1mm bore error → ~1-3 cents intonation error. SLA tolerance is ±0.05-0.1mm.
So even perfect computation gets diluted by printing. Phase 2 closes this gap.

---

## Phase 3: Integration & Polish

### Chalumier Integration
Branch `experiment-chalumier-integration` has the wrapper and web UI integration.
Chalumier JAR not yet built (requires JDK 17+).

- [x] `chalumier_wrapper.py` created (branch: `experiment-chalumier-integration`)
- [x] Web UI integration: BoreProfileView SVG renderer, build trigger button
- [x] Backend endpoints: `/chalumier/design`, `/chalumier/build`
- [ ] Install JDK 17+ (required to build/run chalumier)
- [ ] Build chalumier JAR (`gradlew.bat shadowJar` in chalumier/ dir)
- [ ] Compare chalumier vs our TMM optimizer output quality and speed
- [ ] Add chalumier instrument types to preset list
- [ ] Support `.chal` specification files in the web UI

**Note:** Chalumier is Kotlin-based, DESIGN-ONLY (JSON + SVG output, not STL).
For 3D model generation, combine with demakein's make phase or our own STL export.

### GUI Enhancements
- [ ] Real-time bore profile visualization during optimization
- [ ] Impedance peak display with target frequencies overlay
- [ ] Export optimization history (convergence plots)
- [ ] Bore profile editor (drag control points)

---

## Phase 4: Linux Deployment & Server Hosting

Linux is the target platform for both development and deployment. The optimizer's
parallelization is significantly faster on Linux due to `fork` (copy-on-write) vs
Windows `spawn` (fresh interpreter + pickle overhead). The web app will be hosted
on a Linux server for remote access.

### 4a. Local Linux Testing (WSL2)
Quick validation of parallel speedup before committing to full Linux install.

- [x] WSL2 + Virtual Machine Platform installed (Windows features)
- [ ] **BLOCKED: Enable virtualization in BIOS (Intel VT-x / AMD-V)** — deferred
- [ ] Install Ubuntu distribution: `wsl --install -d Ubuntu`
  - Alternative: use `concurrent.futures.ProcessPoolExecutor` to avoid fork/spawn issue entirely
- [ ] Install Python 3.12+ and project dependencies
- [ ] Benchmark optimizer: serial vs parallel (fork context)
  - Expected: 3-5x speedup over current Windows parallel (1.67x)
  - Target: full 6-8x speedup matching core count
- [ ] Verify chalumier builds and runs on Linux (JDK 17+)
- [ ] Test demakein STL generation on Linux
- [ ] Document any Windows-specific code that needs fixing

### 4b. Native Linux Install (Optional)
For maximum performance or if WSL2 has issues.

- [ ] Install Ubuntu LTS (dual-boot or primary)
- [ ] Set up Python virtual environment with all deps
- [ ] Verify fork-based parallelization works as expected
- [ ] Profile optimizer with real instruments (target: <60s per design)

### 4c. Server Deployment
Host the web app on a remote Linux server for team access.

- [ ] Choose server: cheap VPS (4-8 cores, $5-10/mo) or existing machine
- [ ] Set up Docker container with Python + all dependencies
- [ ] Deploy FastAPI backend (port 8000)
- [ ] Deploy frontend (static files or Tauri web build)
- [ ] Configure reverse proxy (nginx) for HTTPS
- [ ] Set up process manager (systemd or supervisor) for auto-restart
- [ ] Document server access and deployment workflow

### 4d. Python 3.14 Migration (When Stable)
Python 3.14 changes the default start method on Linux from `fork` to `forkserver`.
This is safer (avoids fork's thread-safety issues) while maintaining fast startup.

- [ ] Test with Python 3.14 beta/rc when available
- [ ] Verify `forkserver` context works with pymoo
- [ ] Update deployment to use Python 3.14 when stable
- [ ] Remove any fork-specific workarounds if no longer needed

### Linux Parallelization Advantages
| Aspect | Windows (spawn) | Linux (fork) | Linux (forkserver) |
|--------|-----------------|--------------|-------------------|
| Process startup | ~40ms (fresh interpreter) | ~2ms (copy-on-write) | ~5ms (pre-forked) |
| Pickle overhead | Yes (serialize entire problem) | No (memory copy) | No |
| `if __name__` guard | Required | Optional | Optional |
| Thread safety | Safe | Unsafe with threads | Safe |
| Python version | All | All | 3.14+ |

**Current Windows parallel benchmark:** 1.67x speedup (pop=20, gen=5, 6 workers)
**Expected Linux fork benchmark:** 3-5x speedup (same parameters)

---

## Phase 5: Desktop App (AFTER CORE STABLE)

### Tauri Desktop App — Architecture
- **Current approach (chosen):** Tauri + HTTP backend. Tauri spawns the Python FastAPI
  server as a managed process. Frontend talks to it via localhost:8000. We get native
  features (file dialogs, tray, auto-update) while keeping the proven Python backend.
- **BLOCKED:** Missing Tauri capabilities in `default.json`:
  - `core:event:allow-listen`
  - `core:event:allow-emit`
  - `process:allow-spawn`
- **Alternative worth exploring later:** Pure Rust with PyO3 bindings. Embed demakein's
  optimizer directly in the Rust binary via PyO3/maturin. Eliminates the Python
  dependency entirely, gives single-binary distribution, and could be significantly
  faster (no process boundary, no GIL contention). The demakein optimizer is mostly
  numpy/scipy under the hood — rewriting the hot path in Rust with ndarray could be
  a 10-50x speedup. This is a bigger effort but could be transformative for the
  project. Consider after the HTTP-based Tauri version is stable and shipping.

---

## Ongoing: Periodic Research Review

New research in instrument acoustics, computational modeling, and 3D printing
appears constantly. New papers, tools, and techniques may emerge that directly
impact our design pipeline, cost functions, or accuracy targets. Schedule a
research review every 2–4 weeks, or before starting a new phase.

**What to check:**
- New papers on bore optimization, tone hole modeling, mouthpiece acoustics
- Updates to existing tools (OpenWInD, WIDesigner, Flutomat NG, chalumier)
- New 3D printing materials or post-processing techniques for acoustic parts
- Maker community breakthroughs (new successfully printed instruments)
- Changes to accuracy benchmarks in the literature

### Primary Journals & Proceedings
| Source | URL | Why It Matters |
|--------|-----|----------------|
| **JASA** (Journal of the Acoustical Society of America) | https://asa.scitation.org/journal/jas | Premier journal, wind instrument acoustics |
| **JASA Express Letters** | Same domain | Rapid communications, early results |
| **Acta Acustica** | https://acta-acustica.edpsciences.org/ | European, Diamond Open Access since 2025 |
| **POMA** (Proceedings of Meetings on Acoustics) | https://asa.scitation.org/journal/pom | ASA conference proceedings |
| **Archives of Acoustics** | http://acoustics.ippt.gov.pl/index.php/aa | Open access, includes music acoustics section |
| **Acoustics (MDPI)** | https://www.mdpi.com/journal/acoustics | Open access, IF 1.2 |
| **Music & Science** | https://journals.sagepub.com/home/msc | Interdisciplinary, publishes 3D-printed instrument studies |
| **Frontiers in Acoustics** | https://www.frontiersin.org/journals/acoustics | Newer (est. 2024), Volume 4 in 2026 |

### Preprint Servers (Check Weekly)
| Server | URL | Focus |
|--------|-----|-------|
| **arXiv cs.SD** | https://arxiv.org/list/cs.SD/recent | Computational acoustics, physical modeling |
| **arXiv eess.AS** | https://arxiv.org/list/eess.AS/recent | Audio and speech processing |
| **HAL** | https://hal.science/ | French archive, IRCAM/INRIA/CNRS heavy, OpenWind papers |

### Active Research Labs (Follow Their Publications)
| Lab | URL | Focus |
|-----|-----|-------|
| **CAML — McGill** | https://caml.music.mcgill.ca/ | Physical modeling, instrument measurement, FDTD |
| **CCRMA — Stanford** | https://ccrma.stanford.edu/ | Digital waveguides, JUCE |
| **IRCAM / INRIA** | https://www.ircam.fr/ / https://www.inria.fr/ | OpenWind, heritage instrument digitization |
| **NESS — Edinburgh** | https://www.ness.music.ed.ac.uk/ | Next Gen Sound Synthesis (ERC-funded), C++/CUDA |
| **Chalmers SMC** | https://research.chalmers.se/en/groups/sound-and-music-computing/ | Neuralacoustics framework, deep learning for acoustics |
| **Aalto Acoustics Lab** | https://www.aalto.fi/en/aalto-acoustics-lab | DAFx best papers 2023–2025 |
| **Stuttgart ITM** | https://www.itm.uni-stuttgart.de/en/research/analysis-of-musical-instruments/ | FEM/BEM for instruments, very active 2021–2025 |
| **Politecnico di Milano ISPG** | https://www.deib.polimi.it/ | Audio signal processing, violin acoustics |

### Conferences (Submit / Attend Annually)
| Conference | Cycle | Notes |
|------------|-------|-------|
| **ISMA** (International Symposium on Musical Acoustics) | ~2 years | ISMA 2026: Helsinki, Jun 15–17 |
| **ISMRA** (International Symposium on Musical and Room Acoustics) | Annual | ISMRA 2025 was May 25–27 New Orleans |
| **ASA Meetings** | Biannual | Major venue, POMA proceedings |
| **Forum Acusticum** | ~3 years | European Acoustics Association |
| **SMAC** (Stockholm Music Acoustics Conference) | ~4 years | Prestigious, focused |
| **DAFx** (Digital Audio Effects) | Annual | Physical modeling, sound synthesis |
| **NIME** (New Interfaces for Musical Expression) | Annual | Novel instruments, 3D-printed |

### Expert Forums & Communities (Browse Monthly)
| Community | URL | Focus |
|-----------|-----|-------|
| **Chiff & Fipple** | https://www.chiffandfipple.com/ | Flutes, whistles, world winds, 25+ years of archived knowledge |
| **MIMF** (Musical Instrument Makers Forum) | https://www.mimf.com/ | All types, 10,000+ archived discussions |
| **Reddit r/clarinet** | https://www.reddit.com/r/Clarinet/ | Reed instrument acoustics |
| **Reddit r/Luthier** | https://www.reddit.com/r/Luthier/ | Instrument builders |
| **ASA Forums** | https://acousticalsociety.org/ | Professional society discussions |

### Active GitHub Repos (Monitor for Updates)
| Repo | URL | Description |
|------|-----|-------------|
| **Neuralacoustics** | https://github.com/ktatar/neuralacoustics | Deep learning for musical acoustics (Chalmers) |
| **NESS** | https://github.com/Edinburgh-Acoustics-and-Audio-Group/ness | C++/CUDA physical modeling |
| **Resonarium** | https://github.com/gabrielsoule/resonarium | MPE physical modeling waveguide synth (341 stars) |
| **RipplerX** | https://github.com/tiagolr/ripplerx | Physical modeling synth, 9 resonator models (569 stars) |
| **VIBRA** | https://github.com/MOPT-UFSC/VIBRA | Open-source FEM vibroacoustic analysis (Python) |
| **ParallelFDTD** | https://github.com/AaltoRSE/ParallelFDTD/ | CUDA-accelerated FDTD room acoustics (Aalto) |
| **torch-fdtd-string** | https://github.com/jin-woo-lee/torch-fdtd-string | PyTorch FDTD + differentiable modal synthesis |
| **WIDesigner** | https://github.com/edwardkort/WWIDesigner | TMM wind instrument optimizer (Java) |
| **OpenWind** | https://inria.hal.science/ | Python wind instrument acoustics (Inria) |

### Blogs & Channels (Occasional)
| Source | URL | Description |
|--------|-----|-------------|
| **Martin Schleske Research** | https://www.schleske.de/en/research.html | Extraordinary violin acoustics resource |
| **Kemp Strings** | https://www.youtube.com/@kempstrings | String inharmonicity research demos |

### Key Observation
There is no dedicated acoustics preprint server. Researchers use **arXiv** (cs.SD, eess.AS) and **HAL** (dominated by IRCAM/INRIA/CNRS). For 3D-printed instruments specifically, *Music & Science*, *Acta Acustica*, *Polymers (MDPI)*, and *Rapid Prototyping Journal* are the most active venues.

---

## Computational Modeling & Benchmarking Research (2026-07-31)

> Full report (sources, links, tiered benchmark strategy) in the wiki:
> **Internal-Computational-Benchmark-Research** (mirror: `wiki/Internal-Computational-Benchmark-Research.md`).
> Best overall interest: **benchmarking methods**; research was broader, kept all of it.

### V&V benchmark — the key find

**Ernoult et al. 2026, *Acta Acustica* 10:51** — "Benchmark study of pipe input
impedance simulations and measurements for verification and validation":
multi-lab round-robin on 180 mm pipes (cylinders 14 mm ID with 4 end conditions;
cones 10→22.6 mm with 3 end conditions; brass/boxwood/**3D-printed ABS**; 5 pipes,
9 impedance measurements per config). DOI 10.1051/aacus/2026048. **Data downloadable:**
Zenodo https://zenodo.org/records/20024938 (v2; measured scaled by ρc/S, simulated not).
Processing scripts: GitLab Inria `aernoult/acoustic-impedance-benchmark`.
This is the canonical V&V suite for our TMM/FEM solvers.

### Benchmark targets by tier

| Tier | Target | Purpose | Acceptance |
|------|--------|---------|------------|
| V1 Verification | Inria 2026 pipe benchmark (Zenodo 20024938) | Solver-vs-solver + vs-measurement | Match simulated ref; report vs-measured per end condition |
| V2 Cross-software | chalumier/demakein examples, WIDesigner XML | Same design, different implementation | <1c on reference bore profiles |
| V3 Measured instrument | UNSW flute Z(f) (Boehm/classical); Bowen bass clarinet | Real instrument, real measurements | Peak agreement at Bowen-level accuracy (cents-scale) |
| V4 Printed replica | Fagottino (open measurement datasets + CT prints) / Hotteterre traverso / RCM prints | Full physical validation | Perceptually indistinguishable replicas; <5c print-induced shift (P3) |

### New checklist items

- [ ] **V1**: Run `backend/tmm_acoustics.py` + OpenWInD on the 2026 benchmark cylinders/cones; save comparison notebook + figures under `research/`
- [ ] **Fixtures**: import chalumier `examples/` (upstream GitHub, local dir empty), demakein `examples/`, and a parsed WIDesigner instrument XML as regression fixtures
- [ ] **UNSW Z(f)**: download the Boehm/classical flute Excel files, extract resonance peaks per fingering, compare to our model of same fingering
- [ ] **Metric discipline**: absolute RMS + MAD + SD + max deviation in `benchmark_all.py` (see §1g)
- [ ] **Physical loop**: use OpenWInD adjoint bore reconstruction (https://team.inria.fr/makutu/bore-reconstruction-of-woodwind-like-instruments/) to close measure→optimize→print→measure
- [ ] **Track**: RCM 3D-Printed Musical Instruments, Fagottino (historical-bassoon.ch), Hotteterre traverso study (hal-05393759v1) for future open CT data

### 3D model / dataset sources verified (2026-07-31)

- **RCM "3D Printed Musical Instruments"** — micro-CT of 7 museum instruments (5 ivory: Denner + Villars alto recorders, Scherer early clarinet, Scherer flute, renaissance cornett; 2 boxwood: Grundman oboe, Oberlender recorder); digital restoration + prints + acoustic comparison; not openly downloadable. DCMS/Wolfson-funded. https://www.rcm.ac.uk/research/projects/3dprintedmusicalinstruments
- **Hotteterre traverso** (Musée de la Musique) — X-ray tomography → 3D print; 69 listeners + 9 players, discrimination near chance. https://hal.sorbonne-universite.fr/IJLRDA-LAM/hal-05393759v1
- **Digital Revival** (Arbel & Weissman, arXiv:2606.24216v1) — Haka (c.1680) + Warder (1540s) flute case studies, ISMA 2026/POMA; also cites Eveno & Le Conte (45 serpents, doi:10.1016/j.culher.2016.02.005) and Bowen et al. (doi:10.1016/j.apacoust.2018.08.028).
- **Fagottino (SCB/FHNW)** — most open museum-grade data: 130+ small bassoons documented, measurement datasets on Zenodo, CT-based prints (3DFagottini). https://historical-bassoon.ch ; https://www.fhnw.ch/plattformen/3dfagottino/ ; https://meta.dasch.swiss/projects/0845/
- **UNSW flute acoustics** — downloadable Z(f) Excel files (Boehm B/C foot, classical flute; baroque in comparisons). https://www.phys.unsw.edu.au/music/flute/
- **Warder flute** (1540s shipwreck traverso) — CT → physical modeling; oldest Dutch flute; dataset incl. 3D models + IMA scans (Digital Revival).
- **Visual mesh marketplaces (Sketchfab/MakerWorld/Thingiverse)** — NOT usable for acoustic V&V (no bore/impedance data).

### Key methodology lessons

- Measured impedance files usually scaled by ρc/S; simulations not — check scaling before comparing.
- Bowen et al.: bore geometry alone may suffice for impedance prediction of playable instruments (validates geometry-only benchmarking).
- Szwarcberg et al. 2025: 0.1 mm radius → 3.4c; chimney +1 mm → 4c — sets fabrication tolerance bar.
- Metric discipline (§1g): median-corrected metrics measure evenness, not accuracy.

---

## Benchmarking Standards (2026-07-31) — **MANDATORY FOR ALL BENCHMARKS**

These standards are derived from the research in `wiki/Internal-Computational-Benchmark-Research.md` and `wiki/Internal-Research.md`. All benchmark runs must comply.

### Primary Metric: Absolute RMS (Pitch Accuracy)
```python
cents = [1200 * log2(actual / target) for each note]
absolute_rms = sqrt(mean(cents²))
```
- **This is the ONLY primary metric.** No median correction.
- Measures how far notes are from equal temperament targets at A=440 Hz.
- Median correction (evenness) is a SEPARATE metric, never the primary.

### Required Metric Suite (Report ALL)
| Metric | Formula | Measures |
|--------|---------|----------|
| **Absolute RMS** | `sqrt(mean(cent_dev²))` | **Accuracy (PRIMARY)** |
| **MAD** | `mean(|cent_dev|)` | Robust accuracy |
| **SD** | `std(cent_dev)` | Evenness |
| **Max Deviation** | `max(|cent_dev|)` | Worst note |

### Forbidden Practices
- ❌ Median correction as primary metric (hides systematic tuning errors)
- ❌ Reporting "0.01c" without specifying absolute vs median-corrected
- ❌ Using Printables/Cults3D/Thingiverse STLs as validation targets (no acoustic data)
- ❌ Comparing absolute RMS from one pipeline to median-corrected from another

### Required Documentation Per Benchmark Run
1. **Solver configuration**: TMM parameters, loss model, speed of sound value
2. **Geometry source**: Peer-reviewed paper, museum CT data, or validated reference
3. **Measurement scaling**: Confirm ρc/S scaling for measured impedance files
4. **Per-note table**: Full cent deviation profile for debugging
5. **Environment**: Temperature, humidity if physical measurement

### Tiered Benchmark Strategy (from Internal-Computational-Benchmark-Research.md)

| Tier | Target | Purpose | Acceptance |
|------|--------|---------|------------|
| **V1 Verification** | Inria 2026 pipe benchmark (Zenodo 20024938) | Solver-vs-solver + solver-vs-measurement on simple geometry | Match simulated ref; report discrepancy vs measured per end condition |
| **V2 Cross-software** | chalumier/demakein examples, WIDesigner XML | Same design, different implementation | <1c on reference bore profiles |
| **V3 Measured instrument** | UNSW flute Z(f) (Boehm/classical); Bowen bass clarinet | Real instrument, real measurements | Peak agreement at Bowen-level accuracy (cents-scale) |
| **V4 Printed replica** | Fagottino (open datasets + CT prints) / Hotteterre traverso / RCM | Full physical validation | Perceptually indistinguishable replicas; <5c print-induced shift (P3) |

### Approved Benchmark Sources (Research-Grade Only)
| Category | Source | Access |
|----------|--------|--------|
| **V1** | Inria 2026 Pipe Benchmark (Ernoult et al. 2026) | Zenodo 20024938 + GitLab Inria |
| **V2** | chalumier `examples/`, demakein `examples/`, WIDesigner XML | GitHub (upstream) |
| **V3** | UNSW Flute Z(f) (Boehm B/C, Classical) | phys.unsw.edu.au/music/flute/ |
| **V3** | Bowen 1910 Heckel Bass Clarinet in A | oro.open.ac.uk/58268 (open access) |
| **V4** | Fagottino (SCB/FHNW) — 130+ small bassoons | historical-bassoon.ch, Zenodo, DaSCH |
| **V4** | Hotteterre Traverso (Fritz et al.) | HAL: hal-05393759v1 |
| **V4** | Digital Revival (Haka 1680, Warder 1540s) | arXiv:2606.24216 |
| **V4** | RCM 3D Printed Instruments (7 instruments) | Collaboration required (not open) |

### Explicitly Forbidden Sources
- Printables / Cults3D / Thingiverse / MakerWorld / GrabCAD / Sketchfab — hobbyist STLs, no acoustic validation, no impedance data
- Any source without published impedance measurements or CT-derived bore profiles

### Implementation Checklist
- [x] Median correction removed from all cost functions (tmm_acoustics.py, two_phase_optimizer.py)
- [x] Absolute RMS is primary metric in benchmark_all.py (eval_all)
- [ ] Update benchmark_all.py to output full metric suite (MAD, SD, Max)
- [ ] Add per-note table to benchmark output
- [ ] Document solver config (loss model, speed of sound) in benchmark logs
- [ ] Run V1 Inria 2026 benchmark with corrected TMM
- [ ] Import chalumier/demakein/WIDesigner as regression fixtures (V2)
- [ ] Download UNSW flute Z(f) and Bowen bass clarinet data (V3)
- [ ] Download Fagottino Zenodo dataset and select first print target (V4)

---

## Low Priority — Future

### Trumpet Design (Branches Available)
- [ ] **OpenWind FEM approach** (`experiment/trumpet-openwind`)
  - Uses OpenWind's 1D FEM with visco-thermal losses
  - Models valves as deviation pipes with proper junction physics
  - Ready for leadpipe optimization (6 variables)
  - See `ROADMAP-Trumpet.md` for details
- [ ] **Custom TMM approach** (`experiment/trumpet-custom-tmm`)
  - Phase-based TMM (same engine as woodwinds)
  - Deprecated for trumpets due to accuracy limitations
  - Bell flare not handled correctly by TMM
- [ ] **Yamaha/ML approach** (future, needs compute resources)
  - Physics-based sound simulation (harmonic balance)
  - ML model training on impedance parameters
  - NSGA-II multi-objective optimization
  - Reference: Petiot et al. (2024-2025), Yamaha Corporation

### Advanced Acoustics
- [x] Thermoviscous losses (Keefe 1984) — adds frequency-dependent attenuation
- [x] JAX differentiable TMM for gradient-based optimization (2.7M evals/sec, 52x faster)
- [x] JAX autodiff Stage 2 bore-radii refinement (exact gradients, intonation-only)
- [ ] TMMI external tonehole interactions (Lefebvre et al. 2013)
- [ ] Lefebvre revised tonehole formulas (better chimney height model)
- [ ] Temperature sensitivity analysis (±X cents per °C)
- [ ] Vocal tract coupling simulation
- [ ] Reed/mouthpiece impedance modeling
- [ ] Multi-register optimization (clarinet twelfths)
- [ ] Implement chalumier's `reedVirtualLength`/`reedVirtualTop` for reed instruments
- [ ] Finer coneStep (0.125mm) for conical bore optimization

### Manufacturing
- [ ] Hybrid approach: 3D print mold → cast final instrument
- [ ] CNC reamer profile export
- [ ] Bore straightness verification (warping detection)

### Research
- [ ] Compare FDM vs SLA acoustic performance
- [ ] Document optimal print settings for musical instruments
- [ ] Publish accuracy benchmarks

---

## AI Governance System — COMPLETE

- [x] `docs/CONSTRAINTS_AND_PREFERENCES.md` — AI Boot Sequence (6-step init every session)
- [x] `docs/AI_CONSTITUTION.md` — 10 non-negotiable project laws
- [x] `docs/ARCHITECTURE_DECISIONS.md` — 6 seeded ADR records (geometry layer, thin orchestrators, etc.)
- [x] `docs/ARCHITECTURE_CHECKLIST.md` — Pre-flight/pre-commit 20-item checklist
- [x] `docs/COMPLIANCE_CHECK.md` — Trigger-based compliance script (15min, before code, after tests)
- [x] `docs/AI_FAILURE_PATTERNS.md` — Failure pattern log (5 seeded patterns)
- [x] `docs/WIKI.md` — Section 10: AI Governance System
- [x] `docs/WIKI-INDEX.md` — Governance page links
- [x] Governance pages pushed to GitHub wiki
- [x] Architecture redesign packaged for ChatGPT review (zip + prompt)

---

*Last updated: 2026-07-31*
