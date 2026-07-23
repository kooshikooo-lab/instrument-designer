# Saxophone Fingering Convention

## Source Confirmation

The fingering convention was confirmed by multiple independent sources:
- **WFG (Web Fingering Guide)** — Academic fingering database
- **Tunable** — Saxophone tuner app
- **SaxTeacher UK** — Beginner teaching resource
- **UNSW Acoustics** — School of Physics, University of New South Wales

## Convention

### Going DOWN in pitch (closing holes):
Start from the all-open position (highest note, C#5/C#6 written). Add fingers **from the mouthpiece end** (lowest array index), closing holes one at a time going toward the bell.

### Going UP in pitch (opening holes):
Open holes **from the bell end** (highest array index), going toward the mouthpiece.

## Array Mapping

```python
fingering = [hole_1, hole_2, hole_3, hole_4, hole_5, hole_6]
#              ^mouthpiece-end           bell-end^
```

- `fingering[0]` = hole closest to mouthpiece
- `fingering[5]` = hole closest to bell

## Target Notes (Written / Concert)

| Note (Written) | Concert | Frequency (Hz) | Fingering Array |
|---|---|---|---|
| D5 | F4 | 349.2 | `['closed','closed','closed','closed','closed','closed']` |
| E5 | G4 | 392.0 | `['closed','closed','closed','closed','closed','open']` |
| F5 | Ab4 | 415.3 | `['closed','closed','closed','closed','open','open']` |
| G5 | Bb4 | 466.2 | `['closed','closed','closed','open','open','open']` |
| A5 | C5 | 523.3 | `['closed','closed','open','open','open','open']` |
| B5 | D5 | 587.3 | `['closed','open','open','open','open','open']` |

### Notes NOT Used (Cross-fingerings)
- C5 (concert Eb4, 311Hz) — Only hole 2 closed: `['closed','open','closed','closed','closed','closed']`
- C#5 (concert D4, 293Hz) — All holes closed: `['closed','closed','closed','closed','closed','closed']`
- C6 (concert Eb5, 622Hz) — Cross-fingering breaking cumulative pattern

These are excluded from optimization because they don't follow the cumulative pattern.

## Chromatic Notes

The saxophone is chromatic — additional side keys and pinky keys exist between the 6 main holes:
- Side keys: Bb, C, high E (side of instrument, operated by right hand)
- Palm keys: D, Eb, F, F# (top of instrument, operated by left hand)
- Pinky keys: G#, C#, B, Bb (table keys, operated by left pinky)

These are not modeled in the current optimization but would be needed for a complete instrument simulation.
