# RESEARCH — Acoustic Metamaterials for Musical Instruments

Status: **REFERENCE — saved for future work** (no code changes)
Date: 2026-08-03
Author: desktop (opencode)
Sources: user-shared Claude.ai conversation export
(`Metamaterials in woodwind instruments - Claude.html`, 2026-08-02) + user-shared
Kimi conversation export (`Metamaterials in Instruments - Kimi.html`, 2026-08-03,
low-woodwind family analysis, Section 2.4) + live web research.

## Purpose

Capture research on applying **acoustic metamaterials** to instruments — woodwinds
(especially bass clarinet), brass, strings, and guitar — as reference for future work.
This doc is *ideas and citations only*; it does not change any code. The companion
Claude artifacts (`brass_scaffold.py`, `metamaterial_elements.py`,
`string_metamaterial.py`) are **not** in this repo — they live in the Claude chat.

## TL;DR

Three distinct metamaterial mechanisms map onto instruments:

1. **Helmholtz side-branch / locally-resonant liner** (1D waveguide) — directly applicable
   to a woodwind bore, and a *literal* extension of the existing TMM tonehole/network code.
2. **Sonic-crystal periodic mass loading** (1D string) — Bloch band gaps from periodic
   impedance discontinuities; the string case is the closest thing to a *prototypable*
   physical test.
3. **2D membrane / plate cloaking or resonant-patch damping** (drum, soundboard) — does
   **not** transplant to a bore (single excitation point), but maps to mutes, pads,
   soundboards, and guitar tops.

Key finding for this project: a woodwind's **tonehole lattice already is a periodic
medium** (Benade cutoff / pass-stop bands), i.e. woodwinds are already "accidental"
metamaterials. Engineered resonators are a natural next step, not a foreign insert.

Ranking takeaway (Kimi, §2.4): **low woodwinds are the standout unproven category**
(contrabass clarinet Bb top candidate, ~3 m tube, sub-wavelength features ~10–30 cm);
percussion is the proven case; folded bores add a parallel-waveguide topology a
straight bore cannot reach.

Status 2026-08-03: the Claude-sketched elements are now ported as runnable experiment
scripts in `backend/experiments/` (`metamaterial_elements.py`, `brass_scaffold.py`,
`string_metamaterial.py`, `folded_bore_elements.py`) — see §7. The laptop also has a
production L1 `MetamaterialSideBranch` / L2 `MetamaterialSegment` implementation on
`kalles-main-branch` (not yet on `main`).

## 1. Mechanisms and what transplants

| Mechanism | Structure | Band gap from | Transplants to |
|---|---|---|---|
| Helmholtz side branch | shunt resonator on a waveguide | local resonance, sub-wavelength | **Bore liner, mutes, register/vent tuning** — the TMM `Port` model |
| Bragg / sonic crystal | periodic impedance steps | lattice spacing `a` (gap ~ `c/(2a)`) | strings (mass loads), tonehole lattices (already there) |
| Locally resonant | spring–mass attachments | resonator f0, sub-wavelength | strings, bridge/nut masses, resonant plates |
| Membrane cloaking | mass-ring on 2D membrane | ring boundary traps band | **No** for bore; yes for mutes/pads/drumheads |

The wind-bore case: excitation is at one end only, so the 2D "strike inside vs. outside
the ring" freedom that makes the frame-drum trick work **does not exist** in a bore.
What *does* transfer is the method — patterned resonant elements creating
frequency-dependent dispersion and band gaps — applied to a 1D acoustic waveguide.

## 2. Woodwinds (bass clarinet focus)

### 2.1 Tonehole lattice as an existing periodic structure

- Since Benade, the **cutoff frequency** of the tonehole lattice is understood as a
  result of wave propagation in a periodic medium: below cutoff the lattice is
  evanescent (stop band), above cutoff waves propagate (pass band). This is precisely
  a phononic-crystal band-gap structure.
- Petersen, Kergomard et al. generalized cutoff theory to **conical** lattices
  (saxophone): "On the tonehole lattice cutoff frequency of conical resonators —
  applications to the saxophone," *Acta Acustica* 4, 13 (2020),
  https://doi.org/10.1051/aacus/2020012. Also E. Petersen's thesis *Wave Propagation in
  Periodic Structures Applied to Woodwind Tonehole Lattices* (LMA / Aix-Marseille).
- Implication: **the instrument already contains the metamaterial physics**; we can
  quantify its band structure from the existing geometry (`backend/tone_hole_corrections.py`,
  `backend/core/network.py` ports).

### 2.2 Why bass clarinet specifically

- Cylindrical bore + flared bell → the *cleanest* periodic tonehole lattice in the
  clarinet family, so the band-gap/cutoff theory applies most directly.
- Low fundamental register (down to written Eb3, ~78 Hz) → any local resonator
  (Helmholtz or spring–mass) must be sub-wavelength at **low** frequency, i.e. small
  volumes are required — exactly the regime Helmholtz resonators are good at.
- No published "bass clarinet metamaterial" work surfaced in the searches; the closest
  validated concepts are Helmholtz-resonator arrays (below) and the printed-instrument
  consistency work (Section 4).

### 2.3 Disordered Helmholtz-resonator arrays (new, 2025–26)

