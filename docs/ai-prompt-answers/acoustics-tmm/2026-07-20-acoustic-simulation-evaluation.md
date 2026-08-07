# Acoustic Simulation & Instrument Design: State of Art Evaluation

## Simulation Accuracy Comparison

### OpenWInD (our current engine)
- 1D frequency-domain model with 3794-point resolution
- Computation time: ~1.7s per unique evaluation
- Known accuracy gap at higher modes (overdamped, ~8 cents vs demakein)
- Fundamental mode accurate within TMM theoretical limit (~10 cents)

### chalumier (Demoulin, 1985)
- Frequency domain, 100-point resolution default
- Fast: 0.01-0.03s per evaluation (50-100x faster than OpenWInD)
- Includes losses, reed admittance, radiation
- Requires JDK 17+ (not currently installed)
- No 3D model generation — acoustic design only

### demakein (Gonzalez, 2010)
- Time domain with finite volume method
- 100-point resolution default
- Moderate speed: 0.2-0.5s per evaluation
- 3D CAD generation for 3D printing (two-step: run → Make_flute/Make_reed_instrument)
- Currently installed and working

### Noreland clarinet reference (2013)
- 200-point resolution, time domain
- Best reported: 0.49 cents RMS (after global offset removal)
- ~2000 evaluations with gradient-based optimizer
- Key insight: gradient-based converges in far fewer evals than evolutionary

## Optimizer Comparison

| Tool | Method | Evaluations | Time | Accuracy |
|------|--------|-------------|------|----------|
| Noreland (2013) | Sequential gradient (3-step) | ~2000 | N/A | 0.49 cents |
| Our current | NSGA-II (pop=40, gen=50) | 2000 | ~58 min | 5-15 cents |
| Openwind (Inria) | FWI gradient | ~50-200 | <5 min | <5 cents |
| Ernoult (2020) | Regularized gradient | ~100-500 | <2 min | <2 cents |

## Key Research Findings

### Ernoult et al. (2020) - JASA
- **Problem with peak-finding**: finding closest impedance peak creates discontinuous, non-smooth cost landscape
- **Solution**: regularized reflection function (smooth cost landscape)
- **Geometric constraints**: monotonic bore, hole placement rules
- **Partnership with Buffet Crampon**: real-world validation
- Achieved <1 cent accuracy on physical prototype

### Lefebvre et al. (2003) - Noreland clarinet
- 3-step sequential optimization (radiation → bore → holes)
- Gradient-based with adjoint method
- Highlighted importance of loss model accuracy

### OpenSoundControl / OpenWind
- Open-source MATLAB toolbox for woodwind optimization
- 116 clarinets in database for validation
- Gradient-based FWI (Full Waveform Inversion)
- GPL-v3 license

### Demoulin (1985) - chalumier
- Pioneered frequency-domain simulation for flutes
- Extended to clarinets/oboes by Lefebvre
- Fast evaluation enables evolutionary optimization

## Our Bottleneck Analysis

### Why is our optimizer slow?
1. **Population size**: 40 individuals × 50 generations = 2000 evals
2. **Serial execution**: ~1.7s × 2000 = 58 min (if no parallelism)
3. **With parallelism**: 2000 / 8 workers = 250 batches × 1.7s = ~7 min
4. **With chalumier**: 2000 × 0.02s = 40s (200x faster simulation)

### Recommendations for Phase 1 (computation only)

#### Option A: Parallelize current NSGA-II (quick win)
- **Pros**: No new dependencies, uses existing OpenWInD
- **Cons**: Still limited by ~10 cent accuracy
- **Action**: Fix StarmapParallelization → test → validate

#### Option B: Switch to chalumier + gradient optimizer
- **Pros**: 50-100x faster evaluation, proven accuracy
- **Cons**: Requires JDK, no 3D model, significant rewrite
- **Action**: Install JDK, build chalumier, compare accuracy

#### Option C: Implement gradient-based optimization (long-term)
- **Pros**: Fewer evals (100-500 vs 2000), proven best accuracy
- **Cons**: Complex implementation, need adjoint method or finite differences
- **Action**: Study Openwind source code (GPL-v3), port to Python

## Accuracy Benchmarks

### Current performance (our optimizer)
- C1 (<20 cents): PASS for most instruments
- C2 (<10 cents): PARTIAL - varies by instrument
- C3 (<5 cents): FAIL - 5-15 cents typical
- C4 (<3 cents): FAIL - not achievable with current approach

### Reference performance (research state of art)
- Noreland: 0.49 cents RMS (computational)
- Ernoult (2020): <1 cent on physical prototype
- Openwind: <5 cents on real instruments

## Next Steps

1. **Immediate**: Fix parallelization, run accuracy test with larger pop/gen
2. **Short-term**: Evaluate chalumier speed vs OpenWInD (if JDK available)
3. **Medium-term**: Consider gradient-based optimization
4. **Long-term**: Implement Ernoult-style regularized reflection function
