# Instrument Maker Compromises: Intonation vs Timbre vs Playability
# Research compiled 2026-07-25

## Key Insight
Professional makers routinely **intentionally degrade** intonation to improve timbre, playability, response, dynamic range, and blend. An optimizer that only minimizes pitch error will find solutions real makers would reject.

---

## 1. Tone Hole Adjustments

### Undercutting Trade-off
- Raises pitch AND improves tone quality/volume
- Changes cutoff frequency (controls harmonic content/timbre)
- Asymmetrical undercutting adjusts pitch in one register while leaving other unchanged
- **18 clarinetist experiment** (Greenham 2003): majority preferred rounded (not undercut) edges for "even playing quality" — response uniformity matters more than optimizing any single note

### Cutoff Frequency as Timbre Control
- **Baroque** (small holes, wide spacing) → low fc → dark timbre, cross-fingering dependent
- **Modern** (large holes, close spacing) → high fc → bright timbre, nearly chromatic
- Makers CHOOSE the cutoff frequency, it's not just a consequence of hole placement
- Cross-fingering timbre variety is a FEATURE, not a bug — Baroque composers exploited it

### Radiated Power
- For wide holes, radiated power is nearly independent of hole radius
- **Rounding hole edges** increases power and dynamic range
- Makers can choose smaller holes (less resistance) without losing acoustic power

---

## 2. Benade's Mode Alignment / Harmonic Locking

### Requirements (Benade 1970, 1974)
- 2nd mode resonance must be within **5 cents** of 3rd harmonic of played frequency
- "Slightly inharmonic resonances → pitch changes with dynamic level"
- Same geometry change that improves intonation at low dynamics can worsen it at high dynamics

### NX Clarinet (Benade 1983)
- Register hole sized so "off-node pulling up of pitches... just offsets the effect of embouchure slackening needed to give best tone and response"
- **Direct example of deliberately mistuning for response**
- Professional clarinetists accept mode alignment errors of 30-15 cents, consider <10 cents excellent

---

## 3. Cross-Fingering Compromises

### The Physics
- Standing wave penetrates past first open hole into closed section
- Frequency-dependent penetration → higher resonances become inharmonic
- Notes like F4 and G#4 on baroque flute: weaker higher harmonics → darker, mellower, quieter
- **Haverkamp 2025 (DAGA)**: cross-fingering effect is highly note-specific, not uniform

### The Musical Resource
- Keys with few sharps: bright and loud (no cross-fingerings)
- Keys with flats: dark and quiet (cross-fingerings)
- This was a deliberate compositional tool in Baroque music
- Modern makers add modifications to enable all-key playing → compromise the timbre-intonation relationship

---

## 4. Professional Instrument Differences

### Yamaha CSG Clarinet
- C#/G# tonehole: "not ideally positioned acoustically" → inserted longer, wider tube → mechanical complexity penalty for acoustic fix
- Low E/F: "intentionally tuned lower" to keep other notes in tune
- Chose lightweight system over German system to avoid timbre/resistance penalties

### Buffet R13
- Polycylindrical bore: convergent conical portion corrects upper register intonation
- Heavily undercut tone holes — balanced intonation against timbre
- Players describe distinctive "ping and ring" — timbre choice

### Selmer Mark VI vs Yamaha Custom Z (Saxophone)
- Selmer: higher resistance → "more core" to sound, darker, harder to control intonation
- Yamaha: lower resistance → "free blowing," brighter, "intonation on rails"
- **Key quote**: "the Yamaha intonation looks more even with the tuner but just doesn't sound right to my ear" — Selmer's intonation quirks produce a "musically correct" sound despite being technically less accurate

### Professional Maker (Ruben, Paris)
> "The company I work for has three models that use an identical bore. But the toneholes are not the same size, are not in the same position and are not undercut the same way. This results in a RADICALLY different tone-color."

---

## 5. Resistance / Back Pressure

### The Trade-off
- Larger holes → better intonation → MORE resistance → harder to play
- Smaller holes → worse intonation → LESS resistance → easier fingering
- Benade's NX: "maximum tone hole length/diameter ratio" + "systematic rounding of all sharp edges" to minimize resistance while maintaining acoustic function

### Bowling 2016 Measurements
- Oboe: highest back pressure relative to sound output
- Flute: lowest resistance, most efficient
- Single reeds: reed spends half time in complete contact (closed system)

---

## 6. Intonation vs Timbre: The Pareto Front

### Noreland et al. 2023 (HAL)
- First to simultaneously optimize resonance frequencies AND peak amplitude ratios
- "High residual deviation illustrates the necessary compromise between frequencies of second register (H) and relative magnitudes of second peaks (A)"
- **Intonation and playability CANNOT be simultaneously perfectly optimized**

### Szwarcberg et al. 2025 (Acta Acustica)
- Decreasing register hole radius improves tuning
- BUT "if Rh ≤ 0.5 mm, opening the hole fails to overblow" — instrument breaks
- Some intonation improvements literally break playability

### Tournemène et al. 2018
- First to optimize spectral centroid alongside intonation
- "Musicians are willing to trade some intonation for better timbre"

---

## 7. Target Frequency Considerations

### Equal Temperament is NOT the Right Target
- ET major thirds are ~14 cents sharper than just intonation
- Historical instruments tuned to 55-part octave, not ET
- Enharmonic pairs (G# vs Ab) were ~22 cents apart until ~1850
- Professional instruments tune to a compromise, not pure ET

### What Makers Actually Target
1. Mathematical ET positions (baseline)
2. Adjustments for harmonic locking between registers
3. Intentional deviations for timbre/playability
4. Context-dependent adjustments (leading tones sharper, chord tones toward just)

---

## What Our Optimizer is Missing

### Objectives Real Makers Balance
1. ~~Intonation accuracy~~ (our current focus)
2. **Mode alignment** (harmonic locking — Benade's criterion)
3. **Spectral centroid** (brightness uniformity)
4. **Cutoff frequency** (timbre consistency)
5. **Peak amplitude ratios** (register switching)
6. **Resistance profile** (playing comfort)
7. **Dynamic range** (threshold to maximum)
8. **Response uniformity** (even attack across notes)
9. **Key-dependent timbre variety** (historical instruments)
10. **Ergonomic constraints** (hole spacing/size limits)

### Recommended New Cost Function Terms
1. `mode_alignment_error` = |f₂/3f₁ - 1| in cents (should be <15¢)
2. `spectral_centroid_uniformity` = std(SC) across notes
3. `peak_ratio_constraint` = a₂/a₁ within [min, max]
4. `resistance_proxy` = sum(chimney_height / hole_radius) for open holes
5. `cutoff_frequency_regularity` = std(fc) across fingerings
