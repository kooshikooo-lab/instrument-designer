# Research: Trumpet Open Fingering — Why 243 Hz Instead of 233 Hz?

## Context
We built a Bach 180-37 ML trumpet in OpenWind FEM. Our model:
- Total bore length: 1.335m (without mouthpiece)
- Leadpipe: 0→0.25m, venturi 3mm→4.38mm radius → 5.83mm
- Cylinder: 0.25→0.75m, 5.83mm radius (ML bore)
- Bessel bell: 0.75→1.335m, 5.83mm→61.12mm radius, parameter=0.7
- No mouthpiece modeled

OpenWind FEM gives open fingering fundamental = 243 Hz (= B3 + 73c). Target is Bb3 = 233.08 Hz.

## Observations
- 1.335m open-open: f = c/(2L) = 128 Hz (not 233 Hz; trumpet is NOT simple open-open)
- 1.335m closed-open: f = c/(4L) = 64 Hz (not 233 Hz; trumpet is NOT simple closed-open)
- First impedance peak is ~89 Hz (sub-harmonic)
- Second peak at 243 Hz is the played fundamental

## Our Workarounds
- Interpolated: 1.475m (real with mouthpiece) gave 220 Hz, 1.335m gave 243 Hz, so we computed 1.392m gives exactly 233 Hz
- We now use 1.392m as the model length and get correct Bb3

## What We Need
1. **What is the correct bore length for a Bach 180-37 ML Bb trumpet (UNFOLDED, with mouthpiece)?** Is 1.475m correct? Or should it be different?
2. **How does the mouthpiece affect the fundamental frequency?** Our model has NO mouthpiece. A real trumpet has:
   - Mouthpiece cup (acoustic compliance — lowers frequencies)
   - Mouthpiece backbore (tapered channel — affects impedance)
   - These create an additional volume at the input. What's the acoustic model?
3. **Is 1.335m (without mouthpiece) actually correct for a Bach 180-37?** If the bell flare gives a frequency-dependent effective length, then 1.335m might be right and the mouthpiece might be the sole cause of our 243 Hz vs 233 Hz discrepancy.
4. **Given that the real tube + mouthpiece = ~1.475m, and our tube alone = 1.335m, does the mouthpiece act primarily as:**
   - An added length (~140mm)?
   - A compliance volume (Helmholtz resonator-like)?
   - Both?
5. **Quantify the mouthpiece effect**: How many cents does a Bach 7C mouthpiece lower the open fundamental on a 1.335m tube?
6. **Literature on trumpet mouthpiece acoustics**: Any papers with measured transfer functions or equivalent circuit models? (Backus, Plitnik, Campbell, etc.)

## Specific References We've Used
- Piatt (WVU, 2017) — Professional trumpet measurements (leadpipe, bell profiles)
- Tournemenne & Chabassier (2019) — OpenWind FEM vs TMM for brass
- Petiot (2025) — ML trumpet leadpipe optimization (Yamaha prototype)

## Target
We need to know: is our 243 Hz purely due to missing mouthpiece? Or is our bore geometry wrong? Give actionable fix with dimensions.

Bonus: What's the correct OpenWind way to model a mouthpiece? As a short conical section? A closed volume with a small orifice? Or should we just add 140mm of bore length to model the mouthpiece's effect?
