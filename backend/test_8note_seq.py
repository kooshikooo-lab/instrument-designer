"""Test: Optimize with exact working config (8 notes, sequential, perfect 12ths)."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

# 8 notes: D2, E2, F#2, G2, A2, B2, C#3, D3
targets_1st = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]
targets_2nd = [t * 3 for t in targets_1st]  # perfect 12ths

# Sequential fingerings: each note opens one more hole from the top
# H1=reed end, H7=bell end
chart = []
for i in range(8):
    row = ["open" if j < i else "closed" for j in range(7)] + ["closed"]
    chart.append(row)

print("=== 8-note Sequential (perfect 12ths targets) ===")
for i, (t1, t2, row) in enumerate(zip(targets_1st, targets_2nd, chart)):
    pat = "".join("O" if s=="open" else "X" for s in row[:7])
    print(f"  {t1:.1f}/{t2:.1f} Hz: {pat} R={'X' if i<8 else 'O'}")

hole_positions = [176, 293, 338, 445, 532, 610, 636]

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets_1st,  # optimize for 1st register
    fingering_chart=chart,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,              # evaluate 2nd register too
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(1.0, 0.0),  # only optimize 1st register
    optimize_grad=False,
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80,
                      use_de=False, verbose=True)
t1 = time.time()
print(f'\nTime: {t1-t0:.0f}s')
print(f'Reg1 RMS: {result["final_rms_1st_cents"]:.2f}c')
print(f'Reg2 RMS: {result["final_rms_2nd_cents"]:.2f}c')
print(f'Holes: {[f"{p:.0f}" for p in result["free_hole_positions"]]}')

# Evaluate perfect 12ths
free_pos = sorted(result['free_hole_positions'])
all_pos = sorted(free_pos + [80.0])
all_dia = [11.0]*7 + [2.5]
all_len = [5.0]*7 + [3.0]

inst = tmm_instrument_from_radii(
    positions=all_pos, radii=[d/2.0 for d in all_dia],
    bore_radius=12.5, bore_length=1211.3, closed_end=True,
    hole_lengths=all_len,
)
n_total = len(all_pos)
reg_idx = all_pos.index(80.0)
tonehole_indices = sorted([j for j in range(n_total) if j != reg_idx])

reg1_fs = []
reg2_fs = []
for i in range(8):
    f = ["closed"] * n_total
    for j in tonehole_indices[:i]:
        f[j] = "open"
    f[reg_idx] = "closed"
    reg1_fs.append(f)
    f2 = f.copy()
    f2[reg_idx] = "open"
    reg2_fs.append(f2)

target_wls1 = [SPEED_OF_SOUND / f for f in targets_1st]
target_wls2 = [SPEED_OF_SOUND / f for f in targets_2nd]
freqs1 = inst.compute_fingered_frequencies(target_wls1, reg1_fs, n_register=1)
freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)

print("\n=== Post-optimization evaluation ===")
c1_all, c2_all, c12_all = [], [], []
for n, t1, t2, f1, f2 in zip(["D2","E2","F#2","G2","A2","B2","C#3","D3"], 
                              targets_1st, targets_2nd, freqs1, freqs2):
    c1 = 1200*np.log2(f1/t1) if f1 > 0 else 0
    c2 = 1200*np.log2(f2/t2) if f2 > 0 else 0
    c12 = 1200*np.log2((f2/f1)/3.0) if f1 > 0 and f2 > 0 else 0
    c1_all.append(c1); c2_all.append(c2); c12_all.append(c12)
    print(f"  {n}: 1st={c1:+.0f}c  2nd={c2:+.0f}c  12th={c12:+.0f}c")

c1_arr = np.array(c1_all); c2_arr = np.array(c2_all); c12_arr = np.array(c12_all)
print(f"\n  1st register: offset={np.median(c1_arr):+.0f}c RMS={np.sqrt(np.mean((c1_arr-np.median(c1_arr))**2)):.2f}c")
print(f"  2nd register: offset={np.median(c2_arr):+.0f}c RMS={np.sqrt(np.mean((c2_arr-np.median(c2_arr))**2)):.2f}c")
print(f"  Twelfths: RMS={np.sqrt(np.mean(c12_arr**2)):.2f}c")