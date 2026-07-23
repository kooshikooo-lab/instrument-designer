# Saxophone Optimization Results

## Test Script

`test_simultaneous.py` — L-BFGS-B optimization for 6-hole alto saxophone.

## Parameters

| Parameter | Value | Notes |
|---|---|---|
| n_register | 3 | 2nd harmonic (octave key) |
| OD (outer diameter) | 26.0mm | |
| HD (hole diameter) | 7.5mm | |
| HL (hole length/chimney) | 3.5mm | |
| closed_top | False | Open-open tube model |
| End correction | 0.5 | Standard flange correction |
| Targets | F4, G4, Ab4, Bb4, C5, D5 | Concert frequencies |

## Results

### Sanity Check: All-Closed Bore

L=991mm, r=8.5mm, no holes:
```
n_register=1: f=77.3Hz   (not physical)
n_register=2: f=173.5Hz  (fundamental)
n_register=3: f=347.2Hz  (2nd harmonic, -10c from 349Hz) ← CORRECT
n_register=4: f=520.7Hz  (3rd harmonic)
```

### Theory-Based Initial Positions

Hole positions derived from `c / (2 × target_freq)`:
```
['295', '300', '331', '371', '417', '441'] mm
```

Evenness: 64.4c | Abs: 156.3c | Offset: -151.9c

```
F4 (349Hz):   -14.0c
G4 (392Hz):  -140.1c
Ab4 (415Hz): -137.0c
Bb4 (466Hz): -163.7c
C5 (523Hz):  -183.3c
D5 (587Hz):  -218.2c
```

### L-BFGS-B Optimization (holes only)

Evenness: 61.6c | Abs: 148.9c | Offset: -142.0c

### Radius + Holes Optimization

r=8.5mm (unchanged), Evenness: 61.6c

### Full Optimization (radius + length + holes)

r=8.5mm, L=991mm (unchanged), Evenness: 61.6c

## Analysis

### Problem: All Notes Flat

All optimized notes are flat by 14-218c. The L-BFGS-B optimizer failed to improve over theory-based positions. Possible causes:

1. **Hole positions too close together**: Theory positions span only 295-441mm (146mm range) in a 991mm bore. This clusters holes near the mouthpiece.

2. **Cumulative fingering convention issue**: When holes open from the bell end, the effective length change per hole may be insufficient.

3. **TMM model limitations**: The 1D TMM may not capture the full effect of tone holes on a conical bore. The model uses `closed_top=False` (open-open), which is an approximation.

4. **Hole diameter/chimney height**: The default 7.5mm diameter and 3.5mm chimney may not be appropriate for saxophone. Real saxophones have larger holes (10-15mm) and taller chimneys.

### Next Steps (from literature)

1. **Lefebvre approach**: Optimize bore profile (deviations from straight cone) alongside hole positions
2. **Szwarcberg approach**: Use analytical gradients for multi-parameter optimization
3. **DAGA 2021 approach**: Match impedance peaks note-by-note, considering both first and second impedance peaks
4. **Increase hole diameter**: Try 10-15mm holes (real saxophone range)
5. **Wider hole spacing**: Space holes across more of the bore length

### Clarinet Benchmark (for comparison)

The same optimization framework achieved 4.46c evenness for clarinet with:
- 6 cumulative fingerings
- L-BFGS-B with theory-based initial positions
- Closed-open tube model (closed_top=True)
