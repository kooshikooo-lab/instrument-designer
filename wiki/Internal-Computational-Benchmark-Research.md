# Computational Modeling & Benchmarking Research

> Full report: computational modeling, benchmarking methods, verified 3D models, and
> validation targets for wind instrument design. Sources verified 2026-07-31.
> Saved to the wiki and mirrored on the roadmap (`docs/ROADMAP.md`).

---

## 1. Purpose & Scope

This report consolidates all research on **how we verify and validate** our wind
instrument design pipeline. It covers the full chain:

1. **Computational modeling** — the solvers and tools we use or could use (TMM, OpenWInD, demakein, chalumier, WIDesigner, NESS).
2. **Benchmarking methods** — the specific interest: published V&V benchmarks, measured datasets, cross-software comparisons, and metric standardization.
3. **Verified 3D models & reference objects** — CT-scanned historical instruments, measured bore profiles, open datasets, and 3D-printed replicas usable as benchmark targets.

**Bottom line:** There is no single "golden instrument" dataset for woodwinds yet.
Instead there are *layered* targets: simple-pipe verification benchmarks (fully
downloadable), measured-impedance datasets (downloadable), software instrument
definitions (downloadable), and museum CT scans (real but mostly not open).
The 2026 Inria benchmark is the closest thing to a standard V&V suite we can run
our solvers against today.

---

## 2. Benchmarking Methods (Primary Interest)

### 2.1 V&V benchmark: multi-lab pipe impedance round-robin (2026)

The most important find. A published verification & validation benchmark for
exactly our kind of solver.

| Aspect | Detail |
|--------|--------|
| Paper | "Benchmark study of pipe input impedance simulations and measurements for verification and validation in musical acoustics context" |
| Authors | Ernoult, Viala, Cabaret, Chassabier, Colinot, Dalmont, Doc, Fréour |
| Journal | *Acta Acustica* 10 (2026) 51 |
| DOI | https://doi.org/10.1051/aacus/2026048 |
| Published | 2026-06-19, *Acta Acustica* 10, article 51 |
| Method | Round-robin: multiple research groups independently simulate AND measure input impedance of identical pipes, then compare |
| Objects | 180 mm pipes: cylinders (14 mm ID, 4 end conditions) and cones (10→22.6 mm, 3 end conditions) |
| Materials | Brass, boxwood, and **3D-printed ABS** (directly relevant to our printing work) |
| Replicates | 5 pipes per batch, 9 impedance measurements per (configuration, material) combination |
| Data | Zenodo dataset v2: **https://zenodo.org/records/20024938** ("Acoustic impedance of 180mm long pipes: simulations and measurements") |
| Processing scripts | GitLab (Inria): `aernoult/acoustic-impedance-benchmark` |
| Format | 3-column impedance files (f, Re(Z), Im(Z)); measured scaled by ρc/S, simulated not |
| Why it matters | This is the canonical V&V suite for pipe- and bore-solvers. We should run `tmm_acoustics.py` against the cylinder/cones and compare to both simulated and measured reference curves. |

**Verification vs validation distinction (from the paper):**
- *Verification* — compare our solver to other solvers (OpenWInD, etc.) on identical geometry.
- *Validation* — compare to physical measurement (the round-robin measured data).

### 2.2 Measured impedance databases (validation targets)

| Dataset | What it gives us | Access |
|---------|------------------|--------|
| UNSW Flute Acoustics — **impedance Z(f) downloads** | Z(f) Excel files (4 sheets: \|Z\|, arg(Z), Re(Z), Im(Z)) for Boehm B-foot, Boehm C-foot, and classical flute; comparisons also cover baroque flute and classical flared foot; resonance peak positions per fingering | https://www.phys.unsw.edu.au/music/flute/ (`B foot`, `C foot`, `Classical` downloads + multiphonics) |
| Wolfe/UNSW instrument pages | Multiple instrument impedance measurements (flute, clarinet compendium, saxophone), cutoff frequency theory | https://www.phys.unsw.edu.au/jw/instr.html |
| Bowen et al. (2019) bass clarinet | Impedance computed from measured bore geometry vs measured impedance + playing tests (Heckel bass clarinet in A, 1910); method shown viable for museum instruments | https://doi.org/10.1016/j.apacoust.2018.08.028 (Open Access: http://oro.open.ac.uk/58268) |
| Eveno & Le Conte (2016) serpent study | Non-invasive input impedance of 45 historical serpents (Musée de la Musique), piezo-buzzer 2-mic transfer function; common acoustic behavior across family | https://doi.org/10.1016/j.culher.2016.02.005 |
| BIAS system (Widholm 1995) | Commercial impedance measurement system; methodology reference (used by Bowen et al.) | https://www.widholm.at/wp-content/uploads/2021/01/1995_Brass_wind_instrument_quality_measured_and_evaluated_by_a_new_computer_system.pdf |

