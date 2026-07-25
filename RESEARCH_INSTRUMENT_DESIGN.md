# Deep Research: Instrument Design, Manufacturing & Acoustics

Collected 2026-07-23. Consolidates manufacturing, fingering, acoustics, tuning,
measurement data, spectral analysis, and sound characterization research.

---

## PART 1: MANUFACTURING

### Traditional Saxophone (Selmer, Yanagisawa, Yamaha)
- Body: 0.6–0.7mm brass sheet, cut trapezoidally, rolled, welded at 1000°C, drawn on conical chuck
- Tone holes: drawn-out from oblong holes (Selmer since 1922) — maintains continuous grain
- Hydraulic inflation (Selmer): liquid under pressure into matrix for final dimensions
- Bells: pressed in two half-shells then argon-welded (alto/tenor) or hand-shaped (baritone)
- Average saxophone: 600+ individual parts (Selmer)
- Over 2,000 press dies at Yanagisawa factory

### Traditional Clarinet (Buffet Crampon)
- Grenadilla (Dalbergia melanoxylon) dried for several years
- Bored longitudinally, turned on lathe, seasoned again
- Buffet polycylindrical bore: variable cross-section for tonal character
- Undercutting: tone hole interiors beveled by hand — "major influence on timbre"
- Buffet Greenline: 95% grenadilla powder + 5% polycarbonate/epoxy — eliminates cracking

### CNC Machining
- Standard across all manufacturers for bore drilling, post turning, key stamping
- Bore tolerances: micron-level precision required
- Yanagisawa posts cut on CNC lathes with 2,000+ different press dies

### 3D Printing
| Technology | Best For | Materials | Notes |
|---|---|---|---|
| SLA/MSLA | Mouthpieces, smooth bores | Photopolymer resin | 19μm XY resolution possible |
| SLS | Full bodies, keywork | Nylon PA12, PA11 | Similar mechanical properties to wood |
| FDM | Prototyping, education | PLA, ABS, PETG | Layer lines problematic for precision |
| DMLS/SLM | Metal instruments, keywork | Ti, SS, brass | Often needs secondary CNC |

### 3D Printing Key Facts
- Olaf Diegel (2014): First functional 3D printed sax — SLS nylon PA12, 41 components, 575g
- SLA mouthpieces: hold 0.7mm tip opening within 0.05mm tolerance
- Nylon PA12: very similar mechanical properties to wood
- Geometry dominates performance for diffusers, waveguides, bells
- Surface condition matters more than bulk material for acoustics (Wolfe 2018)

### PVC Pipe Instruments
- Schedule 40 PVC: 1" diameter matches Bb clarinet bore (~14.64mm ID)
- Bart Hopkin: nominal 1/2" PVC conduit ID "remarkably close" to Bb clarinet bore
- Acetal Delrin (POM) recommended as non-toxic alternative to PVC
- Joint sealing: PVC cement (permanent), rubber gaskets (removable)

### Key Manufacturing Tolerances
- Bore: micron-level precision for critical dimensions
- Surface finish: rough internal surfaces act as vibration dampers
- Hole edge sharpness: affects response and tone — undercutting improves versatility
- Wall thickness: Buffet maintains acoustic properties while preventing cracks

---

## PART 2: FINGERING SYSTEMS & KEYWORK

### Boehm System (Flute/Clarinet)
- Ring keys: one finger closes two holes simultaneously
- Plateau keys: solid cups for finger coverage
- Full venting: keys normally OPEN, close when pressed (opposite of pre-Boehm)
- Clarinet: 17 keys + 6 rings standard
- Register key: ~1.0–1.6mm diameter vent, suppresses lower resonances

### Saxophone Keywork
- Octave mechanism: Selmer swivel arm dominates modern design
- Tilting table (Mark VI, 1954): Bb touchpiece tilts when C# depressed
- Articulated G#: any pinky key can activate via interconnected levers
- Palm keys: D, Eb, F — upper stack operated by left palm
- Front F key (Evette 1899): auxiliary lever for altissimo

### Oehler System (German Clarinet)
- Up to 27 keys vs Boehm's 17 keys + 6 rings
- Additional tone holes correct intonation deficiencies
- Zig-zag register key with chimney projecting ~4mm into bore
- Concave mouthpiece table for better reed seal

