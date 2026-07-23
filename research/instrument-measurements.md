# Comprehensive Woodwind Instrument Measurements Library

Complete measured dimensions for recreating professional instruments. Organized by instrument family with all parts documented.

---

## SAXOPHONE FAMILY

### Alto Saxophone — Lefebvre Carbon Fiber Reference Cone (2008/2010)
**Source:** Lefebvre & Scavone, McGill — measured truncated cone for TMM validation
**Used for:** Validating TMM calculations against measurement data

| Parameter | Value | Notes |
|---|---|---|
| Input diameter | 12.5 mm | Mouthpiece end |
| Output diameter | 63.1 mm | Bell end |
| Length | 965.2 mm | Full air column |
| Cone half-angle | 3.00° | Straight cone |
| Material | Carbon fiber + epoxy resin | |

**First 5 impedance maxima (measured vs calculated):** Good agreement below 2 kHz.

---

### Alto Saxophone — Selmer Super Action Series II (SN 438024)
**Source:** Lefebvre & Scavone, Forum Acusticum 2008 — measured with probe microphone

| Parameter | Value | Notes |
|---|---|---|
| Overall bore length | ~1050 mm | Following center bore through bends |
| Bell diameter | 120 mm | |
| Body without toneholes | Not perfectly conical | Two bends + flared bell |
| Measurement precision | >0.1 mm | Stepper motor translation |

**Notes:** TMM calculations poorly estimated tonehole input impedance. "The transmission matrices for the toneholes are very difficult to evaluate due to the complex nature of the geometry that includes a leather pad hanging at a small distance above the hole."

---

### Alto Saxophone — Selmer Neck Dimensions
**Source:** Yamaha Australia comparison, Sax on the Web forum

| Neck Type | Mouthpiece End Diameter | Notes |
|---|---|---|
| Yamaha C1 | 12.13 mm | Smallest taper, most control |
| Yamaha E1 | 12.41 mm | Mid-range, versatile |
| Yamaha V1 | 12.56 mm | Largest, most open/free-blowing |
| Selmer Mk VI (typical) | ~12.0-12.3 mm | Varies by era |

**Yamaha alto neck lengths:** ~195 mm (standard)
**Selmer alto neck lengths:** ~195 mm (standard)

---

### Alto Saxophone — Lefebvre Thesis (2010) Reference Geometry
**Source:** McGill PhD thesis, Chapter 4 — six-tonehole saxophone design

**Mouthpiece model (standard practice):**
- Cylindrical, 15.8 mm diameter × 50 mm length

**Air-column starts:**
- Input diameter: 12.5 mm (there is a diameter jump from mouthpiece)

**Four investigated bore shapes (all from 12.5 mm input):**

| Shape | Description | Cone Angle | Notes |
|---|---|---|---|
| A | Straight cone | 3.0° | Baseline — decent harmonicity for first 9 notes |
| B | Straight cone | 3.5° | Larger angle — improves some, worsens others |
| C | Cylinder (25mm) + cone | 3.0° | Worse harmonicity than straight cones |
| D | Cone (50mm, 3.5°) + cone | 3.0°/3.5° | Worse harmonicity than straight cones |

**Key finding:** "A straight conical tube is not an appropriate geometry for a saxophone." Deviations found on real instruments play a role in proper harmonicity.

---

### Alto Saxophone — Average Modern Dimensions (Postma)
**Source:** sax.mpostma.nl — compilation of 70+ measured instruments

**Conicity ratios (mm length per 1mm width gain):**
| Instrument | Average Conicity |
|---|---|
| Soprano | 1:16.0 |
| Alto | 1:18.0 |
| Tenor | 1:19.1 |
| Baritone | 1:25.7 |

