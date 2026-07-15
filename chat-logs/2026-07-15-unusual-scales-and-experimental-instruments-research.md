# Research: 3D Printed Wind Instruments with Unusual Scales & Experimental Wind Instruments
**Date:** 2026-07-15
**Researcher:** opencode (big-pickle)

---

## PART 1: 3D PRINTED WIND INSTRUMENTS WITH UNUSUAL SCALES

### 1. Why Unusual Scales Matter

Western 12-tone equal temperament (12-TET) is just one of thousands of tuning systems used worldwide. 3D printing is uniquely suited to creating instruments with unusual scales because:

- **No fret constraints**: bore length, tone hole positions, and finger hole spacing can be placed exactly for any tuning
- **Parametric design**: a single parameter change (e.g., switching from 12-TET to 19-TET) produces a completely new instrument
- **Interchangeable parts**: mouthpieces, headjoints, and body segments can be swapped for different tunings
- **Rapid iteration**: print a test version, measure with a tuner, adjust parameters, reprint

### 2. Non-Western Tuning Systems (by Region)

#### A. Middle East & North Africa — Maqam System

**What it is:** Maqam (Arabic), Makam (Turkish), Mugham (Azerbaijani) — modal systems using quarter tones (24-TET), microtonal intervals, and specific melodic progressions.

**Key intervals:** quarter tones (≈50 cents), three-quarter tones (≈150 cents), neutral seconds (≈150 cents), augmented seconds

**Instruments to 3D print:**
- **Ney** (end-blown flute): 5-6 finger holes, open tube. Bore diameter ~1.8-2.5cm, length ~50-60cm for D. Quarter-tone fingering via half-holing.
- **Arghul** (double-pipe double-reed): two parallel tubes, one melody + one drone. Bore ~8mm, length ~30-40cm.
- **Mijwiz** (double-pipe double-reed): similar to arghul, slightly larger bore.
- **Zurna** (double-reed): conical bore, ~30cm, very loud. Pairs with davul drum.

**Design considerations:**
- Quarter tones require precise hole placement (±0.5mm tolerance)
- Half-holing technique means holes should be slightly larger than on Western flutes (6-8mm vs 5-6mm)
- Conical bore instruments (zurna, mizmar) need Build123d `Cone` operations

**3D printing challenges:**
- Double-pipe instruments need perfect alignment between parallel bores
- Reed instruments need separate reed (can be 3D printed from thin PETG)
- Membrane holes (like dizi) require precise drilling post-print

#### B. East Asia — Chinese, Japanese, Korean Systems

**Chinese traditional:**
- **Xiao** (箫): end-blown vertical flute, 8 holes. Bore ~2-2.5cm, length ~70-80cm for key of D/G. Closed mouthpiece with small aperture.
  - Design: bei xiao (narrower bore, capped mouthpiece) vs tang xiao (wider bore, open end)
  - Tuning: traditional Chinese system maps differently from Western (F/G markings = tonic note, not lowest note)
  - 3D printable: yes — MakerWorld has "Chinese Musical Instrument - Dongxiao Flute" by Davinci
  - Key design challenge: the tuning hole matrix in the lower section that affects harmonics

- **Dizi** (笛): transverse bamboo flute with buzzing membrane (dimo). 6 finger holes + 1 thumb hole.
  - The dimo membrane is the key feature — creates a bright, buzzy tone
  - 3D print approach: print the body, use real dimo membrane (onion skin paper) or thin PLA film
  - Hole placement follows pentatonic or heptatonic scales depending on region

- **Hulusi** (葫芦丝): gourd flute with free reed. Multiple pipes, drone + melody.
  - Complex instrument — gourd body, bamboo pipes, free reed mechanism
  - 3D print approach: print gourd body, use separate reed mechanism

