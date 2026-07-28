# Bass Clarinet Bell Harmonic Distortion

## Problem
Our TMM model shows that adding a realistic bell flare (160-220mm length, 44-52mm ID) to the bass clarinet distorts the 12th interval by 40-400 cents. The bell lowers the fundamental (1st register) more than the 3rd harmonic (2nd register), widening the ratio from 3.0 to 3.04-3.45.

Without bell, we achieve 9.5c RMS twelfths. With bell, it degrades to 41c (quadratic, 160mm/44mm) or worse.

## Questions for Research

### Acoustic Physics
1. Is this bell-induced harmonic distortion a real effect in physical bass clarinets, or an artifact of the stepped-cylinder TMM model?
2. Real clarinets have 20-30c 12th error. How much of this comes from the bell vs toneholes vs register hole vs mouthpiece?
3. Does the open tonehole lattice reduce bell effect (since most sound exits through holes, not bell)?

### Bell Design
1. What specific bell profile (flare shape, length, exit diameter) do professional bass clarinet makers use?
2. Are there measurements of input impedance or harmonic ratios for bass clarinet bells?
3. Is there a "standard" bell profile that preserves the 12th while providing good timbre?
4. Are modern bass clarinet bells optimized by FEM to minimize harmonic distortion?

### TMM Modeling
1. Does the stepped-cylinder approximation (80 segments) overestimate bell dispersion?
2. Would OpenWind FEM give different results for the same bell profile?
3. What's the correct end radiation impedance model for a flared bell (unflanged vs flanged correction)?
4. Are viscothermal losses in the bell significant for harmonic distortion?

## Our Best Configurations
- No bell: 1171mm uniform cylinder, 9.5c twelfths
- Quadratic bell (160mm length, 44mm ID): 41c twelfths
- Bessel bell (220mm length, 52mm ID): 423c twelfths
- Short quadratic bell (80mm length, 36mm ID): ~10c predicted

## Next Step
If bell distortion is real, we may need to:
- Use a very short/minimal bell to preserve 12th
- Jointly optimize bell + register hole + toneholes for both registers
- Accept 40c 12th error as "realistic" and move to full chromatic

## Files
- `config/bass_clarinet_7hole_bell.json` - current best config with bell
- `backend/test_bell_quadratic.py` - optimization code
- `backend/tmm_acoustics.py` - TMM engine
- `backend/test_bell_refine.py` - Bessel bell test
- `research/verified-references.md` - all references

## Test Command
```bash
python backend/test_bell_quadratic.py
```
