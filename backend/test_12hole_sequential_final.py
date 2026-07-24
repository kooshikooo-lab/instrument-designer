"""Final benchmark: 12-hole pure sequential (best achievable with 12 holes)."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Pure sequential: each note opens one more hole from reed end
# This is the mathematically optimal 12-hole system
chart = []
for i in range(13):
    row = ["open" if j < i else "closed" for j in range(12)] + ["closed"]
    chart.append(row)

print("=== 12-Hole Pure Sequential (Best Achievable) ===")
for n, row in zip(names, chart):
    pat = "".join("O" if x=="open" else "X" for x in row[:12])
    print(f"  {n:>4}: {pat}  R=X")

hole_positions = [176, 293, 338, 445, 532, 610, 636, 700, 760, 820, 880, 940]

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
    grad_bounds=(6.0, 12.0, 16.0, 22.0),
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=100,
                      use_de=True, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
if 'graduated_diameters' in result:
    print(f"Diameters: {[f'{d:.1f}' for d in result['graduated_diameters']]}")

# Full evaluation both registers
free_pos = sorted(result['free_hole_positions'])
all_pos = sorted(free_pos + [80.0])
grad_diam = result.get('graduated_diameters', [11.0]*12)

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos, 
    [d/2.0 for d in grad_diam] + [2.5/2.0],
    [5.0]*12 + [3.0], 37.0, closed_top=True, cone_step=0.5
)

# Chalumeau
chal_chart = [row[:12] + ["closed"] for row in chart]
target_wls = [SPEED_OF_SOUND / f for f in targets]
freqs1 = inst.compute_fingered_frequencies(target_wls, [r[:12]+["closed"] for r in chart], n_register=1)

# Clarion (12th above = 3x frequency)
clarion_targets = [f * 3 for f in targets]
clar_chart = [row[:12] + ["open"] for row in chart]
target_wls2 = [SPEED_OF_SOUND / f for f in [f*3 for f in targets]]
freqs2 = inst.compute_fingered_frequencies(target_wls2, [r[:12]+["open"] for r in chart], n_register=2)

print(f"\n{'Note':<6} {'Target':>8} {'Chalm':>8} {'Err1(c)':>10} {'Clarion':>8} {'Err2(c)':>10}")
print("-" * 60)
err1_list, err2_list = [], []
for n, t1, t2, f1, f2 in zip(names, targets, [f*3 for f in targets], 
                              inst.compute_fingered_frequencies(target_wls, [r[:12]+["closed"] for r in chart], n_register=1),
                              inst.compute_fingered_frequencies([SPEED_OF_SOUND/(f*3) for f in targets], [r[:12]+["open"] for r in chart], n_register=2)):
    c1 = 1200 * np.log2(f1/t1) if f1 > 0 else 0
    c2 = 1200 * np.log2(f2/(t1*3)) if f2 > 0 else 0
    err1_list.append(c1)
    err2_list.append(c2)
    print(f"  {n:<6} {t1:>8.1f} {f1:>8.1f} {c1:>+10.1f}  {t1*3:>8.1f} {f2:>8.1f} {c2:>+10.1f}")

err1_arr = np.array(err1_list)
err2_arr = np.array(err2_list)
off1 = np.median(err1_arr); off2 = np.median(err2_arr)
rms1 = np.sqrt(np.mean((err1_arr-off1)**2))
rms2 = np.sqrt(np.mean((err2_arr-off2)**2))
print(f"\nChalumeau: offset={off1:+.1f}c RMS={rms1:.2f}c")
print(f"Clarion:   offset={off2:+.1f}c RMS={rms2:.2f}c")

# Twelfths
twelfths = [1200*np.log2((f2/f1)/3) for f1,f2 in zip(freqs1, freqs2) if f1>0 and f2>0]
print(f"Twelfths:  RMS={np.sqrt(np.mean(np.array(twelfths)**2)):.2f}c")