- **Piva, Gower & Abrahams, "Designing band gaps with randomly distributed
  sub-wavelength Helmholtz resonators,"** arXiv:2505.01347 (2025); published in
  *npj Acoustics* 2, 10 (2026), https://doi.org/10.1038/s44384-026-00045-w.
- Key result: **randomly positioned** Helmholtz resonators in a host medium create
  broad / multiple overlapping band gaps, with *explicit asymptotic formulas* for the
  effective (frequency-dependent) bulk modulus — no heavy optimization needed.
- Relevant numbers: ~6% volume fraction gives a band gap around 140 Hz in a 32 mm
  layer; broadening by increasing layer width `W` or volume fraction `φ`.
- Why this matters for us: instead of hand-tuning one resonator, you can specify a
  **designed distribution of side-branch resonator sizes** along a bore segment and get
  a target suppression band from a formula — very compatible with the repo's
  optimization workflows (`backend/two_phase_optimizer.py`, Pareto sweeps).
- Earlier analytic framework: "Tailored acoustic metamaterials. Part I. Thin- and
  thick-walled Helmholtz resonator arrays," *Proc. R. Soc. A* 478:20220124 (2022)
  (Gower et al., Cambridge repository link in search results).

### 2.4 The extended low-woodwind family (Kimi research, 2026-08-03)

A second AI-conversation export (Kimi, "Metamaterials in Instruments") worked the
bass-clarinet idea out into a full family ranking. Key takeaways:

