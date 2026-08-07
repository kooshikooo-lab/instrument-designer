# RESEARCH — OpenWInD FEM Integration & ML Surrogates for Wind-Instrument Optimization

Status: **REFERENCE — saved for future work** (no code changes)
Date: 2026-08-07
Author: laptop (opencode)
Sources: live web research (2026-08-07) + repo state
(`backend/tmm_acoustics.py`, `backend/optimization/topk_polish.py`,
`tests/comparison/dask_topk.py`, `docs/ROADMAP.md` Phase 1).

## Purpose

Capture 2026 research on the two **Phase 1** pillars:
(a) using OpenWInD's spectral-FEM impedance as a validation ground truth for the
project's fast JAX TMM, and (b) ML surrogates for wind-instrument optimization,
which was previously rejected on the shared benchmark contract but now has
**open-source, benchmarked, validated-to-hardware** precedents worth re-scoping.
Ideas and citations only — no code changes.

## TL;DR

1. **OpenWInD is the validation layer, not the fast solver.** Current version
   `openwind 0.12.4` (2026-05-29) ships **both** a 1D Spectral FEM (`FrequentialPipeFEM`)
   and a Transfer Matrix Method (`FrequentialPipeTMM` + `tmm_tools`). That means the
   reference TMM implementation is already in OpenWInD — ideal for cross-checking our
   JAX TMM. OpenWInD stays GPL-3.0 and NumPy-based; keep the shipping fast solver
   separate and permissively licensed.
2. **Adoptable surrogate: the LassoLars descriptor model (Acta Acustica 2024).**
   Predicts 10 playability descriptors from 44 modal parameters (11 poles + residues)
   with ~1% error, ~2 min training, real-time prediction, **open-source code on
   GitHub**. This is the strongest direct template for a surrogate layer.
3. **Adoptable workflow template: FA2025 trumpet leadpipe design.** ML surrogate →
   bi-objective NSGA-II → manufacture → measured (EFP matched ~30 cents, pressure
   thresholds ≤ ~50 Pa). Closest published "design → prototype" validation.
4. **Open research gap:** operator learning (FNO/DeepONet) directly on woodwind/brass
   input impedance appears unpublished — a possible novelty angle, not an adoption target.

## 1. OpenWInD current state (verified 2026-08-07)

- PyPI: `openwind 0.12.4` released 2026-05-29; healthy cadence (0.11.x → 0.12.x
  Sep 2025–May 2026). GPL-3.0, source `gitlab.inria.fr/openwind/openwind`,
  docs `files.inria.fr/openwind/docs`, demo `demo-openwind.inria.fr`.
- **Correction to earlier assumption:** the frequential module solves the 1D
  Telegrapher equations **by Spectral FEM *or* TMM** — both ship in the same module.
  `tmm_tools` exposes `impedance_TMM()`, `zv_yt_TMM()`, `cone_lossy()`,
  `cone_nederveen()`, `multmat()`. A JAX TMM is not present; the reference TMM is.
- Other modules: time-domain sound synthesis (reed/lips coupled via energy-consistent
  finite differences; flute embouchure "coming soon"); **geometry optimization /
  bore reconstruction from measured impedance** (full waveform inversion).
- Modal parameters directly computable: Chabassier & Auvray (JSV 2022),
  DOI 10.1016/j.jsv.2022.116775 — poles/residues from a generalized eigenvalue
  problem (feed these into a surrogate, cf. §2).
- Mesh/API notes: `FrequentialSolver` has frequency-adaptive meshing
  (`update_frequencies_and_mesh()`, `get_orders_mesh()`, `get_elements_mesh()`,
  `discretization_infos()`); design-objective helpers exist natively
  (`resonance_frequencies()`, `resonance_peaks()`, `match_peaks_with_notes()`).
- Geometry-derivative contributions exposed (`get_contrib_dAh_freq`,
  `get_contrib_dAh_indep_freq` — dA/dh w.r.t. cross-section area), matching the
  adjoint workflow in Ernoult et al., JASA 148(5):2864 (2020), HAL hal-02479433.

### FEM vs TMM accuracy

- Reference: Tournemenne & Chabassier, "A comparison of a one-dimensional finite
  element method and the transfer matrix method...", *Acta Acustica united with
  Acustica* (2019), DOI 10.3813/AAA.919364, PDF `hal-01963674v2/file/ACTA_major.pdf`.
  Qualitative agreement for standard bores; FEM is the lossy-telegrapher,
  discontinuity-capable reference.
- TMM validity limits: Inria RR-9254, "About the transfer matrix method..." (Ernoult,
  Chabassier, Rodriguez, Humeau), HAL hal-02019515 — documents where TMM breaks down
  (short elements vs wavelength, strong flare) — exactly the cases to validate with FEM.
- 2024 high-fidelity route (reference-only): Jeanneteau et al., "A combinatorial model
  reduction method for the finite element analysis of wind instruments", IJNME 2024,
  DOI 10.1002/nme.7582 — model-reduced time-harmonic FEM for 2D/3D fidelity if ever needed.

## 2. ML surrogates — adoptable results with numbers

### 2.1 LassoLars descriptor surrogate (primary template)

