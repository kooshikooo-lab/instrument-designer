# Research: Hybrid Instruments, Mouthpiece Cross-Compatibility & Overtone Flutes
**Date:** 2026-07-15
**Researcher:** opencode (big-pickle)

---

## PART 1: HYBRID INSTRUMENT CONCEPTS

### 1. What Makes an Instrument "Hybrid"

A hybrid instrument combines elements from two or more instrument families:
- **Sound production method**: reed + brass embouchure, or slide + valves
- **Bore type**: cylindrical + conical in the same instrument
- **Material**: brass body + woodwind mouthpiece
- **Playing technique**: slide + fingering, or breath + percussion

### 2. Historical Hybrids That Actually Existed

#### A. Cornett (Cornetto) — Renaissance (15th-17th century)
- **What it is:** Wooden instrument with brass-style cup mouthpiece + finger holes
- **Classification:** Hornbostel-Sachs 422.2 (lip-vibrated aerophone with finger holes)
- **Why hybrid:** Brass embouchure (lip vibration) + woodwind fingering (6 holes)
- **Sound:** Brilliant, penetrating — used in church and court music
- **3D printing research:** Royal College of Music + Ricardo Simian have 3D printed cornett replicas from CT scans
- **Significance:** Proves brass+woodwind hybrids can be musically successful

#### B. Saxophone — Adolphe Sax (1841)
- **What it is:** Single-reed mouthpiece (like clarinet) + brass body + conical bore
- **Classification:** Woodwind (despite being made of brass)
- **Why hybrid:** Sax wanted "power of brass + agility of woodwinds"
- **Design:** Single reed → metal tube with conical bore → flared bell
- **Key insight:** The reed provides the excitation (like clarinet), the conical bore provides the harmonic spectrum (like brass), the bell projects the sound

#### C. Superbone / Valide Trombone
- **What it is:** Trombone with BOTH slide AND 3 valves
- **History:** First appeared 19th century (Besson), reinvented 1940s (Brad Gowans "Valide"), 1970s (Maynard Ferguson "Superbone"), 2013 (Schagerl/James Morrison)
- **How it works:** Short 4-position slide + 3 rotary valves
- **Significance:** Slide for glissandi + valves for rapid passages = best of both worlds

#### D. Flugabone (Flugelbone)
- **What it is:** Marching trombone = valve trombone wrapped in flugelhorn shape
- **Bore:** More conical than trombone (like flugelhorn)
- **Sound:** Mellower than trombone, more brilliant than flugelhorn

#### E. Slide Saxophone
- **What it is:** Saxophone with trombone-style slide instead of keys
- **Existence:** Yes — several custom makers have built them
- **Challenges:** Conical bore + slide = intonation very different from cylindrical trombone

#### F. Heckelphone-Clarinet
- **What it is:** Bassoon reed + clarinet-style cylindrical bore
- **Purpose:** Fill gap between bassoon and contrabassoon
- **Status:** Rare, mostly historical curiosity

#### G. Tárogató
- **What it is:** Single reed (like clarinet) + conical bore (like saxophone) + historical Hungarian design
- **Sound:** Warmer than saxophone, more powerful than clarinet
- **Status:** Still played in Hungarian folk music

### 3. Conceptual Hybrid Designs for 3D Printing

#### Concept A: Trombone-Clarinet ("Claronbone")
```
┌─────────────────────────────────────────────────┐
│  CLARINET BELL (flared)                         │
│  ├── Cylindrical bore (12-15mm ID)              │
│  │   ├── Tone holes (clarinet fingering)        │
│  │   │   ├── Keys or open holes                  │
│  │   │   └── Register key (for overblowing)     │
│  │   └── Slide section (short, 4-5 positions)   │
│  │       ├── For glissandi                       │
│  │       └── Replaces lower joint               │
│  └── Single-reed mouthpiece (clarinet type)     │
└─────────────────────────────────────────────────┘
```