**Japanese traditional:**
- **Shakuhachi** (尺八): end-blown bamboo flute, 5 finger holes (1 thumb + 4 front).
  - Modern (fuke) shakuhachi: 54.54cm length, standard model
  - Tuning: roughly pentatonic (D minor pentatonic for standard) but with microtonal inflections
  - 3D printed: well-established — plastic shakuhachi ("shakuhachi yuu") already commercial
  - Academic research: Simian (2023) 3D printed shakuhachi replicas from CT scans
  - Design: sharp utaguchi (blow edge), internal bore treatment critical for tone
  - Weight issue: plastic versions much heavier than bamboo (hollow bamboo structure vs solid plastic)

- **Shinobue** (篠笛): transverse bamboo flute, used in festival music (matsuri).
  - Tuning varies by region — each region has its own pitch standard
  - Usually 6 finger holes, simple cylindrical bore

**Korean traditional:**
- **Daegeum** (대금): large transverse bamboo flute with buzzing membrane (cheong).
  - Similar to Chinese dizi but larger, deeper tone
  - The membrane creates a characteristic buzzing timbre
  - 3D print approach: print body, add membrane slot for real membrane

#### C. South Asia — Indian Raga System

**What it is:** Raga system — melodic frameworks with specific ascending/descending patterns, gamakas (ornaments), and microtonal inflections (shrutis). 22 shrutis per octave.

**Instruments to 3D print:**
- **Bansuri** (bamboo flute): 6-7 finger holes, open bore. Key of C (length ~60cm), Key of G (shorter).
  - Tuning: typically tuned to specific ragas, not chromatic scale
  - 3D print: 12 models on Cults3D, multiple on Thingiverse
  - Design: cylindrical bore, finger holes placed for raga-specific intervals
  - Key challenge: gamakas (slides between notes) require half-holing technique

- **Shehnai** (double-reed): conical bore, metal bell. North Indian equivalent of zurna.
  - Very complex — needs precise reed mechanism
  - 3D print: possible for body, reed still needs traditional materials

- **Pungi** (snake charmer instrument): continuous drone + melody, gourd body + double reed.
  - Historically interesting but ethically complex (snake charming context)
  - 3D print: feasible as a curiosity

#### D. Southeast Asia — Gamelan Tunings

**What it is:** Gamelan orchestras (Indonesia, Java, Bali) use tuning systems that don't match Western pitch standards:
- **Slendro**: 5-note scale, roughly equidistant intervals (~240 cents each)
- **Pelog**: 7-note scale with unequal intervals (mix of ~150 and ~250 cent steps)

**Instruments to 3D print:**
- **Suling** (bamboo end-blown flute): 4-6 finger holes, tuned to slendro or pelog
  - Simple design — cylindrical bore, small instrument (20-30cm)
  - 3D print approach: parameterize hole positions for slendro/pelog tuning

- **Serunai** (double-reed): Indonesian zurna equivalent

#### E. Africa — Mbira/Marimba Tunings

**What it is:** African tuning systems are diverse and don't conform to any single standard:
- Mbira dzavadzimu (Zimbabwe): heptatonic scales, often "stretched" beyond a Western octave
- Most common tuning: Nyamaropa (similar to Western Mixolydian mode)
- Tunings vary by family/region — no single "African tuning"

**Instruments to 3D print:**
- **Mbira/Kalimba**: 3D printed tines on wooden/plastic board
  - Thingiverse: "Tunable chromatic mbira/kalimba" by muradyan_75
  - Design: 17-22 metal tines (can be steel or printed PLA), tuning screws
  - Each tine can be tuned independently — any scale is possible
  - MakerWorld: "Tunable 17-key Kalimba" (C3-E5 range)

- **Nyunga Nyunga**: smaller mbira, 7-8 tines

#### F. Americas — Pre-Columbian & Indigenous