- **Mohamed, Fréour, Vergez, Arimoto, Emiya, Cochelin — "Prediction of trumpet
  performance descriptors using machine learning", *Acta Acustica* 8:65 (2024).**
  DOI 10.1051/aacus/2024042 · HAL hal-04800851.
  - Inputs: 44 modal parameters (11 poles + residues) from input impedance.
  - Data: 12,000 bifurcation diagrams (ANM continuation); training ~2 min.
  - Accuracy: overall ~1%; frequency descriptors (f0min, f0max, f0fold, f0H)
    0.5–0.7 cents; real-time prediction (<1 s); XGBoost identifies 4 professional
    trumpets at 99.50% (PCA) / 81.12% (raw).
  - **Open-source supplementary code:** `github.com/mimoun-mohamed-lab/Prediction-of-trumpet-descriptors`.
- **Fréour et al., FA 2023** (HAL hal-04262291): 199 virtual instruments × 47 virtual
  players; same LassoLars-style sparse regression; mean relative error < 1%; descriptors
  for 100 trumpets in < 5 s on a laptop.

### 2.2 Design→prototype workflow template (adoptable)

- **Petiot, Fréour, Arimoto — "Numerical design of a trumpet lead pipe...",
  Forum Acusticum / EuroNoise 2025, pp. 2833–2839.** DOI 10.61782/fa.2025.0629 ·
  HAL hal-05529764.
  - ML surrogate (bore geometry → intonation + playability) drives **bi-objective
    NSGA-II** on Equivalent Fundamental Pitch + minimum blow pressure over 5 registers.
  - Leadpipe parameterized by 6 variables (5 diameters + length).
  - **Manufactured by Yamaha and tested:** measured EFP matched prediction to ~30 cents
    (Bb3); threshold-pressure differences ≤ ~50 Pa; musician playing tests included.
  - This is the closest validated end-to-end "design → prototype" precedent and maps
    directly onto our `topk_polish` + dask + print + BIAS loop.

### 2.3 Reference-only (context, not adoption targets)

- Petiot, Roatta, Fréour, Arimoto — FA 2023 / INTER-NOISE 2024 (HAL hal-05529863):
  surrogate-assisted derivative-free brass optimization.
- ResoNet PINN (Yokota et al., JASA 156(1):30, 2024, DOI 10.1121/10.0026459):
  needs per-configuration retraining; hard to tune.
- MIT FDTD + deep learning thesis (Wang 2019, dspace.mit.edu/1721.1/123116):
  compute-heavy, dated.
- RL for instrument design (Qasim et al. 2024, arXiv:2412.10237): particle-physics
  detectors, not instruments.
- Operator learning (FNO/DeepONet) for wind impedance: **not found** — an open gap.
  Closest: B-FNO for parametric acoustic waves (*Engineering with Computers*, 2025,
  DOI 10.1007/s00366-024-02103-x).

## 3. Verdict summary

| Item | Verdict |
|---|---|
| OpenWInD Spectral FEM + TMM + inversion + adjoint (GPL) | **Adopt as validation ground truth** |
| OpenWInD as the shipping fast solver | Reject for core (NumPy, GPL, not JAX/GPU) |
| Self-built JAX TMM | Build (precedent: TMMax ~100× NumPy, arXiv:2507.11341) |
| LassoLars descriptor surrogate + open code | **Adopt** (Phase 1) |
| FA2025 ML+NSGA-II design→prototype workflow | **Adopt as workflow template** |
| FNO/DeepONet on wind impedance | Research gap — potential novelty, not adoption |

## 4. Guardrails

- **Phase-1 scope unchanged:** WoodwindOpenWind FEM skeleton + surrogate audit are
  desktop-owned per REMINDERS threads 17-19 and the work separation. This doc only
  informs that work; it changes no code.
- Do **not** re-open the "JAX+dask surrogate warm-start was rejected on the shared
  contract" decision. The 2024/2025 references above are for *re-scoping what a
  surrogate layer would be* (descriptor models fed by modal parameters, not a
  full objective replacement) — different thing, needs its own decision in #23.
- Adopting `openwind` in the live pipeline would be a tool-registry change
  (`docs/TOOLS.md` protocol) — it is already a declared dependency for validation use.

## 5. References

- OpenWInD: https://openwind.inria.fr/ · https://pypi.org/project/openwind/ ·
  https://gitlab.inria.fr/openwind/openwind · demo: https://demo-openwind.inria.fr
- Tournemenne & Chabassier 2019 (FEM vs TMM): DOI 10.3813/AAA.919364 · hal-01963674v2
- Ernoult et al. 2020 (adjoint, JASA): DOI 10.1121/10.0002449 · HAL hal-02479433
- Chabassier & Auvray 2022 (modal params): DOI 10.1016/j.jsv.2022.116775
- Jeanneteau et al. 2024 (model-reduced FEM): DOI 10.1002/nme.7582
- Ernoult et al. 2021 (FWI bore reconstruction, Acta Acustica): DOI 10.1051/aacus/2021038
- Mohamed et al. 2024 (LassoLars surrogate): DOI 10.1051/aacus/2024042 ·
  github.com/mimoun-mohamed-lab/Prediction-of-trumpet-descriptors
- Petiot et al. FA 2025 (leadpipe design→prototype): DOI 10.61782/fa.2025.0629 ·
  HAL hal-05529764
- Fréour et al. FA 2023: HAL hal-04262291
- TMMax (JAX-vectorized TMM, optical): arXiv:2507.11341
