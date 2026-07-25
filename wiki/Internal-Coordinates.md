# Coordinate Systems

## Primary Convention (Locked)

**Position 0 = bell (open end), Position L = reed/mouthpiece (closed end).**

This matches chalumier convention. All code uses this.

### Why This Convention?

- Chalumier (Kotlin demakein) uses this convention
- TMM phase walks from bell (open end) toward reed (closed end)
- Phase starts at 0.5 (open end = bell)
- Resonance when phase is integer at reed (closed end)

## Hole Index Convention

`hole[0]` = closest to bell, `hole[N-1]` = closest to reed.

```python
# 6-hole clarinet, cumulative fingerings
fingerings = [
    ["closed"] * 6,                                    # Lowest note (all closed)
    ["open", "closed", "closed", "closed", "closed", "closed"],  # hole[0] near bell opens first
    ["open", "open", "closed", "closed", "closed", "closed"],
    ...
    ["open", "open", "open", "open", "open", "closed"],  # Highest note
]
```

## Fingering Conventions

### Closed-Open (Clarinet/Bordeaux)

- **Cumulative:** All lower holes + new hole open
- **Hole placement:** Bottom-to-top (lowest note first)
- **Effective bore:** Closing holes extends effective length

### Open-Open (Sax/Flute/Ernoult)

- **Independent:** Only new hole open
- **Hole placement:** Top-to-bottom (highest note first)
- **Each hole:** Creates independent resonator

## TMM Walk Direction

1. Start at bell (position 0, phase = 0.5)
2. Walk toward reed (position L)
3. Accumulate phase through segments, steps, holes
4. At reed: resonance when phase is integer

```python
# Open-open: 0.5 (bell) + 2L/λ + 0.5 (reed) = n
# Closed-open: 0.5 (bell) + 2L/λ + 0.0 (reed) = n
```

## Speed of Sound

Standard: `SPEED_OF_SOUND = 346100.0 cm/s` (matches chalumier, ~25°C)

**Note:** Some modules use inconsistent values (343200-346100). Needs standardization.