**Key methodology lessons:**
- **Measured data in impedance files is usually scaled by ρc/S; simulations are not.** Check the scaling before comparing (the 2026 benchmark documents this explicitly).
- **Bore geometry alone may be sufficient to predict impedance** for playable instruments (Bowen et al. 2019: geometry-only prediction cross-checked against measured impedance and playing tests on a playable Heckel bass clarinet in A from 1910). This validates a geometry-only benchmark approach.
- End-condition (flanged/unflanged, open/closed) is a first-order effect — the 2026 benchmark isolates it with 4 cylinder end conditions.

### 2.3 Metric standardization (our own benchmarking quality)

From `docs/ROADMAP.md` §1g and Internal-Research:

| Metric | Meaning | Notes |
|--------|---------|-------|
| Absolute RMS (c) | Accuracy: `sqrt(mean(cent_dev²))` | What benchmark_all.py reports |
| MAD (c) | Robust accuracy: `mean(\|cent_dev\|)` | Bertsch (1998): inter-player SD 7–15c |
| SD (c) | Evenness: `std(cent_dev)` | Median-corrected metrics measure evenness, NOT accuracy |
| Max deviation (c) | Worst note | Professional standard ~5–10c |

**Critical finding (2026-07-25):** median correction in cost functions measures
*scale evenness*, not *pitch accuracy*. These are not comparable numbers
(0.01c evenness ≠ 0.01c accuracy). Any benchmark we publish must report both.

**Published accuracy anchors:**
- Noreland et al. (2013) logical clarinet: 0.49c RMS (arXiv:1209.3637)
- Ernoult et al. (2020) pentatonic clarinet: <0.025c (doi:10.1121/10.0002449)
- Our Phase 2b: 0.00–0.32c RMS on 5 instruments
- WIDesigner: ~1–5c simple, 5–15c complex instruments

### 2.4 Cross-software benchmarking

| Comparison | Status | Lesson |
|------------|--------|--------|
| Ours vs chalumier (same bore profile) | DONE | TMM matches chalumier given same profile |
| L-BFGS-B refinement from chalumier bore | DONE | 3.5c vs chalumier's 29c (5x better) |
| Ours vs WIDesigner | **TODO** (Phase 1h-d) | Run same instruments through both |
| Ours vs OpenWInD on 2026 benchmark pipes | **TODO** (new) | Verification step, §2.1 |
| Ours vs UNSW flute measured Z(f) | **TODO** (new) | Validation step, §2.2 |
| Ours vs demakein examples | Possible | demakein is the reference Python TMM; examples in repo |

---

## 3. Computational Modeling Landscape

### 3.1 Solvers

| Tool | Type | Model | Relevance |
|------|------|-------|-----------|
| `backend/tmm_acoustics.py` | TMM (stepped bore) | Transfer matrices + Keefe toneholes | Our engine, ported from chalumier/demakein |
| OpenWInD (Inria, GPLv3) | 1D FEM | Axisymmetric bore + toneholes + viscothermal losses | Reference solver; used in the 2026 V&V benchmark; geometry via `[[0,0.5,4e-3,10e-3,'cone']]` or `geometry = filename.txt` |
| demakein (Scavone) | TMM | Parametric flutes/whistles/shawms | Reference Python implementation; examples in repo |
| chalumier (Kotlin) | TMM | demakein port + SVG/JSON output | Reference implementation; `examples/` has instrument specs |
| WIDesigner (Patkau, Java) | TMM + DIRECT-C/BOBYQA | Instrument + tuning XML models | Independent TMM implementation for cross-validation |
| NESS (Edinburgh) | FDTD/waveguide | Full physical modeling | Overkill for static optimization, useful for embouchure research |

### 3.2 Cost functions & resonance tracking