**Cross-category promise ranking** (highest → lowest):
1. Percussion (membranes/plates) — ★★★★★ — *proven* (Bader's frame drum); spatial
   articulation is native and impulsive sounds tolerate narrowband band gaps.
2. **Low woodwinds** (contrabass clarinet, folded bass, contra-alto, low-A baritone
   sax) — ★★★★★ — the standout *unproven* category.
3. Plucked strings / guitar soundboard — ★★★★☆ — strong FEM simulation evidence
   (Lercari et al. 2022, MDPI Appl. Sci. 12:8619); tone-wood scarcity is a driver.
4. Piano soundboard — ★★★☆☆ — rib-stiffened plate is already "metamaterial-like"
   (periodic bracing → band-gap damping).
5. Standard woodwinds (flute, oboe, soprano clarinet, alto/tenor sax) — ★★★☆☆.
6. Bowed strings — ★★☆☆☆ — phononic-crystal strings exist but risk breaking the
   bow/string stick-slip (Helmholtz-motion) coupling → wolf notes.
7. Brass — ★★☆☆☆ — bore must stay smooth for airflow; harmonic series is rigid; a
   band gap = dead register. Wall vibration is acoustically secondary.
8. Lamellophones (mbira/kalimba) — ★★☆☆☆ — acoustically fertile, culturally marginal.

**The folded-geometry advantage.** A folded bore (bassoon-like, Leblanc "paperclip",
double-U contrabass) is not just packaging: it creates **parallel waveguide sections**
separated by a thin wall. In phononic-crystal terms this is a coupled-waveguide
topology a straight instrument cannot replicate — the shared wall could be perforated
periodically to make a directional coupler transferring energy between bore legs at
chosen frequencies (radiation cancellation / notch filtering). Each straight segment
also becomes an independent acoustic module (e.g., segment 1 tuned to the chalumeau
register, segment 2 to the clarion, U-bends as mode converters). Historical precedent:
Grenser's 1793 folded bassoon-like bass clarinet; Papalini's serpentine wood-carved
instrument.

**Within-family ranking** (with the numbers that motivate it):
- **Contrabass clarinet Bb** — ★★★★★. Fontaine-Besson's 1889 pedal clarinet: "a tube
  10 feet (3.0 m) long, in which cylindrical and conical bores are combined. The tube
  is doubled up twice upon itself." Modern Selmer/Leblanc: 71.3 in body, bore
  cylindrical except conical bell joint. Low C sounds Bb0 (~29 Hz); wavelength
  ~11.7 m, so sub-wavelength features are only ~10–30 cm — trivially printable.
  Known defect: lowest notes "unavoidably a little rough" — an impedance-matching
  problem at the cyl→cone transition and bell cutoff that a **graded metamaterial
  bell liner** could fix.
- **Novel-shape folded bass clarinet** — ★★★★★. Designed *around* metamaterials
  rather than retrofitted; ergonomic precedent proven by the 19th-c. folded basses.
- **Contra-alto clarinet Eb** — ★★★★☆. Acoustic length "often exceeds 1.7 m";
  "the least standardized member of the clarinet family" → no sacred design to
  preserve. Leblanc 350 "paperclip" is physically shorter than a Bb bass.
- **Baritone sax (low A)** — ★★★★☆. The low-A extension is a known compromise:
  makers added a cylindrical section between bell and bow, but "these horns generally
  suffer from intonation problems in the lowest few notes." A labyrinthine/corrugated
  **bell insert could create effective acoustic length without physical size**.
  Sax bore supports harmonics ~1:2:3 (UNSW) — more forgiving than clarinet's
  odd-only series. Huge working player base (big band/funk).
- **Standard bass clarinet (straight)** — ★★★☆☆; **bass sax** — ★★★☆☆;
  **alto clarinet / "in-between" keys** — ★★☆☆☆ (rare, non-standardized);
  **contrabass sax** — ★★☆☆☆ (~15 originals exist, 1.9 m tall);
  **subcontrabass sax / tubax** — ★☆☆☆☆ (2.74 m tall, 28.6 kg, G#0 = 25.95 Hz;
  a novelty).

**Cylindrical vs. conical for metamaterial design.** Clarinet (cylindrical, closed
end): odd harmonics only (1:3:5…), sparser mode structure → easier to place band gaps
without swallowing a needed harmonic; constant geometry along the bore → uniform
periodic structures. Sax (conical, closed end): full 1:2:3… series, denser → riskier;
bore tapers → periodic structures must be graded. Verdict: cylindrical-bore clarinets
are the more forgiving first experiments; saxophones are higher-risk/higher-reward in
the bell region (largest diameter, locally near-cylindrical).

**Timbre archaeology / on-demand timbre.** The bass clarinet in A (introduced by Wagner
in *Lohengrin*, 1848; used by Mahler/Strauss/Bartók; now only offered routinely by
custom maker Stephen Fox) has a famously different low-register sound. A bore-surface
metamaterial on a Bb instrument could in principle emulate the A instrument's spectral
signature — timbre-on-demand without a second instrument.

### 2.5 Register-hole / side-branch physics already modeled

- Register holes (vents) are deliberately placed inertances that weaken the
  fundamental mode and force a higher register — see Stanford CCRMA register-hole
  models and Benade. The repo models these as `Port(node_type=REGISTER_VENT)`.
- A register vent is one half of the "resonator array" story; a series of tuned
  side-branch resonators is the other half.

## 3. Strings and drums (Bader group)

- **Bader, Fischer, Münster & Kontopidis, "Metamaterials in musical acoustics: A
  modified frame drum,"** JASA (2019). A 40 cm mylar drum head with 2×10 neodymium
  magnets arranged in a 10 cm-diameter ring produces a band gap roughly 300–400 Hz to
  700–800 Hz: striking inside vs. outside the ring gives **two non-overlapping timbral
  families** (plus a blended zone at the rim). Confirmed by the searches — the original
  research detail is accurate.
- **1D sonic-crystal string** from the same group: a string covered with added masses
  produces a dispersion relation in the harmonic overtones — still has pitch, but a
  very different timbre. Same group's book chapter: Bader et al., "Designing Musical
  Instruments and Room Acoustics with Acoustic Metamaterials," Springer (2024),
  https://doi.org/10.1007/978-3-031-57892-2_16 — covers the string, a labyrinth-sphere
  resonator (band-gap damping at 770 Hz with a back plate, ~60% absorption), and the
  membrane.

## 4. Guitar (user plays electric + acoustic)

- **Perforated / lattice soundboard as a wood-property surrogate** — the best-evidenced
  guitar idea. Espinoza-Oñate et al.: locally coupling tunable mechanical metamaterials
  to a guitar soundboard to absorb / reshape specific resonances. Also an FEM study of
  patterned perforations in classical guitar top plates, motivated by decoupling
  density from stiffness and escaping natural-wood variation.
- **Printed ukulele soundboard consistency**: 3D-printed PLA+ tops were far more
  repeatable than wood (correlation ≈ 0.94 between printed samples vs 0.19–0.65 for
  wood of the same species). This is the *enabling condition* for engineering a
  metamaterial soundboard — the printer can hit target mechanical properties.
- **Electric guitar**: essentially no metamaterial literature (tone is dominated by
  pickup sensing, not body radiation). Transfers that do exist: body chambering as an
  *engineered lattice* (extrapolation, untested), and sonic-crystal strings apply
  identically since they change string dispersion before the pickup.
- **Acoustic guitar air resonance**: the body+soundhole is already a Helmholtz
  resonator (~90–100 Hz). A secondary internal resonator coupled to it is a **direct,
  literal** extension of the existing side-branch model — no new physics.
- **Most prototypable idea overall**: a small mass on a compliant mount clamped to a
  guitar string (or embedded in a printed bridge/saddle) = locally-resonant string
  metamaterial. No bore, no reed, no viscothermal model — just string + clip-on mass +
  a tuner.

## 5. Brass (from the shared conversation)

- The Claude `brass_scaffold.py` demonstrates a corrective Helmholtz resonator in a
  trumpet valve slide: ~15+ cents of pull from a 4 cm³ resonator. Naive placement
  overshot (−16.2 → +12.2 cents on the 1-3 combination); the correct approach is an
  **optimizer loop** with (resonator volume, neck length, position along slide) as free
  parameters and cents-deviation as objective — the exact pattern of
  `backend/two_phase_optimizer.py`.
- Geometry in the sketch is illustrative, not calibrated (round-number bore/bell);
  real dimensions needed before it is quantitative.

## 6. Integration evaluation — mapping onto this repo's TMM

### What exists today

- `backend/tmm_acoustics.py` — TMM resonance phase model. Key helpers:
  `junction2_reply_phase` / `junction3_reply_phase` (pipe junctions), toneholes and
  register vents enter as **side branches**, matching the physics needed for a
  Helmholtz-resonator element. `SPEED_OF_SOUND = 346100.0` (mm/s, canonical chalumier
  value — Law 7).
- `backend/core/network.py` — `Port` dataclass with `node_type` (TONEHOLE /
  REGISTER_VENT); a `HELMHOLTZ` node type is the natural extension point for a
  resonator element.
- `backend/tone_hole_corrections.py` — side-branch / tonehole corrections (line 419
  notes the hole acting as a side branch); this is where cutoff / band-gap metrics
  would slot in.
- `backend/mouthpiece_models.py` (Helmholtz mouthpiece model) and
  `backend/trumpet_acoustics.py` (Helmholtz resonator in the mouthpiece) — the repo
  already computes Helmholtz resonances.
- `backend/experiments/` — ported Claude artifacts (2026-08-03): `metamaterial_elements.py`
  (Helmholtz shunt + local-resonance effective density), `brass_scaffold.py`
  (cyl/cone + bell-flare TMM, radiation, peak finding), `string_metamaterial.py`
  (Bloch band gaps), `folded_bore_elements.py` (folded low-clarinet builder + tonehole
  shunts). All reproduce the Claude conversation's documented outputs exactly; see §7.

### Feasible integration paths (future work, not built)

1. **Helmholtz side-branch element** (lowest friction): add a resonator element to the
   network (`node_type=HELMHOLTZ`, params: cavity volume V, neck length, neck area)
   feeding into the TMM junction math. Reuses `junction2_reply_phase` with the
   resonator's impedance in parallel. Validated on the trumpet-valve case (cent
   deviation), then bass-clarinet bore sections.
