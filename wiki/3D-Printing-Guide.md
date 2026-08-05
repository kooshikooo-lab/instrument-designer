# 3D Printing Guide

> Research-backed additions from `docs/RESEARCH_design_to_finished_instrument.md` (2026-08-05): the pipeline below matches published practice (MIT 3D-printed flute, Diegel SLS saxophone, Ernoult one-day design→print→feedback loop).

## Recommended Process

**SLA (resin) printing** is strongly recommended for acoustic instruments. FDM layer lines create turbulence that degrades tone quality. For instruments with **moving mechanisms** (keys, springs, pivots), consider **SLS nylon** instead — it is tougher than resin and is how the Diegel 3D-printed alto saxophone (41 components, printed + assembled) was made.

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

## Pipeline Research Notes (2026-08-05)

Full detail: `docs/RESEARCH_design_to_finished_instrument.md`.

- **Mesh repair before slicing:** export STL, then run a repair/heal gate (candidates: pymeshlab, pymeshfix, admesh) so the slicer and `stl_verifier.py` always see a watertight, manifold mesh. Not yet adopted — any adoption requires the `docs/TOOLS.md` registry protocol.
- **Tonehole chamfers/undercuts** are an acoustic decision, not cosmetic — published flute/recorder reprints tune hole edges deliberately.
- **Bore reaming with a tapered reamer + gauge** is the single highest-leverage finishing step: the measured bore radius vs. the design radius is what the acoustics assumes.
- **Acoustic pulse reflectometry (APR):** reconstruct the printed bore from a pressure measurement to verify it matches the design after reaming — the strongest QA step for "finished" instruments.
- **Clear UV coating / epoxy bore seal** on SLA bores closes micro-porosity and improves moisture resistance (flutes get wet).
