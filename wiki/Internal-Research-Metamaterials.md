# Acoustic Metamaterials Research

> Created: 2026-08-03 | Sources: Claude.ai + Kimi conversation exports (user-shared),
> live web research (verified 2026-08-03). Status: **REFERENCE — future work only**, no
> code changes.
> Working note: `docs/RESEARCH_acoustic_metamaterials.md` (desktop, uncommitted).
> Structure: this page is organized **by instrument category**, with a per-instrument
> subsection for each major candidate. The low clarinet family (contrabass, contra-alto,
> bass) is the deepest-dive section — see §4.

---

## 1. TL;DR

Three distinct metamaterial mechanisms map onto instruments:

1. **Helmholtz side-branch / locally-resonant liner** (1D waveguide) — directly applicable
   to a woodwind bore, and a *literal* extension of the existing TMM tonehole/network code.
2. **Sonic-crystal periodic mass loading** (1D string) — Bloch band gaps from periodic
   impedance discontinuities; the string case is the closest *prototypable* physical test.
3. **2D membrane / plate cloaking or resonant-patch damping** (drum, soundboard) — does
   **not** transplant to a bore (single excitation point), but maps to mutes, pads,
   soundboards, and guitar tops.

Key finding: a woodwind's **tonehole lattice already is a periodic medium** (Benade cutoff /
pass-stop bands), i.e. woodwinds are already "accidental" metamaterials. Engineered
resonators are a natural next step, not a foreign insert.

Ranking takeaway (Kimi): **low woodwinds are the standout unproven category** (contrabass
clarinet Bb top candidate, ~3 m tube, sub-wavelength features ~10–30 cm); percussion is the
proven case; folded bores add a parallel-waveguide topology a straight bore cannot reach.

## 2. Mechanisms and what transplants

| Mechanism | Structure | Band gap from | Transplants to |
|---|---|---|---|
| Helmholtz side branch | shunt resonator on a waveguide | local resonance, sub-wavelength | **Bore liner, mutes, register/vent tuning** — the TMM `Port` model |
| Bragg / sonic crystal | periodic impedance steps | lattice spacing `a` (gap ~ `c/(2a)`) | strings (mass loads), tonehole lattices (already there) |
| Locally resonant | spring–mass attachments | resonator f0, sub-wavelength | strings, bridge/nut masses, resonant plates |
| Membrane cloaking | mass-ring on 2D membrane | ring boundary traps band | **No** for bore; yes for mutes/pads/drumheads |

The wind-bore case: excitation is at one end only, so the 2D "strike inside vs. outside the
ring" freedom that makes the frame-drum trick work **does not exist** in a bore. What *does*
transfer is the method — patterned resonant elements creating frequency-dependent dispersion
and band gaps — applied to a 1D acoustic waveguide.

## 3. By instrument category — summary ranking

| Rank | Category | Verdict | Proof status | Section |
|---|---|---|---|---|
| ★★★★★ | Percussion (membranes/plates) | Proven timbre-extension | Physical drum built & measured (Bader 2019) | §4 |
| ★★★★★ | **Low woodwinds** (contra, contra-alto, folded bass) | Standout *unproven* candidate | Theory + geometry only; no published work | §5 |
| ★★★★☆ | Plucked strings / guitar soundboard | Strong FEM evidence | Simulation (Lercari 2022); printed prototypes | §6 |
| ★★★★☆ | Low saxophones (bari low-A, bass) | High-value retrofit targets | Known intonation compromises to fix | §7 |
| ★★★☆☆ | Piano soundboard | "Already metamaterial-like" | Rib bracing = periodic structure | §8.3 |
| ★★★☆☆ | Standard woodwinds (flute/oboe/clarinet/sax) | Accidental metamaterials | Tonehole-lattice cutoff theory (Petersen 2020) | §9 |
| ★★☆☆☆ | Bowed strings | Risky | Phononic strings exist; stick-slip coupling risk | §8.2 |
| ★★☆☆☆ | Brass | Poor fit | Band gap = dead register; smooth-bore constraint | §10 |
| ★★☆☆☆ | Lamellophones (mbira/kalimba) | Fertile but marginal | — | §11 |