2. **Band-gap / cutoff metrics from existing geometry**: compute the tonehole-lattice
   stop-band edges from `tone_hole_corrections.py` geometry using the periodic-medium
   theory (Petersen/Kergomard). Add as a timbre-side objective alongside
   `backend/timbre_objectives.py`.
3. **Resonator-distribution design**: use the Piva/Gower/Abrahams effective-properties
   formulas to size a *distribution* of resonator volumes along a bore segment for a
   target suppression band, then run it through the existing optimizers.
4. **String metamaterial calculator** — **DONE**: `backend/experiments/string_metamaterial.py`
   (Bloch transfer-matrix, ported 2026-08-03; band-gap outputs match the Claude
   conversation exactly). It is mechanically the exact analog of the bore transfer
   matrix: state `(Y, F)` ↔ `(pressure, volume velocity)`, `Z0 = sqrt(T·μ)`.
5. **Not worth pursuing**: 2D cloaking in a wind bore (no excitation-position freedom);
   electric-guitar pickup metamaterials (different physics domain).

### Guardrails

- The §6 integration paths are *future-work* items; the ported `backend/experiments/`
  scripts (§7) are the working reference implementations, and the laptop's L1/L2
  land on `kalles-main-branch` first (not yet merged).
- Any new third-party package (none needed for the ported scripts — numpy + scipy only,
  both already declared) would require declaration per the tool-registry guard.
- The TMM numba fast path (`TMM_USE_NUMBA`) is lossless-only; a resonator element that
  adds loss would need to stay on the pure-Python path or extend the njit function.

## 7. Ported Claude artifacts — numerical findings (2026-08-03)

Four scripts from the Claude metamaterials conversation were ported into
`backend/experiments/` and verified against the conversation's documented outputs
(band gaps, brass-valve peaks, folded-bore fundamentals all reproduce exactly):

- `metamaterial_elements.py` — `helmholtz_shunt_matrix` (ABCD shunt: cavity compliance +
  neck inertance + Ingard end corrections + wall loss), `resonance_frequency`, and
  `effective_density_locally_resonant` (Liu-style negative-density local resonance).
- `brass_scaffold.py` — cylinder/cone (Webster `psi=r·p`) matrices, chained bell flare,
  radiation load, `find_impedance_peaks`, `cents`. Demo reproduces the trumpet
  1-3-combination sharpness: open peaks 684.5/715.6/846.2 Hz, the 1-3 nearest partial at
  838.3 Hz (−16.2c), and a 4 cm³ / 24.9 mm-neck Helmholtz resonator in the valve slide
  pulls it to 852.2 Hz (+12.2c) — proving the mechanism and the need for an optimizer
  loop on (V, neck, position) rather than a single hand-tuned shunt.
- `string_metamaterial.py` — Bloch band gaps for rigid mass loading and locally-resonant
  attachment; reproduces the conversation's exact gaps (rigid 5 cm/50 mg:
  (1580.0, 4183.3) + (4768.6, 8000.0); local 100 mg @ 1500 Hz: (921.1, 2925.6) +
  (4183.8, 5918.5)).
- `folded_bore_elements.py` — folded low-clarinet builder + open/closed tonehole shunts,
  reed-end (impedance-max) driver, first-order bend correction. Run results:

| Instrument (illustrative) | straight | folded (n bends) | shift |
|---|---|---|---|
| bass clarinet | 251.4 Hz | 249.6 Hz (1) | −12.8c |
| contra-alto clarinet | 172.7 Hz | 170.4 Hz (2) | −22.9c |
| contrabass clarinet | 63.9 Hz | 62.8 Hz (3) | −27.8c |

**Fold-count trend**: each additional fold pushes the fundamental flat, matching the
reported intonation difficulty of contra-alto/contrabass vs. soprano clarinet — a
testable hypothesis that fold count/geometry is a real contributor, not just "bigger
tube = harder to voice". The bend model is a first-order placeholder; validate against
OpenWInD FEM before trusting magnitudes.

