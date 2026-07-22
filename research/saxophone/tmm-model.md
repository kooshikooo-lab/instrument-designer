# TMM Model — Phase Convention and Register Mapping

## Phase Convention in `tmm_acoustics.py`

```python
def pipe_reply_phase(phase_end: float, length_on_wavelength: float) -> float:
    return phase_end + length_on_wavelength * 2.0
```

**Critical**: The factor of 2.0 means `length_on_wavelength` is actually `L/λ`, and the returned phase is `phase_end + 2L/λ`.

## Open-Open Tube (Saxophone Model)

With `closed_top=False` (both ends open):
- Mouthpiece end phase: 0.5
- Bell end phase: += 0.5
- Total phase: `1 + 2L/λ`

Resonance occurs at integer values of the total phase:
```
1 + 2L/λ = n
2L/λ = n - 1
λ = 2L / (n - 1)
f = c(n - 1) / (2L)
```

## Register Mapping

| n_register | Phase n | Frequency | Musical Meaning |
|---|---|---|---|
| 1 | 1 | DC (f=0) | Not physical |
| 2 | 2 | `c/(2L)` | Fundamental (1st register) |
| 3 | 3 | `c/L` = `2 × c/(2L)` | 2nd harmonic / Octave key |
| 4 | 4 | `3c/(2L)` = `3 × c/(2L)` | 3rd harmonic / 12th |

**For saxophone 2nd register (octave key): use `n_register=3`**

## Verification

All-closed bore at L=991mm, r=8.5mm:
```
n_register=1: f=77.3Hz   (DC-like, not physical)
n_register=2: f=173.5Hz  (fundamental, ~-1211c from 349Hz target)
n_register=3: f=347.2Hz  (2nd harmonic, -10c from 349Hz target) ← CORRECT
n_register=4: f=520.7Hz  (3rd harmonic)
```

## Clarinet vs Saxophone

| Property | Clarinet | Saxophone |
|---|---|---|
| Bore shape | Cylindrical | Conical (approx) |
| closed_top | True (reed closed) | False (conical → open-open) |
| Harmonics | Odd only (1st, 3rd, 5th...) | All (1st, 2nd, 3rd...) |
| n_register for 2nd | n_register=4 (3rd harmonic) | n_register=3 (2nd harmonic) |

## Lefebvre (2011) — Bore Shape

> "A straight conical tube is NOT appropriate for a saxophone. Deviations from a cone are necessary for harmonicity."

For a well-designed instrument, the second resonance should be within about **10 cents** of two times the fundamental resonance frequency. The deviations found on real instruments play a role in proper harmonicity.

## Szwarcberg (2025) — Sensitivity Analysis

- Uses TMM with **analytical gradients** for saxophone optimization
- Studies soprano saxophone, optimizing octave harmonicity
- Key finding: The largest inharmonicity is at the **edges** of the register range
- Reducing register hole radius and increasing chimney height improves tuning
- The method uses first-order sensitivity analysis

## DAGA 2021 — Tone Hole Adjustment

- Uses 1D waveguide model (TMM) for tenor saxophone
- Pitch shift from chimney height increase can be compensated by 20-50% diameter increase
- Redesign is an iterative note-by-note process
- Recommends weighted average of peak deviations of first AND second impedance peaks
