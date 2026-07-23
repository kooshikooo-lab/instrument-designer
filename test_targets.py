import sys, numpy as np
sys.path.insert(0, '.')
from backend.optimizer import _compute_impedance_from_bore, _match_peaks_to_targets, _IMPEDANCE_CACHE
_IMPEDANCE_CACHE.clear()

bore_length = 0.328
n_cp = 12
positions = np.linspace(0, bore_length, n_cp)
radii = np.linspace(0.0065, 0.0075, n_cp)
bore = list(zip(positions.tolist(), radii.tolist()))

result = _compute_impedance_from_bore(bore, freq_range=(50, 3000), n_freqs=5000)
peaks = result['peak_frequencies']
print('Bore peaks:', ['{:.1f}'.format(f) for f in peaks[:10]])

# Option A: Clarinet odd harmonics of C4 (261.6 Hz)
clarinet_targets = [261.6, 261.6*3, 261.6*5, 261.6*7, 261.6*9, 261.6*11]
print('\nClarinet targets (odd harmonics):', ['{:.1f}'.format(f) for f in clarinet_targets])
matched = _match_peaks_to_targets(peaks, clarinet_targets)
for m in matched:
    print('  target={:.1f} actual={:.1f} err={:+.2f} cents'.format(m[0], m[1], m[3]))
rms = np.sqrt(np.mean([abs(m[3])**2 for m in matched]))
print('  RMS: {:.2f} cents'.format(rms))

# Option B: Clarinet scale using odd-harmonic series
# C major on clarinet: C4(262), E4(330), G4(392), C5(523), E5(659), G5(784)
clarinet_scale = [261.6, 329.6, 392.0, 523.3, 659.3, 783.9]
print('\nClarinet scale targets:', ['{:.1f}'.format(f) for f in clarinet_scale])
matched2 = _match_peaks_to_targets(peaks, clarinet_scale)
for m in matched2:
    print('  target={:.1f} actual={:.1f} err={:+.2f} cents'.format(m[0], m[1], m[3]))
rms2 = np.sqrt(np.mean([abs(m[3])**2 for m in matched2]))
print('  RMS: {:.2f} cents'.format(rms2))

# Option C: What targets does a 328mm bore actually support?
print('\nPeak positions relative to fundamental:')
fp = peaks[0]
for i, f in enumerate(peaks[:8]):
    ratio = f / fp
    print('  Peak {}: {:.1f} Hz (ratio: {:.3f}, nearest odd harmonic: {})'.format(
        i, f, ratio, round(ratio)))