**Rigid-cavity resonator feasibility (the important failure mode)** — neck length needed
to tune a rigid Helmholtz resonator to each folded fundamental (r_neck = 10 mm):

| Instrument | V=10 cm³ | V=30 cm³ | V=100 cm³ |
|---|---|---|---|
| bass clarinet (251→250 Hz) | 148.8 cm | 48.5 cm | 13.4 cm |
| contra-alto (173→170 Hz) | unreachable (<3 m) | 105.9 cm | 30.6 cm |
| contrabass (64→63 Hz) | unreachable | unreachable | 235.7 cm |

Design implication (non-obvious, derived from the numbers): a rigid air-column resonator
is **geometry-limited** at low frequencies — pulling a ~63 Hz contrabass fundamental
needs a 2+ m neck. Therefore:
- Rigid Helmholtz resonators are the right tool for **upper partials / formants**
  (same neck-length scale as the ~1 kHz soprano-clarinet case).
- For the **fundamental register**, the locally-resonant liner mechanism
  (`effective_density_locally_resonant`) is the better fit: its tuning knob is spring
  stiffness, not air-column length, so it does not hit this wall.

## 8. Language / tooling notes (from the conversation's open question)

The chat ended with "any thoughts on best languages for coding this?" (unanswered).
Existing repo precedent: Python + numpy for TMM/solvers, numba for hot paths, JAX for
gradients. For resonator/band-gap additions, Python+numpy is the lowest-friction fit
and reuses the optimizer/tooling already in place; the Bloch-string and
effective-properties formulas are all scalar-matrix math, no special language needed.

## References (verified by live search, 2026-08-03)

- Piva, Gower, Abrahams — *Designing band gaps with randomly distributed
  sub-wavelength Helmholtz resonators*, arXiv:2505.01347; npj Acoustics 2, 10 (2026).
- Gower et al. — *Tailored acoustic metamaterials. Part I. Thin- and thick-walled
  Helmholtz resonator arrays*, Proc. R. Soc. A 478:20220124 (2022).
- Petersen, Colinot, Kergomard, Guillemain — *On the tonehole lattice cutoff frequency
  of conical resonators: applications to the saxophone*, Acta Acustica 4, 13 (2020),
  https://doi.org/10.1051/aacus/2020012.
- Bader, Fischer, Münster, Kontopidis — *Metamaterials in musical acoustics: A
  modified frame drum*, JASA (2019).
- Bader et al. — *Designing Musical Instruments and Room Acoustics with Acoustic
  Metamaterials*, Springer (2024), https://doi.org/10.1007/978-3-031-57892-2_16.
- Bowen, Buys, Sharp — *On the accuracy of calculation of the impedance spectra of
  woodwind instruments* (Heckel bass clarinet in A validation, ~10 cents agreement),
  Open University / RCM (2018).
- Ernoult, Vergez, Missoum, Guillemain, Jousserand — *Woodwind instrument design
  optimization based on impedance characteristics with geometric constraints*, JASA
  148:2864 (2020), https://doi.org/10.1121/10.0002449.
- Wolfe — *The Acoustics of Woodwind Musical Instruments*, Acoustics Today 14(1) (2018)
  (UNSW; Helmholtz short-circuit in the flute head joint; tonehole cutoff).
- Stanford CCRMA — register-hole models; JOS tonehole lattice notes (Benade cutoff).
- Kimi (Moonshot AI) conversation export — *Metamaterials in Instruments* (2026-08-03):
  cross-category ranking, folded-geometry (parallel-waveguide) analysis, extended
  low-woodwind family numbers (contrabass Bb, contra-alto Eb, low-A baritone sax,
  bass clarinet in A), Section 2.4.

---

## Appendix A: Verbatim excerpts from the source Claude conversation (2026-08-02)

*Source: `Metamaterials in woodwind instruments - Claude.html` export. The
research doc above synthesizes these passages; they are preserved here for
traceability.*

### A.1 Brass scaffold — mechanism validation and optimizer loop needed

> **Claude:** "Two things worth flagging, both useful:
>
> 1. **The direction and rough magnitude are right, but the naive tuning overshot.**
>    I placed the resonator's own resonance frequency directly at the sharp
>    peak, which is a first guess, not a solved design — the resonator's f0,
>    its position within the slide, and its cavity volume all interact with
>    the surrounding tubing in a way that isn't a clean one-to-one mapping to
>    'how many cents of correction you get.' Real design work here means
>    wrapping this in an optimizer loop (exactly the pattern from your
>    `two_phase_optimizer` / `v2_scipy_optimizer` work) with cents-deviation
>    as the objective and (V, neck length, position-along-slide) as free
>    parameters, rather than hand-placing it. That's the honest state of this
>    sketch: it demonstrates the mechanism has real leverage — more than 15
>    cents of pull from a 4cm³ resonator — not that I've solved the placement
>    problem.
>
> 2. **The geometry is illustrative, not calibrated.**
>    Bore radius, slide lengths, and bell profile are round numbers chosen
>    to produce a plausible-looking impedance curve, not measured from a real
>    Bb trumpet. Before this means anything quantitatively you'd want to
>    swap in your actual leadpipe/valve-tubing/bell dimensions — the
>    `cone_matrix` sanity check (verified against the cylinder limit) means
>    the machinery itself is trustworthy, but garbage-in-garbage-out still
>    applies to the geometry.
>
> **How I'd actually use this**: treat `brass_scaffold.py` as a geometry-input
> problem, not a code problem — drop in real leadpipe/bell profile points and
> real valve slide lengths, then wrap the resonator placement in a small
> optimizer (2-3 parameters: V, neck length, split-point along the slide)
> targeting the known 1-3 and 1-2-3 sharpness numbers from brass acoustics
> literature. That would tell you fairly quickly whether an embedded
> resonator can pull a valve combination into tune without also dragging the
> open partials out of tune — which is really the whole question for whether
> this is a genuinely useful mechanism or just a neat idea."

