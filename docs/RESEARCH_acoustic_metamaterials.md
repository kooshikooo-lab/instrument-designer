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
