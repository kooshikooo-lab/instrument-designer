# Research: Unconventional Wind Instrument Shape Modeling

## Real-World Examples of Non-Traditional Instruments

### 1. Folded Bore Instruments
**Examples:** Trumpet, saxophone, rackett, Komuso 1.8 shakuhachi

The Komuso 1.8 (komuso.org) is a 3D-printable shakuhachi with a folded bore — printed as a single unit, pocket-sized. The designer used OpenSCAD for procedural geometry generation. Key insight: **folded bores work because the standing wave follows the centerline**, regardless of physical folding. Many traditional instruments already use this (trumpet wraps around, rackett coils).

**Modeling approach:** Our existing TMM handles this naturally — just define the bore profile along the centerline path length, ignoring the physical fold.

### 2. Free-Form / Organic Shapes
**Examples:** Printone instruments (bunny, star, cat, cube, sheep shapes)

Umetani et al. (2016) demonstrated fully 3D free-form instruments using boundary element method (BEM):
- Import arbitrary 3D mesh → auto-hollow → place fipple + holes
- BEM formulates resonance as nonlinear minimum eigenvalue problem
- Generalized eigenvalue problem for fast approximate resonance
- Sensitivity-based first-order estimation at >30 FPS
- AutoTune: Newton-Raphson hole size optimization
- **Results:** 5-8 target frequencies with 3-4 holes on bunny, star, sheep, etc.
- Printed on FDM MakerBot, no audible difference between FDM/resin/powder prints

**Key finding:** Surface roughness from FDM printing has minimal effect on fundamental frequency. No interior sanding needed.

### 3. Spline-Based Extrusions
**Examples:** Wang (2019) MIT thesis

GPU-accelerated 3D FDTD simulator + deep learning inverse:
- Random spline bore profiles (1D design domain → revolved to 3D)
- 3D FDTD on 4x GTX 1080 Ti: ~3 sounds/second
- Deep learning: train on random splines → predict shape from desired sound
- Automatic pitch hole placement for given bore + target pitch
- **Limitation:** 1D design domain (spline extrusions only), doesn't exploit full 3D freedom

### 4. Dual-Bore / Bifurcated Instruments
**Examples:** GEMINI Twin Serpents (MONAD Studio)

Two independent bores, each with six copper-reinforced finger holes. One musician stands, one seated — played collaboratively. Chromatic in Bb or C via embouchure + finger combinations.

**Modeling challenge:** Bifurcated acoustic paths require network-level modeling (branching nodes), not simple 1D bore sequences. Our existing AcousticNetwork with Port nodes can handle this.

### 5. Community/Speculative Instruments
**Examples:** Walrus Pipes, Waving Panpipes (Szabó 2024)

3D-printed wind instruments for non-standard tunings and communal playing. Designed as ensembles, not solo instruments. Embody "new meanings and uncommon consonances."

**Relevance:** Non-standard tuning systems (microtonal, just intonation, custom scales) are first-class use cases for computational design.

## Computational Methods Ranked by Applicability

### Tier 1: Direct Extension of Our Platform (Doable Now)

| Method | What | How |
|--------|------|-----|
| **Spline bore profiles** | Variable-radius bore with arbitrary taper | OpenWind already supports spline bore shapes. Our TMM could be extended with spline interpolation. |
| **Folded bore centerlines** | Bore follows non-linear path | Both TMM and OpenWind work on centerline path length. Physical folding is cosmetic only for acoustics. |
| **Arbitrary hole placement** | Holes at any position/angle | Already supported. Chimney angle affects effective length — add correction factor. |
| **Non-standard tuning** | Custom target frequencies | Just change the targets array. Our optimizer already handles arbitrary targets. |
| **Network topology** | Bifurcated/branched paths | AcousticNetwork already has Port (branching) nodes. Need to test with real bifurcated geometries. |

### Tier 2: Moderate Extension (New Module Needed)

