# Desktop Catch-Up: Phase 2b DE Breakthrough + Hole Diameter Optimization

## BRANCH: experiment/bore-profile-optimization (pushed, commits 93422b2 → a13a55b)

## THE PROBLEM
All open-open instruments had terrible accuracy (soprano sax 26c, xaphoon 90c, alto sax 126c).
We blamed the TMM model, refined bounds, tried cumulative fingering, tried wider bounds — nothing worked.

## ROOT CAUSE (found tonight)
**The TMM model was always accurate.** The sequential greedy optimizer was creating hole positions
where the TMM literally cannot find resonances.

Proof: xaphoon sequential holes at [101, 169, 457, 472, 487, 502] created a **288mm gap** between
holes 1 and 2. When fingering opens hole 2 (F4), the effective tube length jumps from ~174mm to
~462mm. The TMM phase for notes F4-B4 hovers at 1.5 — halfway between resonances n=1 and n=2.
No local refinement can fix this because there's no resonance to converge to.

Lefebvre (2013, Acta Acustica) confirms: TMM accuracy is ~10c max even with external tonehole
interactions. Our 90c error was purely an optimizer failure.

## THE FIX: Phase 2b Differential Evolution
After sequential hole placement (Phase 2), add a global re-optimization stage using
`scipy.optimize.differential_evolution` that re-optimizes ALL hole positions simultaneously.

This is exactly what chalumier does (evolutionary algorithm in Optimizer.kt).
The DE uses overlapping bounds scaled to bore length: `lo = i*L/(n_h*1.5+1)`, `hi = (i+2)*L/(n_h*1.5+1)`.

## NEW: Hole Diameter Optimization
Diameters are now co-optimized with positions in Phase 2b DE and Phase 3 refinement.
- Bounds: [bore_radius*0.4, bore_radius*0.9] per hole
- Co-optimized in DE: 2×N_h variables (positions + diameters)
- Refined in L-BFGS-B Stage 3 and Stage 4

## RESULTS (all 7 instruments sub-1c RMS!)

| Instrument | Type | RMS | Time |
|---|---|---|---|
| Chalumeau C | closed-open | **0.00c** | 4.8s |
| Bass Chalumeau Bb | closed-open | **0.00c** | 14.3s |
| Soprano Sax Bb | open-open | **0.03c** | 93.9s |
| Xaphoon C | open-open | **0.00c** | 70.3s |
| Alto Sax Eb | open-open | **0.15c** | 106.2s |
| Tin Whistle D | open-open | **0.91c** | 101.6s |
| Recorder C | open-open (conical) | **0.00c** | 178.6s |

## NEW INSTRUMENTS
- **Tin whistle in D**: 6 holes, cylindrical bore, 6.5mm radius. Simplest open-open instrument.
- **Soprano recorder in C**: 7 holes, conical bore (stepped-cylinder approximation), 5.5mm radius.
  Tests our conical bore modeling.

## FILES CHANGED
- `backend/tmm_optimizer_sequential.py` — Phase 2b DE now co-optimizes diameters + positions. Phase 3 Stage 3/4 also optimize diameters.
- `backend/benchmark_all.py` — Same changes + safe_eval_all for numerical robustness. New instruments: tin_whistle_D, recorder_C.
- `backend/target_frequencies.py` — Added tin_whistle preset + INSTRUMENT_TYPES entry.

## RESEARCH FINDINGS (4 topics explored)

### 1. Hole Diameter Optimization ✅ IMPLEMENTED
Chalumier optimizes hole diameters as first-class variables using `signedSqrt` mapping from [0,1] to [min,max].
We use simpler direct bounds [bore_r*0.4, bore_r*0.9]. Works well — soprano sax improved 0.29c→0.03c.

### 2. TMMI (Transfer Matrix Method with Interactions)
Lefebvre/Scavone/Kergomard 2013. Adds mutual radiation impedance matrix Z for open holes.
Expected 5-10c improvement for agreement with real instruments. "Rather easy to implement."
Key formula: Z_nm = j*k*rho*c * exp(-j*k*d_nm) / (4*pi*d_nm)
**Not implemented yet** — our TMM model is already sub-1c, so TMMI would only help for matching
real instrument measurements.

### 3. More Instruments
- Tin whistle ✅ and recorder ✅ added
- Oboe/bassoon: too complex for 3D printing (double reed, small bore, many keys)
- Clarinet: closed-open, already covered by chalumeau
- Brass: requires bell flare modeling (not yet implemented)

### 4. Spectral Target Optimization
6 impedance-spectrum features shape tone:
1. Peak heights (impedance magnitudes)
2. Peak widths/Q factors
3. Relative amplitudes of first two peaks (register balance)
4. Cutoff frequency fc of tonehole lattice
5. Harmonicity of peaks
6. Spectral slope

Ernoult (2021) phase-based approach: use `sum |arg(Z(w_k)) - phi_k(w_k)|` as cost function.
Could match both intonation AND tone quality simultaneously.
**Not implemented yet** — would require target impedance spectra from real instruments.

## NEXT STEPS FOR DESKTOP
1. Pull latest: `git pull origin experiment/bore-profile-optimization`
2. Run benchmark: `python -m backend.benchmark_all`
3. Consider: TMMI implementation for real-instrument agreement
4. Consider: Spectral target optimization for tone quality matching
5. Consider: More instruments (clarinet, saxophones with larger range)