## 4. Percussion — the proven case

### 4.1 Frame drum (Bader et al. 2019)

- **Bader, Fischer, Münster & Kontopidis, *Metamaterials in musical acoustics: A modified
  frame drum*, JASA 145(5):3086–3094 (2019)**, https://doi.org/10.1121/1.5102168.
- A 40 cm mylar (BoPET) drum head with 2×10 neodymium magnets (5 mm dia × 5 mm) forming rings
  at 8/10/12 cm diameter produces a **band gap ~300–400 Hz to ~700–800 Hz**.
- Striking inside vs. outside the ring gives **two non-overlapping timbral families** (plus a
  blended rim zone) — articulation variety a regular drum cannot produce.
- Theory (ISMA 2019 preprint): band-gap cutoff set by ring radius & magnet spacing; sub-wavelength
  spacing means cloaking, not scattering. https://pub.dega-akustik.de/ISMA2019/data/articles/000045.pdf
- Why it transplants poorly to bores: the effect relies on choosing **excitation position**
  relative to the ring — a bore has one excitation point (reed) and no such freedom (§2).

## 5. Low clarinets — the top candidate family (deep dive)

> Family = Bb contrabass, Eb contra-alto, Bb bass (straight & folded), and the historical
> bass clarinet in A. All cylindrical-bore with closed end → odd-harmonic series, sparser
> modes, uniform geometry (§5.5). All live at low frequency where a sub-wavelength resonator
> is small enough to 3D print (§5.6).

### 5.1 Contrabass clarinet Bb — ★★★★★

- **Why the king candidate.** Fontaine-Besson's 1889 pedal clarinet: "a tube 10 feet (3.0 m)
  long, in which cylindrical and conical bores are combined. The tube is doubled up twice upon
  itself." Modern Selmer/Leblanc: 71.3 in body; bore cylindrical except a conical bell joint.
- **Fundamental.** Low C (written) sounds **Bb0 ≈ 29 Hz**; wavelength ≈ 11.7 m, so
  sub-wavelength metamaterial features are only ~10–30 cm — trivially printable.
- **Known defect to fix.** Lowest notes are "unavoidably a little rough" — an impedance-matching
  problem at the cyl→cone transition and bell cutoff. A **graded metamaterial bell liner**
  (Helmholtz-resonator distribution, §9.3) could smooth it.
- **Why it's the safest first experiment.** The instrument already exists, the register is
  standardized enough to matter to players, and the failure mode (band gap off-target) is
  measurable with the repo's TMM before anything is printed.

### 5.2 Contra-alto clarinet Eb — ★★★★☆

- Transposition: written C sounds Eb1 ≈ 39 Hz — the next step below the contrabass.
- Acoustic length "often exceeds 1.7 m"; it is "**the least standardized member of the clarinet
  family**" → **no sacred design to preserve**; a metamaterial retrofit faces no orthodoxy.
- Leblanc 350 "paperclip" model is physically shorter than a Bb bass — a folded-geometry
  precedent already in production (§5.6).

### 5.3 Bass clarinet (straight Bb) — ★★★☆☆

- Cylindrical bore + flared bell → the *cleanest* periodic tonehole lattice in the clarinet
  family; the band-gap/cutoff theory applies most directly.
- Low register down to written Eb3 ≈ 78 Hz → any local resonator must be sub-wavelength at
  **low** frequency — exactly the regime Helmholtz resonators are good at.
- But: it is heavily standardized and heavily played; retrofit risk is higher than the
  low-clarinet extremes. Rated ★★★☆☆ because it's the *right physics* with the *wrong
  risk profile* — best used as the validation vehicle, not the first product.