| Method | Reference | Status |
|--------|-----------|--------|
| Peak-finding (ours) | — | Non-smooth landscape |
| Unwrapped-phase tracking | Ernoult et al. 2020 (doi:10.1121/10.0002449) | **To implement** (Phase 1h-a); smoother, differentiable |
| Phase-based cost sin²(π·dev) | Ernoult et al. 2020 | Smoother cost surface |

### 3.3 Bore reconstruction (inverse problem)

Impedance measurement → bore profile. Relevant for Phase 2c (measure → optimize → print → measure loop).

| Reference | Method | Relevance |
|-----------|--------|-----------|
| OpenWInD / Inria Makutu team | Adjoint-based inverse bore reconstruction | https://openwind.inria.fr/ ; https://team.inria.fr/makutu/bore-reconstruction-of-woodwind-like-instruments/ |
| Ernoult et al. | Inverse-problem bore reconstruction from Z(f) | Validates "measure impedance, recover geometry" loop |

---

## 4. Verified 3D Models & Reference Objects

### 4.1 CT-scanned museum instruments (real 3D geometry)

> Dedicated reference doc (benchmarking focus, caveats, URLs):
> **[[Internal-CT-Scanned-Instruments]]** · local copy: `docs/REFERENCE_CT_SCANNED_INSTRUMENTS.md`

These are genuine, verified 3D models of historical instruments — the gold standard
for *physical* validation (print a copy, compare acoustically). **Most are not openly
downloadable yet** — they are the strongest candidates for collaboration/requests.