**Acoustic theory:**
- Cylindrical bore + single reed = odd harmonics only (like clarinet)
- Adding a slide changes effective tube length continuously
- Challenge: slide must be airtight AND allow smooth movement
- Bore diameter must stay constant through slide joint

**3D print approach:**
- Print mouthpiece section + tone hole section as one piece
- Print slide sections from PETG (stronger, lower friction)
- Use silicone grease for slide lubrication
- Inner diameter: 12mm for Bb clarinet range

#### Concept B: Saxophone-Flute ("Saxflute")
```
┌─────────────────────────────────────────────────┐
│  SAXOPHONE BELL (flared, conical)                │
│  ├── Conical bore body                          │
│  │   ├── Tone holes (saxophone fingering)       │
│  │   └── Embouchure hole (transverse flute type)│
│  │       └── No reed — player's lips excite air │
│  └── Material: PLA/PETG                         │
└─────────────────────────────────────────────────┘
```

**Acoustic theory:**
- Conical bore + lip excitation = all harmonics (like saxophone)
- No reed = softer, breathier tone
- Transverse embouchure = easier to play than reed
- Range: ~2.5 octaves with good embouchure

#### Concept C: Clarinet-Ocarina ("Clarinetina")
```
┌─────────────────────────────────────────────────┐
│  OCARINA BODY (vessel resonator)                │
│  ├── Spherical/ovoid chamber                    │
│  │   ├── Tone holes (clarinet fingering)        │
│  │   └── Single-reed mouthpiece attached        │
│  └── Hybrid excitation: reed + vessel resonance │
└─────────────────────────────────────────────────┘
```

**Acoustic theory:**
- Vessel resonators produce different harmonic spectrum than tubes
- Clarinet fingering on ocarina body = novel sound
- Challenge: ocarina tone holes are typically 4-6, clarinet needs 17+

#### Concept D: Trombone-Oboe ("Trombone d'Amore")
```
┌─────────────────────────────────────────────────┐
│  DOUBLE REED + SLIDE                             │
│  ├── Conical bore (oboe-like)                   │
│  │   ├── Slide section (trombone-style)         │
│  │   └── Flared bell                            │
│  └── Double reed mouthpiece (oboe type)         │
└─────────────────────────────────────────────────┘
```

**Acoustic theory:**
- Conical bore + double reed = rich, nasal tone (like oboe)
- Slide allows continuous pitch control
- Challenge: double reed is very sensitive to pressure changes
- Range: limited by reed response, not bore length

### 4. Woodwind Mouthpiece Cross-Compatibility

#### How Mouthpieces Work

**Single-reed mouthpieces (clarinet, saxophone):**
- Clarinet mouthpiece: cylindrical bore, narrow, fits into barrel joint (corked shank)
- Saxophone mouthpiece: wider bore, fits onto neck (cork on neck)
- **NOT interchangeable** — different bore dimensions, different reed sizes

**What IS interchangeable within families:**
- Bb clarinet mouthpiece → A clarinet body (same bore, different length)
- Alto sax mouthpiece → other alto sax mouthpieces (same neck diameter)
- Tenor sax mouthpiece → other tenor sax mouthpieces
- **Soprano clarinet mouthpiece → soprano sax mouthpiece?** — NO, different bore shapes

**Mouthpiece parameters that affect compatibility:**
| Parameter | Clarinet | Saxophone | Difference |
|-----------|----------|-----------|------------|
| Bore diameter | ~12mm | ~15-20mm | Incompatible |
| Reed size | 2mm x 12mm | 2mm x 12-15mm | Similar but not same |
| Facing curve | Shorter | Longer | Different response |
| Chamber shape | Square/C | Round/C/U | Different tone |
| Shank type | Cork (insert) | Cork (on neck) | Physical fit |

