import sys, time
sys.path.insert(0, '.')
from backend.inverse_design import analyze_wav, design_scale, match_timbre

t0 = time.time()

# Tier 1
print('Tier 1: analyzing WAV...')
analysis = analyze_wav('test_output/test_G3.wav')
print('  F0: {:.1f} Hz'.format(analysis['fundamental_hz']))
print('  Harmonics: {}'.format(len(analysis['harmonic_frequencies'])))
print('  Confidence: {:.3f}'.format(analysis.get('confidence', 0)))

# Tier 2
print('\nTier 2: designing scale...')
t1 = time.time()
tier2 = design_scale(analysis['fundamental_hz'], analysis['harmonic_frequencies'])
print('  Time: {:.1f}s'.format(time.time() - t1))
candidates = tier2.get('candidates', [])
bc = None
for c in candidates:
    if c.get('success'):
        bc = c
        break
if bc:
    print('  Bore: {:.1f}mm'.format(bc.get('bore_length_mm', 0)))
    print('  Holes: {}'.format(len(bc.get('hole_positions_mm', []))))
    print('  Intonation RMS: {:.2f}c'.format(bc.get('intonation_rms_cents', 0)))
else:
    print('  No successful candidate')
    if candidates:
        for i, c in enumerate(candidates):
            print('  Candidate {}: success={}, error={}'.format(i, c.get('success'), c.get('error')))

# Tier 3
if bc and bc.get('success'):
    print('\nTier 3: matching timbre...')
    t2 = time.time()
    tier3 = match_timbre(bc, analysis, n_gen=15, pop_size=20)
    print('  Time: {:.1f}s'.format(time.time() - t2))
    print('  Success: {}'.format(tier3.get('tier3_success', False)))
    if tier3.get('tier3_success'):
        print('  Init intonation: {:.2f}c'.format(tier3.get('init_intonation_cost', 0)))
        print('  Knee intonation: {:.2f}c'.format(tier3.get('knee_intonation_cost', 0)))
        print('  Init radii: {}'.format(tier3.get('bore_radii_initial', [])))
        print('  Opt radii: {}'.format(tier3.get('bore_radii_optimized', [])))
        radii_opt = tier3.get('bore_radii_optimized', [])
        if isinstance(radii_opt, list) and len(radii_opt) >= 3:
            diffs = [radii_opt[i+1] - radii_opt[i] for i in range(len(radii_opt)-1)]
            signs_n = [1 if d > 0 else (-1 if d < 0 else 0) for d in diffs]
            n_changes = sum(1 for i in range(len(signs_n)-1) if signs_n[i] != 0 and signs_n[i+1] != 0 and signs_n[i] != signs_n[i+1])
            print('  Sign changes: {}'.format(n_changes))

        # Also test min-intonation point from Pareto set (not just knee)
        pf = tier3.get('pareto_set', [])
        if pf:
            best_i = min(range(len(pf)), key=lambda i: tier3['pareto_front'][i][0])
            radii_mininton = pf[best_i]
            print('\n  Min-intonation radii: {}'.format([round(r,2) for r in radii_mininton]))
            if len(radii_mininton) >= 3:
                d2 = [radii_mininton[i+1] - radii_mininton[i] for i in range(len(radii_mininton)-1)]
                s2 = [1 if d > 0 else (-1 if d < 0 else 0) for d in d2]
                n2 = sum(1 for i in range(len(s2)-1) if s2[i] != 0 and s2[i+1] != 0 and s2[i] != s2[i+1])
                print('  Min-intonation sign changes: {}'.format(n2))

        # Cross-validation was planned but never implemented.
        # See ADR-005 for the three-tier pipeline design.

print('\nTotal time: {:.1f}s'.format(time.time() - t0))