### Compliant Mechanisms (3D Printing)
- Patent WO20170243570: integrally formed key with elastomeric material — no springs needed
- Multi-material FFF living hinges: ABS/PLA rigid bodies + TPC flexible hinges
- Vertical flexure hinges: TPU + PLA/PETG for out-of-plane mechanisms
- Olaf Diegel challenge: traditional springs can't grip in plastic upstands

### Key Ergonomics
- Hand maintained in "tennis ball" position (racquetball 5.7cm diameter)
- Finger movement from knuckles (MP joints), not fingertips
- Key press ~10ms, release ~16ms (spring return)
- Professionals: more nearly simultaneous multi-finger transitions

---

## PART 3: ACOUSTIC DESIGN METHODS

### TMM (Transmission Line Matrix)
- Models bore as cascade of 1D waveguide segments (2×2 transfer matrices)
- Very fast: thousands of impedance curves per second
- Accurate for slowly varying bores (< 10 cents error)
- Fails for: flaring bells (higher-order modes), bore curvature
- Our TMM port: `tmm_acoustics.py` — faithful port of chalumier

### Tone Hole Modeling (Keefe, Dalmont, Nederveen)
- T-junction with series impedances (bore air mass) and shunt impedance
- Open tonehole effective length: `te = [(1/k)tan(kt) + b(1.40-0.58(b/a)^2)] / [1-0.61kb·tan(kt)]`
- Tonehole lattice cutoff: `fc ≈ 0.11·(b/a)·v / √(s·t)`
  - Below fc: first open hole acts as short circuit
  - Above fc: waves penetrate past first open hole
- Saxophone cutoff varies significantly across first register (unlike clarinet)

### Bore Profiling
- Bessel horn family: `S(x) = c·(x-x₀)^e` where e = flare parameter
  - e=0: cylinder (clarinet, flute)
  - e=2: cone (oboe, saxophone)
  - e=7: steep horn (impractical)
- Piecewise conical sections optimal for brass bells (Noreland)
- Exponential, catenoidal, parabolic also common

### Bell Design
- Impedance transformer between bore and free space
- Low frequencies radiate omnidirectionally; high frequencies beam forward
- Bell vibrations shift impedance peaks up to 5% (Kausel 2015)

### Software Tools
| Tool | Language | Method | Notes |
|---|---|---|---|
| Openwind | Python | Spectral FEM / TMM | GPL, INRIA, bore reconstruction |
| WWIDesigner | Java | TMM + BOBYQA/DIRECT | Bore + tonehole optimization |
| Demakein | Python | Tree-structure resonance | STL output for 3D printing |
| Chalumier | Kotlin | Evolutionary algorithm | Python port in our codebase |
| MoReeSC | Python | Modal decomposition | Reed interaction simulation |
| NESS Brass | C | FDTD | Brass instrument simulation |
| ARTool | C++ | TMM | Impedance calculation |

### Key References
- Benade (1976): Fundamentals of Musical Acoustics — seminal woodwind theory
- Nederveen (1998): Acoustical Aspects of Woodwind Instruments
- Fletcher & Rossing (1998): Physics of Musical Instruments
- Keefe (1982, 1990): Tone hole models, woodwind air column models
- Ernoult et al. (2020): JASA — impedance-based optimization with constraints
- Noreland et al. (2013): "The Logical Clarinet" — numerical optimization, <10 cents
- Lefebvre & Scavone (2011): McGill PhD — TMM/FEM comparison
- Chaigne & Kergomard (2016): Acoustics of Musical Instruments

---

## PART 4: TUNING & INTONATION

### Temperament
- ET: 100 cents per semitone — all intervals compromised except octave
- Just Intonation: pure ratios (3:2=702c, 5:4=386c) — wind ensembles naturally gravitate here
- Performers instinctively adjust toward JI in harmonic contexts, Pythagorean in melodic

### Reference Pitch
| Standard | Frequency | Usage |
|---|---|---|
| A=440 Hz | ISO 16 standard | USA, UK, ISO |
| A=442 Hz | Most European orchestras | Chicago, Boston, NY Phil |
| A=415 Hz | Baroque (HIP) | ~89.7 cents below A=440 |

