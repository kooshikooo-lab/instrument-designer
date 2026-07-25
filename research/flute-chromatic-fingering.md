# Chromatic Fingering Chart for Concert Flute in C (Boehm System)

## Instrument Specifications

- **Instrument**: Concert Flute in C (Boehm system)
- **Tone Holes**: 17 with ring keys, closed G# mechanism
- **Range**: C4 (261.63 Hz) to C7 (2093.00 Hz) — 3 full octaves
- **Register Mechanism**: Overblowing via embouchure + auxiliary register vents (C#_vent, trill keys). No dedicated octave key.
- **Construction**: Silver or nickel-silver tube, plateau (covered) keys, offset G (modern), split E mechanism assumed

---

## Key Mechanism Description

### Ring Key System

Most tone holes are controlled by ring keys: when a finger presses a ring, a linkage closes the corresponding hole. When the finger lifts, the hole opens. This allows multiple holes to be linked to a single finger motion. The primary linkages are:

| Mechanism | Action | Effect |
|-----------|--------|--------|
| LH1 → C + C#_main | LH1 pressed closes both C (273.3) and C#_main (262.5) | Lifting LH1 opens both C and C#_main |
| LH2 → Bb ring | LH2 ring closes Bb hole (313.2) | Opening Bb requires lifting LH2 |
| LH3 → A ring | LH3 ring closes A hole (335.0) | Opening A requires lifting LH3 |
| RH3 → F + E | RH3 ring closes F (435.3) and E (465.3) through linkage | Lifting RH3 opens both F and E |
| RH4 → foot keys | RH4 rocks to engage D# (496.5), C# foot (563.0), C foot (596.0) | Only one foot key engaged at a time |

### Closed G# Mechanism

The rear G# hole (357.0) is normally **closed** (standing position). Pressing the LH pinky key **opens** the G# hole. This is the "closed G#" (also called "plateau") system found on modern Boehm flutes. The G# key is engaged for notes G#/Ab, A, Bb, and B in all registers, and disengaged (closed) for all other notes.

### LH Thumb B Key

The LH thumb operates the B tone hole (292.5). The B key is held **closed** (thumb pressing) for every note **except B4 and B5**, where the thumb releases to open the B hole.

### Register Vent Behavior

| Register | Notes | Venting Mechanism |
|----------|-------|-------------------|
| **First** (Fundamental) | C4–B4 | All tone holes serve as primary pitch-determining vents. No auxiliary vents needed. |
| **Second** (Overblown octave) | C5–B5 | Same fingerings as first register, overblown via embouchure. C#_main acts as a register vent for D5 by opening slightly to stabilize the octave transition. |
| **Third** (High) | C6–C7 | Trill keys T1 (13.5mm at 237mm) and T2 (9.5mm at 212mm) serve as dedicated register vents. The C#_vent (5.6mm at 244.5mm) is also opened for the highest notes. Fingerings differ from lower octaves. |

The C#_vent (hole index 2, 5.6mm diameter) is a small-diameter hole positioned near the C#_main hole. Because of its small diameter, it acts as a register vent rather than a primary tone hole — it destabilizes the first register to encourage overblowing without significantly altering pitch.

---

## ASCII Diagram: Tone Hole Positions

```
Embouchure end                                                    Foot end
  |                                                                |
  ▼                                                                ▼
  ●       ●   ○   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ●   ○   ●   ●   ○
  |       |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
  T2      T1  Cv  Cm  C   B   Bb  A   G#  G   F#  F   E   Eb  D   C#f Cf
 212     237 245 263 273 293 313 335 357 381 408 435 465 497 530 563 596

Legend:
  T2      = Trill key 2            (9.5 mm)     — register vent (3rd octave)
  T1      = Trill key 1           (13.5 mm)    — register vent (3rd octave)
  Cv      = C# register vent       (5.6 mm)    — register vent
  Cm      = C# main key            (9.5 mm)    — primary vent for C#/D
  C       = LH index C key        (13.5 mm)    — LH1
  B       = LH thumb B key        (13.5 mm)    — LHT (closed for all notes except B4/B5)
  Bb      = LH ring Bb key        (13.5 mm)    — LH2
  A       = LH ring A key         (13.5 mm)    — LH3
  G#      = Rear G# key           (13.5 mm)    — LH pinky (closed standing, press to open)
  G       = RH index G key        (14.4 mm)    — RH1
  F#      = RH middle F# key      (14.4 mm)    — RH2
  F       = RH ring F key         (14.4 mm)    — RH3 (linked to E hole)
  E       = Foot E key            (14.4 mm)    — opens automatically when RH3 lifts
  Eb      = Foot D#/Eb key        (14.4 mm)    — RH4 (rocked back)
  D       = Foot C# key           (15.8 mm)    — RH4 (also called the "C# roller")
  C#f     = Foot C# key           (15.8 mm)    — RH4 (middle position)
  Cf      = Foot C key            (15.8 mm)    — RH4 (rocked forward)

  ● = hole closed (key pressed or covered)
  ○ = hole open (key released or uncovered)
```

Numbers below holes are distances from embouchure center in millimetres (Boehm Design XVI specification).

---

## Fingering Notation

Each row uses this convention:

**Fingering Description**: Prose specifying which fingers press keys and which lift.

**Open Holes**: List of open tone holes using these labels:
- `T1`, `T2` = trill keys
- `Cv` = C# register vent
- `Cm` = C# main body key
- `C` = LH index C key
- `B` = LH thumb B key
- `Bb` = LH ring Bb key
- `A` = LH ring A key
- `G#` = rear G# key (right of A)
- `G` = RH index G key
- `F#` = RH middle F# key
- `F` = RH ring F key
- `E` = foot E key
- `Eb` = foot D#/Eb key
- `D` = foot C# key
- `C#f` = foot C# key
- `Cf` = foot C key

**Register**: Fundamental (1st), Second (overblown 1st), or Third (high, with vent keys).

---

## Chromatic Fingering Chart

### First Octave — Fundamental Register (C4 to B4)

| Note | Frequency (Hz) | Fingering Description | Open Holes | Register |
|------|---------------|----------------------|------------|----------|
| C4 | 261.63 | All holes closed. LH thumb B pressed. C foot key pressed. | None | Fundamental |
| C#4 | 277.18 | C#_main open via separate C# touchpiece. LH thumb B pressed, LH1 pressed (C closed), LH2 pressed, LH3 pressed, G# closed, RH1–3 pressed, C foot key pressed. | Cm | Fundamental |
| D4 | 293.66 | LH1 lifted (C + C#_main open). LH thumb B pressed. LH2–3 pressed. G# closed. RH1–3 pressed. Foot keys open. | Cm, C | Fundamental |
| Eb4 | 311.13 | LH1 lifted, LH2 lifted (Bb opens via ring). LH thumb B pressed. LH3 pressed. G# closed. RH1–3 pressed. | Cm, C, Bb | Fundamental |
| E4 | 329.63 | LH1 lifted, LH2 lifted, LH3 lifted (A opens via ring). LH thumb B pressed. G# closed. RH1–3 pressed. | Cm, C, Bb, A | Fundamental |
| F4 | 349.23 | LH1–3 lifted. RH1 lifted (G opens). LH thumb B pressed. G# closed. RH2–3 pressed. | Cm, C, Bb, A, G | Fundamental |
| F#4 | 369.99 | LH1–3 lifted. RH1–2 lifted (G, F# open). LH thumb B pressed. G# closed. RH3 pressed. | Cm, C, Bb, A, G, F# | Fundamental |
| G4 | 392.00 | LH1–3 lifted. RH1–3 lifted (G, F#, F open; E opens via RH3–E linkage). LH thumb B pressed. G# closed. | Cm, C, Bb, A, G, F#, F, E | Fundamental |
| G#4 | 415.30 | LH1–3 lifted. RH1–3 lifted. G# opened (LH pinky pressed, opens rear G# hole). LH thumb B pressed. | Cm, C, Bb, A, G#, G, F#, F, E | Fundamental |
| A4 | 440.00 | LH1–3 lifted. RH1–3 lifted. G# open. Eb/D# opened (RH4 rocked back). LH thumb B pressed. | Cm, C, Bb, A, G#, G, F#, F, E, Eb | Fundamental |
| Bb4 | 466.16 | **Long Bb**: LH1–2 lifted (C, C#_main, Bb open). LH3 pressed (A closed). G# open. RH1 pressed (G closed). RH2 lifted (F# open). RH3 pressed (F, E closed). LH thumb B pressed. | Cm, C, Bb, G#, F# | Fundamental |
| B4 | 493.88 | LH thumb B **open** (released). LH1 pressed (C, C#_main closed). LH2 open (Bb open). LH3 open (A open). G# open. RH1 pressed (G closed). RH2 open (F# open). RH3 pressed (F, E closed). | B, Bb, A, G#, F# | Fundamental |

### Second Octave — Overblown Register (C5 to B5)

Second-octave notes use the same fingerings as the first octave, overblown via embouchure change. The embouchure is tightened and the airstream directed higher across the embouchure hole to excite the second harmonic (octave).

| Note | Frequency (Hz) | Fingering Description | Open Holes | Register |
|------|---------------|----------------------|------------|----------|
| C5 | 523.25 | Same fingering as C4, overblown. All holes closed, LH thumb B pressed, C foot key pressed. | None | Second |
| C#5 | 554.37 | Same as C#4, overblown. C#_main open, all else closed. C foot key pressed. | Cm | Second |
| D5 | 587.33 | Same as D4, overblown. C#_main and C open. C#_main functions as a register vent to stabilize the octave. | Cm, C | Second |
| Eb5 | 622.25 | Same as Eb4, overblown. | Cm, C, Bb | Second |
| E5 | 659.25 | Same as E4, overblown. | Cm, C, Bb, A | Second |
| F5 | 698.46 | Same as F4, overblown. | Cm, C, Bb, A, G | Second |
| F#5 | 739.99 | Same as F#4, overblown. | Cm, C, Bb, A, G, F# | Second |
| G5 | 783.99 | Same as G4, overblown. | Cm, C, Bb, A, G, F#, F, E | Second |
| G#5 | 830.61 | Same as G#4, overblown. | Cm, C, Bb, A, G#, G, F#, F, E | Second |
| A5 | 880.00 | Same as A4, overblown. | Cm, C, Bb, A, G#, G, F#, F, E, Eb | Second |
| Bb5 | 932.33 | Same as Bb4 (long Bb), overblown. | Cm, C, Bb, G#, F# | Second |
| B5 | 987.77 | Same as B4, overblown. LH thumb B open, LH1 pressed, LH2–3 open, G# open, RH1 pressed, RH2 open, RH3 pressed. | B, Bb, A, G#, F# | Second |

### Third Octave — High Register (C6 to C7)

Third-octave fingerings deviate from the lower octaves. Trill keys (T1, T2) and the C#_vent (Cv) are pressed into service as register vents. Fingerings vary between manufacturers; the chart below gives widely-accepted standard fingerings.

| Note | Frequency (Hz) | Fingering Description | Open Holes | Register |
|------|---------------|----------------------|------------|----------|
| C6 | 1046.50 | C5 fingering (all holes closed, LH thumb B pressed) + T1 trill key open as register vent. | T1 | Third |
| C#6 | 1108.73 | C#5 fingering + T1 open. LH1 pressed (C, C#_main closed via C# touch is possible). Often fingered: LH1 pressed, LH2 open, LH3 open, G# open, RH1 pressed, RH2 open, RH3 pressed, T1 open. | T1, Bb, A, G#, F# | Third |
| D6 | 1174.66 | LH1 open (C, C#_main open), LH2 pressed, LH3 open, G# open, RH1 pressed, RH2 open, RH3 pressed, T1 open. | T1, Cm, C, A, G#, F# | Third |
| Eb6 | 1244.51 | LH1 open, LH2 open (Bb open), LH3 open, G# open, RH1 pressed, RH2 open, RH3 open, T1 + T2 open. | T1, T2, Cm, C, Bb, A, G#, F#, F | Third |
| E6 | 1318.51 | LH1–3 open, G# open, RH1 pressed, RH2 open, RH3 open, T1 open. | T1, Cm, C, Bb, A, G#, F#, F | Third |
| F6 | 1396.91 | LH1 pressed, LH2 open, LH3 open, G# open, RH1 pressed, RH2 open, RH3 pressed, T1 + T2 open. | T1, T2, Bb, A, G#, F# | Third |
| F#6 | 1479.98 | LH1–3 open, G# open, RH1–3 open, T1 + T2 open, C#_vent open. | T1, T2, Cv, Cm, C, Bb, A, G#, G, F#, F, E | Third |
| G6 | 1567.98 | LH1–3 open, G# open, RH1–3 open, T1 + T2 open. | T1, T2, Cm, C, Bb, A, G#, G, F#, F, E | Third |
| G#6 | 1661.22 | LH1–3 open, G# open, RH1–3 open, T1 + T2 open, C#_vent open. | T1, T2, Cv, Cm, C, Bb, A, G#, G, F#, F, E | Third |
| A6 | 1760.00 | LH1–3 open, G# open, RH1 open, RH2 pressed (F# closed), RH3 open, T1 + T2 open. | T1, T2, Cm, C, Bb, A, G#, G, F | Third |
| Bb6 | 1864.66 | LH1 open, LH2 pressed (Bb closed), LH3 open, G# open, RH1 pressed (G closed), RH2 open, RH3 pressed (F closed, E closed), T1 + T2 open. | T1, T2, Cm, C, A, G#, F# | Third |
| B6 | 1975.53 | LH thumb B open, LH1 pressed, LH2 open, LH3 open, G# open, RH1 pressed, RH2 open, RH3 pressed, T1 + T2 open. | T1, T2, B, Bb, A, G#, F# | Third |
| C7 | 2093.00 | All main body holes closed. LH thumb B pressed. LH1 pressed, LH2 pressed, LH3 pressed, G# closed, RH1–3 pressed. T1 + T2 open as register vents. | T1, T2 | Third |

---

## Alternative Fingerings for Tricky Notes

### High C (C6, C7)

| Note | Alternative | Fingering | Use Case |
|------|-----------|-----------|----------|
| C6 | T1-only | Standard from chart above | General use |
| C6 | C#-vent | All closed + LH1 half-hole (C#_vent acts as mini-vent) | Smooth entrance from below |
| C7 | No trills | All closed + embouchure only (no T1/T2) | pp dynamics, some instruments |
| C7 | T1 + T2 + Cv | All closed + T1 + T2 + C#_vent open | Better stability on some flutes |

### F# (F#4, F#5, F#6)

| Note | Alternative | Fingering | Use Case |
|------|-----------|-----------|----------|
| F#4 | Forked | LH1 open, LH2 pressed, LH3 open, G# closed, RH1 pressed, RH2 open, RH3 pressed | When G# key is problematic |
| F#4 | Standard | LH1–3 open, RH1–2 open, RH3 pressed (from chart) | General use |
| F#5 | Forked | Same as F#4 forked, overblown | pp passages |
| F#6 | Short | LH1 pressed, LH2 open, LH3 open, G# open, RH1 pressed, RH2 open, RH3 pressed, T1 only (no T2) | Quieter alt., better intonation on some flutes |

### Bb (Bb4, Bb5)

| Note | Alternative | Fingering | Use Case |
|------|-----------|-----------|----------|
| Bb4 | Long Bb | LH1–2 open, LH3 pressed, G# open, RH1 pressed, RH2 open, RH3 pressed (from chart) | Standard, best intonation |
| Bb4 | Short Bb | LH1–2 open, LH3 pressed, G# open, RH1 pressed, RH2 pressed, RH3 pressed | Faster technique, slightly flat |
| Bb4 | Side Bb | LH1–2 open, LH3 pressed, G# open, RH1–3 pressed + side Bb lever (RH thumb or side key) | Trills between Bb and B, or Bb and A |
| Bb4 | 1-and-1 Bb | LH1 open, LH2 pressed, LH3 open, G# open, RH1 pressed, RH2 open, RH3 pressed | Weak but usable alt. |
| Bb5 | Same options | Overblown versions of the above | Same trade-offs |

### B4

| Alternative | Fingering | Use Case |
|-----------|-----------|----------|
| Standard (chart) | LH thumb open, LH1 pressed, LH2 open, LH3 open, G# open, RH1 pressed, RH2 open, RH3 pressed | General use |
| Open B | LH thumb open, LH1–3 open, G# open, RH1–3 open (all open) + embouchure | Brighter tone, used in jazz/pop |
| Half-hole B | LH thumb open, LH1 half-covered, LH2–3 open, G# open, RH1–3 open | Smoother transition from Bb4 |

---

## Summary of Key Rules

1. **LH thumb B key** is closed (pressed) for all notes except B4 and B5.
2. **C# body key** (Cm) is linked to LH1 — opens when LH1 lifts. A separate C# touch allows opening Cm independently while keeping LH1 pressed (for C#4, C#5).
3. **G# key** is normally **closed** (standing closed). Press LH pinky to **open** it. G# is open for G#/Ab, A, Bb, and B. Closed for all other notes.
4. **Foot keys** (C foot, C# foot, D# foot) are used only for the lowest notes (C4–A4 range). They are open (unpressed) for all other notes.
5. **Second register** (C5–B5) uses identical fingering to the first register; overblowing is achieved entirely through embouchure adjustment and increased air speed.
6. **Third register** (C6–C7) requires modified fingerings with trill keys (T1, T2) and C#_vent opened as auxiliary register vents.
