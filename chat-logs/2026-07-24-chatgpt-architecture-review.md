# ChatGPT Architecture Review — 2026-07-24

## Overall Assessment
- Early stage: bass clarinet optimizer
- Now: general computational acoustics platform
- Core abstractions (AcousticNetwork, solver plugins, staged optimization, coordinate normalization) are strong

## Architecture Scores
| Component | Score |
|-----------|-------|
| AcousticNetwork | ★★★★★ |
| Solver abstraction | ★★★★★ |
| Coordinate system | ★★★★★ |
| Physics plugin system | ★★★★☆ |
| Optimization pipeline | ★★★★☆ |
| Builder architecture | ★★★★★ |
| CAD integration | ★★★★☆ |
| Correction model | ★★★☆☆ (future work) |

## Key Recommendations

### 1. Replace "Port" with "AcousticElement" hierarchy
```
AcousticElement
├── Waveguide (was Segment)
├── Junction
├── SideBranch (was Tonehole, RegisterVent, BrassValve)
├── Radiation
├── Excitation
└── LossModel
```
Removes woodwind-specific terminology, supports reeds, valves, piston ports, rotor valves, tuning slides, leaks, pad compliance, Helmholtz resonators.

### 2. Gaussian Process for Correction Model (not Neural Network)
- FEM samples: hundreds/thousands, not millions
- GP advantages: uncertainty estimates, active learning, identifies regions needing FEM, physics-friendly, easier debugging
- Active learning loop: Optimizer → TMM → GP uncertainty → Choose next FEM sample → Retrain
- Could reduce FEM runs by order of magnitude

### 3. Optimize Impedance, Not Frequencies
- Frequency is only one property; playability depends on impedance peaks, heights, widths, spacing, radiation efficiency
- Make impedance primary solver output:
```python
compute_impedance()
  ↓
find_resonances()
  ↓
playing_frequencies()
```
- Matches Benade, Nederveen, Keefe, OpenWInD literature

### 4. Stage 3 Optimization: Trust-Region Regularization
```
J = J_intonation + λ|x - x_stage2|²
```
Allows escape from poor local basin when benefit is clear, without arbitrary wandering.

### 5. Bell Deferred (Agreed)
Return after TMM matches OpenWInD for: cylinder, cylinder+hole, lattice, register vent.

### 6. Revised Bass Clarinet Target
Minimize: Intonation + Impedance quality + Register consistency + Manufacturability
Professional makers accept small intonation compromises for response/timbre/ergonomics.

### 7. InstrumentModel as Canonical JSON Schema
```json
{
  "instrument": {...},
  "geometry": {...},
  "physics": {...},
  "fingerings": [...],
  "solver_defaults": {...},
  "manufacturing": {...}
}
```
React, CAD, TMM, FEM all consume same object.

### 8. Validation Pyramid (Add to Briefing)
1. Analytical solutions (uniform tubes)
2. Chalumier agreement (TMM port matches reference)
3. OpenWInD agreement (higher-fidelity numerical)
4. Published experimental data (impedance, resonance, tonehole effects)
5. Measurements of real instruments

---

## Research Roadmap (Priorities)

1. **Complete TMM physics** — merge stash fixes + KeefeLoss
2. **Benchmark TMM vs OpenWInD** — cylinder, single hole, multiple holes, register vent, complete bass clarinet
3. **Promote impedance to primary solver output** — resonance extraction as post-processing
4. **Implement GP correction model with active learning** — before neural networks
5. **Validate against measurements** — published data + real instruments

---

## Next Actions for Desktop

1. Merge laptop's TMM fixes from `experiment/tmm-improvements` (true_wavelength_near, reed_virtual_length, whistle_clip)
2. Implement KeefeLoss plugin
3. Run Stage 1 optimization on bass clarinet
4. Define InstrumentModel schema
5. Port build123d STEP export

*Source: ChatGPT response to PROJECT_BRIEFING_FOR_CHATGPT.md*