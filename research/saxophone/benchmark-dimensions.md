# Alto Saxophone Benchmark — Verified Dimensions

## Source: Cults3D 3D-Printable Alto Saxophone (Bb, ~450mm)

This is a simplified 3D-printable design with verified playable dimensions.
Tuned to Bb (fundamental Bb3 ≈ 116.5 Hz). Uses alto sax mouthpiece.

### Bore
- Mouthpiece End OD: 24.2mm (fits standard alto sax mouthpiece)
- Bell End ID: 40mm
- Total Length: 450mm (including mouthpiece neck)
- Taper: 1:25 (1mm diameter increase per 25mm length)
- Wall Thickness: 2mm

### Tone Hole Positions (from mouthpiece end)
| Hole | Position (cm) | Diameter (mm) | Notes |
|------|--------------|---------------|-------|
| 6 (highest) | 8-11 | 6-8 | Upper holes |
| 5 | 12-15 | 6-8 | Upper holes |
| 4 | 16-19 | 6-8 | Upper holes |
| 3 | 20-23 | 7-9 | Lower holes |
| 2 | 24-27 | 7-9 | Lower holes |
| 1 (lowest) | 28-32 | 7-9 | Lower holes |

### Bell
- Inner Diameter: 40-45mm
- Flare: 10-15mm wider than bore

---

## Source: Postma's Measured Dimensions (Modern Alto Sax)

From sax.mpostma.nl — actual measurements of production instruments.

### Key Ratios
- **Average alto conicity**: 1:18.0 (1mm diameter per 18mm length)
- **Tone hole ratio** (hole area / bore area): 25-40%
- **Truncated volume**: ~16cc (modern) vs ~20cc (vintage)
- **10% diameter reduction** ≈ **10 cents flattening**

### Tone Hole Numbering (Postma convention)
- Hole #1: Bottom (plays written Bb-B)
- Hole #6: Third finger right hand (plays written E-F)
- Holes #22-25: Palm keys and high F#
- Register holes: #23, #24

### Key Observations
1. Tone holes get **proportionally smaller** higher up the instrument
2. Closed tone holes (#3, #5, #11) have **built-in cross-fingering corrections** — the next higher hole is relatively larger
3. The C# hole (#18) is intentionally small due to intonation problems
4. Palm key holes have shifted downward and enlarged over time
5. "A saxophone is not a precision instrument" — 10% deviation is within embouchure control

---

## Source: Selmer Series II Alto (Ukshini & Dirckx, 2025)

Measured with probe microphone through bore.

- **Overall length**: ~1050mm (following center bore)
- **Bell diameter**: 120mm
- **Measurement precision**: >0.1mm (stepper motor translation)
- Notes measured: D3 through C#5 (first register)

---

## Source: Yamaha YAS-280 (Student Model)

- Key: Eb
- Bell: Two-piece
- Auxiliary Keys: High F#, Front F
- Neck: 280 style
- Mouthpiece: 4C
- Known for "excellent intonation" in student category

---

## Source: Szwarcberg (2025) — Soprano Sax Reference Model

Complete TMM model with measured dimensions.

### Geometry
- **Input radius (R1)**: 4.6mm
- **Half-angle (ϕ)**: 1.74°
- **Cylindrical mouthpiece length (Lcyl)**: fixed to match missing cone volume

### Register Holes
| Hole | Radius (mm) | Chimney (mm) | Position L1 (mm) | Notes |
|------|------------|-------------|-----------------|-------|
| Upstream | 0.85 | 4.0 | 40 | For A4-F#5 |
| Downstream | 1.4 | 4.0 | 130 | For Bb3-G#4 |

### Key Findings
- Largest inharmonicity at **edges** of 2nd register range
- Reducing register hole radius and increasing chimney height **improves tuning**
- Downstream hole: decreasing Rh by 0.1mm lowers inharmonicity by ~3.4 cents (for D4/D5)
- Upstream hole: increasing Lh by 1mm reduces inharmonicity by ~4 cents (for A4/A5)

---

## Source: DAGA 2021 — Wooden Saxophone Redesign

Jupiter JTS-789 tenor saxophone measured via CT scan.

### Key Findings
- Metal sax wall thickness: ~0.7mm
- Wooden sax wall thickness: ~6mm (minimum)
- Chimney height increase of 6mm can be compensated by **20-50% diameter increase**
- Tone hole ratio δ = b/r:
  - Normal saxophone: 0.54 (±0.08)
  - Wooden saxophone: 0.75 (±0.13)
- Original tone hole **positions should be shifted** toward mouthpiece for wooden design

---

## Implications for Our TMM Model

### Critical Bug Found
Our theory positions used `c / (2.0 * freq)` which gives the **fundamental register** position.
For n_register=3 (2nd harmonic / octave key), positions should be `c / freq`.

### Correct Theory Positions (for 2nd harmonic)
| Note | Freq (Hz) | Position from mouthpiece (mm) |
|------|-----------|------------------------------|
| E5 | 392 | c/392 = 883 |
| F5 | 415 | c/415 = 834 |
| G5 | 466 | c/466 = 742 |
| A5 | 523 | c/523 = 662 |
| B5 | 587 | c/587 = 589 |

### What Real Alto Saxophones Tell Us
1. **Bore is NOT a straight cone** — neck narrows, bell flares
2. **Tone hole sizes vary** — not uniform; smaller higher up, corrections for cross-fingerings
3. **Chimney height matters** — ~0.7mm (metal) vs ~6mm (wood) dramatically affects tuning
4. **Register hole placement** is critical — must align with pressure nodes of 2nd mode
5. **Mouthpiece volume** compensates for truncated cone — typically ~16cc for alto