**Key insight:** Mouthpieces are NOT interchangeable between instrument families because:
1. Bore dimensions differ (cylindrical vs conical)
2. Reed sizes differ (soprano clarinet reed ≠ tenor sax reed)
3. Chamber geometry affects harmonic content differently
4. Physical attachment method differs (insert vs. onto)

**However:** Within the clarinet family, mouthpieces CAN be swapped:
- Bb clarinet mouthpiece → Bass clarinet (with adapter)
- Bb clarinet mouthpiece → Eb clarinet (with adapter)
- Bb clarinet mouthpiece → Contrabass clarinet (with adapter)

**And** within the saxophone family:
- Alto sax mouthpiece → C-melody sax (with adapter)
- Tenor sax mouthpiece → C-melody sax (with adapter)
- Soprano sax mouthpiece → C soprano sax (with adapter)

### 5. Designing a Modular Mouthpiece System

```
MODULAR MOUTHPIECE CONCEPT:
┌─────────────────────────────────────────────────┐
│  UNIVERSAL MOUTHPIECE BODY                      │
│  ├── Standard reed table (flat surface)         │
│  ├── Interchangeable baffle inserts             │
│  │   ├── Jazz baffle (deep, round chamber)      │
│  │   ├── Classical baffle (shallow, C chamber)  │
│  │   └── Pop baffle (high step baffle)          │
│  ├── Modular shank adapter                      │
│  │   ├── Clarinet shank (12mm, cork)           │
│  │   ├── Alto sax shank (15mm, cork)           │
│  │   ├── Tenor sax shank (18mm, cork)          │
│  │   └── PVC pipe adapter (20mm, friction)     │
│  └── Standard ligature mount                    │
└─────────────────────────────────────────────────┘
```

**3D print approach:**
- Print body + baffle as one piece
- Print shank adapters as separate pieces
- Use friction fit + O-ring for airtight seal
- Material: PLA+ for body, PETG for shank (durability)

---

## PART 2: OVERTONE FLUTES — COMPREHENSIVE RESEARCH

### 1. What is an Overtone Flute

An overtone flute (also called harmonic flute) is the simplest type of flute:
- **No finger holes** (or very few — 1-3 max)
- Sound is produced by **overblowing** — blowing harder produces higher harmonics
- The player alternately opens and closes the bottom end with a finger
- Open end = even + odd harmonics (1st, 2nd, 3rd, 4th, 5th...)
- Closed end = odd harmonics only (1st, 3rd, 5th, 7th...) — drops an octave

**Result:** A diatonic scale is available by combining open and closed end positions with different blowing strengths.

### 2. The Harmonic Series on an Overtone Flute

For a tube in the key of G (fundamental = G3 ≈ 196 Hz):

**Open end harmonics:**
| Harmonic | Ratio | Frequency | Note (approx) | Interval from root |
|----------|-------|-----------|---------------|-------------------|
| 2nd | 2:1 | 392 Hz | G4 | Octave |
| 3rd | 3:2 | 588 Hz | D5 | Octave + 5th |
| 4th | 4:1 | 784 Hz | G5 | 2 octaves |
| 5th | 5:4 | 980 Hz | B5 | 2 octaves + 3rd |
| 6th | 6:1 | 1176 Hz | D6 | 2 octaves + 5th |
| 7th | 7:4 | 1372 Hz | F6 | 2 octaves + 7th |
| 8th | 8:1 | 1568 Hz | G6 | 3 octaves |

**Closed end harmonics (odd only):**
| Harmonic | Ratio | Frequency | Note (approx) | Interval |
|----------|-------|-----------|---------------|----------|
| 1st | 1:1 | 196 Hz | G3 | Fundamental |
| 3rd | 3:1 | 588 Hz | D5 | Octave + 5th |
| 5th | 5:1 | 980 Hz | B5 | 2 octaves + 3rd |
| 7th | 7:1 | 1372 Hz | F6 | 2 octaves + 7th |

