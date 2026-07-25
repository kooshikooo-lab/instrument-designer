"""Quick bore length check."""
import sys
sys.path.insert(0, '.')
import numpy as np
from backend.bore_optimizer_lbfgs import _pava_isotonic, _compute_impedance, _match_peaks

v = 331.3 + 0.606 * 20.0
bore_len = v / (4 * 261.6)
print("Auto bore length:", round(bore_len*1000, 0), "mm")

targets = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]

for r in [0.005, 0.007, 0.0074, 0.010]:
    radii = np.full(12, r)
    positions = np.linspace(0, bore_len, 12)
    bore = list(zip(positions.tolist(), radii.tolist()))
    peak_freqs, _ = _compute_impedance(bore, (50, 3000), 5000, 20.0)
    matched = _match_peaks(peak_freqs, targets)
    raw_cents = np.array([m[3] for m in matched])
    offset = np.median(raw_cents)
    corrected = np.abs(raw_cents - offset)
    rms = float(np.sqrt(np.mean(corrected**2)))
    print("r={:.0f}mm: peaks={}, RMS={:.1f}, offset={:+.1f}".format(r*1000, len(peak_freqs), rms, offset))
    for tf, actual, _, ec in matched[:3]:
        print("  {:.1f} -> {:.1f} ({:+.1f} cents)".format(tf, actual, ec))
