# Desktop Catch-Up: Phase 2b DE Breakthrough (2026-07-23)

## BRANCH: experiment/bore-profile-optimization (pushed, commit 93422b2)

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

~15-20 seconds per instrument.

## RESULTS (all 5 instruments sub-0.3c RMS!)

| Instrument | Before | After |
|---|---|---|
| Chalumeau C | 0.25c | 0.25c |
| Bass Chalumeau | 0.20c | 0.20c |
| Soprano Sax Bb | 26.3c | **0.29c** |
| Xaphoon C | 90.77c | **0.01c** |
| Alto Sax Eb | 126c | **0.02c** |

## FILES CHANGED
- `backend/tmm_optimizer_sequential.py` — Added Phase 2b in `SequentialBoreOptimizer.run()`
- `backend/benchmark_all.py` — Added Phase 2b in `sequential_refined()`, added DE import

## KEY RESEARCH REFERENCES
- Lefebvre PhD thesis (2010): TMM max ~1c for single toneholes, ~10c with multi-hole interactions
- Lefebvre/Scavone/Kergomard (2013): External tonehole interactions cause 5-10c shift, not 90c
- Kaboodi/Poma (2024): TMMi validation for şimşal, confirms TMM accuracy
- Chalumier C++ (MarkChuCarroll/chalumier): Uses evolutionary optimization — same approach we now use

## TO VERIFY
Pull and run: `python -m backend.benchmark_all`

## CHALUMIER COMPARISON
Read chalumier's Instrument.kt and ResonanceMath.kt — the tonehole model is IDENTICAL to our
Python port. Same `junction3ReplyPhase` formula. Same `holeLengthCorrection`. The difference was
always the optimizer, not the model.
