# Acoustic Metamaterial Implementation Research — 2026-08-03

Goal: figure out how to implement acoustic-metamaterial elements in the
phase-based TMM (`backend/tmm_acoustics.py`) and the modular component model
(`backend/modular_components.py`), grounded in the research docs already in
the repo (wiki/Internal-Computational-Benchmark-Research.md, the 07-18 AI
novel-instrument-design research, intonation-accuracy research) plus targeted
literature search.

## TL;DR — recommended implementation path

The cleanest, physically-validated, code-idiomatic entry point is the **tone
hole / side-branch junction already in the codebase** (`junction3_reply_phase`,
the `('hole', ...)` action). A Helmholtz-resonator (HR) side branch is a
straightforward generalization of the open/closed tone hole: instead of
treating the branch as a plain pipe of `open_length`/`closed_length`, model it
as a neck + cavity whose **frequency-dependent shunt admittance** sets the
branch phase. This reproduces stopbands / negative-effective-bulk-modulus
behavior and slots into the existing phase-walk unchanged.

Two complementary levels:

- **Level 1 — explicit side-branch array (per-resonator).** N HRs spaced
  periodically along a bore section. Directly generalizes the existing hole
  mechanism; validated against Fahy's duct side-branch theory and FEM in the
  literature. Cost: N extra `junction3` actions.
- **Level 2 — effective-medium segment (homogenized).** Replace a bore segment
  with a "metamaterial pipe" whose propagation constant is
  k_eff(ω) = ω·sqrt(ρ_eff/K_eff) from a homogenization formula (Dell/Krynkin/
  Horoshenkov TMM-derived expressions, or the npj Acoustics 2026 random-HR
  formula). Trades per-resonator resolution for O(1) cost per segment and gives
  dispersion curves / bandgap edges directly.

Level 3 (future): membrane-type negative-effective-density wall liner via a
frequency-dependent wall impedance (lined-duct model).

## Why the tone-hole junction is the natural anchor

Current TMM walk (from `docs/PHYSICS_PRINCIPLES.md` and `tmm_acoustics.py`):

```
phase = 0.5                      # open end
pipe:   phase = pipe_reply_phase(phase, seg_length / wavelength)
step:   phase = junction2_reply_phase(area_a, area_b, phase)
hole:   hole_phase = pipe_reply_phase(-0.5, open_length / wavelength)  # open
        phase = junction3_reply_phase(area_bore, area_bore, hole_area, phase, hole_phase)
```

`junction3_reply_phase` (tmm_acoustics.py:125) already implements a three-pipe
junction — main bore (a0, a1) plus a side branch (a2) with branch phase p2:

```python
def junction3_reply_phase(a0, a1, a2, p1, p2):
    shift1, shift2 = floor(p1+0.5), floor(p2+0.5)
    return untanner(a1/a0 * tanner(p1-shift1) + a2/a0 * tanner(p2-shift2)) + shift1 + shift2
```

An HR attached to the bore is exactly this junction: a0 = a1 = bore area, a2 =
neck area, and the branch phase p2 is set by the HR's input admittance rather
than by a simple pipe length. This is the Fahy "Helmholtz resonator side
branch" (§8.6.7, Foundations of Engineering Acoustics): the branch presents low
impedance near resonance → strong wave reflection → a transmission/stopband
dip. Same geometry the code already solves for tone holes — so the acoustic
math, end-correction machinery (`hole_length_correction`), and loss hooks all
reuse.

## Physics / literature anchors

### Helmholtz resonator side branch (Level 1 core)
- Fahy, "Sound in Waveguides", §8.6.7: side-branch HR impedance, resonance
  reflection, lumped single-resonance model, wider effective bandwidth when the
  branch mouths into a duct (radiation resistance) vs a free room.
- A lined/dual HR array (two HRs on one duct) and parallel HR arrays: the
  parallel array gives ~2× the energy-storage capacity (C_TL) of a dual HR —
  relevant when placing multiple resonators around the bore.
