"""Test: ChatGPT cross-fingering chart with proper 12-hole + register implementation."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

# Targets for 12-hole chromatic (D2 to D3, chalumeau register)
targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# ChatGPT cross-fingering chart (13 notes x 13 holes)
# H1-H7: primary (diatonic), H8-H10: corrective, H11-H12: vents, R: register
# 1=open, 0=closed
chart_binary = [
    # D2: all closed
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    # D#2: H7+H9 open (H8 closed between)
    [0,0,0,0,0,0,1,0,1,0,0,0,0],
    # E2: H7 only
    [0,0,0,0,0,0,1,0,0,0,0,0,0],
    # F2: H6+H7
    [0,0,0,0,0,1,1,0,0,0,0,0,0],
    # F#2: H5+H7+H8 (H6 closed)
    [0,0,0,0,1,0,1,1,0,0,0,0,0],
    # G2: H5+H6+H7
    [0,0,0,0,1,1,1,0,0,0,0,0,0],
    # G#2: H4+H6+H7+H8 (H5 closed)
    [0,0,0,1,0,1,1,1,0,0,0,0,0],
    # A2: H4+H5+H6+H7
    [0,0,0,1,1,1,1,0,0,0,0,0,0],
    # Bb2: H3+H5+H6+H7+H8 (H4 closed)
    [0,0,1,0,1,1,1,1,0,0,0,0,0],
    # B2: H3+H4+H5+H6+H7
    [0,0,1,1,1,1,1,0,0,0,0,0,0],
    # C3: H2+H4+H5+H6+H7+H8+H11 (H3 closed)
    [0,1,0,1,1,1,1,1,0,0,1,0,0],
    # C#3: H1+H3+H4+H5+H6+H7+H9+H12 (H2 closed)
    [1,0,1,1,1,1,1,0,1,0,0,1,0],
    # D3: H1-H7 open
    [1,1,1,1,1,1,1,0,0,0,0,0,0],
]

# Convert to string format
chart_str = [["open" if x else "closed" for x in row] for row in chart_binary]

print("=== ChatGPT Cross-Fingering Chart ===")
for i, (name, row) in enumerate(zip(names, chart_binary)):
    pat = "".join("O" if x else "X" for x in row[:12])
    reg = "O" if row[12] else "X"
    print(f"  {name:>4}: {pat}  R={reg}")

# Initial guess: holes distributed along bore with bell-end first for cross-fingerings
# H1 (closest to reed) to H12 (closest to bell), R at 80mm
hole_positions = [500, 600, 700, 800, 900, 950, 1050, 1100, 1150, 1120, 650, 1180]

print(f"\nInitial positions: {[f'{p:.0f}' for p in hole_positions]}")

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
    register_weights=(0.15, 1.0),
    optimize_grad=True,
    grad_bounds=(6.0, 12.0, 16.0, 22.0),
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80,
                      use_de=True, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
if 'graduated_diameters' in result:
    print(f"Diameters: {[f'{d:.1f}' for d in result['graduated_diameters']]}")

# Detailed evaluation
free_pos = sorted(result['free_hole_positions'])
all_pos = sorted(free_pos + [80.0])
grad_diam = result.get('graduated_diameters', [11.0]*12)

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos, 
    [d/2.0 for d in grad_diam] + [2.5/2.0],
    [5.0]*12 + [3.0], 37.0, closed_top=True, cone_step=0.5
)

target_wls = [SPEED_OF_SOUND / f for f in targets]
freqs = inst.compute_fingered_frequencies(target_wls, chart_str, n_register=1)

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