**Combined scale (practical range):**
```
Open:  G4  B4  D5  F#5  G5  A5  B5  C6  D6
Close: G3  D4  B3  F4   G4  D5  B4  F5  G5
```

This gives a Mixolydian-like scale with a flat 7th, plus passing tones from partial shading of the end.

### 3. Global Overtone Flute Traditions

#### A. Europe

**Koncovka (Slovakia)**
- Length: 50-80cm, bore: 15-18mm
- Material: elder wood (traditional), PVC (modern)
- 3 holes near end (for additional scale access)
- Key: C to G
- Sound: haunting, ethereal
- UNESCO: Fujara and its music listed as intangible heritage

**Fujara (Slovakia)**
- Length: 140-200cm (!), bore: 20-25mm
- Material: elder, sycamore, or PVC
- 3 holes near end for diatonic scale access
- Key: G to Bb (contrabass range)
- Sound: deep, meditative, "shepherd's voice"
- National instrument of Slovakia
- Played standing, held vertically

**Tilinca / Tylynka (Romania/Ukraine)**
- Length: 30-100cm, bore: 12-20mm
- Material: wood, reed, or PVC
- No holes or 1 half-tone hole
- Sound: simple, folk-like
- Very easy to make — any hollow tube works

**Seljefløyte / Willow Flute (Scandinavia)**
- Length: 25-50cm, bore: 15-20mm
- Material: willow bark (spring only, traditional) or PVC (modern)
- Transverse embouchure (played sideways)
- Sound: bright, pastoral
- Norwegian: seljefløyte, Finnish: pajupilli, Swedish: salgflöjt

**Kalyuka (Russia/Ukraine)**
- Length: 30-80cm, bore: 10-15mm
- Material: hollow plant stems (traditional) or wood
- Sound: breathy, gentle
- Historically seasonal (plant stems only available in summer)

**Tabor Pipe / Tinička (Czech/Slovak)**
- Length: 30-50cm, bore: 15-18mm
- Material: wood or PVC
- 3 finger holes (adds more notes than pure overtone)
- Played with one hand (other hand plays drum)

#### B. Asia

**Chinese Dongxiao** (partially overtone)
- End-blown, 4-6 finger holes
- Uses overblowing for upper register

**Indian Bansuri** (partially overtone)
- 6-7 finger holes, overblowing for upper register
- Raga-specific ornaments via half-holing

#### C. Americas

**Native American Overtone Flute**
- Simple tube, no holes or 1-2 holes
- Used for meditation and ceremony
- Drone + overtone creates "spirit voice"

**Kaypacha (Argentina)**
- South American overtone flute
- Related to Sepic flutes of indigenous peoples

### 4. PVC Overtone Flute Builds

#### A. DIY BY BRAS System (Nicolas Bras)

**The most systematic approach to PVC overtone flutes:**

**20mm Overtone Flute Head (3D printed):**
- Dimensions: 24 × 24 × 48mm (without connector) or 69mm (with connector)
- Weight: 9g (head only) or 16g (with connector)
- Compatible with: 20mm PVC pipe (European standard, 1.6mm wall)
- Print: 0.2mm layer, 4 walls, 15% infill
- Material: PLA or PETG

