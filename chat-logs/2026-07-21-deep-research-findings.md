# Deep Research Findings — Desktop Session 7 (2026-07-21)
## Broad investigation into woodwind acoustics, optimization, and instrument design

---

## 1. WHY OUR BATCH TEST FAILS (38.78 cents vs 2.00 cents small)

**Root cause: `np.inf` corrupts NSGA-II crowding distance computation.**
- pymoo's `calc_crowding_distance` does `norm = max(F) - min(F)`, then divides by norm
- When any solution has `np.inf` objective: `np.inf - np.inf = nan` -> all crowding distances become 0/NaN
- With pop=40: more solutions corrupt the normalization -> NSGA-II selection becomes random
- With pop=10: fewer corrupted solutions, less impact
- **FIX**: Revert `np.inf` back to `1e10` (laptop's code review change was wrong about this)

---

## 2. NORELAND "LOGICAL CLARINET" (2013) — THE GOLD STANDARD

**Paper:** https://arxiv.org/abs/1209.3637 | Published: Acta Acustica 99, pp.615-628 (2013)
**Authors:** Noreland, Kergomard, Laloë, Vergez, Guillemain, Guilloteau

### Method
- **Gradient-based least-squares** (MATLAB `lsqnonlin`), NOT evolutionary
- 1D transmission line network with visco-thermal losses (Keefe formulas)
- Tone holes as T-junctions with series/shunt impedances
- 50+ design variables: hole positions, radii, chimney lengths
- Bore was **fixed cylindrical** (14.75mm) — only tone hole geometry was optimized

### Objective Function
Sum of squared RELATIVE frequency errors:
```
R_{2k-1} = (f_tilde^k - f1^k) / f_tilde^k      (1st resonance vs target)
R_{2k}   = (3*f_tilde^k - f2^k) / (3*f_tilde^k)  (2nd resonance vs 3x target)
```
No weighting — all notes contribute equally.

### Two-Phase Optimization (CRITICAL INSIGHT)
- **Phase 1**: Optimize only 19 first-register notes (1st + 2nd resonances)
- **Phase 2**: Use Phase 1 as seed, add second-register notes
- "Little success was achieved omitting Phase 1" — starting from scratch fails
- Phase 2 is far more sensitive to initial guess

### Results
- < 10 cents RMS throughout full clarinet range
- Best designs: < 5 cents for most notes
- Experimental prototype: measured vs computed avg deviation 1.97 cents
- After correcting ~12 cent flat offset (shorten tube): remaining errors < 5 cents

### Register Hole Finding
- Optimization pushes register hole to MINIMUM allowed radius (1mm) with LONG chimney
- Maximize shunt acoustic mass (reactive perturbation)
- Dedicated register hole essential — dual-use hole gives poor results

### Key Collaborators (still active)
- Jean Kergomard (CNRS/LMA): tone hole lattice theory
- Christophe Vergez (CNRS/LMA): nonlinear dynamics, MoReeSC framework
- Philippe Guillemain (LMA): reed instrument sound production
- Martin Berggren (Umeå): adjoint methods, topology optimization

### No open-source code released.

---

## 3. ERNOULT (2020-2021) — FULL WAVEFORM INVERSION

**Paper:** JASA 148(5), 2864-2877 (2020) | DOI: 10.1121/10.0002449
**Paper:** Acta Acustica (2021) — FWI approach

### Critical Findings
1. **Traditional peak matching creates discontinuous cost functions** — peaks merge/disappear during optimization
2. **Solution: Phase-based resonance definition** using unwrapped angle of reflection function R(f)
   - R(f) = (Z(f) - 1) / (Z(f) + 1)
   - Phase accumulates monotonically even when peaks merge
3. **Gradient via adjoint method** — same linear system, different source terms
4. Demonstrated on pentatonic clarinet with bore + holes simultaneously optimized
5. 14-parameter instrument reconstructed in ~1 minute
6. Collaboration with Buffet Crampon (real manufacturing constraints)

### Why this matters for us
Our current approach uses peak detection -> discontinuous -> NSGA-II can't exploit gradient info.

---

## 4. CHALUMIER / DEMAKEIN — PRACTICAL APPROACH

### Chalumier (Kotlin, MarkCC)
- Port of Demakein, evolutionary algorithm
- TMM for impedance computation
- Design + SVG output + model commands
- MarkCC's goal: "modern printable basset horn"
- ~5 min for simple flute, ~10 min for complex cross-fingered instrument
- No academic backing but practical results

### Demakein (Python, Paul Harrison)
- Predecessor to chalumier
- Design + CNC/3D-print ready output
- Built-in instruments: flutes, whistles, shawms
- Uses nesoni framework (PyPy recommended for speed)
- Active: v1.1, July 2025

### WWIDesigner (Java, Edward Kort)
- Two-stage: DIRECT (global) + BOBYQA (local)
- "Tens of thousands of geometries in minutes"
- Supports fipple flutes, transverse flutes, single/double reed, lip-reed
- GitHub: github.com/edwardkort/WWIDesigner

---

## 5. KEY ACOUSTIC CONCEPTS

### Tone Hole Lattice
- Open holes act as HIGH-PASS filter for standing waves
- Below cutoff (fc): instrument behaves as shorter tube near first open hole
- Above fc: waves propagate along full bore
- Clarinet fc ~ 1500 Hz; modern flutes fc ~ 2000-2200 Hz
- Benade formula: fc = 0.11 * (b/a) * c / sqrt(s * l_eff)

### Bore Shapes & Harmonics
- **Cylindrical + closed end** (clarinet): odd harmonics only (1, 3, 5, 7...)
- **Cylindrical + open end** (flute): all harmonics (1, 2, 3, 4...)
- **Conical + closed end** (oboe): all harmonics (cone compensates)
- **Conical + reed** (saxophone): all harmonics, louder

### Impedance Peak Detection Problems
- Zero crossings of Im(Z) are DISCONTINUOUS under geometry perturbation
- Peaks merge/disappear -> optimizer loses track
- Phase-based approach (Ernoult) solves this
- 0.2 Hz frequency step recommended for accurate detection

### 3D Printing Validation
- Yamamoto 2025: CT-scanned oboe -> 3D print -> musicians COULDN'T TELL THE DIFFERENCE
- PLA, ABS, wood-filled PLA all performed similarly
- Material matters less than geometry (confirms Benade's prediction)

---

## 6. BETTER OPTIMIZATION APPROACHES

### What the literature uses:
| Study | Algorithm | Result |
|-------|-----------|--------|
| Noreland 2013 | Levenberg-Marquardt (gradient) | <5 cents |
| Ernoult 2020 | SQP + adjoint gradient | Sub-cent |
| Kort/WWIDesigner | DIRECT + BOBYQA | Fast convergence |
| Tournemenne 2017 | MADS + surrogates | Good brass results |
| Petiot 2025 | ML surrogate + NSGA-II | Yamaha prototype built |

### Our approach issues:
1. NSGA-II is WRONG algorithm — every successful instrument uses gradient-based
2. pop=15 far too small for 12 control points (need 4n = 48+)
3. No gradient info = blind search
4. One-shot optimization without good initialization

### Recommended alternatives:
1. **Two-phase like Noreland**: optimize simple objective first, then refine
2. **CMA-ES**: best derivative-free for continuous problems
3. **L-BFGS-B with finite differences**: fast if cost function is smooth enough
4. **Ernoult's phase-based formulation**: smooth cost function, enables gradients
5. **Start from known good bore** (Buffet R13 dimensions: entry 14.8mm, exit 15mm, ~660mm)
6. **Weighted sum single objective**: frequency accuracy is primary, evenness/projection are secondary

---

## 7. BORE GEOMETRY REFERENCE (Bb Clarinet)

| Location | Typical Diameter |
|----------|-----------------|
| Barrel entry | 14.8-15.2 mm |
| Barrel exit | 14.6-14.9 mm |
| Upper joint mid | 14.3-14.8 mm |
| Throat tones | ~14.3 mm (narrowest) |
| Lower joint | 14.6-14.8 mm |
| Bell entry | 14.8-15.0 mm |
| Total acoustic length | ~650-670 mm |

---

## 8. SOURCES

| # | Reference | URL |
|---|-----------|-----|
| 1 | Noreland "Logical Clarinet" | https://arxiv.org/abs/1209.3637 |
| 2 | Ernoult JASA 2020 | https://doi.org/10.1121/10.0002449 |
| 3 | Ernoult FWI 2021 | https://acta-acustica.edpsciences.org/articles/aacus/full_html/2021/01/aacus210048/aacus210048.html |
| 4 | Ernoult benchmark 2026 | https://acta-acustica.edpsciences.org/articles/aacus/pdf/2026/01/aacus260043.pdf |
| 5 | Ablitzer peak-picking 2021 | https://acta-acustica.edpsciences.org/articles/aacus/full_html/2021/01/aacus210061/aacus210061.html |
| 6 | Szwarcberg sensitivities 2025 | https://doi.org/10.1051/aacus/2025039 |
| 7 | Benade "Fundamentals" (1976) | Book — Oxford University Press |
| 8 | OpenWInD | https://openwind.inria.fr/ |
| 9 | OpenWInD demo | https://demo-openwind.inria.fr/ |
| 10 | Chalumier | https://github.com/MarkChuCarroll/chalumier |
| 11 | Demakein | https://github.com/pfh/demakein |
| 12 | WWIDesigner | https://github.com/edwardkort/WWIDesigner |
| 13 | Petiot ML trumpet 2025 | https://doi.org/10.1121/2.0002163 |
| 14 | Yamamoto 3D-printed oboe | https://doi.org/10.1250/ast.e24.92 |
| 15 | Darabundit Port-Hamiltonian reed 2025 | https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2025.1519450/full |
| 16 | Wolfe cutoff/cross-fingering | https://newt.phys.unsw.edu.au/jw/cutoff.html |
| 17 | Noreland brass bore 2010 | https://pubs.aip.org/asa/jasa/article/128/3/1391/599056 |
| 18 | MoReeSC | https://hal.science/hal-00770238 |
| 19 | Umeå Design Optimization Group | https://www.umu.se/en/research/groups/design-optimization |
| 20 | Neuralacoustics framework | https://aimc2024.pubpub.org/pub/5cl1cvmy |
