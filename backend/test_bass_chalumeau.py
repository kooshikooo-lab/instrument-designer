"""Test: Bass clarinet chalumeau register only (no register hole)."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# 13 notes chromatic D2 to D3 (chalumeau register)
targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Sequential fingering: each note opens one more hole from top
chart = []
for i in range(13):
    row = ["open" if j < i else "closed" for j in range(7)] + ["closed"]
    chart.append(row)

# Initial guess: evenly spaced
initial = [i * 1211.3 / 8 for i in range(1, 8)]

print("=== Bass Clarinet Chalumeau Only (7 holes, no register hole) ===")
for i, (n, t, row) in enumerate(zip(names, targets, chart)):
    pat = "".join("O" if s=="open" else "X" for s in row[:7])
    print(f"  {n}: {t:.1f}Hz  {pat}")

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
    fixed_holes=[],
    register_weights=(1.0, 0.0),
    optimize_grad=False,
)

result = opt.optimize(initial_positions=initial, bounds_per_hole=100,
                      use_de=True, verbose=True)
t1 = time.time()

print(f"\nTime: {t1-t0:.0f}s")
print(f"RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")

# Detailed evaluation
free_pos = sorted(result['free_hole_positions'])
all_pos = free_pos
all_dia = [11.0] * 7
all_len = [5.0] * 7

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos, all_dia, all_len, 37.0,
    closed_top=True, cone_step=0.5
)

target_wls = [SPEED_OF_SOUND / f for f in targets]
freqs = inst.compute_fingered_frequencies(target_wls, chart, n_register=1)

print(f"\n{'Note':<6} {'Target':>8} {'Actual':>8} {'Error(c)':>10}")
print("-" * 40)
errors = []
for n, t, f in zip(names, targets, freqs):
    c = 1200 * np.log2(f/t) if f > 0 else 0
    errors.append(c)
    print(f"  {n:<6} {t:>8.1f} {f:>8.1f} {c:>+10.1f}")

err_arr = np.array(errors)
offset = np.median(err_arr)
rms = np.sqrt(np.mean((err_arr - offset)**2))
print(f"\nOffset: {offset:+.1f}c  RMS(relative): {rms:.2f}c")
print(f"Absolute RMS: {np.sqrt(np.mean(err_arr**2)):.2f}c")