**Kit configurations (all 3D printed heads + PVC pipe):**
1. **1-hole semitone** (C, C#) — simplest
2. **3-hole major** (C, D, E, F) — diatonic
3. **6-hole chromatic** (C, C#, D, D#, E, F, F#) — most capable

**Available head sizes:**
- 20mm head (standard) — for 20mm PVC pipe
- 25mm head (large bore) — for 25mm PVC pipe
- 100mm head (experimental) — for large-scale instruments

**Key features:**
- Precise fipple geometry for clear, responsive tone
- Modular connector system for mixing heads/bodies
- Friction-fit to PVC pipe (wrap tape for airtight seal)
- Blueprints included for each configuration

**YouTube tutorial:** "How to build your Overtone Flute 20mm BY BRAS" (Dec 2024)

#### B. FujaraHead (Slovakia)

**3D printed overtone flute heads since 2020:**
- Based on traditional Slovak koncovka/fujara design
- 3D printed head + PVC or wooden body
- Precision bore for accurate tuning
- Available in multiple keys

#### C. MakerWorld / Printables Models

**Head for transverse overtone flute (Seljefløyte):**
- By user Ialohrr
- Compatible with 16mm PVC pipe
- Friction fit, transverse embouchure
- Blow hole offset from fipple (sound not aimed at ear)
- Print: 0.2mm layer, 4 walls, 15% infill
- No finger holes — pure overtone

#### D. Durius Flutes (PVC Fujara)

**Handcrafted PVC fujara sets:**
- 3-piece set: keys of A, D, and C
- Main pipe in A (can be played as willow flute)
- 432Hz version for meditation
- Hand-painted decorative designs
- Made to order, ~$100-200

#### E. Flutopedia PVC Fujara Guide

**Materials needed:**
- 1.5" PVC pipe (4-foot piece)
- Acetone (for softening/stretching)
- Sandpaper, files
- 30 days of acetone soaking for custom bore taper

### 5. Overtone Flute Design Parameters

#### Key = Fundamental Frequency

| Key | Length (open tube) | Length (closed tube) | Bore Diameter |
|-----|-------------------|---------------------|---------------|
| C4 | ~171cm | ~86cm | 15-20mm |
| D4 | ~152cm | ~76cm | 15-20mm |
| E4 | ~135cm | ~68cm | 15-20mm |
| F4 | ~128cm | ~64cm | 15-20mm |
| G4 | ~114cm | ~57cm | 15-20mm |
| A4 | ~102cm | ~51cm | 15-20mm |
| Bb4 | ~96cm | ~48cm | 15-20mm |

**Formula:**
```
Open tube: L = v / (2 * f)
Closed tube: L = v / (4 * f)
Where v = 343 m/s (speed of sound at 20°C)
```

#### Bore Diameter Ratio

The ratio of bore diameter to length affects playability:
- **Ratio 1:30** (e.g., 15mm bore, 450mm length) — easy to overblow, clear harmonics
- **Ratio 1:20** (e.g., 15mm bore, 300mm length) — moderate effort, good for beginners
- **Ratio 1:10** (e.g., 15mm bore, 150mm length) — harder to overblow, limited range

**Sweet spot:** 1:20 to 1:30 for most players.

#### Fipple Design

**Slit fipple (most common):**
```
    ┌──────────────┐
    │   Blow hole   │
    │   ┌──────┐   │
    │   │ Slit │   │  ← Air jet strikes sharp edge
    │   └──────┘   │
    │              │
    │   Bore       │
    └──────────────┘
```

**Transverse fipple (Scandinavian style):**
```
    ┌──────────────┐
    │              │
    │   ┌──────┐   │
    │   │ Hole │   │  ← Transverse embouchure hole
    │   └──────┘   │
    │              │
    │   Bore       │
    └──────────────┘
```

**3D printed fipple geometry:**
- Air jet width: 2-3mm
- Striking edge angle: 30-45 degrees
- Duct length: 10-15mm
- Duct height: 2-3mm

### 6. Adding Tone Holes to Overtone Flutes

Some overtone flutes have 1-3 additional holes that extend the scale:

**1-hole semitone (BY BRAS):**
- Position: ~15cm from bottom
- Diameter: 8mm
- Adds: chromatic semitone (e.g., C → C#)
- Fingering: thumb covers/uncovers

**3-hole major (BY BRAS):**
- Positions: evenly spaced in bottom third
- Diameter: 8mm each
- Adds: diatonic scale (e.g., C, D, E, F)
- Fingering: thumb + 2 fingers

**6-hole chromatic (BY BRAS):**
- Positions: closely spaced in bottom third
- Diameter: 6mm each (smaller for precision)
- Adds: chromatic notes (C, C#, D, D#, E, F, F#)
- Fingering: thumb + 5 fingers (like recorder)

**Fujara 3-hole:**
- Positions: near bottom, spaced for harmonic scale access
- Diameter: 10-12mm
- Allows: full diatonic scale + overblowing for upper register

### 7. Acoustic Physics of Overtone Flutes

#### Why Overblowing Works

In a tube, sound waves reflect at both ends:
- **Open end:** reflection with no phase change (pressure node)
- **Closed end:** reflection with 180° phase change (pressure antinode)

The resonant frequencies depend on boundary conditions:
- **Open-open tube:** f_n = n * v / (2L) — all harmonics present
- **Open-closed tube:** f_n = n * v / (4L) — only odd harmonics

When you overblow:
1. You increase air velocity through the fipple
2. The jet becomes unstable and "jumps" to the next resonant mode
3. The tube "selects" the nearest harmonic frequency
4. Higher blowing pressure → higher harmonic excited

#### End Correction

The effective acoustic length is slightly longer than the physical length:
```
L_eff = L_physical + 0.6 * r (for open end)
L_eff = L_physical + 0.3 * r (for closed end, partially)
Where r = bore radius
```

For a 15mm bore flute: end correction ≈ 4.5mm (open) or 2.25mm (closed)

#### Half-Covering the End

Partially covering the open end:
- Lowers the pitch slightly between harmonics
- Creates a "whoosh" or "scatter" effect
- Allows microtonal inflections
- Traditional technique for expression

### 8. PVC + 3D Printed Head: Complete Build Guide

#### Materials
- PVC pipe: 16-25mm diameter, cut to length for your key
- 3D printed head: BY BRAS system or custom design
- Sandpaper: 220 grit (for deburring)
- Transparent tape: for airtight seal between head and pipe
- Optional: food-safe epoxy for bore coating

#### Step-by-Step

1. **Calculate pipe length** for your desired key:
   ```
   Key of G: L = 343 / (2 * 196) = 0.875m = 87.5cm
   ```

2. **Cut PVC pipe** to calculated length (+5mm for trimming)

3. **Deburr pipe** ends with 220-grit sandpaper

4. **Print head** (BY BRAS 20mm or 25mm):
   - Material: PLA+ or PETG
   - Settings: 0.2mm layer, 4 walls, 15% infill
   - No supports needed (designed for printability)

5. **Assemble:**
   - Wrap 2-3 layers of transparent tape around pipe end
   - Insert into 3D printed head (friction fit)
   - Test for airtight seal (blow into head, listen for leaks)

6. **Tune:**
   - Play open G (second harmonic)
   - If sharp: shorten pipe slightly
   - If flat: add more tape to extend effective length

7. **Optional: Add tone holes:**
   - Mark positions from BY BRAS blueprints
   - Drill with 8mm bit (for 20mm bore)
   - Deburr holes with sandpaper

#### Expected Results
- **Print time:** ~1 hour for head
- **Assembly time:** ~15 minutes
- **Cost:** ~$2-5 in materials
- **Range:** 2-3 octaves (harmonic series)
- **Accuracy:** ±10 cents with good technique

### 9. Design Considerations for 3D Printed Overtone Flute Heads

#### Critical Dimensions

| Parameter | 20mm Head | 25mm Head | 100mm Head |
|-----------|-----------|-----------|------------|
| Bore ID | 20mm | 25mm | 100mm |
| Air jet width | 2.5mm | 3mm | 8mm |
| Striking edge angle | 35° | 35° | 30° |
| Duct length | 12mm | 15mm | 40mm |
| Duct height | 2.5mm | 3mm | 8mm |
| Overall length | 48-69mm | 60-85mm | 150-200mm |

#### Print Orientation

**Best: Print vertically (upright)**
- Fipple features print cleanly
- No supports needed on bore surface
- Layer lines aligned with airflow (less turbulence)

**Avoid: Print horizontally**
- Bore surface has layer lines perpendicular to airflow
- Supports needed inside bore
- Fipple geometry less precise

#### Material Choice

| Material | Sound | Durability | Cost | Recommendation |
|----------|-------|-----------|------|----------------|
| PLA | Bright, clear | Low (brittle) | $ | Good for prototyping |
| PLA+ | Bright, clear | Medium | $ | Best for beginners |
| PETG | Warm, smooth | High | $$ | Best for durability |
| ABS | Warm, smooth | High | $$ | Good if available |
| Wood PLA | Warm, woody | Medium | $$ | Aesthetic choice |

### 10. Hybrid Overtone + Conventional Flute Concepts

#### Concept: "Dual-Mode Flute"
```
┌─────────────────────────────────────────────────┐
│  3D PRINTED HEAD (dual mode)                    │
│  ├── Mode 1: Overtone (no reed, pure breath)   │
│  │   └── Play by overblowing harmonic series    │
│  ├── Mode 2: Fipple (duct flute, like recorder)│
│  │   └── Play with finger holes for chromatic   │
│  └── Swap heads on same PVC body                │
└─────────────────────────────────────────────────┘
```

**BY BRAS system enables this:**
- Same 20mm PVC body
- Overtone head (no holes) → meditative, breath-controlled
- Fipple head (with duct) → more notes, easier melody
- Chromatic head (6 holes) → full chromatic scale

#### Concept: "PVC Shakuhachi with Overtone Head"
```
┌─────────────────────────────────────────────────┐
│  SHAKUHACHI BODY (PVC, 54cm)                    │
│  ├── 5 finger holes (traditional)               │
│  ├── 3D printed shakuhachi head (utaguchi)      │
│  └── OR 3D printed overtone head                │
│      └── Play same body two different ways      │
└─────────────────────────────────────────────────┘
```

---

## PART 3: NEW INSTRUMENTS TO ADD TO THE APP

### From Hybrid Research

| Instrument | Type | Category | Notes |
|-----------|------|----------|-------|
| Cornett | Historical hybrid | Woodwind+Brass | Lip-vibrated + finger holes, 3D printed from CT scans |
| Superbone | Modern hybrid | Brass | Slide + valves, trombone family |
| Tárogató | Reed hybrid | Woodwind | Single reed + conical bore, Hungarian |
| Saxophone | Original hybrid | Woodwind | Single reed + brass body + conical bore |

### From Overtone Flute Research

| Instrument | Type | Category | Notes |
|-----------|------|----------|-------|
| Koncovka | Overtone flute | Flute | Slovak, 50-80cm, 3 holes, elder/PVC |
| Fujara | Overtone flute (large) | Flute | Slovak, 140-200cm, national instrument |
| Tilinca | Overtone flute | Flute | Romanian, 30-100cm, simplest type |
| Seljefløyte | Overtone flute | Flute | Norwegian, willow bark/PVC, transverse |
| Kalyuka | Overtone flute | Flute | Russian, plant stem/wood |
| Tabor Pipe | Overtone flute | Flute | Czech/Slovak, 3 holes, one-hand play |
| Willow Flute | Overtone flute | Flute | Scandinavian, seasonal willow bark |
| Kaypacha | Overtone flute | Flute | Argentine, South American |

### PVC + 3D Print Specific

| Instrument | Type | Category | Notes |
|-----------|------|----------|-------|
| PVC Overtone Flute (BY BRAS) | Modern overtone | Flute | 3D printed head + PVC pipe, modular |
| PVC Fujara | Modern overtone | Flute | PVC pipe + 3D printed head |
| PVC Koncovka | Modern overtone | Flute | PVC pipe + 3D printed head |
| PVC Transverse Overtone | Modern overtone | Flute | 16mm PVC + transverse 3D head |

---

## PART 4: DESIGN FORMULAS

### Overtone Flute Length Calculator

```python
import math

v = 343.0  # speed of sound m/s at 20°C

def overtone_flute_length(key_freq, open=True):
    """Calculate overtone flute length for a given fundamental frequency."""
    if open:
        return v / (2 * key_freq)  # open tube
    else:
        return v / (4 * key_freq)  # closed tube

# Example: Key of G
f_G = 196.0  # Hz
L_open = overtone_flute_length(f_G, open=True)
L_closed = overtone_flute_length(f_G, open=False)
print(f"Key of G: Open tube = {L_open*100:.1f}cm, Closed tube = {L_closed*100:.1f}cm")

# Key of D (common for folk flutes)
f_D = 293.7  # Hz
L_D = overtone_flute_length(f_D, open=True)
print(f"Key of D: Open tube = {L_D*100:.1f}cm")
```

### Harmonic Frequency Table

```python
def harmonic_frequencies(fundamental, n_harmonics=8):
    """Generate harmonic series frequencies."""
    return [fundamental * n for n in range(1, n_harmonics + 1)]

# For key of G
freqs = harmonic_frequencies(196.0, 8)
for i, f in enumerate(freqs, 1):
    print(f"  {i}th harmonic: {f:.0f} Hz")
```

### Tone Hole Position Calculator (for overtone flutes with holes)

```python
def tone_hole_position(total_length, target_freq, fundamental_freq, bore_radius):
    """Calculate position of a tone hole from the open end."""
    # Effective tube length for target note
    L_target = v / (2 * target_freq)
    # Position from open end
    position = total_length - L_target
    # End correction
    end_correction = 0.6 * bore_radius
    return position - end_correction
```

---

## Sources

### Overtone Flutes
- jeremymontagu.co.uk/OvertoneFlutes.html — comprehensive overtone flute taxonomy
- en.wikipedia.org/wiki/Overtone_flute — global overview
- folkfluteworld.com — Ultimate Guide to the Overtone Flute
- flutetunes.com/articles/overtone-flute — history, makers, build guides
- fujara.sk — Slovak koncovka and fujara (UNESCO heritage)
- fujaraflutes.com — Winne Clement, master maker (Belgium)
- fujarahead.com — 3D printed overtone flute heads (Slovakia)
- overtoneflute.fi — Finnish overtone flute builder
- instrumentsbybras.com — Nicolas Bras DIY BY BRAS system (3D printed heads)
- flutopedia.com/fujara_craft.htm — PVC fujara build guide

### PVC Flute Builds
- instructables.com/DIY-PVC-Pipe-Flutes — simple PVC flute with rubber glove membrane
- drivenoutside.com — Making Simple PVC Flutes (Instructables)
- thealteredgoddess.com — Kari Tauring PVC overtone flute guide
- youtube.com: "How to build your Overtone Flute 20mm BY BRAS"
- youtube.com: "3 PVC Overtone Flutes I built: Koncovka, Tabor, Fujara"
- duriusflutes.co.uk — Handcrafted PVC fujara sets

### Hybrid Instruments
- Adolphe Sax (1841): "power of brass + agility of woodwinds" → saxophone
- Wikipedia: Trombone (superbone, flugabone, valve trombone)
- Wikipedia: Clarinet (history, mouthpiece system)
- Wikipedia: Mouthpiece (woodwind) — clarinet vs sax compatibility
- woodwindharmony.com — Choosing mouthpieces for different woodwinds
- D'Addario — Clarinet & Saxophone mouthpiece comparison charts
- Yamaha — Mouthpiece guide for brass & woodwind

### Academic
- Simian, R. (2023). "3D-Printed Musical Instruments: Lessons Learned from Five Case Studies"
- Royal College of Music — 3D Printed Musical Instruments project (cornett replicas)
- NIME 2016: "3D Modelling and Printing of Microtonal Flutes"
