"""Final: Reed-end sequential base + proper cross-fingerings (working approach)."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# WORKING APPROACH: Reed-end sequential base + cross-fingerings for chromatics
# H1 = closest to reed, H12 = closest to bell
# Sequential base: each note opens one more hole from reed end
# Cross-fingerings: additional holes for chromatics

chart = [
    # D2: all closed
    [0,0,0,0,0,0,0,0,0,0,0,0, 0],
    # D#2: H1 open (side key near reed)
    [1,0,0,0,0,0,0,0,0,0,0,0, 0],
    # E2: H1+H2 open
    [1,1,0,0,0,0,0,0,0,0,0,0, 0],
    # F2: H1+H2+H3 open
    [1,1,1,0,0,0,0,0,0,0,0,0, 0],
    # F#2: H1+H2+H3+H4 (F# key)
    [1,1,1,1,0,0,0,0,0,0,0,0, 0],
    # G2: H1+H2+H3+H5 (RH1)
    [1,1,1,0,1,0,0,0,0,0,0,0, 0],
    # G#2: H1+H2+H3+H4+H5 (G# key)
    [1,1,1,1,1,0,0,0,0,0,0,0, 0],
    # A2: H1+H2+H5 (LH1+LH2+RH1)
    [1,1,0,0,1,0,0,0,0,0,0,0, 0],
    # A#2: H1+H5 (LH1+RH1) or side Bb key (H8)
    [1,0,0,0,1,0,0,1,0,0,0,0, 0],
    # B2: H1+H5+H6 (LH1+RH1+RH2)
    [1,0,0,0,1,1,0,0,0,0,0,0, 0],
    # C3: H1+H5+H6+H7 (LH1+RH1+RH2+RH3)
    [1,0,0,0,1,1,1,0,0,0,0,0, 0],
    # C#3: H1+H5+H6+H7+H8 (side C#)
    [1,0,0,0,1,1,1,1,0,0,0,0, 0],
    # D3: H1-H8 open (all main holes)
    [1,1,1,1,1,1,1,1,0,0,0,0, 0],
]

chart_str = [["open" if x else "closed" for x in row] for row in chart]

print("=== Realistic Reed-End Cross-Fingering Chart ===")
for n, row in zip(names, chart_str):
    pat = "".join("O" if x=="open" else "X" for x in row[:12])
    print(f"  {n:>4}: {pat}  R={'O' if row[12]=='open' else 'X'}")

# Initial guess: working 12-hole sequential positions
hole_positions = [176, 293, 338, 445, 532, 610, 636, 700, 760, 820, 880, 940]

print(f"\nInitial: {[f'{p:.0f}' for p in hole_positions]}")

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart_str,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.0, 1.0),
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

# Evaluate both registers
free_pos = sorted(result['free_hole_positions'])
all_pos = sorted(free_pos + [80.0])
grad_diam = result.get('graduated_diameters', [11.0]*12)

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos, 
    [d/2.0 for d in grad_diam] + [2.5/2.0],
    [5.0]*12 + [3.0], 37.0, closed_top=True, cone_step=0.5
)

# Chalumeau (register closed)
chalumeau_chart = [row[:12] + ["closed"] for row in chart_str]
target_wls = [SPEED_OF_SOUND / f for f in targets]
freqs1 = inst.compute_fingered_frequencies(target_wls, chalumeau_chart, n_register=1)

# Clarion (register open, 12th above = 3x frequency)
clarion_targets = [f * 3 for f in targets]
clarion_chart = [row[:12] + ["open"] for row in chart_str]
target_wls2 = [SPEED_OF_SOUND / f for f in clarion_targets]
freqs2 = inst.compute_fingered_frequencies(target_wls2, clarion_chart, n_register=2)

print(f"\n{'Note':<6} {'Target':>8} {'Chalm':>8} {'Err1(c)':>10} {'Clar':>8} {'Err2(c)':>10}")
print("-" * 60)
err1_list, err2_list = [], []
for n, t1, t2, f1, f2 in zip(names, targets, clarion_targets, freqs1, freqs2):
    c1 = 1200 * np.log2(f1/t1) if f1 > 0 else 0
    c2 = 1200 * np.log2(f2/t2) if f2 > 0 else 0
    err1_list.append(c1)
    err2_list.append(c2)
    print(f"  {n:<6} {t1:>8.1f} {f1:>8.1f} {c1:>+10.1f}  {t2:>8.1f} {f2:>8.1f} {c2:>+10.1f}")

err1_arr = np.array(err1_list)
err2_arr = np.array(err2_list)
off1 = np.median(err1_arr); off2 = np.median(err2_arr)
rms1 = np.sqrt(np.mean((err1_arr-off1)**2))
rms2 = np.sqrt(np.mean((err2_arr-off2)**2))
print(f"\nChalumeau: offset={off1:+.1f}c RMS={rms1:.2f}c")
print(f"Clarion:   offset={off2:+.1f}c RMS={rms2:.2f}c")