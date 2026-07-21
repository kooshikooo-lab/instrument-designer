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
- [x] STL generation: added Make_flute/Make_reed_instrument step after optimization
- [x] Quick mode support for demakein designs (faster draft iterations)
- [x] chalumier wrapper module (ready when JDK is available)
- [x] Error handling: _run_design try/except, unified job status responses
- [x] freecad_engine.py: robust JSON parsing from stdout
- [x] YAML bore_length unit consistency (mm throughout)
- [x] validate_optimizer.py: fixed paths, phased thresholds, portability

---

## Phase 1: Computational Accuracy & Speed (CURRENT FOCUS)

> **Before starting work here:** Check the "Periodic Research Review" section
> below for new papers or tool updates that may change the approach.

Everything here is software-only — no printing required. The goal is a fast,
accurate optimizer that matches or exceeds demakein/chalumier on reference instruments.

**Target: <3 cents computational error, <60 seconds per design.**

### 1a. Speed — Parallelize Optimizer
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

### 1b. Accuracy — Bore Quality Constraints
- [ ] Add monotonicity constraint (docstring promises it, code doesn't implement it)
  - `n_ieq_constr=0` in current code — bore can go backwards
  - Must land BEFORE increasing control points — extra DOF without constraints = jaggier bores
  - Implementation: inequality constraint `bore[i+1] >= bore[i]` for all i
- [ ] Add smoothness constraint (penalize large radius jumps between adjacent points)
- [ ] Add global pitch offset correction (shift all peaks by constant cents offset)
- [ ] Improve scale evenness objective (currently std of diffs, consider musical intervals)
- [ ] Add support for clarinet odd-harmonic tuning (every other peak)

### 1c. Validation — Benchmark Against Other Software
Our optimizer should match or exceed demakein/chalumier accuracy on the same
reference instruments. This is the "match or exceed" requirement.

- [ ] Run optimizer on all reference instruments (clarinet_Bb, penny_whistle_D, recorder_soprano)
- [ ] Run demakein on same reference instruments and compare accuracy
- [ ] Run chalumier on same reference instruments (when JDK available)
- [ ] Document accuracy comparison: ours vs demakein vs chalumier
- [ ] If ours is worse, identify why and fix
- [ ] If ours is better, document what we did differently

### 1d. Bore Representation
Sequencing: smoothness constraint first, then more control points.
- [ ] Test with more control points (12 → 20-30 for complex profiles)
  - Only after monotonicity constraint is in place

### Computational Accuracy Targets
| Phase | Target | Requirements | Status |
|-------|--------|--------------|--------|
| C1 | <20 cents | Parallelizer + current code | First milestone |
| C2 | <10 cents | Monotonicity constraint + tuning | After C1 |
| C3 | <5 cents | Noreland-level (0.49 cents RMS) | Stretch goal |
| C4 | <3 cents | Best-case everything | Ultimate goal |

**Benchmark:** Noreland clarinet (2013) achieved 0.49 cents RMS fundamental,
<5 cents after removing global offset. We should match this.

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
- [ ] Install JDK 17+ (required to build/run chalumier)
- [ ] Build chalumier JAR (`gradle shadowJar`)
- [ ] Create chalumier wrapper (like demakein_wrapper.py) for the design server
- [ ] Compare chalumier vs demakein output quality and speed
- [ ] Add chalumier instrument types to preset list
- [ ] Support `.chal` specification files in the web UI

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

## Low Priority — Future

### Advanced Acoustics
- [ ] Temperature sensitivity analysis (±X cents per °C)
- [ ] Vocal tract coupling simulation
- [ ] Reed/mouthpiece impedance modeling
- [ ] Multi-register optimization (clarinet twelfths)

### Manufacturing
- [ ] Hybrid approach: 3D print mold → cast final instrument
- [ ] CNC reamer profile export
- [ ] Bore straightness verification (warping detection)

### Research
- [ ] Compare FDM vs SLA acoustic performance
- [ ] Document optimal print settings for musical instruments
- [ ] Publish accuracy benchmarks

---

*Last updated: 2026-07-22*