**Tone hole characteristics:**
- Typical diameter: 25-40% of bore area at that point
- Tone holes get proportionally smaller higher up (stronger in soprano, weaker in baritone)
- Closed holes (#3, #5, #11) have built-in cross-fingering corrections (next higher hole is relatively larger)
- Hole #18 (C#) is intentionally small due to intonation problems
- 10% tone hole diameter reduction ≈ 10 cents flattening

**Bore profile notes:**
- Altos: fairly straight cones, sometimes including bottom bow; bottom bows can show S-shaped twist
- Necks: have curved profile making a step downward relative to main conicity
- Recent tendency: wider necks = brighter but sharper in upper 2nd register
- Bells: preceded by piece of tubing with wider conicity than main cone
- Truncated volume (mouthpiece replacement): ~16cc (modern) vs ~20cc (vintage)

---

### Alto Saxophone — Yamaha YAS-480 (Eveno/Scavone Study)
**Source:** Eveno et al., ISMA 2014 — pad resonator study

Used as identical reference instruments (4 consecutive serial numbers).
Standard production dimensions — used for perceptual studies.

---

### Tenor Saxophone — CT Scanned Jupiter JTS-789
**Source:** DAGA 2021 — Wooden Saxophone Redesign

| Parameter | Value | Notes |
|---|---|---|
| Metal wall thickness | 0.7 mm | Standard metal sax |
| Wooden wall thickness (min) | 6 mm | For durability |
| Tone hole ratio δ (b/r) | 0.54 (±0.08) | Normal metal sax |
| Wooden sax tone hole ratio | 0.75 (±0.13) | After compensation |
| Chimney height increase | 6 mm | Wood wall vs metal |
| Diameter compensation | 20-50% increase | For 6mm chimney increase |
| Reed correction volume | 6 ml | Added to transmission line |

**Key findings:**
- Tone hole positions should be shifted toward mouthpiece for wooden design
- Original main bore must be slightly shortened (prolonged chimneys lower pitch)
- Iterative note-by-note process starting from lowest hole (B3) to highest (C#5)

---

### Soprano Saxophone — Szwarcberg Reference Model (2025)
**Source:** Szwarcberg, geometric sensitivity analysis

| Parameter | Value | Notes |
|---|---|---|
| Input radius (R1) | 4.6 mm | Mouthpiece end |
| Half-angle (ϕ) | 1.74° | |
| Cylindrical mouthpiece length | Fixed to match missing cone volume | |

**Register Holes:**
| Hole | Radius (mm) | Chimney (mm) | Position L1 (mm) | Purpose |
|---|---|---|---|---|
| Upstream | 0.85 | 4.0 | 40 | A4-F#5 range |
| Downstream | 1.4 | 4.0 | 130 | Bb3-G#4 range |

**Sensitivity results:**
- Reducing downstream register hole radius by 0.1mm → lowers inharmonicity by ~3.4 cents (D4/D5)
- Increasing upstream chimney height by 1mm → reduces inharmonicity by ~4 cents (A4/A5)
- Largest inharmonicity at edges of 2nd register range

---

### Soprano Saxophone — Chen & Smith (2009)
**Source:** Australian Acoustical Society

| Parameter | Value | Notes |
|---|---|---|
| Total length | 710 mm | Including mouthpiece |
| Half-angle | 1.74° | |
| Mouthpiece volume | 2.25 cm³ | |
| Mouthpiece internal length (Lm) | 44 mm | |
| Missing cone volume | 3.35 cm³ | |
| Register hole diameter | 2 mm | |
| Register hole depth | 6 mm | |
| Tone hole cutoff frequency | 1340 ± 240 Hz | |

---

### Tenor Saxophone — Chen & Smith (2009)
**Source:** Australian Acoustical Society

| Parameter | Value | Notes |
|---|---|---|
| Total length | 1490 mm | Including mouthpiece |
| Half-angle | 1.52° | |
| Tone hole cutoff frequency | 760 ± 250 Hz | |

---

### Alto Saxophone — Selmer Mark VI (SN 64XXX) Tone Hole Rim Diameters
**Source:** Sax on the Web forum — measured with micrometer (±0.15 mm)

**Note:** These are rim diameters (for fitting pads/resonators), not bore diameters.

| Hole | Function | Rim Diameter (mm) |
|---|---|---|
| Low Bb | Bottom key | 38.0 |
| Low B | | 38.0 |
| Low C# | | 34.35 |
| Low C | | 33.0 |
| Low Eb | | 33.0 |
| D (lower stack) | | 36.5 |
| E (lower stack) | | 29.5 |
| F (lower stack) | | 27.5 |
| F# (lower stack) | | 23.0 |
| Alt F# | | 23.5 |
| G# | | 25.5 |
| G (upper stack) | | 23.5 |
| A (upper stack) | | 19.75 |
| Bis Bb | | 15.0 |
| B (upper stack) | | 19.25 |
| C (upper stack) | | 10.25 |
| Side key Bb | | 19.5 |
| Side key C | | 19.5 |
| Palm D | | 13.5 |
| Palm Eb | | 13.5 |
| Side key high E | | 13.5 |
| Palm F | | 13.5 |

**Mark VI Pad Sizes (key cups):**
| Key | Pad Size (mm) | Spring |
|---|---|---|
| Low Bb | 44.5 | .037 × 38.5 |
| Low B | 44.5 | .037 × 38.5 |
| Low C# | 40.5 | .043 × 45.75 |
| Low C | 40.5 | .037 × 36.75 |
| Low Eb | 40.5 | .040 × 48.5 |
| D (lower) | 42.5 | .040 × 38.25 |
| E (lower) | 36.5 | .040 × 38.25 |
| F (lower) | 34.5 | .040 × 30.5 |
| F# (lower) | 30.5 | .040 × 39.5 |
| G# | 30.5 | .030 × 38.5 |
| G (upper) | 30.5 | .040 × 29.75 |
| A (upper) | 26.5 | .037 × 34.5 |
| Bis Bb | 24.5 | .030 × 31 |
| B (upper) | 26.5 | .032 × 35.25 |
| C (upper) | 14.5 | .030 × 38.5 |
| Palm D/Eb/F/F# | 18.5 | various |
| Side key Bb/C/E | 24.5/24.5/18.5 | various |
| Octave key | 9.5 | .032 × 34 |

---

### Alto Saxophone — Cults3D 3D-Printable Reference
**Source:** Cults3D — simplified playable design

| Parameter | Value | Notes |
|---|---|---|
| Key | Bb (one step below alto Eb) | Simplified |
| Mouthpiece end OD | 24.2 mm | Fits standard alto mouthpiece |
| Bell end ID | 40 mm | |
| Total length | 450 mm | Including mouthpiece neck |
| Taper | 1:25 | 1mm diameter per 25mm length |
| Wall thickness | 2 mm | |

**Tone Hole Positions (from mouthpiece end):**
| Hole | Position (cm) | Diameter (mm) | Notes |
|---|---|---|---|
| 6 (highest) | 8-11 | 6-8 | Upper holes |
| 5 | 12-15 | 6-8 | |
| 4 | 16-19 | 6-8 | |
| 3 | 20-23 | 7-9 | Lower holes |
| 2 | 24-27 | 7-9 | |
| 1 (lowest) | 28-32 | 7-9 | |

---

### Postma Tone Hole Rules of Thumb
**Source:** sax.mpostma.nl

- Tone hole diameter: 25-40% of bore area at that location
- 10% diameter reduction ≈ 10 cents flattening
- Formula for 10% smaller hole: sqrt(d² × 0.9) where d = original diameter
- Closed tone holes capture air and flatten pitch (more effect closer to mouthpiece)
- Open tone holes allow fundamental + first overtone at full voice

---

## CLARINET FAMILY

### Buffet R13 — Polycylindrical Bore (Multiple Measurements)
**Source:** ClarinetPerfection.com, woodwind.org forum, various technicians

**Bore dimensions:**
| Part | Diameter (mm) | Notes |
|---|---|---|
| Upper joint entry (top) | 14.78-15.09 | Varies by serial number/era |
| Upper joint exit (bottom) | 14.53-14.68 | Polycylindrical = stepped |
| Lower joint entry | 14.64-14.84 | |
| Lower joint exit | 14.61-14.66 | |

**Specific serial number measurements:**
| Serial # | Year | Top (mm) | Bottom (mm) | Notes |
|---|---|---|---|---|
| 30,056 | 1946 | 14.9 | 14.8 | Pre-R13 |
| 51,660 | 1955 | 14.84 | 14.64 | Early R13 |
| 55,156 | 1955 | 14.80 | 14.66 | Early R13 |
| 242,913 | 1983 | 14.8 | 14.7 | Standard R13 |

**Register key:**
| Parameter | Pro Model (42xxx) | Academy (42xxx) | Academy (38xxx) |
|---|---|---|---|
| Distance from top | 18.75 mm | 19.5 mm | 19.75 mm |
| Diameter | 2.55 mm | 2.75 mm | 2.75 mm |

---

### Buffet R13 — Tone Hole Diameters (Pro vs Academy)
**Source:** ClarinetPerfection.com

| Hole | Pro (42xxx) (mm) | Academy (42xxx) (mm) | Notes |
|---|---|---|---|
| 1st trill | 4.69 | 4.42 | Upper joint |
| 2nd trill | 5.48 | 4.76 | |
| 3rd trill | 4.55 | 4.64 | |
| 4th trill (Bb) | 5.90 | 5.26 | |
| Throat A | 5.08 | 4.46 | |
| Throat Ab | 5.05 | 4.55 | |
| F | 4.00 | 4.10 | |
| Top ring | 4.60 | 4.86 | |
| 2nd ring | 6.70 | 6.85 | |
| C/G | 6.95 | 7.10 | |
| Sliver Bb | 5.40 | 5.45 | |
| C#/G# | 4.74 | 4.80 | |

**Key finding:** "All the toneholes are smaller on the Academy." Academy has larger bore to compensate.

---

### Buffet R13 vs BC-20 — Tone Hole Positions
**Source:** ClarinetPerfection.com

| Hole | R13 Position (mm from top) | R13 Dia (mm) | BC-20 Position (mm) | BC-20 Dia (mm) |
|---|---|---|---|---|
| **Upper Joint** | | | | |
| Top ring | 5.20 | 5.65 | 4.98 | 5.30 |
| 2nd ring | 6.60 | 6.85 | 6.57 | 6.84 |
| C/G | 7.55 | 7.75 | 7.68 | 8.08 |
| **Lower Joint** | | | | |
| Top ring | 7.90 | 8.25 | 8.09 | 8.38 |
| 2nd ring | 7.35 | 7.61 | 7.75 | 8.00 |
| Lower ring | 8.85 | 9.15 | 9.40 | 9.60 |

**Note:** These appear to be cm not mm for positions — need verification.

---

### Buffet Clarinet — Comprehensive Bore Database
**Source:** ClarinetPerfection.com

| Model | Bore (mm) | Type |
|---|---|---|
| Prestige RC | 14.64 | Polycylindrical |
| E12 | 14.65 | Polycylindrical |
| Prestige R13 | 14.64 | Polycylindrical |
| R13 | 14.64 | Polycylindrical (.574") |
| R13 (1974 measured) | 15.09 top / 14.68 bottom | Polycylindrical |
| R13 (1994 measured) | 15.01 top / 14.76 bottom | Polycylindrical |
| E-11 (2757xx) | 15.05 top / 14.68 bottom | |
| Recital (442) | 14.30 | |
| Signature (442) | 14.60 | |
| Festival | 14.64 | Polycylindrical |
| Opus II | 14.61 | |
| DGDG (Daniel Gautier) | 14.62 | More RC-like upper bore |

---

### Other Clarinet Bores
**Source:** ClarinetPerfection.com

| Make/Model | Bore (mm) | Notes |
|---|---|---|
| Leblanc L-27 Symphonic | 14.75 / 14.80 cyl | |
| Leblanc L-300 | 14.60 | |
| Leblanc Dynamic H | 15.0 cyl | Cylindrical |
| Selmer USA Signet | 14.55 | |
| Noblet 45 | 14.85 | |
| Centered Tone | 15.0 | Selmer documentation |
| Buescher True Tone | 15.5 | |
| Peter Eaton International | 14.9 | |
| Peter Eaton Elite | 15.27-15.35 | |
| Couesnon Monopole | 14.68 cyl | Cylindrical |

---

### Noreland "Logical Clarinet" — Optimized Design (2013)
**Source:** Acta Acustica / arXiv

**Design principles:**
- All tone hole positions, diameters, and chimney lengths vary regularly
- Gradually larger tone holes toward bell (away from reed)
- With dedicated register hole: <10 cents throughout whole range
- Built and tested with artificial blowing machine — good agreement with predictions

---

## FLUTE FAMILY

### Boehm Flute — Powell Modern Scale
**Source:** Powell Flutes / Cooper Scale

**Standard modern flute dimensions:**
| Parameter | Value | Notes |
|---|---|---|
| Bore diameter | 19.05 mm (0.750") | Cylindrical |
| Headjoint taper | parabolic | From embouchure to cork |
| Sounding length (C foot) | ~600 mm | Center of embouchure to end of foot |
| Sounding length (B foot) | ~635 mm | |

---

### Modern Flute — Design XVI (Lasewski/Murray)
**Source:** Murray Flute, Design XVI specification

| Parameter | Value | Notes |
|---|---|---|
| Embouchure | 11.7 × 10.2 mm | |
| Chimney depth | 4.7 mm (+) | |
| Cork position | 17.5 mm | From embouchure center |
| Tube ID | 0.7485" (19.012 mm) | |
| Wall thickness | 0.014" (0.356 mm) | |

**Tone hole positions and diameters:**
| Vent # | Note | Position from embouchure (cm) | Vent Dia (cm) |
|---|---|---|---|
| 1 | T2 (D#) | 21.20 | 0.95 |
| 2 | T1 (D) | 23.70 | 1.35 |
| 3 | C# (2) | 24.45 | 0.56 |
| 4 | C# (1) | 26.25 | 0.95 |
| 5 | C | 27.33 | 1.35 |
| 6 | B | 29.25 | 1.35 |
| 7 | A# | 31.32 | 1.35 |
| 8 | A | 33.50 | 1.35 |
| 9 | G# | 35.70 | 1.35 |
| 10 | G | 38.13 | 1.44 |
| 11 | F# | 40.75 | 1.44 |
| 12 | F | 43.53 | 1.44 |
| 13 | E | 46.53 | 1.44 |
| 14 | D# | 49.65 | 1.44 |
| 15 | D | 53.00 | 1.58 |
| 16 | C# | 56.30 | 1.58 |
| 17 | C | 59.60 | 1.58 |

**Head Taper Design XIII:**
| Length from embouchure (cm) | Diameter (mm) |
|---|---|
| 0 | 16.50 |
| 2 | 16.50 |
| 2.25 | 16.70 |
| 2.5 | 17.05 |
| 2.75 | 17.50 |
| 3 | 17.90 |
| 3.25 | 18.15 |
| 3.5 | 18.30 |
| 4 | 18.45 |
| 4.5 | 18.55 |
| 5 | 18.65 |
| 5.5 | 18.70 |
| 7.5 | 18.80 |
| 11 | 19.01 |
| 12+ | 19.01 (cylindrical) |

---

### Baroque/Traverso Flute — Beaudin Workshop Measurements
**Source:** flutebeaudin.com — measured from original instruments

**Best bore diameter for each pitch:**
| Pitch (Hz) | Bore Diameter (mm) |
|---|---|
| 385 | 20.4 |
| 390 | 20.2 |
| 395 | 20.0 |
| 400 | 19.8 |
| 405 | 19.6 |
| 410 | 19.4 |
| 415 | 19.2 |
| 420 | 19.0 |

**Measured baroque flutes:**
| # | Maker | Bore (mm) | Pitch (Hz) | Material | Collection |
|---|---|---|---|---|---|
| 5 | G.A. Rottenburgh | 19.2 | 415 | Boxwood | Bart Kuijken |
| 6 | Lecler | 19.2 | 415 | Ivory | Brussels Museum |
| 12 | A. Grenser | 18.75 | 415 | Boxwood | Den Haag Museum |
| 26 | Anonymous | 19.8 | | Ebony | Berlin Museum |
| 104 | Stanesby Jr. | 19.6 | 410 | Ivory | Miller Collection |
| 109 | Beaulieu | 20.0 | | Ebony | Collection M. Arita |

---

### Modern Flute Headjoint Dimensions
**Source:** goferjoe.com — measured from collection

| Headjoint | OD (in) | Wall (in) | Sounding Length (mm) | Notes |
|---|---|---|---|---|
| Haynes 18530 ('47 Laurent) | .768 | .010/.011 | 596 | ss |
| Haynes 23950 ('54 14k) | .771 | .0105/.009 | 635b | sg |
| Haynes 28017 ('59) | .773 | .013/.013 | 598 | ss |
| Powell 1775 ('57) | .775 | .0125/.012 | 635b | ss |
| Powell 2577 ('65) | .775 | .014/.013 | 636b | ss |
| Muramatsu 29529 ('82) | .778 | .015/.014 | 595 | ss |
| Muramatsu 27126 ('81) | .778 | .0145/.015 | 594 | ss |

**Powell headjoint 2788 (platinum):**
- Embouchure: 10.37 × 12.14 mm × 4.85 mm depth
- Silver Haynes embouchure plate
- Wall: 0.014"

---

## OBOE FAMILY

### Oboe — Three Historical Instruments Compared
**Source:** Busch dissertation (1972) — 1807, 1916, 1968 oboes

**General measurements:** Detailed comparison of bore dimensions, tone hole positions, diameters, key mechanism measurements. The 1807 oboe has consistently wider bore than the other two.

**Tone hole measurement method:**
- Bore diameter at each tone hole obtained by measuring depth and diameter
- Wall thickness computed, then inner bore diameter calculated
- Distance from center of tone hole to upper end of each joint measured
- Measurements to closest 0.1 mm

---

### Baroque Oboe — Piguet Collection Measurements
**Source:** hoboy.net — nine oboes measured with fixed gauges

**Measurement method:**
- Series of ~90 plexiglass gauges, filed to oval shape, accuracy ±0.01 mm
- Gauges screwed onto thin brass rod (3 × 265 mm)
- Joint held upside down, gauge passed in with light pressure
- Two readings per gauge: max depth and min depth (rotated 90°)
- Distances accurate to ±1.0 mm
- Tone hole lengths measured with depth gauges

**Each oboe described in three pages:**
1. Half outline with diameters (mm) on right, distances on left
2. Fingerholes and keys by retouched rubbings with lengthwise × crosswise diameters
3. Internal measurements with fixed gauges

---

### Baroque Oboe — Bouterse Analysis
**Source:** FoMRHI Comm. 2097

**Typical dimensions:**
| Parameter | Value | Notes |
|---|---|---|
| Narrowest bore | ~4-6 mm | At top |
| Bell rim diameter | 40+ mm | |
| Cone average | ~1:40 | Discounting bell |
| Virtual apex distance | ~145-252 mm | Above top end (depends on cone) |
| Total sounding length | ~572 mm | |

**Bore structure:**
- Very narrow at top (~6 mm), very wide at bell (40+ mm)
- Irregular cone / truncated cone
- Top section (smallest bore to hole 1): critical for D and E intervals
- Theoretical apex: 160-252 mm above top end (varies by maker)

---

## BASSOON FAMILY

### German System Bassoon — Heckel (Selected Group)
**Source:** Rochester study (65 instruments measured)

**Measurement method:**
- Diameter readings at ends of all segments (excluding bocal)
- At one-inch intervals within segments
- Visual representation vs hypothetical reference cone

**Key findings:**
- Six well-defined patterns of variation from reference cone found in select group
- Bore walls not uniformly smooth in most instruments
- U-tube fittings often mismatched to boot joint bore holes
- Out-of-roundness present but not harmful in itself
- Altered bassoons improved in tonal resonance, ease of response, and intonation

---

### Bassoon — Montreal University Database (PAFI)
**Source:** ISMA 2019, Houde-Turcotte

**Measurement bench:**
- Specialized bench with tool head moving along bore interior
- Two arms with rollers contacting bore walls
- Triangle piece converts diameter to transversal movement
- Digital indicator + digital caliper
- Data recorded every 0.7s
- Measurements on two axes (rotated 90°) for ovality detection

**Tone hole measurements:**
- Set of graduated mandrels for diameter
- Angle measured with protractor framework
- Undercutting documented by profile cross-sections

---

### Bassoon — Crook/Bocal Dimensions
**Source:** Curtit et al. (Vienna Talk 2019)

**Measurement accuracy:** 2% of diameter dimensions

**Crook fabrication measurements:**
| Stage | Avg Diameter Difference from Mandrel | Notes |
|---|---|---|
| Straight (0.5mm sheet) | 0.076 mm (1.1%) | |
| Straight (0.6mm sheet) | 0.068 mm (1.1%) | |
| After bending (0.5mm) | +0.08 mm | Bending effect |
| After bending (0.6mm) | +0.1 mm | Bending effect |
| Variable thickness sheet | 0.32 mm (4.6%) | Different sound perceived |

---

### Bassoon — Anon19-O-Peebles Historical Measurements
**Source:** David Rachor archive

**Wing joint:**
| Feature | Position from top (mm) | Diameter (mm) |
|---|---|---|
| F tone hole | 214 [231] | 5.5 × 5.6 |
| E tone hole | 305 [300] | 8.1 × 6.9 |
| D tone hole | 410 [390] | 8.3 × ~6.5 |

**Boot joint (down bore):**
| Feature | Position from socket (mm) | Diameter (mm) |
|---|---|---|
| C tone hole | 105 | 6.2 × 7.1 |
| B natural | 145 | 8.1 |
| Bb (closed) | 183 | 4.7 |
| Vent (Bb only) | 282 [283] | 10.8 × 11.6 |
| A tone hole | 311 [310] | 8.2 × 8.0 |

**Boot joint (up bore):**
| Feature | Position from socket (mm) | Diameter (mm) |
|---|---|---|
| G tone hole | 335 [333] | 9.5 × 10.0 |
| F tone hole | 170 | 10.5 × 9.5 |

**Long joint:**
| Feature | Position from small tenon (mm) | Diameter (mm) |
|---|---|---|
| E (low D key) | 53 [55] | 13.7 × 13.8 |
| Eb (stands closed) | 116 | 8.7 |
| D (low C key) | 255 [258] | 11.5 × 11.8 |
| C# (stands closed) | 390 | 10.8 |
| C (low B key) | 478 [482] | 13.5 × 13.4 |

**Bocal:**
- Length over top: 34.3 cm
- Length bottom: 31.5 cm
- Bottom diameter: 8.5 mm
- Reed end: ~3.9 mm

---

## CROSS-INSTRUMENT RELATIONSHIPS

### Tongue/Hole Size Relationships (Postma)

| Feature | Sax | Clarinet | Flute |
|---|---|---|---|
| Tone hole/bore ratio | 25-40% | Varies widely | ~7-10% (open holes) |
| Chimney height (metal) | ~0.7 mm | N/A (drilled) | ~0.35 mm |
| Chimney height (wood) | ~6 mm | ~3-5 mm | N/A |
| Bore type | Conical | Cylindrical | Cylindrical |
| Register keys | 2 (octave) | 1 (12th) | 0 (overblows octave) |
| End condition | Open (bell) | Closed (reed) | Open (embouchure) |

### Intonation Tolerance by Instrument

| Quality Level | Saxophone | Clarinet |
|---|---|---|
| Professional (target) | ±5 cents | ±3-5 cents |
| Good | ±10 cents | ±5-10 cents |
| Acceptable | ±15 cents | ±10-15 cents |
| Problematic | >20 cents | >20 cents |

### Sensitivity Coefficients

| Parameter | Effect | Source |
|---|---|---|
| 10% tone hole diameter reduction | ~10 cents flat | Postma |
| 1mm chimney height increase | ~4 cents (register hole, soprano sax) | Szwarcberg 2025 |
| 0.1mm register hole radius decrease | ~3.4 cents improvement | Szwarcberg 2025 |
| 6mm chimney height increase (tenor) | 20-50% diameter compensation needed | DAGA 2021 |
| Pad without resonator | Lower impedance peaks by several dB | Eveno 2014 |
| Pad with metal vs plastic resonator | No perceptible difference to musicians | Eveno 2014 |

---

## REFERENCES

1. Lefebvre, A. (2010). "Computational Acoustic Methods for the Design of Woodwind Instruments." McGill PhD thesis.
2. Lefebvre, A. & Scavone, G. (2011). "On the bore shape of conical instruments." J. Canadian Acoustical Association.
3. Lefebvre, A. & Scavone, G. (2008). "Input Impedance Measurements of Conical Acoustic Systems." Forum Acusticum, Aalborg.
4. Lefebvre, A. & Scavone, G. (2012). "Characterization of woodwind instrument toneholes with FEM." JASA 131(4).
5. Szwarcberg (2025). "Geometric sensitivity of modal parameters in wind instrument models."
6. DAGA 2021. "Tone Hole Adjustment for a Wooden Saxophone Using an Open-Source 1D Waveguide."
7. Noreland, D. et al. (2013). "The logical clarinet: numerical optimization of the geometry of woodwind instruments." Acta Acustica.
8. Postma, M. sax.mpostma.nl — Bore profiles, Tone holes measurements (70+ instruments).
9. Chen, K. & Smith, J. (2009). "Saxophone Acoustics: Introducing a..." Australian Acoustical Society.
10. Eveno, P. et al. (2014). "A perceptual study on the effect of pad resonators on the saxophone." ISMA.
11. Busch, D. (1972). "A Technical Comparison of an 1807, a 1916, and a 1968 Oboe." Penn State.
12. Houde-Turcotte, V. (2019). "Generation and Analysis of a Database of Geometrical and Acoustic Properties of Bassoons." ISMA.
13. ClarinetPerfection.com — Bore measurements database.
14. Beaudin, J.F. flutebeaudin.com — Baroque flute technical drawings.
15. Murray Flute / Lasewski — Design XVI specifications.
16. Goferjoe.com — Headjoint diameter measurements.
