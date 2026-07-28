"""Quick accuracy + speed test on one reference instrument."""
import sys, os, time
sys.path.insert(0, '.')
import numpy as np
from backend.optimizer import _compute_impedance_from_bore, BoreOptimizer

bore = []
for line in open('backend/reference_instruments/penny_whistle_D.csv'):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    parts = line.split()
    if len(parts) >= 2:
        bore.append((float(parts[0]), float(parts[1])))

print("Bore: {} points, length={:.3f}m".format(len(bore), bore[-1][0]))

result = _compute_impedance_from_bore(bore, freq_range=(50, 3000), n_freqs=1000)
peak_freqs = result['peak_frequencies']
print("Ground truth peaks: {}".format(len(peak_freqs)))
for i, f in enumerate(peak_freqs[:8]):
    print("  Peak {}: {:.1f} Hz".format(i+1, f))

target_freqs = peak_freqs[:6]

# --- Serial test ---
print("\n=== SERIAL (n_workers=1) ===")
t0 = time.time()
optimizer_s = BoreOptimizer(
    target_frequencies=target_freqs,
    n_control_points=8,
    bore_length=bore[-1][0],
    min_radius=0.003,
    max_radius=0.020,
    pop_size=20,
    n_generations=10,
    seed=42,
    n_workers=1,
)
result_s = optimizer_s.run(verbose=False)
t_serial = time.time() - t0
best_s = result_s['best_candidates'][0]
detailed_s = optimizer_s.evaluate_single(best_s['variables'])

total_err_s = sum(abs(m['error_cents']) for m in detailed_s['matched_frequencies'])
avg_err_s = total_err_s / len(detailed_s['matched_frequencies'])
print("Time: {:.1f}s".format(t_serial))
print("Avg error: {:.1f} cents".format(avg_err_s))
for m in detailed_s['matched_frequencies']:
    print("  {:7.1f} -> {:7.1f}  ({:+.1f} cents)".format(m['target'], m['actual'], m['error_cents']))

# --- Parallel test ---
import os
ncpu = os.cpu_count() or 1
print("\n=== PARALLEL (n_workers={}) ===".format(ncpu))
t0 = time.time()
optimizer_p = BoreOptimizer(
    target_frequencies=target_freqs,
    n_control_points=8,
    bore_length=bore[-1][0],
    min_radius=0.003,
    max_radius=0.020,
    pop_size=20,
    n_generations=10,
    seed=42,
    n_workers=ncpu,
)
result_p = optimizer_p.run(verbose=False)
t_parallel = time.time() - t0
best_p = result_p['best_candidates'][0]
detailed_p = optimizer_p.evaluate_single(best_p['variables'])

total_err_p = sum(abs(m['error_cents']) for m in detailed_p['matched_frequencies'])
avg_err_p = total_err_p / len(detailed_p['matched_frequencies'])
print("Time: {:.1f}s".format(t_parallel))
print("Avg error: {:.1f} cents".format(avg_err_p))
for m in detailed_p['matched_frequencies']:
    print("  {:7.1f} -> {:7.1f}  ({:+.1f} cents)".format(m['target'], m['actual'], m['error_cents']))

# --- Summary ---
print("\n=== SUMMARY ===")
print("Serial:   {:.1f}s, {:.1f} cents".format(t_serial, avg_err_s))
print("Parallel: {:.1f}s, {:.1f} cents".format(t_parallel, avg_err_p))
if t_serial > 0:
    print("Speedup:  {:.2f}x".format(t_serial / t_parallel))
