# Acoustics Research: Register Hole Physics & TMM Limitations

## The Problem
We built a TMM (Transfer Matrix Method) model of a Bb bass clarinet. The 1st register (chalumeau) works well — we get correct fundamental frequencies and can optimize tonehole positions for even intonation.

However, the 2nd register (clarino, register hole open) fails: the TMM predicts ~5:1 frequency ratio instead of the correct 3:1 (12th).

## Our Setup
- Tube: 1171mm, 25mm bore, closed-top (reed end)
- Toneholes: 7 at positions 180, 300, 346, 455, 545, 624, 652mm from reed, 11mm dia
- Register hole: at 279mm, 3.5mm dia × 3mm chimney
- All holes open in Bordeaux method (bottom-to-top)

## What We Expected
With register hole OPEN:
- Fundamental (1st harmonic) ≈ 73 Hz should be suppressed
- 3rd harmonic ≈ 3 × 73 = 219 Hz should ring (this is the 12th = 2nd register)

## What We Got
- TMM find_resonance(n_register=3) gives 384 Hz (ratio ~5.25:1)
- This is close to the 5th harmonic, not the 3rd
- Register hole diameter sensitivity: 2.5-6mm all give 4.0-5.25:1 ratios (never 3:1)

## Possible Explanations

### A. Linear TMM is insufficient
Szwarcberg (2024) argues that nonlinear losses in the register hole are the decisive physical phenomenon for second register production. The register switch may be a nonlinear bifurcation that linear impedance can't predict. In this case we should:
- Design register hole using linear impedance to make the 2nd register well-tuned (optimize impedance peaks with register open)
- Trust that nonlinear physics will cause the correct register to speak

### B. Our register hole is too small/different from real instruments
On a soprano clarinet (Buffet Crampon Festival), the register tube is 13mm long × 3mm diameter. This is a TALL narrow chimney. On our bass clarinet we used 3mm × 3.5mm — very short. Should the bass clarinet register hole also be a tall chimney (like 8-13mm long)? A taller chimney changes the shunt impedance and might produce different behavior.

### C. Wrong position
We placed the register hole at 279mm (23.8% of tube length). The 3rd harmonic pressure node is at L/3 = 390mm. If the hole is too far from the node, it disturbs the 3rd harmonic too much. Debut et al. found optimum near 21% of effective length (including mouthpiece). Maybe our 23.8% is off?

### D. Tonehole lattice interferes
We have a tonehole at 300mm — only 21mm from the register hole at 279mm. Two small holes close together might create a combined acoustic load that changes the effective impedance.

### E. TMM find_resonance searching in wrong range
Our target wavelength for the 3rd harmonic is λ = c/(3×73) = 1.56m. Maybe find_resonance should search closer to 1.56m but it's finding 5th harmonic at λ = c/384 = 0.89m because the 3rd harmonic peak is weak or missing.

## Experiments Needed
1. **Single-hole test**: Remove all 7 toneholes, just test register hole alone at various positions. Does the 3:1 ratio appear?
2. **Register hole height sweep**: Try 3mm, 6mm, 10mm, 13mm chimney heights. Does a taller chimney change the ratio?
3. **Position sweep**: Test register at 200, 279, 390, 500mm. Which gives closest to 3:1?
4. **Impedance spectrum**: Plot Z(f) for the open-register case. What does the actual impedance look like? Are there clear peaks at 73, 219, 365 Hz?

## Specific Questions
1. Can linear TMM predict the register switch? If yes, what makes our model wrong?
2. Is the register hole fundamentally a nonlinear element? (Szwarcberg seems to argue yes)
3. If nonlinear, what's the minimal model that captures the physics? Time-domain simulation? Or can we still use linear impedance for optimization and trust that the nonlinear reed will select the correct register?
4. What's the correct register hole chimney height for a 25mm bore bass clarinet? The soprano uses 13mm × 3mm. Scaled by bore ratio (25/15 = 1.67): 13×1.67 = 22mm length, 3×1.67 = 5mm diameter? Or does the chimney height not scale with bore?
5. Debut et al. used r=1.5mm, h=13mm for soprano (7.5mm bore). That's a very tall skinny chimney. Why such a tall chimney? What's the acoustic function?
6. If linear TMM can handle register holes, show the correct impedance spectrum we should expect for a 1171mm tube + register hole at 279mm.

## References
- Debut, Kergomard, Laloë (2005) Applied Acoustics 66, 365-409. arXiv:physics/0309051
- Szwarcberg et al. (2024) arXiv:2404.07540
- Szwarcberg et al. (2025) arXiv:2601.01981
- Dalmont et al. (2002) — Impedance measurements of clarinet register hole
- Takahashi et al. — Role of register hole in register selection (two-delay model)