**Native American Flute:**
- Tuning: typically minor pentatonic (A=C# for key of A)
- Two-chamber design: slow air chamber + sound chamber
- 3D print: multiple models — "Native American Drone Flute (F#, A=432Hz)" on Printables
- Design: bird block (fetish) on top, 5-6 finger holes
- Brown University research: 3D printing replicas of 19th-century Kiowa courting flute (ethical considerations documented)

**Quena** (Andean):
- End-blown flute, notched lip plate, 6 finger holes + thumb hole
- Tuning: roughly pentatonic but with microtonal inflections
- 3D print: possible, straightforward cylindrical bore

### 3. Microtonal & Experimental Scale Designs

#### A. Quarter-Tone Flutes (24-TET)
- University of Wollongong research (2016): 3D printed microtonal flutes
- Approach: calculate finger hole positions for each quarter-tone step
- Target accuracy: <5 cents deviation
- Both recorder and transverse flute head designs tested
- Interchangeable mouthpieces for different tunings
- Key finding: mathematical models give ~30 cents accuracy, iterative printing/testing achieves <5 cents

#### B. Bohlen-Pierce Scale
- 13-tone macrotonal scale, replaces octave with tritave (3:1 ratio)
- Designed for odd-number harmonics (3:5:7:9 tetrad)
- Existing instruments: BP clarinets, BP guitars, BP kalimba
- 3D print approach: ideal candidate — unusual bore lengths not possible with standard instruments
- Bore length calculations: use tritave ratio instead of octave ratio

#### C. Harry Partch's 43-Tone Scale
- Just intonation scale based on ratios of 11 or smaller
- 43 tones per octave, each with unique character
- Existing instruments: Cloud Chamber Bowls, Quadrangularis Reversum, Zymo-Xylo
- 3D print approach: Cloud Chamber Bowls are ideal — tuned resonant vessels

#### D. 19-TET and 31-TET
- 19 equal divisions of the octave: closer to meantone than 12-TET
- 31 equal divisions: excellent approximation of meantone, very smooth
- Instruments: 19-TET flutes, 31-TET organs
- 3D print: recalculate all hole positions for new step size

#### E. Just Intonation Flutes
- Flutes tuned to pure harmonic ratios (2:3:4:5:6)
- Each key/position is a different ratio
- 3D print approach: calculate exact bore length for each ratio
- Challenge: changing key requires completely different hole positions

### 4. Design Workflow for Unusual-Scale Wind Instruments

#### Step 1: Choose Your Scale
```
For 24-TET quarter-tones:
  frequency = base_freq * 2^(n/24)  where n = 0,1,2,...,23

For Bohlen-Pierce:
  frequency = base_freq * 3^(n/13)  where n = 0,1,2,...,12

For Just Intonation:
  frequency = base_freq * ratio[n]
  e.g., [1/1, 16/15, 9/8, 6/5, 5/4, 4/3, 45/32, 3/2, ...]

For Slendro:
  frequency = base_freq * 2^(n*0.4)  roughly 5 equidistant notes in an octave
```

#### Step 2: Calculate Bore Length
```
For open tube (flute, bansuri):
  L = v / (2 * f)
  where v = speed of sound (~343 m/s at 20°C), f = frequency

For closed tube (recorder, whistle):
  L = v / (4 * f)

For half-closed (shakuhachi):
  L = v / (4 * f) * correction_factor
```

#### Step 3: Calculate Hole Positions
```
For each note n:
  effective_length = v / (2 * f_n)  or v / (4 * f_n)
  hole_position = total_length - effective_length

Correction factors needed for:
  - End correction (≈0.6 * radius for open holes)
  - Wall thickness effects
  - Embouchure offset
  - Adjacent hole interaction
```

#### Step 4: Build 3D Model
```
Using Build123d or OpenSCAD:
1. Create outer tube (Cylinder with wall_thickness)
2. Create inner bore (Cylinder for cylindrical, Cone for conical)
3. Subtract inner from outer
4. Add tone holes at calculated positions (Cylinder + CSG subtract)
5. Add embouchure/mouthpiece
6. Export STL
```

#### Step 5: Verify & Iterate
```
1. Print at 0.2mm layer height
2. Measure with electronic tuner (phone app works)
3. Compare measured frequencies to target
4. Adjust hole positions based on deviation
5. Reprint and re-measure
Target: ±5 cents accuracy for all notes
```

---

## PART 2: NEW AND EXPERIMENTAL WIND INSTRUMENTS

### 1. Guthman Musical Instrument Competition (2024-2026)

The premier competition for new musical instruments, held annually at Georgia Tech. Called "The Pulitzer of the New Instrument World" by The Guardian.

#### 2024 Finalists & Winners

| Instrument | Creator | Country | Description | Placement |
|-----------|---------|---------|-------------|-----------|
| **VocalCords** | Max Addae | USA | Rubber cords that modify vocals in real time through physical touch | 1st Place |
| **Babel Table** | Jean-François Laporte | Canada | Latex membranes + compressed air → voice-like sounds (percussive to birdsong) | 2nd Place |
| **Thales** | Nicola Privato | Italy | Electromagnetic sensors for continuous pitch control | Finalist |
| **X.E.K.I.** | Zhang, Chen, Kofinakos | USA | Motion-responsive keyboard for physical expression | Finalist |
| **YUAN** | Chi Wang | USA | Data-driven controller: capacitive touch + brightness + motion | Finalist |
| **Sonògraf** | — | — | Audiovisual instrument: drawing/collage → sound via camera | Finalist |

#### 2025 Finalists & Winners

| Instrument | Creator | Country | Description | Placement |
|-----------|---------|---------|-------------|-----------|
| **Chromaplane** | Passepartout Duo & KOMA Elektronik | Italy/Germany | Electromagnetic field instrument, isomorphic layout, fully analog | 1st Place |
| **Mulatar** | Lockruf Music | UK/Germany | Slide guitar + harp + percussion hybrid, moving bridges | 2nd Place + People's Choice |
| **Dinosaur Choir: Adult Corythosaurus** | Courtney Brown & Cezary Gajewski | USA | CT-scanned dinosaur skull + physically-based modeling synthesis | 3rd Place |
| **3 Axis MIDI Guitar** | Andrew Reid | USA | XY pad + pressure-sensitive trackpad + effect control | Judges' Special Award |
| **Udderbot** | Jacob Barton | USA | Novel wind instrument | Judges' Commendation |
| **ModμMIDI** | Emily Koh et al. | Singapore/Georgia | Microtonal MIDI controller | Judges' Commendation |
| **Hacked Double Trumpet** | Nicolas Bras | France | Modified trumpet with additional valves/bores | Finalist |
| **Dinosaur Choir (various)** | — | — | Various extinct creature reconstructions | Finalist |

#### 2026 Finalists

- Competition held March 13-14, 2026
- 10 finalists from around the world
- Judges: Gérard Assayag, Kerry Hagan, Vivek Maddala

### 2. Specific Experimental Wind Instruments

#### A. Hydraulophone
- **Inventor:** Steve Mann (1985, patented 2011)
- **How it works:** Water jets → player blocks jets with fingers → pressure changes → sound
- **Sound:** Rich, fluid, gurgling. Calming and expressive.
- **Classification:** New category — liquid-state acoustic instrument
- **Variants:**
  - Reed-based (moving parts)
  - Reedless/fipple (no moving parts, simpler maintenance)
  - Electric (hydrophone amplification + MIDI)
  - Water-in-air, air-in-water, water-in-water
- **Range:** 12-88 jets, fully polyphonic
- **Applications:** Music therapy, public art, science centers, interactive installations
- **Notable installations:** Ontario Science Centre (world's largest), Legoland California, Copenhagen Experimentarium
- **Between Music:** commissioned custom hydraulophone for Aquasonic underwater concert series
- **3D print potential:** HIGH — jet plates, manifold systems, resonant chambers all printable

#### B. Dinosaur Choir
- **Creator:** Courtney Brown (Georgia State) & Cezary Gajewski (Smithsonian)
- **How it works:** CT scans of dinosaur fossils → 3D-printed skull reconstructions → physical modeling synthesis → musician blows into mouthpiece → computational voice box → sound resonates through printed skull
- **2025 Guthman:** 3rd place with Adult Corythosaurus
- **Significance:** Bridges paleontology, 3D printing, and music
- **3D print potential:** The skull IS 3D printed — the instrument is the print itself

#### C. Circle Guitar
- **Creator:** Anthony Dickens (UK)
- **How it works:** Programmable wheel strums strings, player presses lightly to control
- **Bypasses:** manual strumming limitations
- **Creates:** new kinds of guitar music impossible with traditional technique

#### D. Harpejji
- **Inventor:** Tim Meeks (2007)
- **How it works:** Strings laid flat on board, played by tapping (like keyboard layout but vertical)
- **Sound:** Blends piano versatility with guitar feel
- **Significance:** Intuitive for both pianists and guitarists

#### E. Glissonic Glissotar
- **What it is:** Wind instrument using glissando as primary technique
- **Sound:** Smooth, unbroken glide from one pitch to another
- **Significance:** Challenges traditional note-by-note wind playing
- **3D printed versions:** Yes — Glissonic sells 3D printed bio-composite versions

#### F. Venova
- **Inventor:** Yamaha (2017)
- **How it works:** Recorder-like fingering + saxophone-like sound
- **Material:** High-quality resin
- **Significance:** Portable, accessible, award-winning design
- **3D print potential:** moderate — resin printing would work

#### G. Eigenharp
- **What it is:** Electronic instrument with 120+ keys
- **Plays:** hundreds of sounds, loops, effects in real-time
- **Significance:** Bridges electronic and acoustic music boundaries

#### H. Ondes Martenot
- **Inventor:** Maurice Martenot (1928)
- **How it works:** Electronic instrument with keyboard + ring on wire
- **Sound:** Eerie, wavering tones
- **Usage:** Film scores (Lord of the Rings, Ghostbusters), classical compositions
- **Significance:** One of the earliest electronic instruments still in active use

#### I. Theremin
- **How it works:** Hand movements in air control pitch and volume (no touch)
- **Sound:** Eerie, wavering — synonymous with 1950s sci-fi
- **Significance:** First fully electronic instrument, played without physical contact

#### J. Glass Armonica (Crystallophone)
- **Inventor:** Benjamin Franklin (1761)
- **How it works:** Spinning glass bowls played with dampened fingers
- **Sound:** Ethereal, ghostly — "once thought to drive performers mad"
- **Modern variant:** Between Music commissioned underwater version by Andy Cavatorta

#### K. Sea Organ
- **Inventor:** Nikola Bašić (2005, Zadar Croatia)
- **How it works:** Ocean waves → tubes under marble steps → polyphonic music
- **Classification:** Architecture as instrument — played by wind and sea
- **Significance:** Permanent public installation, no player needed

#### L. Sharpsichord
- **Creator:** Henry Dagg
- **How it works:** Solar-powered pin-barrel harp, plays programmed sequences
- **Appearance:** Victorian contraption
- **Sound:** Metallic, chiming tones

### 3. Emerging Categories in Experimental Wind Instruments

#### A. Bio-Acoustic Instruments
- 3D printed animal skull resonators (Dinosaur Choir)
- Museum artifact replication for research and performance
- Ethical considerations: Brown University's Kiowa courting flute project documented cultural protocols

#### B. Fluid-State Instruments
- Hydraulophone family (water)
- Glass armonica (friction on glass)
- Waterphone (bowed metal rods in water chamber — horror film staple)

#### C. Electromagnetic Instruments
- Chromaplane (2025 Guthman winner)
- Thales sensors (2024 Guthman finalist)
-原理: electromagnetic induction → continuous pitch control

#### D. Motion-Responsive Instruments
- X.E.K.I. (body movement → digital sound)
- Circle Guitar (programmable strumming wheel)
- Harpejji (tapping interface)

#### E. AI-Assisted Instruments
- Sonògraf (drawing → sound via camera + AI)
- Instruments that learn from player behavior
- Real-time AI processing of acoustic input

### 4. Design Principles for Experimental Wind Instruments

#### A. Interface Innovation
1. **Remove traditional constraints**: don't require standard fingering
2. **Make the body an instrument**: wearable instruments, body-position-responsive
3. **New input modalities**: breath + gesture + light + proximity
4. **Accessibility first**: instruments for people with different abilities

#### B. Sound Production Innovation
1. **Non-traditional resonators**: animal skulls, 3D-printed shapes, water chambers
2. **Hybrid acoustic-electronic**: acoustic instrument + digital processing
3. **Physical modeling synthesis**: computational voice boxes driven by breath
4. **Electromagnetic excitation**: strings/rods excited by fields, not plucked/bowed

#### C. Manufacturing Innovation
1. **3D printing as design tool**: iterate quickly, test acoustics, refine
2. **CT scanning + replication**: scan historical instruments, study, modify, print
3. **Parametric design**: one file → infinite variations
4. **Multi-material printing**: different infill densities for different acoustic properties

---

## PART 3: HOW TO DESIGN THEM — PRACTICAL GUIDE

### 1. Software Stack for Unusual-Scale Instruments

| Tool | Use Case | Learning Curve |
|------|----------|---------------|
| **OpenSCAD** | Parametric bore + hole generation | Medium |
| **Build123d** (Python) | Complex CSG, STEP export | Medium-High |
| **JSCAD** (browser) | Quick parametric prototyping | Low-Medium |
| **Fusion 360** | Free for education, full CAD | High |
| **FreeCAD** | Open source, parametric | Medium |
| **OpenWInD** | Acoustic simulation | High |
| **MATLAB/Python** | Frequency analysis, tuning calculation | Medium |

### 2. Acoustic Calculation Methods

#### Method A: Simple Tube Theory (±30 cents accuracy)
```python
import math

# Speed of sound at 20°C
v = 343.0  # m/s

def open_tube_length(freq):
    """Calculate length for open tube (flute, bansuri)."""
    return v / (2 * freq)

def closed_tube_length(freq):
    """Calculate length for closed tube (recorder, whistle)."""
    return v / (4 * freq)

# For a scale (e.g., 12-TET)
base = 440.0  # A4
for n in range(12):
    freq = base * (2 ** (n / 12))
    length_m = open_tube_length(freq)
    length_mm = length_m * 1000
    print(f"Note {n}: {freq:.1f} Hz → tube length {length_mm:.1f} mm")
```

#### Method B: End-Corrected Formula (±10 cents accuracy)
```python
def corrected_length(freq, radius_mm):
    """Include end correction for more accurate results."""
    radius_m = radius_mm / 1000
    end_correction = 0.6 * radius_m  # for open end
    raw_length = v / (2 * freq)
    return raw_length - end_correction
```

#### Method C: Iterative Measurement (±2 cents accuracy)
```
1. Print instrument with Method A or B calculations
2. Measure each note with electronic tuner
3. Calculate deviation: cents_error = 1200 * log2(measured_freq / target_freq)
4. Adjust hole position: delta_position ≈ -cents_error * (tube_length / 1200)
5. Reprint and re-measure
6. Repeat until all notes within ±5 cents
```

### 3. Build123d Template for Microtonal Flute

```python
from build123d import *
import math

# Scale definition (example: 24-TET quarter-tones)
BASE_FREQ = 440.0  # A4
NUM_NOTES = 24
v = 343.0  # speed of sound m/s

def freq_from_step(n):
    return BASE_FREQ * (2 ** (n / NUM_NOTES))

def open_tube_length(freq):
    return v / (2 * freq)

# Parameters
WALL_THICKNESS = 2.0  # mm
BORE_RADIUS = 10.0    # mm
HOLE_RADIUS = 3.0     # mm
NUM_SEGMENTS = 64

# Calculate total tube length (longest note = lowest frequency)
min_freq = freq_from_step(0)
total_length_m = open_tube_length(min_freq) * 1000  # convert to mm

# Create outer tube
outer = Cylinder(
    radius=BORE_RADIUS + WALL_THICKNESS,
    height=total_length_m,
    align=(Align.CENTER, Align.CENTER, Align.MIN)
)

# Create inner bore
inner = Cylinder(
    radius=BORE_RADIUS,
    height=total_length_m + 1,
    align=(Align.CENTER, Align.CENTER, Align.MIN)
)

# Start with tube
instrument = outer - inner

# Add tone holes for each note
for n in range(1, NUM_NOTES):
    freq = freq_from_step(n)
    effective_length = open_tube_length(freq) * 1000  # mm
    hole_position = total_length_m - effective_length
    
    # Create hole
    hole = Cylinder(
        radius=HOLE_RADIUS,
        height=WALL_THICKNESS + 4,
        align=(Align.CENTER, Align.CENTER, Align.CENTER)
    ).moved(Location((0, 0, hole_position)))
    
    # Subtract hole from instrument
    instrument = instrument - hole

# Add embouchure hole
embouchure = Cylinder(
    radius=BORE_RADIUS * 0.6,
    height=WALL_THICKNESS + 2,
    align=(Align.CENTER, Align.CENTER, Align.CENTER)
).moved(Location((0, 0, total_length_m - 5)))

instrument = instrument - embouchure

# Export
export_stl(instrument, "microtonal_flute_24tet.stl")
```

### 4. Post-Processing for Acoustic Quality

1. **Bore smoothing**: sand inner surface with 220-grit → epoxy coating → fine sand
2. **Hole deburring**: remove any stringing/overhangs from hole edges
3. **Joint fitting**: 0.1mm tolerance, sand to fit, apply petroleum jelly for seal
4. **Leak testing**: plug one end, blow into other, listen for hisses
5. **Tuning verification**: electronic tuner, adjust by enlarging/repositioning holes

### 5. Open-Source 3D Printed Instruments with Unusual Scales

| Instrument | Scale/Tuning | Source | Notes |
|-----------|-------------|--------|-------|
| Microtonal Flute (UoW) | Subharmonic microtonal | NIME 2016 paper | Recorder + transverse, interchangeable mouths |
| Adjustable Microtonal Guitar | Custom fret spacing | Tolgahan Çoğulu (2014 Guthman winner) | Not wind, but principle applies |
| Bohlen-Pierce Clarinet | 13-TET BP scale | xen.wiki | Unusual tritave-based tuning |
| Shakuhachi (various) | Pentatonic + microtonal | Thingiverse, Printables | Well-established designs |
| Native American Flute | Minor pentatonic | Printables, MakerWorld | Multiple keys available |
| D5 Drone Flute | Hijaz tuning | MakerWorld | Middle Eastern scale |
| Chromatic Mbira | Any scale | Thingiverse | 17-key tunable |
| PVC Shakuhachi | Pentatonic | PVC flute projects | $1/30min build |

---

## PART 4: RECOMMENDATIONS FOR INSTRUMENT DESIGNER APP

### New Instruments to Add (from this research)

#### Unusual Scale Instruments
1. **Quarter-Tone Ney** — Middle Eastern end-blown flute with 24-TET fingering
2. **Slendro Suling** — Indonesian bamboo flute, 5-note equidistant scale
3. **Pelog Suling** — Indonesian bamboo flute, 7-note unequal scale
4. **Bohlen-Pierce Recorder** — 13-tone tritave-based recorder
5. **Harry Partch Cloud Chamber Bowl** — tuned resonant vessel, 43-tone scale
6. **Just Intonation Flute** — pure harmonic ratios, customizable
7. **Dizi (with membrane slot)** — Chinese transverse flute with buzzing dimo
8. **Xiao** — Chinese vertical end-blown flute, 8 holes
9. **Quena** — Andean end-blown flute, notched lip

#### Experimental Instruments
10. **Hydraulophone** — water-jet instrument (body only, needs pump system)
11. **Dinosaur Choir Resonator** — 3D-printed skull resonator for physical modeling
12. **Circle Guitar Resonance Chamber** — experimental acoustic body
13. **Sea Organ Module** — wave-driven resonant tube section

### Parametric Presets to Add

```javascript
const MICROTONAL_PRESETS = {
  "quarter-tone-flute": {
    name: "Quarter-Tone Flute (24-TET)",
    description: "24-note equal temperament flute",
    scale: "24-TET",
    notes_per_octave: 24,
    interval_cents: 50,
  },
  "bohlen-pierce-recorder": {
    name: "Bohlen-Pierce Recorder",
    description: "13-tone tritave-based recorder",
    scale: "BP-13",
    notes_per_octave: 13,
    interval_ratio: "3/1",
  },
  "slendro-suling": {
    name: "Slendro Suling",
    description: "5-note equidistant Indonesian flute",
    scale: "Slendro",
    notes_per_octave: 5,
    interval_cents: 240,
  },
  "pelog-suling": {
    name: "Pelog Suling",
    description: "7-note unequal Indonesian flute",
    scale: "Pelog",
    notes_per_octave: 7,
    intervals: [0, 120, 240, 370, 500, 620, 750], // cents from tonic
  },
  "maqam-quarter-tone": {
    name: "Maqam Quarter-Tone Flute",
    description: "Middle Eastern flute with quarter-tone intervals",
    scale: "Maqam",
    notes_per_octave: 24,
    intervals: "maqam_rast",
  },
  "xiao-c-major": {
    name: "Xiao (Chinese Vertical Flute)",
    description: "8-hole end-blown flute in C/F",
    scale: "Pentatonic + chromatic",
    notes: 8,
    key: "C/F",
  },
  "harry-partch-43": {
    name: "Partch Scale Instrument",
    description: "43-tone just intonation resonator",
    scale: "Partch-43",
    notes_per_octave: 43,
  },
};
```

---

## Sources

### Academic Papers
- Simian, R. (2023). "3D-Printed Musical Instruments: Lessons Learned from Five Case Studies." *Music & Science*, 6.
- Simian, R. (2025). "Tackling Complexity with Additive Manufacturing: Wind Musical Instruments as a Case Study." *Music & Science*.
- Dabin, M. et al. (2016). "3D Modelling and Printing of Microtonal Flutes." *NIME 2016*.
- Zoran, A. (2011). "The 3D Printed Flute: Digital Fabrication and Design of Musical Instruments."
- Loomis, J. (2025). "3D Printing Reproductions of Indigenous Instruments in Museum Collections." *Music & Science*.
- Loomis, J. (2025). "3D Printing Reproductions of Indigenous Instruments in Museum Collections." *Brown University*.

### Guthman Competition
- guthman.gatech.edu/2024-competition
- guthman.gatech.edu/2025-competition
- guthman.gatech.edu/2026-competition

### Microtonal Resources
- xen.wiki — Bohlen-Pierce scale
- xen.wiki — Just intonation
- microtonal.miraheze.org — Microtonal encyclopedia

### Hydraulophone
- Mann, S. (2005). "Hydraulophone design considerations."
- mannlab.com/hydraulophone
- Wikipedia: Hydraulophone

### 3D Printed Instruments
- Thingiverse Musical Instruments group
- Printables.com/flute, /windinstrument
- MakerWorld Musical Instruments collection
- Cults3D wind instrument STL files
- Royal College of Music — 3D Printed Musical Instruments project

### World Flutes
- ellisflutes.com — Xiao (bei xiao and tang xiao)
- Wikipedia: Mbira (tuning systems)
- Wikipedia: Shakuhachi
