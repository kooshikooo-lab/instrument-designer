"""Test: 12-hole chromatic with graduated diameter optimization."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]

N_FREE = 12
N_FIXED = 1

chart = []
for i in range(13):
    row = ["closed"] * (N_FREE + N_FIXED)
    for j in range(i):
        row[j] = "open"
    row[N_FREE] = "closed"
    chart.append(row)

hole_positions = [88, 176, 234, 293, 338, 392, 445, 488, 532, 571, 610, 636]

print("=== 12-hole: optimizing positions + graduated diameters ===")
t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.15, 1.0),
    optimize_grad=True,
    grad_bounds=(6.0, 14.0, 10.0, 20.0),
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=60,
                      use_de=False, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
positions = result['free_hole_positions']
if 'd_min_mm' in result:
    print(f"d_min={result['d_min_mm']:.1f}mm d_max={result['d_max_mm']:.1f}mm")
    for i, (p, d) in enumerate(zip(positions, result['hole_diameters'])):
        print(f"  Hole {i+1}: pos={p:.0f}mm dia={d:.1f}mm")
