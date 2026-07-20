import sys, numpy as np
sys.path.insert(0, '.')
from backend.optimizer import _compute_impedance_from_bore, _match_peaks_to_targets, _IMPEDANCE_CACHE
_IMPEDANCE_CACHE.clear()

bore_length = 0.328
n_cp = 12
positions = np.linspace(0, bore_length, n_cp)

# Test 1: Perfect cylindrical bore (clarinet-like)
radii_cyl = np.full(n_cp, 0.007)  # 7mm constant
bore_cyl = list(zip(positions.tolist(), radii_cyl.tolist()))
result = _compute_impedance_from_bore(bore_cyl, freq_range=(50, 3000), n_freqs=5000)
print('Cylindrical bore (7mm constant):')
print('  Peaks found:', len(result['peak_frequencies']))
print('  Peak freqs:', ['{:.1f}'.format(f) for f in result['peak_frequencies'][:12]])

# Test 2: Typical clarinet bore (slight flare)
radii_clar = np.linspace(0.0065, 0.0075, n_cp)
bore_clar = list(zip(positions.tolist(), radii_clar.tolist()))
result2 = _compute_impedance_from_bore(bore_clar, freq_range=(50, 3000), n_freqs=5000)
print('\nClarinet bore (6.5mm to 7.5mm):')
print('  Peaks found:', len(result2['peak_frequencies']))
print('  Peak freqs:', ['{:.1f}'.format(f) for f in result2['peak_frequencies'][:12]])

# Test 3: With wider range and more freq resolution
_IMPEDANCE_CACHE.clear()
result3 = _compute_impedance_from_bore(bore_cyl, freq_range=(50, 5000), n_freqs=8000)
print('\nCylindrical bore (extended range 50-5000Hz, 8000 pts):')
print('  Peaks found:', len(result3['peak_frequencies']))
print('  Peak freqs:', ['{:.1f}'.format(f) for f in result3['peak_frequencies'][:15]])

# Match to clarinet targets
freqs = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]
matched = _match_peaks_to_targets(result['peak_frequencies'], freqs)
print('\nMatching to clarinet targets:')
for m in matched:
    print('  target={:.1f} actual={:.1f} err={:+.2f} cents'.format(m[0], m[1], m[3]))