### A.2 Frame drum / membrane cloaking — verified and contextualized

> **Claude:** "Good — that claim from the other AI checks out, with the details
> basically accurate. It's Bader, Fischer, Münster & Kontopidis's 2019 JASA
> paper on a modified frame drum, and the mechanism is real: adding point
> masses arranged in a ring on the drum membrane produces cloaking behavior,
> where frequencies within a certain band can't leave the ring when the drum
> is struck at its center. The physical implementation was a 40cm mylar
> frame-drum membrane with a 10cm-diameter ring marked out by 2×10 neodymium
> magnets stuck to front and back, and the resulting band gap sits between
> roughly 300–400 Hz and 700–800 Hz, depending on the ring diameter.
> Striking inside the ring gives that gapped spectrum, striking outside
> gives an ordinary drum spectrum, and striking at the rim gives something
> in between — so the 'two non-overlapping timbral families'
> characterization is fair, and there's actually a third, blended zone at
> the boundary.
>
> Worth knowing this is part of a broader program from the same group, not a
> one-off: the same paper set also covers a one-dimensional metamaterial
> string with added masses producing a dispersion relation in the harmonic
> overtones — a detectable but very different pitch character — and a
> labyrinth-sphere resonator with clear band-gap damping, small enough to
> be usable in loudspeakers, instruments, or room acoustics.
>
> **Where this sits relative to your project, and why it's a genuinely
> different animal than the bore-acoustics work:**
>
> The drum and string cases are 2D/1D *distributed vibrating structures*
> with a spatial dimension the excitation can be localized within (you
> strike a specific point on a membrane, or a specific point on a string).
> The cloaking effect depends on that — the ring is a spatial boundary
> that traps certain frequencies inside it. A clarinet bore doesn't have
> that kind of spatial freedom for the player; excitation happens at one
> end (the reed), and the 'space' the wave travels through is 1D by
> construction. So direct transplant of the *cloaking* mechanism
> isn't really available to you — there's no meaningful 'strike inside vs.
> outside the ring' analog in a wind instrument, because there's only one
> place air gets pumped in.
>
> What *does* transplant, though, is the underlying method, not the specific
> cloaking geometry: periodic or patterned mass/stiffness loading creating
> frequency-dependent dispersion and band gaps. That's precisely what the
> Helmholtz side-branch and locally-resonant liner ideas from earlier in
> this conversation are doing to your bore — same toolkit (add resonant
> elements, get selective band suppression or dispersion shaping), just
> applied to a 1D acoustic waveguide instead of a 2D membrane or a string.
> The frame-drum and sonic-crystal-string work is good validation that the
> *general* metamaterial-in-acoustic-instruments idea is sound and has been
> demonstrated experimentally, even though the specific mechanism (spatial
> cloaking on a 2D membrane) isn't one you can borrow directly for a bore.
>
> **One place it might transplant more literally**: if you ever get into
> pad/key mechanism design, or resonant elements in a bell or mute wall
> (the brass mute idea from earlier), those *are* effectively small 2D
> plates or membranes, and the mass-ring/cloaking mechanism could apply
> there in something closer to its original form — e.g., a mute's flat
> reflective surface with an embedded mass pattern shaping which frequencies
> get reflected vs. absorbed. That's a more direct lift from the Bader work
> than anything in the main bore."

### A.3 Guitar metamaterial research synthesis

