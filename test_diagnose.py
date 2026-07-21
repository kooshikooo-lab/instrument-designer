"""Diagnose optimizer convergence issues."""
import sys
sys.path.insert(0, r"C:\instrument-designer")

import numpy as np
from backend.optimizer import _compute_impedance_from_bore, _match_peaks_to_targets, BoreOptimizer

# Known good bore (penny whistle D)
known_bore = [
    (0.0, 0.0075), (0.05, 0.0075), (0.1, 0.0075),
    (0.15, 0.0075), (0.2, 0.0075), (0.25, 0.0075), (0.3, 0.0075),
]

# Compute what the known bore actually produces
result = _compute_impedance_from_bore(known_bore, freq_range=(50, 3000), n_freqs=2000, temperature=20.0)
print("=== KNOWN BORE ANALYSIS ===")
print(f"Peak count: {len(result['peak_frequencies'])}")
for i, (f, m) in enumerate(zip(result['peak_frequencies'][:8], result['peak_magnitudes'][:8])):
    print(f"  Peak {i+1}: {f:.2f} Hz (|Z|={m:.2e})")

# Test: can the optimizer REPRODUCE the known bore's peaks?
# Target: the peaks the known bore produces
target = result['peak_frequencies'][:4]  # first 4 peaks
print(f"\nTarget frequencies: {target}")

# Run optimizer with GOOD parameters
print("\n=== RUNNING OPTIMIZER ===")
opt = BoreOptimizer(
    target_frequencies=target.tolist(),
    n_control_points=7,
    bore_length=0.300,
    min_radius=0.005,
    max_radius=0.012,
    pop_size=50,
    n_generations=100,
    seed=42,
)
print(f"Bore length: {opt.bore_length:.3f} m")
print(f"Freq range: {opt.freq_range}")
print(f"Running 50 pop x 100 gen...")

result = opt.run(verbose=False)
print(f"Designs: {len(result['designs'])}")

# Analyze best candidate
best = result['best_candidates'][0]
print(f"\nBest candidate:")
print(f"  freq_err={best['objectives']['frequency_accuracy']:.2f}")
for m in best['matched_frequencies']:
    print(f"  {m['target']:7.1f} -> {m['actual']:7.1f} Hz  ({m['error_cents']:+.1f} cents)")

# Also try: what if we just use the known bore's variables?
print("\n=== DIRECT REPRODUCTION TEST ===")
known_vars = [0.0075] * 7
detailed = opt.evaluate_single(known_vars)
print("Known bore evaluation:")
for m in detailed['matched_frequencies']:
    print(f"  {m['target']:7.1f} -> {m['actual']:7.1f} Hz  ({m['error_cents']:+.1f} cents)")
print(f"  All peaks: {[f'{p:.1f}' for p in detailed['all_peak_frequencies'][:8]]}")

# Check: does the optimizer even have enough frequency resolution?
print("\n=== FREQUENCY RESOLUTION TEST ===")
result_low = _compute_impedance_from_bore(known_bore, freq_range=(50, 3000), n_freqs=500, temperature=20.0)
result_high = _compute_impedance_from_bore(known_bore, freq_range=(50, 3000), n_freqs=2000, temperature=20.0)
result_ultra = _compute_impedance_from_bore(known_bore, freq_range=(50, 3000), n_freqs=5000, temperature=20.0)

print(f"500 freq samples:  peaks = {[f'{p:.2f}' for p in result_low['peak_frequencies'][:4]]}")
print(f"2000 freq samples: peaks = {[f'{p:.2f}' for p in result_high['peak_frequencies'][:4]]}")
print(f"5000 freq samples: peaks = {[f'{p:.2f}' for p in result_ultra['peak_frequencies'][:4]]}")
