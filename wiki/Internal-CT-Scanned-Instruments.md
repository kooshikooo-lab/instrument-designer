# CT-Scanned Historical Instruments — Benchmarking Reference

> Verified 3D geometry of historical woodwind instruments, obtained by CT/micro-CT
> scanning and X-ray tomography. These are the strongest possible reference objects
> for *physical* benchmarking: print a verified replica and compare acoustically.
> Sources verified 2026-07-31. See also [[Internal-Computational-Benchmark-Research]].

---

## 1. Why CT scans matter for benchmarking

A CT scan gives the **true internal geometry** (bore profile, tonehole undercuts,
chimney walls) of an intact historical instrument — data that is otherwise
unavailable without destructive disassembly. This makes CT-derived models the gold
standard for:

- **Bore-profile benchmarks** — exact radius vs position curves to feed TMM/FEM.
- **Physical validation** — print a verified replica, measure its impedance, compare to the original's measured behavior and to simulation.
- **Perceptual validation** — published listening tests show 3D-printed replicas can be near-indistinguishable from originals (Hotteterre traverso study).
- **Design reference** — historical instruments encode centuries of maker refinement (Denner, Hotteterre, Scherer).

## 2. Projects & datasets

| Project | Instruments | Scanning method | Data availability |
|---------|-------------|-----------------|-------------------|
| **RCM 3D Printed Musical Instruments** (Rossi Rognoni, Royal College of Music + U. Turin) | 7 instruments: 5 ivory (two alto recorders — Jacob Denner, Paul Villars; early clarinet — George Heinrich Scherer; flute — Ignaz Scherer; renaissance cornett) + 2 boxwood (oboe — Jacob Grundman; recorder — Johann W. Oberlender) | Micro-CT (Brett Clark, NHM London) + digital restoration (Xiccato & Tansella); acoustical comparison with originals | Not open; project page + "3D Printing and Musical Heritage" conference (2024-03-18) + YouTube playlist. Best collaboration candidate. |
| **Hotteterre traverso** E.999.6.1 (Musée de la Musique, Paris; Fritz group, IJLRDA-LAM) | Traverso attributed to Jacques Martin Hotteterre (c. 1707–1727) | X-ray tomography → stereolithography print | Study open on HAL; data per journal availability statement |
| **Fagottino** (Schola Cantorum Basiliensis / FHNW) | 130+ small bassoons (fagottini/tenoroons) documented; instrument measurement datasets on Zenodo | CT-based 3D prints (3DFagottini) | **Open** — most open museum-grade dataset found: measurement datasets on Zenodo, metadata at meta.dasch.swiss/projects/0845 |
| **Warder flute** (Huis van Hilde, NL) | 1540s shipwreck Renaissance traverso (oldest surviving flute in the Netherlands); studied with c.1680 Haka traverso (Rijksmuseum) | CT (TU Delft) + physical modeling; replicas by Roberto Bando; dataset: 3D models (exterior + bore), IMA volumetric scans, geometric measurements | Digital Revival project (arXiv:2606.24216v1, ISMA 2026/POMA); 3D scan on Sketchfab (Instrumenta exhibition) |
| **Qiao border pipes** (Queen's Univ. Belfast PhD) | Historical border pipes | Manual + flatbed + 3D scan + CT; SLS printing | Open-access thesis with STL models in appendix; openNSP_Project (OpenSCAD Northumbrian small-pipes) on GitHub |

## 3. Using them as benchmark targets

| Tier | Use | Acceptance |
|------|-----|------------|
| V3 | Bore-profile → impedance comparison (if measured Z(f) available) | Peak agreement at Bowen-level accuracy (cents-scale) |
| V4 | Print verified replica → measure → compare vs simulation and original | Perceptually indistinguishable replica; <5c print-induced shift (P3 target) |

**Key methodology findings:**
- Bowen et al. (2019, *Applied Acoustics* 143:84–99): bore geometry alone can predict impedance of playable instruments — validated vs measured impedance + playing tests on a 1910 Heckel bass clarinet in A. https://doi.org/10.1016/j.apacoust.2018.08.028
- Eveno & Le Conte (2016, *J. Cultural Heritage* 20:615–621): non-invasive impedance measurement of 45 serpents (Musée de la Musique) — routine and reliable. https://doi.org/10.1016/j.culher.2016.02.005
- Fritz et al. (Hotteterre traverso): 3D-printed copy vs wooden facsimile — 69 listeners + 9 players, discrimination near chance. Replicas are valid research instruments.
- Szwarcberg et al. (2025): fabrication tolerance bar — 0.1 mm radius → 3.4c, chimney +1 mm → 4c.

## 4. Caveats

- **Mostly not openly downloadable** — RCM and Musée de la Musique data are not public; Fagottino is the open exception. For the others, request collaboration or wait.
- **External vs internal geometry** — scans capture walls; bore must be extracted from the internal air column (segmentation step).
- **Materials differ** — a 3D-printed ABS/UV-resin replica has different losses than ivory/boxwood; impedance peaks shift with wall losses. Correct via simulation (materials known) or calibration.
- **Historical tuning ≠ modern** — pitch standards (A440 vs A415 etc.) and temperament differ; normalize before comparing cents.

## 5. Full URL list

| Source | URL |
|--------|-----|
| RCM 3D Printed Musical Instruments | https://www.rcm.ac.uk/research/projects/3dprintedmusicalinstruments |
| Hotteterre traverso study (HAL) | https://hal.sorbonne-universite.fr/IJLRDA-LAM/hal-05393759v1 |
| Digital Revival: Haka & Warder flutes (arXiv) | https://arxiv.org/abs/2606.24216 |
| Fagottino / historical bassoon (SCB/FHNW) | https://historical-bassoon.ch |
| 3D Fagottini (FHNW) | https://www.fhnw.ch/plattformen/3dfagottino/ |
| Fagottino project metadata (DaSCH) | https://meta.dasch.swiss/projects/0845/ |
| Bowen et al. 2019 Applied Acoustics | https://doi.org/10.1016/j.apacoust.2018.08.028 |
| Eveno & Le Conte 2016 J. Cultural Heritage | https://doi.org/10.1016/j.culher.2016.02.005 |
| openNSP_Project (OpenSCAD small-pipes) | https://github.com/Z-QIAO/openNSP_Project |

---

## 6. Related

- [[Internal-Computational-Benchmark-Research]] — full benchmarking report (V1–V4 tiered strategy)
- [[Internal-Research]] — topic-indexed reference tables
- [[3D-Printing-Guide]] — printing conventions for replica work
- Roadmap: `docs/ROADMAP.md` → "Computational Modeling & Benchmarking Research"
