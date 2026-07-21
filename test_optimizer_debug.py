"""Debug test of the bore optimizer."""
import sys
sys.path.insert(0, r"C:\instrument-designer")

from backend.optimizer import _compute_impedance_from_bore
import numpy as np

# Test with a simple cylindrical bore
bore = [(0.0, 0.005), (0.1, 0.005), (0.2, 0.005), (0.3, 0.005), (0.4, 0.005), (0.5, 0.005)]
result = _compute_impedance_from_bore(bore, freq_range=(100, 2000), n_freqs=500)

print("Peak frequencies:", result["peak_frequencies"])
print("Peak magnitudes:", result["peak_magnitudes"])
print()
print("Number of peaks:", len(result["peak_frequencies"]))
print()

# Target frequencies
target = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3]
print("Target frequencies:", target)
print()

# Check if peaks are close to targets
for tf in target:
    idx = np.argmin(np.abs(result["peak_frequencies"] - tf))
    actual = result["peak_frequencies"][idx]
    error_cents = 1200 * np.log2(actual / tf)
    print(f"  Target {tf:.1f} Hz -> Closest peak {actual:.1f} Hz (error: {error_cents:.1f} cents)")
