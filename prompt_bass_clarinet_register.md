# Research: Bass Clarinet Register Hole — Physics and Optimization

## Context
We are building a Bb bass clarinet in TMM and need to design the register key (speaker key). The bass clarinet is a closed-open cylindrical pipe (reed at one end, bell at the other) that overblows at the 12th (3rd harmonic: 1f, 3f, 5f, 7f...).

## Our Physics Understanding
- Register hole vents the fundamental (pressure node) to enable the 2nd register
- Traditional placement: ~1/3 of total tube length from the reed
- Modern professional models (Selmer, Buffet, Yamaha) add a SECOND vent near 2/3 L for altissimo
- Cutoff frequency for 23.5mm bore: fc = c/(2π) × 2.405/a ≈ 11.2 kHz
- The register hole must be ABOVE cutoff frequency for the fundamental but BELOW cutoff for the 3rd harmonic

## What We Need
1. **arXiv paper: "Analysis and optimisation of the tuning of the twelfths for a clarinet resonator"** (physics/0309051) — Can you find this paper and give us:
   - The exact mathematical model for register hole optimization
   - Key equations for register hole position as function of bore diameter and length
   - How register hole diameter affects the 12th interval (does a bigger hole flatten/sharp the 2nd register?)
   - How register hole length (chimney height) affects tuning

2. **Two-vent systems**: 
   - Exact positions of primary and secondary register vents on professional bass clarinets (Selmer Privilege, Buffet Prestige, Yamaha YCL-821 II)
   - How the second vent improves the 3rd register (5th harmonic)?
   - Mechanism: is the second vent always open? Toggled by a thumb key? Both?

3. **Quantitative relationship**: Given a bass clarinet of total length L:
   - Register hole position P (mm from reed) as function of L
   - Register hole diameter D as function of bore diameter
   - Expected 12th interval error (±cents) as function of (P, D) deviation from optimum
   - How to compute optimal (P, D) using the cutoff frequency gradient method

4. **Is the register hole position on a bass clarinet exactly 1/3 L?** Or is it adjusted to compensate for:
   - Bell flare effects at low frequencies
   - Mouthpiece compliance
   - The U-bend perturbation
   - Tonehole lattice effects

5. **Direct application to our problem**: 
   - Our bass clarinet: bore 25mm, total length ~1500-1800mm
   - Compute: optimal register hole position in mm from reed
   - Compute: optimal register hole diameter
   - Compute: expected 12th tuning error with these values
   - Compute: is a second vent beneficial and where?

## Literature References
Please cite specific papers, equations, and measured values. We need numbers, not general principles.

## Target
Give us the mathematical design equations and a worked example for our specific dimensions.