- Non-uniform / graded HR arrays (IOP 2025, "Non-uniform Helmholtz resonator
  arrays for broadband sound manipulation"): uniform periodic arrays give
  Bragg + resonant bandgaps but are bandwidth-limited by symmetry; graded
  arrays give impedance matching and "rainbow trapping" → broadened
  attenuation. This is the design knobs roadmap: {spacing, resonator volume,
  neck radius, neck length, gradient profile}.

### Effective medium / homogenization (Level 2 core)
- Dell, Krynkin & Horoshenkov, "The use of the transfer matrix method to
  predict the effective fluid properties of acoustical systems" (Applied
  Acoustics 182, 2021; open access): derives simple low-frequency analytical
  expressions for effective properties of a waveguide side-loaded by N
  Helmholtz resonators, validated against full TMM and numerical computation.
  This is exactly our Level 2: bore + periodic HR side branches → ρ_eff(ω),
  K_eff(ω) → k_eff(ω).
- npj Acoustics (2026), "Designing band gaps with randomly distributed
  sub-wavelength Helmholtz resonators": effective bulk modulus with resonance
  factor z(λ_j), β*_eff(k) = β / ((1-φ) + Σ z(λ_j)·φ_j), ρ* = ρ·(1+φ)/(1-φ).
  Gives a closed-form stopband estimator for scattered placements.
- 2D HR arrays (arXiv 2202.09941): multipole + matched asymptotics for the
  first band surface / subharmonic bandgap — background reading; overkill for
  1D bore but defines what "bandgap edge" means we should reproduce.

### Negative-effective-density / membrane types (Level 3, future)
- Yang et al. 2008 (PRL), membrane-type acoustic metamaterial with negative
  dynamic mass; Naify et al. TL of membrane arrays. Modeled as a wall
  impedance / lined duct, not a junction — needs the propagation segment to
  carry a frequency-dependent wall admittance. Higher effort, listed as future.

### 3D-print constraints (this repo prints instruments)
- Ciochon et al. 2023 (J. Sound & Vibration), already cited in
  chat-logs/2026-07-18-intonation-accuracy-research.md: FDM layer height
  (0.10–0.25 mm) measurably shifts HR/metamaterial performance. So any
  implemented resonator must expose print-resolution parameters (layer height,
  roughness) to the tuner/optimizer.

### Inverse-design tie-ins already researched in repo
- AR-VAE (2024): inverse design of ventilated acoustic resonators from target
  acoustic response — 25× MSE reduction. Directly applicable as the
  surrogate/inverse model for resonator arrays once the forward TMM supports
  them.
- CNN inverse design of microperforated-panel absorbers (2025): the
  perforated-panel element is a Level-2/3 effective-medium candidate for
  bore-lining absorbers.
- LLM-based inverse design (PMC 2025): agent/ChatGPT + fine-tuned DeepSeek for
  metamaterial design "in one minute" — matches the repo's existing
  AI-assistant + surrogate direction.

## Concrete implementation sketch (idiomatic to this codebase)

### New primitive: `MetamaterialSideBranch` (Level 1)
Data (units mm, matching TMM):
- `position_mm` — where the neck mouths into the bore
- `neck_radius_mm`, `neck_length_mm` (with `hole_length_correction`-style end
  corrections: ~0.6–0.85r outer, 1.0r inner per UNSW/Fahy)
- `cavity_volume_mm3` (or cavity geometry → volume)
- optional `resistive_layer` (porous sheet / screen resistance, Fahy
  recommendation to suppress flow noise) and `layer_height_mm` print knob

Branch phase from shunt admittance (frequency domain):
- M = ρ·(L'_neck)/S_neck   (L'_neck = neck length + end corrections)
- C = V_cavity/(ρ·c²)
- Z_s = R + j·(ω·M − 1/(ω·C))    (R = viscous + resistive-layer losses)
- branch admittance ratio ∝ tanner(p2) form used by junction3, so solve
  p2(ω) from the admittance so the existing `junction3_reply_phase` math is
  reused verbatim. (Implementation detail: pick the phase such that
  tan(p2) reproduces the normalized shunt admittance; losses add an imaginary
  part → complex phase — the loss model hooks already handle complex phase.)

Constructor additions to `TMMInstrument`:
- new optional param `meta_slots: Optional[list]` (each a
  `MetamaterialSideBranch`), events appended in `_prepare_phase()` like holes;
  `resonance_phase()` gets a `meta` action handled exactly like `hole` but
  with `p2` from the HR admittance at the current wavelength.

### Level 2: `MetamaterialSegment`
- A bore segment flagged as metamaterial, with N resonators + spacing.
- Homogenize → ρ_eff(ω), K_eff(ω) (Dell et al. 2021 formulas), compute
  k_eff(ω), then the segment contributes phase 2·Re(k_eff)·L instead of
  2·L/λ inside `pipe_reply_phase` (dispersion). Stopband = segment where
  Re(k_eff) → 0 / bandgap in phase crossing.