> **Claude:** "This is a much richer research area than I expected — there's a
> real, small but active line of guitar-specific metamaterial work, and it
> maps onto ideas your printer is unusually well-suited to test.
>
> **Acoustic guitar — soundboard/top-plate work is the most developed strand.**
> Two threads exist: Espinoza-Oñate and colleagues explored locally coupling
> tunable mechanical metamaterials to a guitar soundboard to absorb specific
> frequency ranges and change its vibrational properties, essentially the
> 2D-plate analog of the Helmholtz side-branch idea — a resonant patch
> bonded onto the top, tuned to selectively damp or reshape particular
> resonances rather than changing the whole plate. Separately, a numerical
> FEM study modeled mechanical metamaterials (deliberately patterned
> perforation geometries) in classical guitar top plates, evaluating impact
> on modal behavior, sound pressure level, and structural integrity under
> actual string tension, concluding the approach is feasible and beneficial
> — and the stated motivation is the interesting part: it lets a maker
> independently tune density and stiffness rather than being at the mercy
> of natural wood variation, addressing the classic luthier problem where
> two guitars built the same way from the same tree still sound different
> because of intrinsic material inconsistency.
>
> **This connects directly to your fabrication advantage.** There's a
> directly relevant printed-instrument study: researchers compared ukulele
> soundboards made from Engelmann spruce, Chilean laurel, and 3D-printed
> PLA+, and found the printed plates were dramatically more consistent
> between samples — correlation around 0.94 between printed plates versus
> only 0.19–0.65 between natural wood plates of the same species. That's
> not really a metamaterial result on its own, but it's the enabling
> condition for one: it confirms your printer can hit repeatable target
> mechanical properties, which is exactly what a perforated/lattice
> metamaterial soundboard design needs in order to be worth engineering
> in the first place.
>
> **Electric guitar** doesn't show up in this literature at all — the
> metamaterial research is squarely acoustic (vibrating plates and strings),
> and electric guitar tone is dominated by string vibration sensed
> electromagnetically by the pickup, not by the body radiating sound. That
> said, a couple of things do transfer: body chambering (already a
> mainstream tone-shaping technique) is structurally the same problem as
> the guitar-top perforation work — engineered internal lattice geometry to
> hit a target stiffness/mass/damping profile instead of relying on which
> slab of wood you got. And the sonic-crystal string concept (periodic mass
> loading, from the Bader/Kontopidis work mentioned earlier) applies
> identically to a steel or nylon guitar string regardless of whether it's
> amplified magnetically or acoustically, since it changes the string's
> own dispersion before the signal ever reaches a pickup or a soundboard.
>
> **One thing worth flagging as a genuinely available idea, not speculation**:
> an acoustic guitar's body-plus-soundhole is already a Helmholtz resonator
> (the classic 'main air resonance,' usually around 90–100 Hz). That means
> the side-branch element from your `metamaterial_elements.py` isn't just
> an analogy for guitar work — a secondary internal resonator coupled to
> that main air cavity is a literal, direct extension of code you already
> have, no new physics needed.
>
> **Most prototypable idea overall**: a small mass on a compliant mount
> clamped to a guitar string (or embedded in a printed bridge/saddle piece)
> is a buildable object, unlike an equivalent structure inside a woodwind
> bore. That's probably the most immediately prototypable idea in this
> whole conversation if you ever want a fast physical test: no bore, no
> reed, no viscothermal loss model — just a string, a clip-on resonant
> mass, and a tuner."

### A.4 String metamaterial — Bloch band gaps and physical interpretation

> **Claude:** "Here's the mass-loaded string element I promised, implemented
> via the Bloch transfer-matrix method (same technique as computing
> phononic-crystal band structure) — includes both a rigid periodic
> mass-loading case (the classical Brillouin loaded-string problem, closest
> to the Bader '1D string' result) and a spring-mass local-resonator case
> (the modern locally-resonant-metamaterial mechanism, closer to what gives
> a genuine deep sub-wavelength band gap):
>
> ```text
> Rigid periodic mass-loading (5cm spacing, 50mg masses):
>   Gaps: (1580.0, 4183.3), (4768.6, 8000.0)
>   → first gap's upper edge lands almost exactly at c/(2a) = 4183 Hz,
>     confirming it's Bragg-scattering behavior set by lattice spacing
>
> Locally-resonant attachment (100mg mass, spring tuned to 1500 Hz):
>   Gaps: (921.1, 2925.6), (4183.8, 5918.5)
> ```
>
> One honest note on that second result: the gap opens at 921 Hz, below the
> resonator's own bare tuning of 1500 Hz — that's real physics
> (hybridization between the resonator and the string pulls the gap edge
> down from the nominal f0, an 'avoided crossing' effect), not a bug, but
> it does mean 'tune the resonator to f0 and expect the gap to sit exactly
> there' is only a first approximation — same lesson as the trumpet
> valve-slide case: naive placement gets you in the right neighborhood, a
> proper design needs a small optimizer loop around this function rather
> than hand-picking (mass, spring stiffness) once.
>
> **Physically, what a spring-mass string attachment could even mean for a
> guitar** — this isn't just a math abstraction. A small mass on a compliant
> mount clamped to a string (or embedded in a printed bridge/saddle piece)
> is a buildable object, unlike an equivalent structure inside a woodwind
> bore. That's probably the most immediately prototypable idea in this
> whole conversation if you ever want a fast physical test: no bore, no
> reed, no viscothermal loss model — just a string, a clip-on resonant
> mass, and a tuner."

### A.5 Open question on languages (unanswered in conversation)

> **User:** "also, any thought on best languages for coding this?
> this being very broad, from the more traditional modeling to metamaterial related modeling"
>
> *No response recorded in the export — the conversation ended here. See §8
> for this repo's precedent (Python + numpy/numba/JAX).*

---

## Appendix B: Verbatim excerpts from the continuation Claude conversation (2026-08-03)

*Source: `Metamaterials in woodwind instruments2 - Claude.html` export.
This continuation focused on folded low clarinets, a general bore-modeling
and optimization framework, and a JAX-autodiff Helmholtz element.*

### B.1 Folded low clarinets — concrete problem, failure mode, design implication

> **Claude:** "Folded low clarinets are a good target for this — the folds
> themselves are a known source of the notoriously rough intonation on
> contra-alto/contrabass instruments, which gives the metamaterial
> approach a concrete problem to aim at rather than just a novelty."

