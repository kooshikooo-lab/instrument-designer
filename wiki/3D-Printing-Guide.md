# 3D Printing Guide

## Recommended Process

**SLA (resin) printing** is strongly recommended for acoustic instruments. FDM layer lines create turbulence that degrades tone quality.

## Material

| Material | Pros | Cons | Use Case |
|----------|------|------|----------|
| **Standard Resin** | Cheap, easy to print | Brittle, yellowing | Prototyping |
| **Engineering Resin** (e.g., Siraya Tech Blu) | Strong, durable, food-safe options | More expensive | Final instruments |
| **ABS-like Resin** | Impact resistant, good surface finish | Moderate cost | Good all-around |
| **Water-washable Resin** | Easy post-processing, no IPA needed | Less durable | Quick prototypes |

## Print Settings

| Parameter | Recommended | Notes |
|-----------|-------------|-------|
| Layer Height | 25-50 µm | Thinner = smoother bore surface |
| Exposure Time | Per resin spec | Over-exposure widens bore |
| Lift Speed | Slow (1-2 mm/s) | Reduces warping on long bores |
| Orientation | Vertical (bore axis vertical) | Minimizes supports inside bore |
| Support Type | Light, external only | No supports inside bore |

## Post-Processing

1. **IPA wash** — 3-5 minutes in 99% IPA
2. **UV cure** — 10-15 minutes at 405nm
3. **Bore reaming** — Use a reamer or drill bit to clean bore interior
4. **Sanding** — 400-800 grit for bore surface finish
5. **Sealing** — Optional: thin coat of clear resin or lacquer for airtightness

## Multi-Part Prints

Long instruments (bass clarinet, baritone sax) may need to be printed in sections:
- Print sections with registration features (tongue-and-groove or pin joints)
- Join with epoxy or cyanoacrylate
- Verify bore continuity after joining

## Tolerance Compensation

SLA printing tolerance is ±0.05-0.1mm. For acoustic accuracy:
- **Bore diameter:** Scale down by 0.1-0.2mm (compensate for resin shrinkage)
- **Hole diameter:** Scale up by 0.1-0.2mm (holes shrink more than bores)
- **Bore length:** Scale up by 0.1-0.3% (axial shrinkage)

## Acoustic Validation

After printing, validate with impedance measurement:
- Compare designed vs measured resonance frequencies
- Typical deviation: 5-15 cents (manufacturing is the bottleneck, not computation)
- See [[Internal-Research-Measurement]] for measurement techniques
