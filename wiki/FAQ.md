# FAQ

## General

### What instruments can I design?
91 instruments across 10 families: flutes, clarinets, saxophones, whistles, chalumeaux, recorders, ocarinas, brass, membrane instruments, and mouthpieces. See [[Instrument-Library]].

### How accurate is the optimizer?
Computational accuracy: sub-0.1 cents RMS on most instruments. Physical accuracy after 3D printing: typically 5-15 cents (limited by manufacturing tolerance, not computation).

### Can I design custom instruments?
Yes. Define bore profile, fingering chart, and target frequencies in a JSON config file. The optimizer will find optimal hole positions and diameters.

### What's the difference between the branches?
See [[Branch-Comparison]] for a detailed comparison. In short:
- `laptop` — Active development, all features
- `main` — Stable shared branch
- `option-a-tauri` — Tauri desktop UI
- `refactor/architecture-redesign` — Solver-agnostic architecture

## Acoustics

### What is TMM?
Transfer Matrix Method — a computational method that models sound propagation through cylindrical/conical pipe segments. Fast enough for optimization (microseconds per evaluation).

### What are viscothermal losses?
Sound absorption due to viscosity and thermal conduction at the bore walls. Modeled using Keefe (1984) with Sutherland's temperature correction. Adds frequency-dependent attenuation and phase shift.

### What is n_register?
The harmonic register index. For open-open pipes (flute, sax), n_register=2 is the fundamental. For closed-open pipes (clarinet), n_register=1 is the fundamental. Auto-detected: `n_register = 1 if closed_top else 2`. Peak-search per-note detection (`detect_registers`) is available for cases where the scalar default fails (over-long closed-top bores, octave-boundary notes).

### Why does my instrument sound different from the prediction?
Several factors:
1. **Manufacturing tolerance** — bore errors of 0.1mm cause 1-3 cents intonation error
2. **Embouchure correction** — players adjust pitch by 10-40 cents with lip pressure
3. **Reed/mouthpiece** — not modeled in the TMM (simplified as boundary condition)
4. **Radiation** — simplified end corrections, not full FEM radiation impedance

## Optimization

### What cost function does the optimizer use?
**Absolute RMS** of cent deviations from equal temperament targets. This measures pitch accuracy (how close to the right notes). See [[Optimization]] for details.

### What is median correction and why was it removed?
Median correction subtracted the median deviation before computing RMS. This measured scale evenness (relative spacing) instead of accuracy (absolute pitch). An instrument can be perfectly even but 15c sharp — median correction would report 0c error. See [[Optimization#Metric-Standardization]] for the full analysis.

### How long does optimization take?
Depends on instrument complexity:
- Simple (6 holes, diatonic): 5-15 seconds
- Complex (12+ holes, chromatic): 60-180 seconds
- Multi-register: 120-300 seconds

### Can I optimize for timbre as well as intonation?
Not yet. Ernoult et al. (2020) proved these are inherently at odds — optimizing both requires a Pareto front approach. This is planned as a stretch goal. See [[Optimization#Timbre-Optimization]].

## 3D Printing

### What printer should I use?
SLA (resin) printer recommended. FDM layer lines create turbulence. See [[3D-Printing-Guide]].

### What resin should I use?
Engineering resin (Siraya Tech Blu, Elegoo ABS-like) for final instruments. Standard resin for prototyping. See [[3D-Printing-Guide#Material]].

### How accurate do I need to be?
±0.1mm bore tolerance. SLA printing achieves ±0.05-0.1mm. Post-process with reaming for bore accuracy.

## Troubleshooting

### Optimizer times out
Increase `maxiter` or reduce `popsize`. Check that target frequencies are physically achievable for the bore length.

### Bore profile is non-monotonic
Add monotonicity constraint (bore[i+1] >= bore[i]). See ROADMAP.md Phase 1d.

### Notes are systematically sharp/flat
This is usually a bore length issue. Try adjusting the initial bore length estimate. The optimizer should correct this, but bad initial guesses can cause convergence to local minima.

### Import errors
Run `pip install -r requirements-server.txt` from the repo root. Ensure Python 3.12+ is installed.