> **Claude (after running the folded bore model):**
> ```text
> bass clarinet:      251.4 Hz straight -> 249.6 Hz folded (1 bend)   -12.8 cents
> contra-alto:        172.7 Hz straight -> 170.4 Hz folded (2 bends)  -22.9 cents
> contrabass:          63.9 Hz straight -> 62.8 Hz folded (3 bends)   -27.8 cents
> ```
>
> **The trend** — more folds, larger flat-ward shift — matches what's
> actually reported about these instruments being harder to keep in tune
> than soprano clarinet, and gives you a testable hypothesis: fold
> count/geometry is a real contributor, not just "bigger tube = harder to
> voice."
>
> **The more useful result was the failure mode, not a clean fix.**
> I initially tried to correct the contrabass fundamental with a rigid
> Helmholtz resonator the same way as the trumpet valve slide earlier —
> and it required an unreasonable neck length. The feasibility table makes
> why explicit: pulling a ~250 Hz bass-clarinet fundamental into tune
> needs a 13–150 cm neck depending on cavity size; a ~63 Hz contrabass
> fundamental needs 2+ meters even with a generous 100 cm³ cavity. That's
> not a bug, it's the physics — a rigid air-column resonator's tuning is
> fundamentally geometry-limited, and low frequencies demand long
> geometry.
>
> **The actual design implication**: for these low instruments, rigid
> Helmholtz resonators are the right tool for shaping upper partials and
> formants (same neck-length scale as the ~1kHz soprano clarinet work
> earlier), but the wrong tool for correcting the fundamental itself. For
> that register, the locally-resonant liner mechanism from
> `metamaterial_elements.py` (`effective_density_locally_resonant`) is a
> better fit precisely because its tuning knob is spring stiffness, not
> physical air-column length — it doesn't hit this wall. That's a real,
> non-obvious conclusion from working through the numbers rather than
> something I'd have guessed going in."

### B.2 General bore modeling + benchmarking + optimization framework (Part A + B)

> **Claude:** "Good to know — I have scipy here but not jax or pymoo (no
> network in this sandbox to install them). I'll build and fully test the
> scipy-based parts, and write the JAX-autodiff piece to mirror the tested
> math exactly (since that's what plugs into your existing JAX branch) —
> flagged clearly as untested-here rather than pretending I ran it.
>
> **Part A finding worth flagging**: the sanity test surfaced something
> real, not a bug — opening the tonehole closest to the reed produced a
> *lower* impedance peak (201.6 Hz) than fully closed (425.1 Hz), which
> is backwards from the usual 'opening a hole raises pitch' intuition.
> Checking all peaks shows it's genuinely the strongest resonance in the
> range, not noise...
>
> That resolved cleanly — my demo's frequency scan started at 200 Hz and
> clipped the true fundamental (141.5 Hz); the '425 Hz' I originally
> reported was actually the 3rd harmonic of a closed-open pipe series.
> Once scanned from 30 Hz, the physics checks out (odd-harmonic series
> for all-closed; partial-venting behavior — real physics, not a bug —
> for the too-small tonehole).
>
> **Part B: benchmarking metrics + two-phase optimizer** (fully tested
> here with scipy; JAX/pymoo pieces flagged separately since I can't
> install them in this sandbox)...
>
> That sensitivity result is a grid-resolution artifact, not a real zero
> — worth catching and fixing rather than shipping:
>
> Now it gives a real, actionable number — 0.4 cents of expected pitch
> drift from ±0.1mm print tolerance on that hole's position for this
> design, well within the audible-just-noticeable-difference range, which
> is exactly the kind of check that matters before committing a design to
> print.
>
> One more piece to sketch — the JAX-autodiff version for your existing
> branch (I can't test this here since jax isn't installed and I have no
> network access to add it, but it mirrors the tested
> `helmholtz_shunt_matrix` math exactly, so translation risk is low):"

### B.3 JAX resonator sketch (flagged untested)

> **Claude:** "Here's the mass-loaded string element I promised,
> implemented via the Bloch transfer-matrix method... [string metamaterial
> code already in Appendix A.4]
>
> **JAX-autodiff version of the Helmholtz shunt element**, for use in the
> project's existing JAX optimizer branch.
>
> ```python
> STATUS: UNTESTED IN THIS SANDBOX. jax isn't installed here and this
> sandbox has no network access to install it. This mirrors
> metamaterial_elements.helmholtz_shunt_matrix line-for-line (same
> formulas, same variable names), which HAS been tested -- so translation
> risk is low, but run this yourself before trusting it.
> ```
>
> **Why this matters for your project specifically**: your JAX branch's
> known limitation is that it can't differentiate with respect to hole
> positions/diameters because they're baked into a static action chain at
> trace time. A resonator defined purely algebraically like this (no
> Python-level branching on the frequency array, no scipy calls) traces
> cleanly and IS differentiable end-to-end with respect to every
> geometric parameter passed in — V, neck_length, neck_radius all become
> ordinary JAX tracers. Use `jax.grad` / `jax.value_and_grad` directly
> instead of finite differences, which should sidestep the PAVA-plateau
> and slow-serial-finite-difference issues from your `two_phase_optimizer`
> work.
>
> For a multi-element chain (several resonators + bore segments), the
> same pattern extends: write the whole chain multiplication in
> `jax.numpy` (jnp.matmul / the `@` operator both trace fine), and
> `jax.grad` will differentiate through the ENTIRE chain automatically —
> true adjoint-equivalent gradients, no finite differences, no PAVA
> plateau."
