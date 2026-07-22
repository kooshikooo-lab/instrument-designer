# Intonation Tolerance — What's Acceptable?

## Design Target: ±5 cents

From Lefebvre thesis (2010):
> "We believe that the tuning of an instrument should have a general accuracy of **±5 cents**."

The smallest detectable frequency difference is ~8 cents at 200Hz, ~3 cents at 1kHz (Hartmann, 1996). Professional musicians demand high accuracy.

## Real-World Instrument Performance

### Saxophone
- **Professional horns as-received**: 25-30 cents range (saxontheweb.net forum)
- **After professional setup**: 10-15 cents range (key height, tone hole mods)
- **"Excellent" horns**: 5-10 cents variance
- **Larry Teal study (1943)**: -10c (low Eb) to +16c (high C#) for alto
- **YAS-875EX user report**: worst note E2 sharp by ~20 cents

### Clarinet
- **Good instrument**: generally within 5 cents (woodwind.org forum)
- **Acceptable range**: ±5-10 cents
- **Normal for many clarinets**: ±20 cents (correctable with embouchure)
- **Clark Fobes**: "A ten cent spread between the twelfths is very acceptable"
- **Professional setup goal**: 3-5 cents

### Chinese National Standard (QB/T 1947.1-2026)
- Edge-blown/double reed: ≤ ±15 cents, adjacent difference ≤ 10 cents
- Free reed: ≤ ±10 cents, adjacent difference ≤ 5 cents

## Perception Thresholds

| Deviation | Perception |
|---|---|
| < 5 cents | Barely detectable by trained listeners |
| 5-10 cents | Noticeable with focused listening |
| 10-20 cents | Clearly audible to most listeners |
| > 20 cents | "Huge difference" — obvious to everyone |

### Key findings from research:
- **Seashore (1938)**: 80% accurate at detecting 12 cents
- **Parker (1983)**: Accurate to ~20 cents for sequential tones
- **Karrick (1998)**: Set 6 cents as threshold for "in tune"
- **Byo et al. (2011)**: 5 cents as threshold for "in tune"
- **Clark (2012 dissertation)**: 7.5-10 cents reliably discriminable
- **Vos (1982)**: 20-25 cents identification threshold for intervals

## What This Means for Our Optimization

### Our current results: 61.6 cents evenness
This is **way outside acceptable range**. A well-made saxophone should be within 10-15 cents.

### Optimization targets:
1. **Minimum viable**: < 15 cents evenness (acceptable amateur instrument)
2. **Good**: < 10 cents evenness (professional quality)
3. **Excellent**: < 5 cents evenness (top-tier professional)

### Important notes from literature:
1. **No instrument is perfectly in tune** — all have inherent pitch tendencies
2. **Player compensation** is expected — embouchure, voicing, alternate fingerings
3. **Register differences** are normal — clarinet's twelfths inherently cause issues
4. **Setup matters** — pad height, cork thickness, mouthpiece selection all affect tuning
5. **Context matters** — just intonation vs equal temperament (up to 14 cents difference for major thirds)

### For our TMM model:
- The model's accuracy limit is ~10 cents (Lefebvre thesis)
- Our 61.6c result suggests either model error or incorrect fingering/n_register
- Need to verify the TMM implementation matches expected behavior
