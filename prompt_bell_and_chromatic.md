# Bass Clarinet Bell Design & Full Chromatic Scale

## Context
We have a working bass clarinet model with 7-hole D major diatonic scale (D2-D3) + register hole, validated to 0.04c RMS 1st register, 7.96c RMS 2nd register, 9.5c RMS twelfths. Configuration:
- Bore: 1211.3mm × 12.5mm radius (uniform cylinder)
- Register hole: 80mm from reed, 2.5mm diameter, 3mm chimney
- 7 toneholes: [176, 293, 338, 445, 532, 610, 636]mm from reed, 11mm diameter
- Closed-top TMM model (Bordeaux method)

Next step: Add bell and expand to full 3-octave chromatic (D2-D5).

## Research Questions

### Bell Design
1. Bass clarinet bell dimensions: typical length from last tonehole to bell opening? For a ~1.2m bore, what bell length (200-350mm)?
2. Flare profile: exponential vs Bessel vs polynomial? What expansion rate (typical flare coefficient for bass clarinet)?
3. Opening diameter: typical bass clarinet bell opening (50-65mm)?
4. How does the bell affect the lowest 2-3 notes? Does it mainly affect fundamental (all holes closed) or the first few open-hole notes?
5. On a closed-open instrument, the bell doesn't radiate at low frequencies (the toneholes do). How important is bell geometry for intonation vs timbre?
6. Typical wall thickness and material for bass clarinet bell?

### Full Chromatic Layout
1. For a bass clarinet in Bb, what are the standard tonehole positions for a full chromatic scale? Is there a reference table?
2. How are cross-fingerings handled (F/F# on clarinet)?
3. Do higher notes use smaller-diameter toneholes? What's the typical size progression?
4. How many toneholes total on a bass clarinet? (soprano has 17-18, bass typically 13-15 + extra keys)
5. What's the gap between the last tonehole and the bell start?

### Mechanical
1. Typical key mechanism for bass clarinet register key (mounted on neck vs upper joint)?
2. Bass clarinet neck dimensions (S-curve length, bore diameter, curvature)?
3. Does the register key position change with instrument size (bass vs soprano)?

## Files
- `config/bass_clarinet_7hole.json` - current working configuration
- `backend/tmm_acoustics.py` - TMM engine for woodwinds
- `backend/tmm_optimizer_sequential.py` - SequentialBoreOptimizer

## Test Commands
```bash
python backend/bass_clarinet_full_test.py
```
