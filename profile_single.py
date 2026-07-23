"""Profile: time a single OpenWInD evaluation with UNIQUE bore profiles."""
import sys, os, time, random
sys.path.insert(0, '.')
from backend.optimizer import _compute_impedance_from_bore

bore = []
for line in open('backend/reference_instruments/penny_whistle_D.csv'):
    line = line.strip()
    if not line or line.startswith('#'):
        continue
    parts = line.split()
    if len(parts) >= 2:
        bore.append((float(parts[0]), float(parts[1])))

print("Bore: {} points, length={:.3f}m".format(len(bore), bore[-1][0]))

# Time 5 evaluations with UNIQUE bore profiles (different radii each time)
times = []
for i in range(5):
    # Perturb radii slightly so cache doesn't match
    perturbed = [(pos, rad * (1.0 + random.uniform(-0.01, 0.01))) for pos, rad in bore]
    t0 = time.time()
    _compute_impedance_from_bore(perturbed, freq_range=(50, 3000), n_freqs=5000)
    t1 = time.time()
    elapsed = t1 - t0
    times.append(elapsed)
    print("  Eval {}: {:.3f}s".format(i+1, elapsed))

avg = sum(times) / len(times)
print("\nAverage: {:.3f}s per evaluation".format(avg))
print("For pop=20, gen=10: 200 evals = {:.0f}s = {:.1f}min".format(avg * 200, avg * 200 / 60))
print("For pop=40, gen=50: 2000 evals = {:.0f}s = {:.1f}min".format(avg * 2000, avg * 2000 / 60))
