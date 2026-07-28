# TRUMPET VALVE 3 BUG - Paste this into Claude Desktop

## Research Question
Why does pressing valve 3 on a Bb trumpet make the resonance go HIGHER instead of lower?

## Geometry (Bach 180-37 ML, meters)
Main bore segments:
- [0, 0.05, 0.003, 0.00438, 'linear']          # mouthpiece receiver
- [0.05, 0.25, 0.00438, 0.00583, 'linear']      # leadpipe taper
- [0.25, 0.75, 0.00583, 0.00583, 'linear']      # central cylinder
- [0.75, 1.335, 0.00583, 0.06112, 'bessel', 0.7] # bell flare

Valve definitions (OpenWind format: position, reconnection, radius, length):
- V1: 0.30, 0.46, 0.005, 0.16   (+160mm, whole tone)
- V2: 0.47, 0.54, 0.005, 0.07   (+70mm, semitone)
- V3: 0.55, 0.82, 0.005, 0.27   (+270mm, minor third)

## Experimental Data (OpenWind FEM results)
| Fingering | Deviation | Frequency | Expected | Correct? |
|-----------|-----------|-----------|----------|---------|
| Open      | none      | 243 Hz    | Bb3=233  | +7c     |
| V1 only   | +160mm    | 234 Hz    | Ab3      | lower ✓ |
| V2 only   | +70mm     | 240 Hz    | A3       | lower ✓ |
| V3 only   | +270mm    | 253 Hz    | G3~195   | HIGHER ✗ |
| V1+V2     | +230mm    | 232 Hz    | G3       | lower ✓ |
| V2+V3     | +340mm    | 251 Hz    | ~F3      | HIGHER ✗ |
| V1+V3     | +430mm    | 245 Hz    | ~F3      | HIGHER ✗ |
| V1+V2+V3  | +500mm    | 244 Hz    | ~E3      | HIGHER ✗ |

Key observation: Any combination involving V3 goes HIGHER than open.

## What I need
1. Why does adding 270mm of tubing via V3 raise the pitch?
2. Is this an OpenWind modeling artifact or a real physics effect?
3. How should valve deviation pipes be configured correctly?
