# Research: TMM Tonehole Model Validation
## Goal: Understand the phase-based TMM model and validate it for bass clarinet at 70-150Hz

## Context
We are using the phase-based TMM from `backend/tmm_acoustics.py` (ported from chalumier/demakein). 
The core math uses a "tanner/untanner" transformation:
- `tanner(phase) = tan(π * phase)` 
- `untanner(x) = atan(x) / π`
- Junction3 formula: `untanner(a1/a0 * tanner(p1-s1) + a2/a0 * tanner(p2-s2)) + s1 + s2`
- Open hole phase: `-0.5 + 2*L_hole/λ`
- Closed hole phase: `0.0 + 2*L_hole/λ`

## Observed Behavior
1. With 11mm holes on 25mm bore, 1st register (n_register=1) gives UNIFORM offset (~-78c) for all notes
2. With 20mm holes, 1st register gives NON-UNIFORM errors (varying from -85c to -12c)
3. With 11mm holes, 2nd register (n_register=2) gives NON-UNIFORM errors (7.96c RMS)
4. At very low frequencies (λ >> L_hole), the open hole phase approaches -0.5, which in the tan domain approaches tan(-π/2) → -∞

## Questions
1. What does `tanner(phase)` represent physically? Is it Z/j (normalized reactance), the reflection coefficient phase, or something else?
2. Is the junction3 formula correctly modeling parallel impedance combination at a 3-port junction?
3. Why does the open hole at low freq produce ~-0.5 phase shift? Is this physically correct?
4. What is the cut-off frequency below which the open hole model loses accuracy?
5. How does the chalumier reference handle this? Is there a low-frequency correction?
6. For a bass clarinet with 25mm bore and 11mm holes, what is the expected Q factor of the open-hole vent at 70Hz? At 150Hz?
7. Should we use graduated hole sizes (small near reed, large near bell)?

## References to Check
- Keefe, D.H. (1982). "Acoustical wave propagation in cylindrical ducts: Transmission line parameter approximations for isothermal and nonisothermal boundary conditions." JASA.
- Nederveen, C.J. (1969, 1998). "Acoustical Aspects of Woodwind Instruments."
- Benade, A.H. (1976). "Fundamentals of Musical Acoustics."
- Dalmont, J.P. et al. "Time domain simulation of clarinet." 
- chalumier source: https://github.com/demakein/chalumier
