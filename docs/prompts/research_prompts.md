# Research Prompts for ChatGPT/Claude

## Prompt 1: Clarinet Cross-Fingering Chart Validation

**Context**: Building a bass clarinet design automation tool. Using TMM (Transmission Matrix Method) acoustics model validated as correct. 7-hole diatonic works perfectly (0.04¢ RMS 1st register, 7.96¢ 2nd register, 9.5¢ twelfths). 12-hole chromatic sequential is hard-limited to ~15¢ RMS regardless of hole size (tested 8-20mm uniform, graduated). 

**Question**: You provided a 13×13 cross-fingering chart for 12 holes + register. The chart opens holes from the BELL END first (H7 for D#/E, H6 for F, etc.), progressing toward the reed end. But real clarinets open holes from the REED END first (thumb hole, then L1, L2...). 

Is your chart correct for a 12-hole bass clarinet? Or does it have the hole order reversed? The chart produces D# with H7+H9 (H8 closed between), but on a real clarinet D# is typically LH thumb + side key, not a bell-end hole.

Please provide a corrected cross-fingering chart with:
1. Explicit mapping: hole index → physical key (LH1, LH2, LH3, LH4/pinky, RH1, RH2, RH3, RH4/pinky, side keys, throat keys)
2. Written pitch → fingering for chalumeau register (written D2 to B4)
3. Clarion register fingerings (register key + chalumeau modifications)
4. Explanation of which holes are "primary" (diatonic) vs "corrective" (chromatic cross-fingerings) vs "vents"

**Physics constraint**: 1211mm × 25mm bore, 70-150Hz fundamental, holes are small (11mm) relative to wavelength (2-5m) so they're weakly perturbing, not terminating.

---

## Prompt 2: Register Hole Physics for Bass Clarinet

**Context**: Register hole at 80mm from reed, 2.5mm diameter, 3mm chimney. Works for 7-hole diatonic. For 12-hole chromatic, the 2nd register (n_register=2, 3rd harmonic) has ~15¢ RMS error.

**Questions**:
1. Is 80mm the correct register hole position for a 1211mm bore? Theory says ~L/15 for 12th venting.
2. Should the register hole diameter change with more toneholes? Benade suggests register hole size affects venting effectiveness.
3. For clarion register (12th above), do ALL fingerings use the same register hole open, or are there register hole modifications (half-hole, different vent)?
4. Why does the 7-hole diatonic achieve 7.96¢ RMS on 2nd register but 12-hole chromatic only 15¢? Is it the cross-fingering interference?

---

## Prompt 3: 12-Hole Chromatic Bass Clarinet Design - Literature Survey

**Context**: Standard Boehm bass clarinet has ~18-22 toneholes with complex keywork. We're modeling a simplified 12-hole system.

**Questions**:
1. What is the minimal number of toneholes for a fully chromatic bass clarinet (written D2 to G5)?
2. How do professional low-C bass clarinets handle the 3 extra semitones (C2, C#2, D2)?
3. What are the standard cross-fingerings for D#/Eb, F#/Gb, G#/Ab, A#/Bb, C#/Db in the chalumeau register?
4. Reference: Benade (1976) Ch.20-24, Nederveen (1998), Keefe (1982), Debut-Kergomard-Laloë (2005) - which fingerings do they recommend?
5. Is there a known "optimal" hole layout for 12-14 holes that achieves <10¢ RMS?

---

## Prompt 4: Optimization vs Physics Limits

**Context**: Sequential 12-hole (each note opens one more hole from reed end) gets 15.5¢ RMS on 2nd register. This appears to be a hard physics limit. Cross-fingering charts from literature get worse (46-200¢). 

**Questions**:
1. Is 15¢ RMS the theoretical limit for sequential 12-hole on 1211mm × 25mm bore?
2. Can cross-fingerings actually beat this, or is the bore simply too long for effective cross-fingering at 70-150Hz?
3. Benade mentions "tonehole lattice" - does a clarinet NEED the full lattice (all semitone holes) for good intonation, or can a reduced set work?
4. What about bore taper? Conical bore (like saxophone) vs cylindrical (clarinet) - how much does taper help intonation?
5. Should we optimize bore profile (taper) simultaneously with hole positions?

---

## Prompt 5: TMM Model Validation - Low Frequency Behavior

**Context**: TMM model validated as correct (tanner = normalized admittance, junction3 = parallel admittance addition, -0.5 phase = R=-1). 70-150Hz is deep in plane-wave regime (8kHz cutoff for 25mm bore).

**Observation**: 11mm holes produce uniform -78¢ offset in 1st register. This is expected physics (high Q shunt impedance at low frequencies). Holes are not effective vents until higher frequencies.

**Question**: Given that holes are weakly perturbing at 70-150Hz, is the very concept of "hole position determines pitch" flawed for the chalumeau register? Should we instead optimize for the CLARION register (220-440Hz) where holes are more effective, and accept that chalumeau will have a systematic offset correctable by mouthpiece pull?

---

## Prompt 6: Complete Bass Clarinet Design Parameters

**Need**: Reference design for a modern professional bass clarinet (low C model)
- Bore profile (cylindrical sections + taper + bell flare)
- Tonehole positions, diameters, chimney heights for ALL holes
- Register hole(s) position, diameter, chimney
- Keywork layout mapping holes to fingers
- Measured impedance peaks for each fingering

**Sources to check**: 
- Benade's measurements
- Yamaha/Selmer/Buffet technical specs
- Recent acoustic papers (Szwarcberg 2024, 2025)
- OpenWind FEM models

---

## Usage Instructions

Submit these prompts to ChatGPT (web) or Claude (web) for deep research. Use the API for coding tasks only. Copy relevant responses to `research/verified-references.md`.