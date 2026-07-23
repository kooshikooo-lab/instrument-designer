"""Quick test: global optimizer with DE for 12-hole chromatic."""
import sys, math, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

N_FREE = 12
N_FIXED = 1

chart = []
for i in range(13):
    row = ["closed"] * (N_FREE + N_FIXED)
    for j in range(i):
        row[j] = "open"
    row[N_FREE] = "closed"
    chart.append(row)

# Initial guess from 7-hole interpolation
hole_positions = [85, 108, 143, 188, 233, 278, 323, 367, 412, 457, 501, 546]

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=1,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
)

print("Phase 1: DE (10 iter, small pop)...")
result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80, use_de=True, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Result: RMS={result['final_rms_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
