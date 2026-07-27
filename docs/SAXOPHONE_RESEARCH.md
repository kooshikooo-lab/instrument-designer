# Saxophone Acoustics Research — Expert Sources & Benchmark Data

**Date:** 2026-07-22  
**From:** Laptop (via comprehensive web research)  
**For:** Desktop — to create benchmark saxophone instruments

---

## Key Expert Sources

### 1. UNSW (Joe Wolfe's Lab) — Gold Standard
- **Soprano sax half angle:** 1.74°
- **Tenor sax half angle:** 1.52°
- **Adolphe Sax original taper:** 3° total (1.5° half angle)
- Impedance measurement databases for soprano/tenor available at:
  https://newt.phys.unsw.edu.au/music/saxophone/
- Key papers:
  - Chen, Smith, Wolfe (2011) "Saxophonists tune vocal tract resonances" JASA 129, 415-426
  - Chen, Smith, Wolfe (2009) "Saxophone acoustics: introducing a compendium of impedance and sound spectra" Acoustics Australia 37(1), 18-23

### 2. McGill (Lefebvre & Scavone) — Bore Optimization
- **Critical finding:** "A straight conical tube is NOT appropriate for a saxophone"
- Deviations from perfect cone are NECESSARY for harmonicity
- **WIAT toolkit:** Python TMM package for woodwind design
  - Download: https://caml.music.mcgill.ca/wiat/download/wiat-0.1.0.zip
- Key papers:
  - Lefebvre & Scavone (2011) "On the bore shape of conical instruments" Canadian Acoustics 39(3), 128-129
  - Lefebvre PhD thesis (2010) "Computational Acoustic Methods for the Design of Woodwind Instruments"
  - Lefebvre & Scavone (2012) "Characterization of woodwind instrument toneholes with the finite element method" JASA 131(4), 3153-3163

### 3. OpenWInD (Inria) — Desktop's Tool
- Python TMM/FEM impedance, optimization, sound simulation
- https://openwind.inria.fr/
- Reference: Tournemenne & Chabassier (2019) Acta Acustica 105(5), 838-849

### 4. Marten Postma's Saxophone Measurements
- Tone hole diameters, bore diameters, ratios
- http://sax.mpostma.nl/EN/
- Key data: tone holes are 25-40% of local bore diameter

### 5. Nederveen — "Acoustical Aspects of Woodwind Instruments"
- Referenced by multiple sources as containing detailed saxophone measurements

---

## Design Rules from Experts

### Tone Hole Sizing
- **Standard:** 25-40% of local bore diameter (mpostma.nl)
- Holes smaller than 10% of bore diameter have significant acoustic impact
- Lower register holes are larger, upper register holes smaller
- The trend is stronger in sopranos than baritones

### Tone Hole Placement
- **6% rule:** ~6% of total bore length per chromatic step (actual: 0.0594631)
- This ONLY applies when tone hole = bore diameter
- Smaller holes → move closer to mouthpiece to compensate
- Spacing based on D chromatic scale (palm keys and low notes are "afterthoughts")

### Bore Design
- Adolphe Sax: 3° total taper (1.5° half angle)
- Real saxophones deviate from straight cone:
  - Upper bore: cylindrical mouthpiece section (~15.8mm dia, 50mm long)
  - Bell flare: increases radiation but minimal acoustic impact
  - Bow curvature: diameter at bow < body tube at join point
- **Closed tone holes** flatten pitch and absorb upper partials
- **Open tone holes** act like a second bell, but less pronounced for smaller holes

### Harmonicity Requirements
- Second resonance should be within ~10 cents of 2× fundamental
- Straight cone achieves this for first 9 notes, then fails
- Real instruments use bore deviations (not just cone angle changes) to fix this

---

## Standard Saxophone Dimensions

| Instrument | Key | Total Length | Body Length | Bore Range | Bell Diameter | Half Angle |
|------------|-----|-------------|-------------|------------|---------------|------------|
| Soprano | Bb | 73-79 cm | straight | 12-14.5 mm | 8-9 cm | 1.74° |
| Alto | Eb | ~65 cm | ~58 cm | 13-17 mm | 11-12 cm | ~1.6° (interp.) |
| Tenor | Bb | ~91 cm | ~76 cm | 15-20 mm | 14-16 cm | 1.52° |
| Baritone | Eb | ~122 cm | ~91 cm | 19-26 mm | 18-20 cm | ~1.4° (est.) |

