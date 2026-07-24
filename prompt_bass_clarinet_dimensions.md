# Research: Bass Clarinet — Real Measured Dimensions

## Context
We are building a Bb bass clarinet from scratch using TMM (Transfer Matrix Method) acoustic simulation + differential evolution optimization. Our soprano clarinet TMM model achieves sub-0.3c RMS intonation on benchmarks. We need to scale to bass clarinet.

## Our Current Model (likely wrong)
From `modular_components.py`:
- Bore diameter: 25mm (12.5mm radius, cylindrical)
- Total unfolded length: 1800mm (including U-bend)
- Neck: S-curve, 180mm, bore 12.5mm
- Upper joint: 320mm × 12.5mm radius, 6 keys
- Lower joint: 350mm × 12.5mm radius, 5 keys
- Bell: exponential flare, 280mm, 12.5mm→55mm radius
- Register key: 8-10mm diameter

## Known Physics
- Bass clarinet is a closed-open pipe (reed at one end, bell at the other)
- Lowest note: written E3, sounding D3 (146.8 Hz) — or is it Bb1 (58 Hz)?
  - For Bb1 (58 Hz): L = c/(4f) = 343/(4×58) = 1.478m (closed-open quarter-wave)
  - For D3 (147 Hz): L = 343/(4×147) = 0.583m (this is soprano clarinet length!)
  - Wait — the transposition: Bb bass clarinet written C sounds Bb1 (58 Hz). Low E (written E3) sounds D3 (147 Hz). So the FUNDAMENTAL length should be for Bb1 = ~1.48m.

But wait — does the bass clarinet overblow at the 12th (3rd harmonic) like the soprano? With a register hole to vent the fundamental and produce the 2nd register? The total length must accommodate both registers.

## What We Need
1. **Total unfolded tube length** (including mouthpiece, neck, U-bend, bell) for a REAL Bb bass clarinet — give mm
2. **Bore profile**: is it truly cylindrical throughout? Any tapers? Where? By how much?
3. **Actual measured inner bore diameters** at key points (mm):
   - Mouthpiece receiver
   - Neck (S-curve) bore
   - Upper joint (top, middle, bottom)
   - Lower joint (top, middle, bottom)
   - Bell (start, flare progression, end)
4. **Tonehole positions**: distance from reed tip (mm) for ALL 17-21 toneholes in a professional bass clarinet (Buffet, Selmer, or Yamaha)
5. **Tonehole diameters** (mm) for each hole
6. **Register key**: position, diameter, mechanism
7. **Bell flare**: start position, flare length, opening diameter, flare type (exponential/Bessel/other)
8. **U-bend geometry**: does it add acoustic length beyond just connecting upper/lower joints?

## Specific Measured References Needed
- Buffet Crampon Prestige 1193 bass clarinet measurements
- Selmer Privilege bass clarinet bore profile
- Yamaha YCL-631 / YCL-821 II measurements
- Any published acoustic measurements from papers

## Questions
1. A closed-open pipe for Bb1 (58 Hz) needs L = c/(4f) = 1.48m. An 1800mm tube gives f = c/(4×1.8) = 47.6 Hz (≈Gb1). Is our 1800mm estimate wrong, or does the bass clarinet NOT follow the simple quarter-wave formula because of the bell flare?
2. Are bass clarinet toneholes spaced for a diatonic chromatic scale? Or is only the first register (chalumeau) diatonic with the second register (clarino) filling chromatic gaps?
3. What is the ACTUAL acoustically-measured total length of a Bb bass clarinet? (Not physical instrument height — unfolded tube length)

## Target
We need EXACT dimensions to build a TMM model and run DE optimization. Even ±5mm uncertainty in positions will give ±30c intonation errors. We need measurements, not estimates.

## Cite Sources
Provide author, year, journal/book, and specific measurement values in mm. If speculation, mark clearly.
