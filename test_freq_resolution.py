"""Test: how many frequency points do we actually need?"""
import sys, os, time
sys.path.insert(0, '.')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
from openwind import ImpedanceComputation
from scipy.signal import find_peaks

bore_str = "test_bore.csv"
with open(bore_str, 'w') as f:
    for i in range(12):
        f.write(f"{i * 0.65/11} 0.0074\n")

targets = np.array([261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6])

for n_freqs in [1000, 2000, 3000, 5000]:
    t0 = time.time()
    freqs = np.linspace(50, 10500, n_freqs)
    ic = ImpedanceComputation(freqs, bore_str, unit="m", diameter=False, temperature=20.0)
    freq = np.array(ic.frequencies)
    Z = np.array(ic.impedance)
    mag = np.abs(Z)
    dt_sim = time.time() - t0
    
    # Detect peaks
    peak_height = np.max(mag) * 0.02
    peaks, _ = find_peaks(mag, height=peak_height, distance=2, prominence=peak_height * 0.5)
    
    # Match to targets
    peak_freqs = freq[peaks]
    matched = []
    for tf in targets:
        idx = np.argmin(np.abs(peak_freqs - tf))
        actual = peak_freqs[idx]
        cents = 1200.0 * np.log2(actual / tf) if tf > 0 and actual > 0 else 1e10
        matched.append((tf, actual, cents))
    
    raw_cents = np.array([m[2] for m in matched])
    offset = np.median(raw_cents)
    corrected = np.abs(raw_cents - offset)
    rms = np.sqrt(np.mean(corrected**2))
    
    print(f"n_freqs={n_freqs:5d}: {dt_sim:.3f}s, {len(peaks)} peaks, "
          f"RMS={rms:.2f} cents, offset={offset:.1f}")
    for tf, actual, cents in matched:
        print(f"  target={tf:.1f} actual={actual:.1f} cents={cents:+.1f}")

os.remove(bore_str)