- Keeps the phase-walk sweep (`wavelength_near`, `find_resonance`) intact —
  only the segment's phase accumulation becomes frequency-dependent.

### Validation strategy (aligns with the repo's layered V&V + cross-solver audit)
1. Unit: single HR side branch on a rigid duct — compare stopband dip frequency
   and width against Fahy's analytic side-branch formula and against a small
   FEM (e.g. the FEniCSx helmholtz path already listed in repo research, or
   scikit-FEM) — target <5% on resonance frequency.
2. Effective medium: periodic array — compare Level-2 k_eff dispersion against
   the explicit Level-1 array (self-consistency), and both against FEM.
3. Cross-solver: the existing OpenWInD integration (`trumpet_openwind.py`) can
   serve as the independent check for an HR-laden bore (this mirrors the
   "Kimi K3 claim validation" cross-solver cross-validation pattern in
   docs/AI_FAILURE_PATTERNS.md — TMM vs OpenWind must agree, or the
   disagreement must be explained by convention/1D assumptions).
4. Print-fidelity: sweep layer_height 0.10/0.16/0.25 mm to bound resonance
   drift per Ciochon et al.
5. Regression: existing 114-test parity suite must stay green; a
   `meta=None` default must produce bit-identical phase walks.

### Design knobs to expose for the optimizer/surrogate
- array: N, spacing, resonator positions (uniform / graded / random)
- per resonator: neck radius, neck length, cavity volume, neck end corrections
- liner: resistive-layer resistance, membrane parameters (Level 3)
- print: layer height, minimum wall thickness, overhang constraints
  (reuse `printability.py`)

These map onto the existing inverse-design (`inverse_design.py`,
`pareto_optimizer.py`) and surrogate/elite-tail machinery (the current
hybrid warm-start design search) as new continuous design variables.

## Decision / recommendation
1. Implement **Level 1 (explicit HR side-branch array)** first — it is a
   minimal, validated generalization of the existing tone-hole junction, costs
   no new physics machinery, and gives measurable stopbands/harmonicity
   changes that can be verified against OpenWInD and (optionally) FEM.
2. Add **Level 2 (effective-medium segment)** as an optional fast path once
   Level 1 parity tests exist (self-consistency = Level 2 vs Level 1).
3. **Level 3 (membrane liner)** only if a specific instrument goal needs
   negative-density behavior that HR arrays cannot deliver.
4. Keep all of it behind feature flags / optional constructor args so the
   existing 114-test parity suite and the numba fast path
   (`TMM_USE_NUMBA`, lossless-only) are unaffected. The lossless-only fast path
   guard must treat metamaterial segments as "lossy/unsupported → fall back to
   the Python walk" until a numba branch model is added.

## Sources
- Fahy, Foundations of Engineering Acoustics, §8.6.7 "The Helmholtz Resonator
  Side Branch".
- Dell, Krynkin, Horoshenkov, Applied Acoustics 182 (2021) 108259 — TMM
  effective fluid properties of side-branch-loaded waveguides (open access).
- npj Acoustics (2026) — band gaps with randomly distributed sub-wavelength
  Helmholtz resonators; effective β*, ρ* formulas.
- IOP (2025), "Non-uniform Helmholtz resonator arrays for broadband sound
  manipulation" — uniform vs graded arrays, rainbow trapping.
- ScienceDirect (2018), "Acoustic performance of different Helmholtz resonator
  array configurations" — dual vs lined vs parallel HR arrays, C_TL.
- arXiv 2202.09941 — 2D Helmholtz resonator arrays (background).
- Yang et al., PRL 101 (2008) — membrane-type AM, negative dynamic mass.
- Luan, Wang, Li, Scavone — "Acoustical Analysis of the Chinese Transverse
  Flute (dizi) using the Transfer Matrix Method" — membrane hole as a branch
  element (adjacent precedent in woodwind TMM).
- Ciochon et al., JSV (2023) — FDM surface roughness vs metamaterial
  performance (via chat-logs/2026-07-18-intonation-accuracy-research.md).
- Repo-internal: chat-logs/2026-07-18-ai-novel-instrument-design-research.md
  (AR-VAE, CNN absorber, LLM metamaterial design); wiki/Internal-*-Research.md;
  docs/PHYSICS_PRINCIPLES.md; backend/tmm_acoustics.py.
