"""Test: CORRECT bass clarinet - bell-end-first openings (real physics)."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

# Bass clarinet written D2 (73.4Hz) to D3 (146.8Hz) - chalumeau register
# H1 = closest to REED (LH1), H12 = closest to BELL
# Real physics: open from BELL END first (H12, H11, H10... toward H1)
# D2 (lowest): all closed
# D#2: open H12 (nearest bell)
# E2: open H11+H12
# F2: open H10+H11+H12
# etc. up to D3: H1-H12 all open

# This is the CORRECT physics - exactly what ChatGPT gave us
# 13 notes, 12 holes, register key at 80mm (closed for chalumeau)

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Bell-end-first fingering chart (12 holes H1..H12 from reed to bell, R=register)
# D2: all closed
# D#2: H12 open (bell-end hole)
# E2: H11+H12 open
# F2: H10+H11+H12 open
# F#2: H9+H10+H11+H12 open
# G2: H8+H9+H10+H11+H12 open
# G#2: H7+H8+H9+H10+H11+H12 open
# A2: H6+H7+H8+H9+H10+H11+H12 open
# A#2: H5+H6+H7+H8+H9+H10+H11+H12 open
# B2: H4+H5+H6+H7+H8+H9+H10+H11+H12 open
# C3: H3+H4+H5+H6+H7+H8+H9+H10+H11+H12 open
# C#3: H2+H3+H4+H5+H6+H7+H8+H9+H10+H11+H12 open
# D3: H1+H2+H3+H4+H5+H6+H7+H8+H9+H10+H11+H12 open (all 12 open)

# This is PURELY sequential from bell end - but real clarinet has cross-fingerings!
# Let me add cross-fingerings for the chromatics that need them:
# F#2, G#2, A#2, C#3 need cross-fingerings

# ChatGPT's cross-fingering chart (bell-end first, H1=reed, H12=bell):
chart = [
    # D2: all closed
    [0,0,0,0,0,0,0,0,0,0,0,0, 0],
    # D#2: H7+H9 open (cross: H8 closed between)
    [0,0,0,0,0,0,1,0,1,0,0,0, 0],
    # E2: H7 open
    [0,0,0,0,0,0,1,0,0,0,0,0, 0],
    # F2: H6+H7 open
    [0,0,0,0,0,1,1,0,0,0,0,0, 0],
    # F#2: H5+H7+H8 open (cross: H6 closed)
    [0,0,0,0,1,0,1,1,0,0,0,0, 0],
    # G2: H5+H6+H7 open
    [0,0,0,0,1,1,1,0,0,0,0,0, 0],
    # G#2: H4+H6+H7+H8 open (cross: H5 closed)
    [0,0,0,1,0,1,1,1,0,0,0,0, 0],
    # A2: H4+H5+H6+H7 open
    [0,0,0,1,1,1,1,0,0,0,0,0, 0],
    # A#2: H3+H5+H6+H7+H8 open (cross: H4 closed)
    [0,0,1,0,1,1,1,1,0,0,0,0, 0],
    # B2: H3+H4+H5+H6+H7 open
    [0,0,1,1,1,1,1,0,0,0,0,0, 0],
    # C3: H2+H4+H5+H6+H7+H8+H11 open (cross: H3 closed, H11 vent)
    [0,1,0,1,1,1,1,1,0,0,1,0, 0],
    # C#3: H1+H3+H4+H5+H6+H7+H9+H12 open (cross: H2 closed, H12 vent)
    [1,0,1,1,1,1,1,0,1,0,0,1, 0],
    # D3: H1-H7 open (sequential from reed end now)
    [1,1,1,1,1,1,1,0,0,0,0,0, 0],
]

chart_str = [["open" if x else "closed" for x in row] for row in chart]

print("=== CORRECT Bell-End-First Fingering Chart (ChatGPT) ===")
for n, row in zip(names, chart_str):
    pat = "".join("O" if x=="open" else "X" for x in row[:12])
    print(f"  {n:>4}: {pat}  R={'O' if row[12]=='open' else 'X'}")

# INITIAL GUESSES: holes near BELL for low notes, toward REED for high notes
# H12 (opens for D#2) should be NEAR BELL (~1000-1100mm for ~77Hz)
# H11 (opens for E2) slightly toward reed
# ...
# H1 (opens for D3) should be NEAR REED (~150-200mm for ~147Hz)
# Effective length = 343000/(4*f) ≈ 1100mm at 77Hz, 580mm at 147Hz
# With small holes, position > effective length

# Hole positions from REED (H1) to BELL (H12):
# H1 (reed end, opens last for D3): ~200mm
# H2: ~300mm  
# H3: ~400mm
# H4: ~500mm
# H5: ~600mm
# H6: ~700mm
# H7 (opens for E2): ~800mm
# H8: ~880mm
# H9: ~950mm
# H10: ~1000mm
# H11: ~1050mm
# H12 (bell end, opens first for D#2): ~1100mm

hole_positions = [200, 300, 400, 500, 600, 700, 800, 880, 950, 1000, 1050, 1100]

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

# Evaluate
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