| Method | What | How |
|--------|------|-----|
| **1D FEM (OpenWind)** | Arbitrary bore shapes with viscothermal losses | OpenWind's spectral FEM handles splines, Bessel horns, cones. Already integrated as wrapper. Need to wire into optimizer. |
| **Phase-based optimization** | Robust cost function for complex impedance | Ernoult et al. unwrap reflection phase for smooth gradient. We already have `phase_cost()` — validate on complex shapes. |
| **Sensitivity-based optimization** | Analytical gradients for TMM | Szwarcberg et al. (2025) derive ∂f/∂geometry analytically from TMM. Enables gradient-based bore profile optimization. |
| **Full Waveform Inversion** | Reconstruct bore from measured impedance | Ernoult et al. (2021) use gradient of FEM cost function. Could validate our designs against physical measurements. |

### Tier 3: Significant New Capability (Research Project)

| Method | What | How |
|--------|------|-----|
| **3D BEM (Printone-style)** | Full 3D resonance simulation | Implement BEM eigenvalue solver. Interactive design at >30 FPS with sensitivity updates. |
| **3D FDTD + DL inverse** | Sound → shape via deep learning | GPU-accelerated 3D wave simulation + neural network inverse. Wang's approach. |
| **Coupled oscillator simulation** | Real instrument sound (not just impedance) | OpenWind has time-domain reed/lip coupling. Need to extend for our optimizer's timbre objective. |

## Practical Implementation Roadmap

### Phase A: Bore Profile Freedom (Quick Win)
1. Replace fixed bore_radius with spline-based bore profile in INSTRUMENTS config
2. Extend `tmm_instrument_from_radii` to accept spline control points
3. Add bore profile as optimization variable (DE can handle it)
4. Test on: stepped bore, parabolic taper, Bessel horn

### Phase B: OpenWind FEM Integration (Medium Effort)
1. Wire OpenWind's spline bore support into our optimizer loop
2. Use OpenWind as accuracy validator (cross-check against TMM)
3. Enable arbitrary bore shapes that TMM can't handle (strong curvature, bifurcations)
4. Add OpenWind gradient estimation (finite-difference on FEM) for local refinement

### Phase C: Network Topology Design (Research)
1. Model bifurcated paths using AcousticNetwork Port nodes
2. Allow optimizer to discover topology (which branches connect where)
3. Test on: dual-bore instruments, side-branch resonators, Helmholtz resonators
4. Target instruments like rackett (coiled bore with multiple channels)

### Phase D: Full 3D (Long-Term)
1. Integrate BEM solver for interactive 3D shape exploration
2. Import STL meshes → auto-hollow → simulate resonance
3. Deep learning surrogate for fast evaluation during optimization
4. Export optimized 3D shape → STL → 3D print

## Key References

1. **Printone** — Umetani et al. (2016). ACM SIGGRAPH. BEM-based interactive design. https://doi.org/10.1145/2980179.2980250
2. **MIT FDTD+DL** — Wang (2019). MIT thesis. GPU 3D FDTD + deep learning inverse. https://hdl.handle.net/1721.1/123116
3. **OpenWind** — INRIA. 1D FEM Python library. https://openwind.inria.fr/
4. **Phase-based optimization** — Ernoult et al. (2020). HAL. https://hal.science/hal-02479433v1
5. **TMM Sensitivity** — Szwarcberg et al. (2025). Acta Acustica. Analytical ∂f/∂geometry. https://acta-acustica.edpsciences.org/articles/aacus/full_html/2025/01/aacus250082/aacus250082.html
6. **Full Waveform Inversion** — Ernoult et al. (2021). Acta Acustica. Bore reconstruction from measurements. https://doi.org/10.1051/aacus/2021048
7. **FEM for Woodwinds** — Debut (2009). McGill thesis. https://escholarship.mcgill.ca/concern/theses/sf268697f
8. **Komuso 1.8** — Folded bore shakuhachi. https://komuso.org/1.8/
9. **Walrus Pipes** — Szabó (2024). Jazz Research Journal. 3D-printed community instruments.
10. **TMM vs FEM** — Tournemenne & Chabassier (2019). Acta Acustica. 1D FEM advantages.
11. **3D Printed Cornett** — Tonks (2025). Music & Science. Decade of experimentation.
12. **Complexity in AM** — Simian (2025). Topological complexity for manufacturing.