- No published "bass clarinet metamaterial" work surfaced in searches; closest validated
  concepts are Helmholtz-resonator arrays (§9.3) and printed-instrument consistency work (§6.4).

### 5.4 Bass clarinet in A — timbre archaeology / on-demand timbre

- Introduced by Wagner in *Lohengrin* (1848); used by Mahler, Strauss, Bartók; now only
  offered routinely by custom maker Stephen Fox. Has a famously different low-register sound.
- Idea: a bore-surface metamaterial on a Bb instrument could emulate the A instrument's
  spectral signature — **timbre-on-demand without a second instrument**. This is the strongest
  "what does a metamaterial buy you" pitch for players.

### 5.5 Novel-shape folded bass clarinet — ★★★★★

- Designed *around* metamaterials rather than retrofitted. Ergonomic precedent proven by the
  19th-c. folded basses (Grenser 1793 bassoon-like bass clarinet; Papalini's serpentine).
- The folded layout gives the **parallel-waveguide topology** (§5.6) that makes coupled-bore
  metamaterial tricks available at all.

### 5.6 The folded-geometry advantage (cross-cutting)

A folded bore (bassoon-like, Leblanc "paperclip", double-U contrabass) creates **parallel
waveguide sections** separated by a thin wall — a coupled-waveguide topology a straight
instrument cannot replicate. The shared wall could be perforated periodically (directional
coupler / notch filter transferring energy between bore legs at chosen frequencies); each
straight segment becomes an independent acoustic module (segment 1 = chalumeau register,
segment 2 = clarion, U-bends as mode converters).

### 5.7 Cylindrical vs. conical for metamaterial design

Clarinet (cylindrical, closed end): odd harmonics only (1:3:5…), sparser modes → easier to
place band gaps without swallowing a needed harmonic; constant bore → uniform periodic
structures. Sax (conical, closed end): full 1:2:3… series → riskier; taper → structures must
be graded. Verdict: cylindrical-bore clarinets are the more forgiving first experiments.

## 6. Plucked strings / guitar (user plays electric + acoustic)

### 6.1 Guitar soundboard — mechanical metamaterials (Lercari 2022)

- **Lercari, Gonzalez, Espinoza, Longo, Antonacci, Sarti, *Using Mechanical Metamaterials in
  Guitar Top Plates: A Numerical Study*, MDPI Appl. Sci. 12(17):8619 (2022)**,
  https://doi.org/10.3390/app12178619.
- FEM of a Torres (1884) model with elliptical perforations (2 mm deep, not through-cut):
  metamaterials tune the response (eigenfrequencies + SPL) **without compromising structural
  integrity** → enables non-traditional woods with bespoke density/stiffness.
- **Fischer et al., *Sound designing classical guitars through metamaterials*, JASA 155(3_Suppl):A59
  (2024)** — alternation of magnet masses and placement determine bandgap location/strength
  (extends the frame-drum approach to the guitar top).

### 6.2 Acoustic guitar air resonance — literal side-branch model

The body+soundhole is already a Helmholtz resonator (~90–100 Hz); a secondary internal
resonator coupled to it is a **direct, literal** extension of the existing side-branch model —
no new physics.

### 6.3 Electric guitar — minimal metamaterial surface

Essentially no metamaterial literature (tone dominated by pickup sensing, not body radiation).
Transfers that do exist: body chambering as an engineered lattice (extrapolation, untested);
sonic-crystal strings apply identically since they change string dispersion before the pickup.

### 6.4 Printed ukulele soundboard consistency (enabler)

3D-printed PLA+ tops far more repeatable than wood (correlation ≈ 0.94 between printed samples
vs 0.19–0.65 for wood of the same species) — the *enabling condition* for engineering a
metamaterial soundboard: the printer can hit target mechanical properties.

### 6.5 Most prototypable idea overall

A small mass on a compliant mount clamped to a guitar string = locally-resonant string
metamaterial. No bore, no reed, no viscothermal model — just string + clip-on mass + tuner.

## 7. Low saxophones — retrofit targets

### 7.1 Baritone sax (low A) — ★★★★☆

- The low-A extension is a known compromise: makers added a cylindrical section between bell
  and bow, but "these horns generally suffer from intonation problems in the lowest few notes."
- A labyrinthine/corrugated **bell insert could create effective acoustic length without
  physical size**.
- Sax bore supports harmonics ~1:2:3 (UNSW) — more forgiving than clarinet's odd-only series.
  Huge working player base (big band/funk).

### 7.2 Bass sax — ★★★☆☆

- Between baritone and contrabass; existing (rare) instruments — same bell-region compromise
  logic as §7.1 but with a far smaller player base.

### 7.3 Contrabass sax — ★★☆☆☆

- ~15 original instruments exist, ~1.9 m tall; scarce enough that standardization and demand
  are weak — novelty economics.

### 7.4 Subcontrabass sax / tubax — ★☆☆☆☆

- 2.74 m tall, 28.6 kg, lowest note G#0 = 25.95 Hz. A physical novelty; metamaterial value
  (sub-wavelength acoustic length) is real but demand is minimal.

## 8. Strings (bowed) and piano

### 8.1 1D sonic-crystal string (Bader group)

A string covered with added masses produces a dispersion relation in the harmonic overtones —
still has pitch, but a very different timbre. Same group's book chapter: Bader et al.,
*Designing Musical Instruments and Room Acoustics with Acoustic Metamaterials*, Springer (2024),
https://doi.org/10.1007/978-3-031-57892-2_16 — covers the string, a labyrinth-sphere resonator
(band-gap damping at 770 Hz with a back plate, ~60% absorption), and the membrane.

### 8.2 Bowed strings — ★★☆☆☆

Phononic-crystal strings exist but risk breaking the bow/string stick-slip (Helmholtz-motion)
coupling → wolf notes. High-risk timbre experiment; not recommended first.

### 8.3 Piano soundboard — ★★★☆☆

Rib-stiffened plate is already "metamaterial-like" (periodic bracing → band-gap damping). A
designed lattice could replace bracing, but the soundboard is load-bearing (≈1 ton string
tension) — structural constraints dominate.

## 9. Standard woodwinds — the accidental metamaterial

### 9.1 Tonehole lattice as an existing periodic structure

- Since Benade, the **cutoff frequency** of the tonehole lattice is understood as wave
  propagation in a periodic medium: below cutoff the lattice is evanescent (stop band), above
  cutoff waves propagate (pass band) — precisely a phononic-crystal band gap.
- Petersen, Kergomard et al. generalized cutoff theory to **conical** lattices (saxophone):
  *On the tonehole lattice cutoff frequency of conical resonators — applications to the
  saxophone*, Acta Acustica 4, 13 (2020), https://doi.org/10.1051/aacus/2020012.
- Implication: the instrument already contains the metamaterial physics; we can quantify its
  band structure from the existing geometry (`backend/tone_hole_corrections.py`,
  `backend/core/network.py` ports).

### 9.2 Why bass clarinet specifically (same physics, §5.3)

Cylindrical bore + flared bell → the *cleanest* periodic tonehole lattice in the clarinet
family → band-gap/cutoff theory applies most directly; low fundamental register (~78 Hz) → the
sub-wavelength regime Helmholtz resonators excel at.

### 9.3 Disordered Helmholtz-resonator arrays (new, 2025–26)

- **Piva, Gower & Abrahams**, *Designing band gaps with randomly distributed sub-wavelength
  Helmholtz resonators* — npj Acoustics 2, 10 (2026), https://doi.org/10.1038/s44384-026-00045-w;
  arXiv:2505.01347.
- Key result: **randomly positioned** Helmholtz resonators create broad / multiple overlapping
  band gaps with *explicit asymptotic formulas* for effective bulk modulus — no heavy
  optimization needed. ~6% volume fraction gives a band gap around 140 Hz in a 32 mm layer.
- Why it matters: instead of hand-tuning one resonator, specify a **designed distribution of
  side-branch resonator sizes** for a target suppression band from a formula — very compatible
  with the repo's optimization workflows (`backend/two_phase_optimizer.py`, Pareto sweeps).
- Directly applicable to the low-clarinet **graded bell liner** of §5.1.

## 10. Brass — ★★☆☆☆

- The Claude `brass_scaffold.py` demonstrates a corrective Helmholtz resonator in a trumpet
  valve slide: ~15+ cents of pull from a 4 cm³ resonator. Naive placement overshot (−16.2 →
  +12.2 cents on the 1-3 combination); correct approach is an **optimizer loop** with
  (resonator volume, neck length, position along slide) as free parameters and cents-deviation
  as objective — the exact pattern of `backend/two_phase_optimizer.py`. Geometry is illustrative,
  not calibrated.
- Why brass is a poor fit overall: bore must stay smooth for airflow; harmonic series is rigid;
  a band gap = dead register; wall vibration is acoustically secondary.

## 11. Lamellophones (mbira/kalimba) — ★★☆☆☆

- Acoustically fertile (plucked tines with a resonator box) but culturally marginal; no strong
  use-case or player base to justify early work.

## 12. Integration mapping onto this repo's TMM

### 12.1 What exists today

- `backend/tmm_acoustics.py` — TMM resonance phase model; `junction2_reply_phase` /
  `junction3_reply_phase` (pipe junctions); toneholes and register vents enter as **side
  branches**, matching the physics needed for a Helmholtz-resonator element.
  `SPEED_OF_SOUND = 346100.0` mm/s (canonical chalumier value — Law 7).
- `backend/core/network.py` — `Port` dataclass with `node_type` (TONEHOLE / REGISTER_VENT); a
  `HELMHOLTZ` node type is the natural extension point.
- `backend/tone_hole_corrections.py` — side-branch/tonehole corrections; where cutoff /
  band-gap metrics would slot in.
- `backend/mouthpiece_models.py` + `backend/trumpet_acoustics.py` — the repo already computes
  Helmholtz resonances.

### 12.2 Feasible integration paths (future work, not built)

1. **Helmholtz side-branch element** (lowest friction): add `node_type=HELMHOLTZ` (cavity
   volume V, neck length, neck area) feeding into `junction2_reply_phase` with the resonator's
   impedance in parallel.
2. **Band-gap / cutoff metrics from existing geometry**: compute tonehole-lattice stop-band
   edges (Petersen/Kergomard periodic-medium theory) as a timbre-side objective.
3. **Resonator-distribution design**: use Piva/Gower/Abrahams effective-properties formulas to
   size a distribution of resonator volumes for a target suppression band, then run through the
   existing optimizers.
4. **String metamaterial calculator**: port `string_metamaterial.py` (Bloch transfer matrix) as
   a standalone script — mechanically the exact analog of the bore transfer matrix.
5. **Not worth pursuing**: 2D cloaking in a wind bore (no excitation-position freedom);
   electric-guitar pickup metamaterials (different physics domain).

### 12.3 Guardrails

- All of the above are *future-work* items; nothing is implemented.
- Any new third-party package would require declaration per the tool-registry guard.
- The TMM numba fast path (`TMM_USE_NUMBA`) is lossless-only; a resonator element that adds loss
  must stay on the pure-Python path or extend the njit function.

## 13. References (verified by live search, 2026-08-03)

### Metamaterials in musical instruments

- Bader, Fischer, Münster, Kontopidis — *Metamaterials in musical acoustics: A modified frame
  drum*, JASA 145(5):3086–3094 (2019). https://doi.org/10.1121/1.5102168 (PubMed PMID 31153336;
  open PDF https://rolfbader.de/wp-content/uploads/2019/06/Bader_etal_2019_MetamaterialFrameDrum.pdf).
- Bader, Fischer, Münster, Kontopidis — *Metamaterials in Musical Instruments*, ISMA 2019
  (band-gap cutoff theory for the magnet-ring drum).
  https://pub.dega-akustik.de/ISMA2019/data/articles/000045.pdf
- Bader et al. — *Designing Musical Instruments and Room Acoustics with Acoustic Metamaterials*,
  Springer (2024). https://doi.org/10.1007/978-3-031-57892-2_16
- Fischer et al. — *Sound designing classical guitars through metamaterials*, JASA 155(3_Suppl):A59
  (2024). https://pubs.aip.org/asa/jasa/article/155/3_Supplement/A59/3302007
- Gomez, Alberti, Spiousas, Salzano, Edelstein, Eguia — *Tunable sonic crystals as an extension
  of acoustical musical instruments*, ISMRA 2016 (La Plata). Cited in Acta Acustica 2022/2
  reference list.

### Metamaterials — mechanisms & fabrication

- Piva, Gower, Abrahams — *Designing band gaps with randomly distributed sub-wavelength
  Helmholtz resonators*, npj Acoustics 2, 10 (2026). https://doi.org/10.1038/s44384-026-00045-w
  (arXiv:2505.01347)
- Gower et al. — *Tailored acoustic metamaterials. Part I. Thin- and thick-walled Helmholtz
  resonator arrays*, Proc. R. Soc. A 478:20220124 (2022).
- Khodabakhsh, Movahhedy, Mohammadi — *A Helmholtz resonator based on spiral neck acoustic
  metamaterial for noise reduction*, Applied Acoustics 240:110957 (2025) —
  spiral neck shifts resonance ~5000→3000 Hz; 3D printed, impedance-tube validated.
  https://doi.org/10.1016/j.apacoust.2025.110957
- Lucklum — *3D Acoustic Metamaterial Using Interconnected Helmholtz Resonators*, DAS|DAGA 2025
  (pp. 1017–20), DTU — interconnected HR lattice, FEM + 3D print + impedance tube.
  https://doi.org/10.71568/dasdaga2025.414
- *3D printed small-scale acoustic metamaterials based on Helmholtz resonators* (IEEE) — additive
  manufacturing breaks the mass law; 3D-printed HR arrays create band gaps with deep attenuation.
  https://ieeexplore.ieee.org/document/8234381
- Pichard, Richoux, Groby — *Experimental demonstrations ... band gap tunability and negative
  refraction in two-dimensional sonic crystal*, JASA 132:2816–2822 (2012). https://doi.org/10.1121/1.4744974
- Meier et al. — *Scalable phononic metamaterials: Tunable bandgap design and multi-scale
  experimental validation*, Materials & Design 252:113778 (2025). https://doi.org/10.1016/j.matdes.2025.113778

### Woodwind acoustics — tonehole lattice & design

- Petersen, Kergomard et al. — *On the tonehole lattice cutoff frequency of conical resonators:
  applications to the saxophone*, Acta Acustica 4, 13 (2020). https://doi.org/10.1051/aacus/2020012
- Bowen, Buys, Sharp — *On the accuracy of calculation of the impedance spectra of woodwind
  instruments* (Heckel bass clarinet in A validation, ~10 cents agreement), Open University / RCM (2018).
- Ernoult, Vergez, Missoum, Guillemain, Jousserand — *Woodwind instrument design optimization
  based on impedance characteristics with geometric constraints*, JASA 148:2864 (2020).
  https://doi.org/10.1121/10.0002449
- Wolfe — *The Acoustics of Woodwind Musical Instruments*, Acoustics Today 14(1) (2018) (UNSW;
  tonehole cutoff). https://www.phys.unsw.edu.au/jw/

### Background

- Wikipedia — *Acoustic metamaterial* (mechanisms, sonic crystals, phononic crystals).
  https://en.wikipedia.org/wiki/Acoustic_metamaterial
