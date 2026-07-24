# Project Review: Woodwind & Brass Design Automation

## What We've Built
Open-source computational tool for designing wind instruments using TMM (Transfer Matrix Method) for woodwinds and OpenWind FEM for brass. Python + scipy optimization (L-BFGS-B + differential evolution).

**GitHub**: https://github.com/kooshikooo-lab/instrument-designer  
**Branch**: experiment/trumpet-openwind

## Results So Far (good news)

### Woodwinds — excellent intonation
After Phase 2b DE re-optimization, all 7 benchmark instruments achieve sub-0.3c RMS:
- Chalumeau C (6 holes): 0.30c RMS
- Tin whistle (6 holes): 0.91c RMS  
- Soprano recorder (7 holes): 0.00c RMS
- All 7 instruments: < 1c RMS relative intonation

### Clarinet benchmarks
- Diatonic chalumeau (TMMBoreOptimizerJAX): ~0.3c RMS
- Bass chalumeau 8-hole: ~3-5c RMS (TMMBoreOptimizer), 0.00c RMS (SequentialBoreOptimizer after offset removal)
- Key finding: SequentialBoreOptimizer gives PERFECT relative evenness but with systematic offset (-104c for bass clarinet, -242c for bass chalumeau) from closed-hole loading

### Trumpet (OpenWind FEM)
- OpenWind model built: 1.335m tube + Bach 7C mouthpiece (cup 17mm + throat 8mm + backbore 55mm + receiver 25mm)
- Valve model working: all 8 combos lower correctly
- Open fingering: 243 Hz (=B3+73c) on 1.335m tube
- Mouthpiece expected to lower ~15-35c, but remaining discrepancy needs investigation

## Current Blockers

### 1. REGISTER HOLE DOESN'T WORK IN TMM (CRITICAL)
We added a register hole to the bass clarinet TMM model and tested 2nd register:
- Geometry: 1171mm tube × 25mm bore, register hole at 279mm (23.8% of L), 3.5mm dia × 3mm chimney
- 1st register works: 73-156 Hz (D2-D3), reasonable errors  
- 2nd register FAILS: TMM finds 5th harmonic (~5:1 ratio) instead of 3rd harmonic (~3:1 = 12th)
- The register hole SHOULD suppress the fundamental and enable the 12th, but our TMM doesn't reproduce this

**Questions:**
- Is our TMM register hole model incorrect? We model it as a simple open side hole (shunt impedance + series impedance). Does the TMM correctly handle the transition from fundamental-suppressed to 3rd-harmonic-dominant?
- The Debut-Kergomard equation: kΔℓ ≈ -(Sh/Sh')·cos²(kℓ)/(kℓ) predicts the length correction. But does this actually cause the register to switch? Or is the register switch a NONLINEAR phenomenon that linear TMM can't model?
- Szwarcberg (2024, arXiv:2404.07540) says "nonlinear losses in the register hole are the decisive physical phenomenon for second register production." Does this mean our LINEAR TMM is fundamentally unable to simulate the register switch? Do we need a time-domain or nonlinear model?
- If linear TMM can't model register switching, how can we design the register hole? Should we just optimize for the 2nd register impedance peaks (with register hole open) and trust the nonlinear physics to make the register switch work?

### 2. SYSTEMATIC OFFSET FROM CLOSED HOLES
The SequentialBoreOptimizer's Phase 1 optimizes bore length with NO holes, but the final instrument has 7-8 closed holes. The closed holes add acoustic mass, lowering all frequencies by a systematic offset:
- Bass clarinet (7 holes closed): -104c
- Bass chalumeau (8 holes closed): -242c

The relative intonation is perfect (0.00c RMS after removing offset). This offset would be trivially corrected by mouthpiece position in a real instrument.

**Questions:**
- Is -104c for 7 closed holes on a 25mm bore physically realistic? Or does the TMM overestimate closed-hole loading?
- Should Phase 1 include dummy closed holes to pre-compensate?
- For a real bass clarinet, how much does inserting the mouthpiece change the pitch?

### 3. BELL FLARE OPTIMIZATION BREAKS
When we add bore profile optimization (6 control points for bell flare), Phase 3 fails:
- Bore length changes by -150mm (too aggressive)
- Hole position bounds are ±20mm, insufficient to compensate
- Result: 339c RMS failure

**Questions:**
- Should bell flare be a FIXED profile (only hole positions optimized), not a free variable?
- What's the correct approach: optimize holes on uniform bore, THEN add bell flare as post-processing?
- Is the TMM even accurate for bell flares? Should we use OpenWind for the bell section?

### 4. PROJECT DIRECTION
- Bass clarinet is the top priority (user's instrument)
- Should we build a simplified bass clarinet (diatonic, 7 holes, no register) first, or go straight to full chromatic with register?
- Should we switch to OpenWind FEM for any part of the bass clarinet (bell, register hole)?
- Priority order: register hole physics → bell flare → 2nd benchmark (with both registers working)

## Key References
- Debut, Kergomard, Laloë (2005) Applied Acoustics 66, 365-409 — "Analysis and optimisation of the tuning of the twelfths for a clarinet resonator"
- Szwarcberg et al. (2024) arXiv:2404.07540 — "Second register production on the clarinet: nonlinear losses in the register hole as the decisive physical phenomenon"
- Szwarcberg et al. (2025) arXiv:2601.01981 — "How localized nonlinear losses condition the acoustical design of a self-sustained oscillator"
- Lefebvre (2011) — Saxophone TMM acoustics
- Nederveen (1969) — Woodwind instrument acoustics
- Virtual Bass Clarinet in Modalys (Academia.edu)

## Specific Help Needed
1. **Is linear TMM sufficient for register hole design?** If not, what's the minimal model we need?
2. **Why is our 2nd register ratio ~5:1 instead of 3:1?** Is the register hole at wrong position, wrong size, or is the TMM model wrong?
3. **Closed-hole loading**: Is -104c from 7 closed holes on 25mm bore realistic?
4. **Bell flare**: Correct approach for TMM optimization?
5. **Bass clarinet priority**: Should we do simple diatonic first or full chromatic with register?
6. **Trumpet mouthpiece**: Does our explicit geometry look correct? Expected frequency shift from adding mouthpiece to 1.335m tube?

Please provide mathematical analysis where possible, not just general advice.