### Register Tube Design (Clarinet — Szwarcberg et al. 2024–2026)
- Diameter: 3.0 mm (strictly >2.5, <3.5) for reliable register transition
- Chimney height: 13mm best compromise; 7mm only E5-G#5 in tune
- Placement: ~84mm from barrel top (~1/3 total bore length)
- Nonlinear losses essential — without them, simulations never produce 2nd register

### Cross-Fingerings
- Standing waves propagate past first open hole with increasing strength at higher frequencies
- Inharmonic resonance spacing → darker timbre (weakened high harmonics)
- Modern large-hole flutes minimize cross-fingering effects

### Tone Hole Lattice
- Saxophone cutoff varies across register (unlike clarinet ~constant)
- Cutoff determined by hole geometry and spacing, independent of source
- Severity of cutoff matters more than cutoff frequency for timbre

---

## PART 5: PROFESSIONAL INSTRUMENT MEASUREMENTS

### Clarinet Bore Dimensions (mm)
| Make/Model | Bore Diameter |
|---|---|
| Buffet R13 | 14.64 (0.577") polycylindrical |
| Buffet Tosca | 14.55 (0.573") |
| Buffet Vintage R13 | 14.48 (0.570") |
| Selmer Signature | 14.60 (0.575") |
| Selmer Centered Tone | 14.95 top / 15.10 bottom |
| Selmer Series 9 | 14.935 (0.588") |
| Yamaha 34 | 15.13 top / 14.68 lower |
| Conn 424 | 15.45 top / 15.22 bottom |
| LeBlanc Concerto | 14.61 cylindrical |
| Buescher True Tone | 15.5 (0.600") |

### Bass Clarinet Dimensions (from research)
| Brand/Model | Bore (mm) | Notes |
|---|---|---|
| Selmer Privilege | 23.5/23.4 | Professional |
| Buffet Prestige/Tosca | ~24.0 | Professional |
| Leblanc 430S | 24.00 | Historical |
| Typical range | 22–25 | Varies significantly |

### Bass Clarinet Keywork Variation (CRITICAL)
- Different brands have different solutions for certain notes
- Low C vs Low Eb: different bore lengths, key mechanisms, bell sizes
- Register hole: position and dimensions vary between manufacturers
- Some use double-register systems for extended range
- Fork fingerings and alternate fingerings differ between brands

### Saxophone Measurements
- Alto bore at neck: ~12.0 mm; at bell: ~60 mm
- Alto total conical length: ~1750 mm
- Tenor bore at neck: ~13.5 mm; at bell: ~72 mm

### Buffet R-13 Impedance Peaks (Holz, UIUC)
All holes closed, Concert F3:
| Harmonic | Freq (Hz) | Type |
|---|---|---|
| 1 | 185.5 | Max |
| 3 | 549.5 | Max |
| 5 | 912.5 | Max |
| 7 | 1286.5 | Max |
| 11 | 2019.5 | Max |
| 13 | 2452.5 | Max |

### UNSW Clarinet Impedance (Wolfe et al.)
- Mean resonance spacing: f_n/n = 131.5 ± 0.5 Hz
- Even harmonics systematically weaker in low register
- Cutoff: ~2.5–3 kHz

### Selmer Saxophone Factory (Cottier, Gibiat 2014)
- Over 10,000 impedance measurements in factory database
- Harmonicity profiles, bore optimization from impedance data

### Benade Archive (Stanford MARL)
- Complete bore measurements, tonehole dimensions, blueprints
- Buffet A and Bb clarinets, Buffet bass clarinet
- Marigaux clarinets, Selmer Albert-system
- Boosey & Hawkes #236498 (Reginald Kell's)
- NX experimental clarinet, saxophones, bassoons, flutes
- URL: https://ccrma.stanford.edu/marl/Benade/research.html

### Measurement Databases
| Source | Instruments | Data Type |
|---|---|---|
| UNSW (Wolfe) | Bb Clarinet, Flute, Sax | Impedance spectra + sound |
| McGill CAML | Saxophone, conical systems | Impedance spectra |
| Good-Sounds.org | 12 instruments, 15 pros | Audio + Essentia features |
| IRCAM ECRINS | All instruments | 117K sounds, 6 mics |
| RWC Database | Flute, oboe, clarinet | Monophonic samples |
| Selmer Paris Factory | Saxophones | 10K+ impedance measurements |

---

## PART 6: SPECTRAL ANALYSIS & SOUND CHARACTERIZATION

### Clarinet Spectral Characteristics
- Low register: odd harmonics dominant (cylindrical closed-open pipe)
- 1st & 3rd harmonics strongest; even harmonics weakened
- Upper register: even/odd distinction decreases
- SPL range: 62-84 dB typical; 4-21 harmonics; highest 3094-4893 Hz

### Saxophone Spectral Characteristics
- All harmonics present (conical bore)
- Symphonic: harmonics fall off linearly in dB
- Jazz: harmonics strong below 5kHz, abrupt cutoff ~5kHz, more inharmonic energy
- Mouthpiece pitch correlates: A5→symphonic, Eb5→jazz (Gupta & Nair)

### Timbre Dimensions
- 3D timbre space: Attack Time, Spectral Centroid, Odd/Even Harmonic Ratio
- 7-dimensional: Affinity, Sharpness, Harmonicity, Monotony, Medium Contrast, Medium Affinity + f0

### Mouthpiece Effects on Spectrum
- Small chamber → emphasis upper harmonics → "brighter"
- Large chamber → emphasis lower harmonics → "darker"
- Baffle → further upper harmonic emphasis
- A-frame (trapezoidal) → vowel "E"
- U-frame (rectangular) → vowel "A"
- Tip opening affects response more than tone

### Reed Effects
- Harder reeds: stronger high harmonics, more resistance
- Softer reeds: weaker high harmonics, easier response
- Reed brand differences measurable in spectral analysis

### Player Effects
- Embouchure: saxophone vocal tract can bend pitch 330 cents downward
- Vibrato: ~54 cents max variation via lip pressure
- Dynamics: affect harmonic content significantly
- Player-to-player variability is significant — "the player matters as much as the instrument"

### Measurement Tools
- Sonic Visualiser: Vamp plugins for spectral analysis
- IRCAM AudioSculpt: FFT, LPC, True Envelope, partial following
- Timbra: online feature extraction and comparison
- Essentia: open-source audio analysis library

### Sound Sample Libraries
- VSL: 25K+ clarinet samples, 52K+ saxophone samples
- Spitfire: BBC SO Professional, 67 instruments, 1M+ samples
- Good-Sounds.org: 15 pros, 12 instruments, Zenodo download

---

## PART 7: FUTURE DIRECTION — SPECTRAL TARGET OPTIMIZATION

### Concept
Use frequency analysis of professional instrument recordings to create target spectral
profiles. The optimizer would then aim to match both:
1. Intonation accuracy (frequency alignment) — already implemented
2. Spectral envelope (harmonic content) — future work

### Approach
1. Record professional instrument with known mouthpiece/reed setup
2. Extract spectral envelope per note (harmonic amplitudes, spectral centroid, rolloff)
3. Use as impedance target in TMM optimization
4. Adjust bore profile and hole dimensions to match both frequency AND spectral targets

### Key Challenges
- Mouthpiece, reed, and player technique profoundly affect sound
- Impedance peaks → radiated sound is nonlinear (reed nonlinearity, vocal tract filtering)
- Need to separate instrument contribution from player contribution
- Spectral envelope depends on dynamic level (louder = more harmonics)

### What We Can Do Now
- TMM impedance spectra already show resonance structure per note
- Harmonic amplitudes from impedance peaks relate to spectral envelope
- Could add spectral envelope matching as secondary optimization objective
- Good-Sounds.org provides pre-extracted features for reference instruments

### Important Caveat
The exact mouthpiece, reed, and player technique matters "quite a bit."
A Selmer Mark VI with a classical mouthpiece sounds very different from
the same horn with a jazz mouthpiece. Our optimization targets the BORE
and TONE HOLES — the mouthpiece/reed/embouchure layer sits on top.