| Project | Instruments | Method | Access |
|---------|-------------|--------|--------|
| **RCM "3D Printed Musical Instruments"** (Rossi Rognoni, Royal College of Music + U. Turin) | 7 instruments: 5 ivory (two alto recorders: Jacob Denner + Paul Villars; early clarinet: George Heinrich Scherer; flute: Ignaz Scherer; renaissance cornett) + 2 boxwood (oboe: Jacob Grundman; recorder: Johann W. Oberlender) | Micro-CT scanning → digital restoration → 3D printing accurate historical copies; acoustical comparison with originals + player/audience studies | Project page: https://www.rcm.ac.uk/research/projects/3dprintedmusicalinstruments ; "3D Printing and Musical Heritage" online conference (2024-03-18) + YouTube playlist; funded by DCMS/Wolfson Museum and Galleries Improvement Fund |
| **Hotteterre traverso** (Musée de la Musique, Paris) | Traverso E.999.6.1 attributed to Jacques Martin Hotteterre (c. 1707–1727) | X-ray tomography → stereolithography 3D-printed copy; perceptual + playing comparison vs original | Study: https://hal.sorbonne-universite.fr/IJLRDA-LAM/hal-05393759v1 (Fritz group / IJLRDA-LAM); *Music & Science* 2025 |
| **Fagottino** (Schola Cantorum Basiliensis, FHNW) | 130+ small bassoons (fagottini/tenoroons) documented; instrument measurement datasets on Zenodo | CT-based 3D prints + measurement datasets | **Open**: https://historical-bassoon.ch ; 3D prints: https://www.fhnw.ch/plattformen/3dfagottino/ ; metadata: https://meta.dasch.swiss/projects/0845/ |
| **Warder flute** (Huis van Hilde, NL) | 1540s shipwreck Renaissance traverso (oldest surviving flute in NL); studied alongside c.1680 Haka traverso | CT scan (TU Delft) → geometry-based physical modeling; replicas built by Roberto Bando; dataset: 3D models (exterior + bore interior), IMA volumetric scans, geometric measurements | *Digital Revival* project, arXiv:2606.24216v1 (ISMA 2026 / POMA); 3D scan also on Sketchfab (Instrumenta exhibition) |
| **Qiao border pipes** (Queen's Univ. Belfast PhD) | Historical border pipes | Manual + flatbed + 3D scan + CT; SLS printing; STL models in thesis appendix | Open access thesis; openNSP_Project GitHub (OpenSCAD Northumbrian small-pipes) |

### 4.2 Digital revival / non-invasive characterization

- **"Digital Revival: Acoustic Documentation and Digital Reactivation of Historical Woodwind Instruments"** — Arbel & Weissman, arXiv:2606.24216v1 (ISMA 2026, Helsinki; to appear in POMA). Project with Rijksmuseum / Kunstmuseum Den Haag / Huis van Hilde: documents the **Richard Haka traverso (c. 1680)** and the **Warder flute (1540s)** via high-resolution sampling, scan data, physical modeling, and EWI-controlled playback.
- Its background cites the two methods most relevant to us:
  - **Eveno & Le Conte (2016, *J. Cultural Heritage* 20:615–621, DOI 10.1016/j.culher.2016.02.005)** — non-invasive input-impedance measurement of **45 serpents** (Musée de la Musique; piezo buzzer, 2-mic transfer function); consistent resonance characteristics across specimens.
  - **Bowen et al. (2019, *Applied Acoustics* 143:84–99, DOI 10.1016/j.apacoust.2018.08.028)** — bore-geometry-only impedance prediction validated against measured impedance + playing tests for a playable 1910 Heckel bass clarinet in A.
  - **Key takeaway:** non-invasive impedance measurement of fragile originals is now routine; geometry-based prediction is validated for playable instruments.

### 4.3 3D-printed replica acoustic studies (validation methodology)

| Study | Finding | Relevance |
|-------|---------|-----------|
| Hotteterre traverso perceptual study (Fritz et al.) | 3D-printed copy vs wooden facsimile: 69 listeners + 9 players; discrimination near chance level; players found the wooden facsimile richer/warmer, the print "overly easy and homogeneous" | 3D-printed replicas can be perceptually indistinguishable — validates printing as a research/benchmark tool |
| RCM project | CT → digital restoration → print of 7 instruments | Methodology for producing verified 3D benchmark models |
| Bowen bass clarinet | Geometry-only impedance prediction validated | Geometry is the benchmark variable, not material |
| Szwarcberg et al. (2025) sensitivity | 0.1 mm radius → 3.4c; chimney +1 mm → 4c | Fabrication tolerance target for benchmark acceptance |

---

## 5. Consumable Reference Data (Directly Downloadable)

These are the *actionable* benchmark inputs today:

| Source | Content | How to consume |
|--------|---------|----------------|
| Inria pipe benchmark (Zenodo 20024938) | Measured + simulated impedance, 180 mm cylinders & cones, brass/boxwood/ABS | Compare `tmm_acoustics.py` output to reference curves (§2.1) |
| UNSW flute page | Z(f) Excel files (Boehm B/C foot, classical flute; baroque flute in comparisons) | Impedance validation targets; resonance peaks per fingering |
| WIDesigner repo | Instrument + tuning XML (tonehole positions/diameters, bore transitions) | Parse XML as regression fixtures |
| chalumier repo `examples/` | Reference `.chal` instrument definitions | Port as fixtures (local `chalumier/` dir is empty; fetch upstream: github.com/MarkChuCarroll/chalumier) |
| demakein repo `examples/` | simple_reedpipe, simple_flute, simple_shawm, stepped_shawm | Reference Python designs |
| OpenWInD geometry format | `[[start, end, r1, r2, 'shape']]` or text file | Feed geometry directly to FEM for cross-check |
| Fagottino (SCB/FHNW) | Measurement datasets on Zenodo + CT-based 3D-printed small bassoons | Most open museum-grade dataset found: https://historical-bassoon.ch ; https://www.fhnw.ch/plattformen/3dfagottino/ |

**Not usable for acoustic benchmarks** (visual meshes only, no bore/impedance data):
Sketchfab museum collections (e.g. clarinet mouthpiece CT scans), MakerWorld/Thingiverse/
Printables/Cults3D/GrabCAD instrument models. Good for reference/inspiration, not V&V.

---

## 6. Recommendations

### Tiered benchmark strategy

| Tier | Target | Purpose | Acceptance |
|------|--------|---------|------------|
| **V1 (Verification)** | Inria 2026 pipe benchmark (Zenodo 20024938) | Solver-vs-solver + solver-vs-measurement on simple geometry | Match simulated reference; report discrepancy vs measured per end condition |
| **V2 (Software cross-check)** | chalumier/demakein examples, WIDesigner XML | Same-design, different-implementation agreement | <1c on reference bore profiles |
| **V3 (Measured instrument)** | UNSW flute Z(f) (Boehm/classical); Bowen bass clarinet | Real instrument, real measurements | Peak agreement at Bowen-level accuracy (cents-scale) |
| **V4 (Printed replica)** | Fagottino models / Hotteterre traverso copies / RCM prints | Full physical validation | Perceptually indistinguishable replicas (Fritz result); <5c print-induced shift (P3 target) |

### Actions for our pipeline

- [ ] **V1**: Run `backend/tmm_acoustics.py` and OpenWInD on the 2026 benchmark cylinders/cones; store comparison notebook + figures under `research/`.
- [ ] **Metric discipline**: report absolute RMS + MAD + SD + max deviation in `benchmark_all.py` (already planned in ROADMAP §1g).
- [ ] **Fixture import**: add chalumier `examples/`, demakein `examples/`, and a parsed WIDesigner XML as regression fixtures.
- [ ] **UNSW Z(f)**: download the Boehm/classical flute Excel files, extract resonance peaks per fingering, compare to our model of the same fingering.
- [ ] **Physical loop (Phase 2)**: leverage bore reconstruction (OpenWInD adjoint, Ernoult FWI) to close measure→optimize→print→measure.
- [ ] **Tracking**: RCM / Fagottino / Hotteterre projects for future open CT data (RCM data not yet downloadable; Fagottino measurement datasets already on Zenodo).

---

## 7. Full Reference List (URLs)

| Reference | URL |
|-----------|-----|
| Ernoult et al. 2026 Acta Acustica V&V benchmark | https://doi.org/10.1051/aacus/2026048 |
| 2026 benchmark dataset (Zenodo v2) | https://zenodo.org/records/20024938 |
| 2026 benchmark scripts (GitLab Inria) | https://gitlab.inria.fr/aernoult/acoustic-impedance-benchmark |
| RCM 3D Printed Musical Instruments | https://www.rcm.ac.uk/research/projects/3dprintedmusicalinstruments |
| Hotteterre traverso study (HAL) | https://hal.sorbonne-universite.fr/IJLRDA-LAM/hal-05393759v1 |
| Digital Revival: Haka & Warder flutes (arXiv) | https://arxiv.org/abs/2606.24216 |
| OpenWInD | https://openwind.inria.fr/ |
| OpenWInD (thecowgoesmoo fork, GitHub) | https://github.com/thecowgoesmoo/openwind |
| Makutu bore reconstruction | https://team.inria.fr/makutu/bore-reconstruction-of-woodwind-like-instruments/ |
| chalumier | https://github.com/MarkChuCarroll/chalumier |
| demakein | https://github.com/garyscavone/demakein |
| WIDesigner | https://github.com/edwardkort/WWIDesigner |
| UNSW flute acoustics | https://www.phys.unsw.edu.au/music/flute/ |
| UNSW instrument measurements | https://www.phys.unsw.edu.au/jw/instr.html |
| Fagottino / historical bassoon (SCB/FHNW) | https://historical-bassoon.ch |
| 3D Fagottini (FHNW) | https://www.fhnw.ch/plattformen/3dfagottino/ |
| Fagottino project metadata (DaSCH) | https://meta.dasch.swiss/projects/0845/ |
| Bowen et al. 2019 Applied Acoustics (open.ac.uk) | http://oro.open.ac.uk/58268 |
| Eveno & Le Conte 2016 J. Cultural Heritage | https://doi.org/10.1016/j.culher.2016.02.005 |
| openNSP_Project (OpenSCAD small-pipes) | https://github.com/Z-QIAO/openNSP_Project |
| Noreland 2013 logical clarinet | https://arxiv.org/abs/1209.3637 |
| Ernoult et al. 2020 JASA | https://doi.org/10.1121/10.0002449 |
| BIAS (Widholm 1995) | https://www.widholm.at/wp-content/uploads/2021/01/1995_Brass_wind_instrument_quality_measured_and_evaluated_by_a_new_computer_system.pdf |

---

## 8. Related Pages

- [[Internal-Research]] — topic-indexed reference tables (this report is the companion deep-dive)
- [[Internal-CT-Scanned-Instruments]] — dedicated reference doc on CT-scanned historical instruments (benchmarking focus)
- [[Internal-Goals]] — project goals, accuracy targets
- [[3D-Printing-Guide]] — printing conventions the printed-replica work must align with
- Roadmap: `docs/ROADMAP.md` → "Computational Modeling & Benchmarking Research" section
