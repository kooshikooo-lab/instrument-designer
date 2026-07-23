# Research Findings: Saxophone Bore Optimization (2026-07-23)

## Key Papers Analyzed

### 1. Ernoult (2021) - Full Waveform Inversion for bore reconstruction
**Source**: Acta Acustica, doi:10.1051/aacus/2021038

**Critical finding for saxophone hole placement:**

Section 4.2.1: "The locations of the holes have a good degree of independence, if only fingerings with one open hole are used (xxxo, xxox, xoxx and oxxx). The location of each hole can be recovered by performing independent optimizations on the corresponding fingering (hole 4 from xxxo, hole 3 from xxox, etc.), after having first recovered the main bore length from the all closed fingering."

**Reconstruction strategy:**
1. Main bore length from all-closed fingering (xxxx)
2. Hole locations from LAST to FIRST, each with only that hole open
3. Rough estimation: ~5 seconds, 8 iterations per hole
4. Refined reconstruction: all 14 parameters, ~1 minute, 15 iterations

**Observable choice:** Complex reflection coefficient R = (Z-1)/(Z+1) is best for optimization
**Frequency range:** Low frequencies [100, 500 Hz] for hole locations, full range for dimensions

### 2. Szwarcberg et al. (2025) - Geometric sensitivity of modal parameters
**Source**: Acta Acustica, arXiv:2506.16220

- Analytical sensitivity gradients for TMM resonators
- Applied to soprano saxophone register hole optimization
- Key insight: reducing register hole radius and increasing chimney height improves harmonicity
- First-order sensitivity: decreasing Rh by 0.1 mm lowers inharmonicity by 3.4 cents
- Larger variations need higher-order corrections

### 3. Lefebvre & Scavone (2011) - Saxophone bore shape
**Source**: McGill CAA-ACA proceedings

- "straight conical tube is NOT appropriate for saxophone"
- Deviations from straight cone are NECESSARY for second resonance harmonicity
- Cylinder segment or increased taper in upper bore helps but not sufficient
- Optimization of bore shape + hole positions needed simultaneously

### 4. Manachinskaia (2026) - Pocket saxophone design
**Source**: UPV thesis

- TMM + least-squares tuning works within 10 cents
- Lossy TMM validated against OpenWInD FEM
- Entrance volume correction needed for played notes vs impedance peaks
- MATLAB lsqnonlin for bound-constrained optimization

### 5. HAL Woodwind Design Optimization Preprint
**Source**: hal-02479433

- Phase-based resonance definition for smooth cost function
- SQP (sequential quadratic programming) for optimization
- Low-frequency approximation as initial design
- Effective position: P_eff(n) = c/(4*f) for first open hole

### 6. Nederveen - Calculations on clarinet holes
- Simple formulas for hole placement with ~mm accuracy
- Hole function < 0.2 to avoid impurities between registers
- Closed hole row effect: spread volume over main tube

## Key Differences: Clarinet vs Saxophone

| Aspect | Clarinet (closed-open) | Saxophone (open-open) |
|--------|----------------------|----------------------|
| Placement order | Bottom-to-top | Top-to-bottom |
| Fingering | All existing closed, new open | Only new hole open |
| Register | n_register = 1 | n_register = 2 |
| Bore length | c/(4*f) | c/(2*f) |
| Bore shape | Straight cone OK | Needs deviations |

## Implementation Status

### Branch: experiment/independent-hole-placement
- Phase 2: 0.0 cents per hole (perfect placement)
- Phase 3: Nelder-Mead refinement degrades solution (136 cents)
- Need to investigate refinement phase issue

### Next Steps
1. Fix Phase 3 refinement - use all-fingerings evaluation, not just single-hole
2. Try bore profile optimization (not just uniform)
3. Test on soprano sax (simpler geometry)
4. Consider analytical gradients (Szwarcberg approach)
