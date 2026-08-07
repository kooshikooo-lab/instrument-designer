# RESEARCH — CT-Scan Benchmarking & Bore Reconstruction (Phase 2, Issue #47)

Status: **REFERENCE — saved for future work** (no code changes)
Date: 2026-08-07
Author: laptop (opencode)
Sources: live web research (2026-08-07) + repo state
(`backend/two_phase_optimizer.py`, `docs/ROADMAP.md` Phase 2, REMINDERS thread 18).

## Purpose

Phase 2 (Issue #47) plans to download **FT40/FT44** fagottini from Zenodo, extract
bore profiles, run the two-phase optimizer, and document RMS vs CT ground truth.
This doc turns that plan into concrete, verified steps and corrects a few
assumptions in prior notes (the "Virtual 3D Clarinet Museum" is photogrammetry,
not CT; MUSICES bulk DICOM is not openly downloadable).

## TL;DR

1. **FT40 & FT44 are fully open access** — CT-derived 3D models (STL) are on the
   DaSCH project `ark:/72163/1/0845` (CC BY 4.0), with Zenodo bore-measurement PDFs
   (FT40 DOI 10.5281/zenodo.3241619; FT44 DOI 10.5281/zenodo.4287374). No
   permission needed — direct download.
2. **Pipeline: Slicer + VMTK** (`Extract Centerline` → `Cross-Section Analysis`)
   returns per-point centerline coordinates *and radii* as numpy arrays — i.e. a
   radius-vs-arclength profile — and works directly on the STL meshes, so no DICOM
   handling is required for FT40/FT44.
3. **Accuracy bar from the literature:** bore-reconstruction via OpenWInD FWI
   achieves ≤0.1 mm radii, ≤0.5 mm hole positions, ≤0.3 mm chimneys (Ernoult 2021,
   ~1 min on a laptop); impedance peak agreement <10 cents is the standard for
   TMM-vs-measured. Use these as sanity thresholds.
4. **Honest gap:** no published study directly reports "TMM-simulated impedance vs
   impedance from a CT-derived bore with RMS error" — this project's Phase 2 would
   be the first. That is an opportunity, not a risk to the plan.

## 1. Datasets (verified 2026-08-07)

- **FT40** — Anonymous (11), 4-key fagottino, Germany ca. 1750–1790, private Swiss
  collection. Zenodo DOI **10.5281/zenodo.3241619** (bore measurements, photos,
  endoscopic video). https://www.fhnw.ch/plattformen/3dfagottino/3d-printed-ft40/
- **FT44** — Johannes & Georg H. Scherer (3), 4-key, Butzbach 1760–70, Museum für
  Musikinstrumente der Universität Leipzig. Zenodo DOI **10.5281/zenodo.4287374**.
  https://www.fhnw.ch/plattformen/3dfagottino/3d-printed-ft44/
- **The key asset:** DaSCH project `ark:/72163/1/0845`, "Fagottini and tenoroons"
  (Agrell et al. 2023), **Full Open Access, CC BY 4.0**, contains STL 3D models of
  all six CT-scanned instruments (**FT6, FT30, FT40, FT42, FT44, FT50**), each Zip
  holding the **round-bore version, the corrected-bore version, and the keys**.
- Scan pipeline (Domínguez 2025, DOI 10.1177/20592043251352948): scanned at Fraunhofer
  EZRT, Fürth; raw data exported as DICOM; air columns segmented; meshes cleaned;
  manual corrections where degraded/ovalized (largest internal diameter per
  cross-section). FT40's bell was clean; metal staples in butt/long joints added noise.

### Corrections to prior notes

- **Virtual 3D Clarinet Museum** (Wang, *Música Hodie* 2025, DOI 10.5216/mh.v25.83307):
  147 historical clarinets, but **photogrammetry (±0.05 mm) + bore gauges at 5 mm
  intervals — NOT CT**; no downloadable dataset. Existence proof only.
- **MUSICES / GNM Nürnberg** (DFG 2014–2017): >100 objects digitized, DICOM selected
  for long-term usability; the "50 µm voxel" figure from earlier notes is **unverified**;
  bulk DICOM download is **not** exposed — per-object access only.
  https://musices.gnm.de/ · final report DOI 10.58286/23696

## 2. Bore-extraction tooling

- **Recommended path — 3D Slicer + VMTK extension:** `Extract Centerline`
  (Voronoi / maximal-inscribed-sphere centerline between endpoints) → `Cross-Section
  Analysis`, which returns per-point centerline coordinates **and radii** (numpy
  arrays) — a radius-vs-arclength profile.
  https://github.com/vmtk/SlicerExtension-VMTK · community-confirmed on open hollow
  tubes of varying radius (Slicer discourse #37245, #22183).
- **Thresholding:** Otsu/adaptive threshold choice measurably shifts extracted
  dimensions (micro-CT thresholding study, PMC11594970) — document the threshold
  when defining the bore wall.
- **Python:** scikit-image `skeletonize`, SimpleITK/ITK (DICOM I/O), `skan`,
  trimesh/VTK for centerlines.
- **Closest published analogue:** "Digital Revival" (arXiv 2606.24216) extracted bore
  geometry / wall thickness / curvature of historical traversos from CT/IMA volumes
  for acoustic modeling.

## 3. Bore reconstruction from acoustic measurement (for the same benchmark)

- **APR (layer peeling):** Sharp PhD 1996 (Edinburgh); step size `c/(2·f_max)`;
  distinguishes leadpipes differing by <0.1 mm radius (Meas. Sci. Technol. 13, 2002,
  DOI 10.1088/0957-0233/13/5/313); crook reconstruction ~0.15 mm, APR vs TMFC ~0.2 mm
  (Hendrie PhD 2007).
- **Impedance-based optimization:** Kausel 2004, IEEE TIM 53(4), DOI 10.1109/TIM.2004.831440
  (Rosenbrock on BIAS-measured impedance, robust but slow); Dalmont et al. 2012,
  JASA 131(1):708 — bassoon-crook accuracy ~2% of diameter (straight <1.1%, bent ~2.5%).
- **Full Waveform Inversion (best target for the two-phase optimizer):**
  Ernoult, Chabassier, Rodriguez, Humeau, *Acta Acustica* 5:47 (2021),
  DOI 10.1051/aacus/2021038. Adjoint-gradient inversion, **~1 min on a laptop** for a
  14-variable instrument; measured vs manual-geometry agreement **≤0.5 mm
  (hole positions/length), ≤0.1 mm (radii), ≤0.3 mm (chimneys)**. Implemented GPL-3.0
  in OpenWInD (module 3). Authors' caveat: many tone holes + keywork remain open
  (hal-03231946).

## 4. CT ground truth validating 1D/TMM models

- The **fagottino program itself** is the strongest example: per-instrument Model I
  (as-is CT bore) vs Model II (idealized round bore), printed and compared
  acoustically/perceptually — differences judged minor (Domínguez 2025).
- Bowen, Buys, Dart, Sharp, *Applied Acoustics* 143:84–99 (2019),
  DOI 10.1016/j.apacoust.2018.08.028: Keefe/Dalmont-type TMM of a Heckel bass clarinet
  vs measured impedance — peaks agree **<10 cents** (geometry from calipers, not CT).
- **No published TMM-vs-CT-bore RMS study exists** — Phase 2 fills the niche.

## 5. Recommendation — what to try first

1. Download FT40/FT44 STLs from DaSCH `ark:/72163/1/0845` (CC BY 4.0, direct).
2. Extract radius profiles with Slicer+VMTK (`Extract Centerline` → `Cross-Section
   Analysis`) from both the round-bore and corrected-bore STLs — two ground truths,
   plus an ovality test via min/max diameters per section.
3. Benchmark the two-phase optimizer against OpenWInD's FWI module on a synthetic
   conical+4-hole bore first (reproduce the 2021 figures: ≤0.1 mm radii, ≤0.5 mm hole
   positions), then target impedance computed from the FT40/FT44 CT bores.
4. Cross-check extracted profiles against the Zenodo bore-measurement PDFs.
5. Report **RMS(profile)** and **RMS(impedance)** vs CT ground truth. Success bar:
   sub-0.5 mm profile agreement and <10-cent resonance agreement.
6. Do **not** plan the benchmark around MUSICES raw DICOM or the Clarinet Museum
   until access is confirmed; the STL path needs no requests.

## 6. Guardrails

- **Phase-2 timing:** CT-scan benchmarking is desktop-owned per REMINDERS thread 18
  ("after Phase 1"). This doc is the prepared research base for that thread; it
  changes no code.
- `danish_recorder_ct.pdf` (local, thread-6.1) remains an additional local target if
  the desktop wants a third ground truth.
- Regenerable artifacts (STL downloads, extracted profiles, JSON dumps) must live
  outside the repo / in `test_output/` — same rule as everything else.

## 7. References

- DaSCH fagottini/tenoroons (STL models): https://ark.dasch.swiss/ark:/72163/1/0845
- FT40 Zenodo: https://doi.org/10.5281/zenodo.3241619
- FT44 Zenodo: https://doi.org/10.5281/zenodo.4287374
- Domínguez 2025 (scan + print workflow): DOI 10.1177/20592043251352948
- SlicerVMTK: https://github.com/vmtk/SlicerExtension-VMTK
- Ernoult et al. 2021 (FWI): DOI 10.1051/aacus/2021038 · hal-03231946
- Kausel 2004: DOI 10.1109/TIM.2004.831440
- Dalmont et al. 2012: https://pubs.aip.org/asa/jasa/article/131/1/708/822991
- Sharp 2002 (APR): DOI 10.1088/0957-0233/13/5/313
- Bowen et al. 2019: DOI 10.1016/j.apacoust.2018.08.028
- MUSICES/GNM: https://musices.gnm.de/ · final report DOI 10.58286/23696
- Wang 2025 (clarinet museum, photogrammetry): DOI 10.5216/mh.v25.83307
- Digital Revival (traverso CT → acoustic model): arXiv 2606.24216