### Xaphoon (Pocket Sax)
- Key: C (also Bb, D, G)
- Total length: **32 cm** (for C model)
- Bore: **Cylindrical** (not conical!)
- Holes: 9 (8 front + 1 thumb)
- Reed: Standard tenor sax reed
- Range: 2 octaves
- Similar to chalumeau in range

### 3D-Printed Alto Sax (Cults3D)
- Conical bore, 6 holes + thumb octave key
- Compatible with standard alto sax mouthpiece and reed
- Simplified fingering for accessibility
- Dimensions: ~45cm total

---

## 3D-Printed Instrument Ecosystem

### Demakein (Paul Harrison)
- https://github.com/pfh/demakein
- Python tools for woodwind instrument design + 3D printing
- Built-in: flutes, whistles, shawms, reedpipes
- **All closed-top instruments** (no sax-type open-open)
- Parametric: transposable, customizable
- Uses `demakein.design.Instrument_designer` class
- API: `inner_diameters`, `outer_diameters`, `hole_diameters`, `fingerings`

### WIAT (McGill)
- Python TMM impedance computation
- Tone hole modeling with FEM corrections
- Optimization routines (not fully released)

### OpenWInD (Inria)
- TMM/FEM impedance + sound simulation
- Bore reconstruction from measured impedance
- Full instrument optimization framework

---

## Key Finding for Our Alto Sax Problem

**Lefebvre & Scavone (2011) confirmed that a straight conical tube is NOT appropriate for a saxophone.** This means our current TMM optimizer (which assumes a straight cone via `as_stepped()`) may be fundamentally limited for alto sax. The bore shape itself needs to deviate from a perfect cone.

Real saxophone manufacturers:
1. Start with a cone
2. Add cylindrical sections at mouthpiece end
3. Modify bore profile at various points
4. Simultaneously optimize tonehole positions AND bore shape
5. Use trial-and-error with professional players

**The 6% rule and tone hole sizing rules are only starting points** — real instruments require simultaneous bore + tonehole optimization.

---

## Recommended Benchmark Instruments

### 1. Xaphoon (Easiest — start here)
- Cylindrical bore (simplest geometry)
- 32cm length, 9 holes
- Key of C: C4 to C6
- No bore optimization needed — just hole placement
- Well-documented, commercially available

### 2. Simple Soprano Sax
- Straight conical bore (no bends)
- 6 holes + octave key
- Half angle ~1.74°
- Bb soprano: Bb3 to ~F5

### 3. Alto Sax (Most Complex)
- Curved bore (bow section)
- 6+ holes + octave key
- Half angle ~1.6°
- Eb alto: Eb3 to ~C5
- **May require bore profile modifications** for harmonicity

### 4. Baritone Sax
- Largest bore, most holes
- Eb baritone: Eb2 to ~C4
- Most challenging for 3D printing

---

## References

1. Chen, J.M., Smith, J. and Wolfe, J. (2009) "Saxophone acoustics: introducing a compendium of impedance and sound spectra" Acoustics Australia 37(1), 18-23
2. Chen, J.M., Smith, J. and Wolfe, J. (2011) "Saxophonists tune vocal tract resonances in advanced performance techniques" JASA 129, 415-426
3. Lefebvre, A. and Scavone, G. (2011) "On the bore shape of conical instruments" Canadian Acoustics 39(3), 128-129
4. Lefebvre, A. (2010) "Computational Acoustic Methods for the Design of Woodwind Instruments" PhD thesis, McGill University
5. Lefebvre, A. and Scavone, G. (2012) "Characterization of woodwind instrument toneholes with the finite element method" JASA 131(4), 3153-3163
6. Nederveen, C.J. "Acoustical Aspects of Woodwind Instruments" (Revised Edition, Northern Illinois University Press, 1998)
7. Dalmont, J.P. et al. (1995) "Some aspects of tuning and clean intonation in reed instruments" Applied Acoustics 46, 19-60
8. Wolfe, J. "Introduction to saxophone acoustics" https://newt.phys.unsw.edu.au/jw/saxacoustics.html
9. Postma, M. "Tone holes; diameters, ratios" http://sax.mpostma.nl/EN/
10. Sax Gourmet "I Don't Want To Bore You: Saxophone Bores Explained" https://www.saxgourmet.com/
