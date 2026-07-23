"""Test: ChatGPT cross-fingering chart with proper initial guess (bell-end first)."""
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

# ChatGPT chart: [H1..H12, R]
chart_str = [
    ["closed"]*12 + ["closed"],  # D
    ["closed"]*6 + ["open","closed","open"] + ["closed"]*3 + ["closed"],  # D#
    ["closed"]*6 + ["open"] + ["closed"]*5 + ["closed"],  # E
    ["closed"]*5 + ["open","open"] + ["closed"]*5 + ["closed"],  # F
    ["closed"]*4 + ["open","closed","open","open"] + ["closed"]*4 + ["closed"],  # F#
    ["closed"]*4 + ["open","open","open"] + ["closed"]*5 + ["closed"],  # G
    ["closed"]*3 + ["open","closed","open","open","open"] + ["closed"]*4 + ["closed"],  # G#
    ["closed"]*3 + ["open","open","open","open"] + ["closed"]*5 + ["closed"],  # A
    ["closed"]*2 + ["open","closed","open","open","open","open"] + ["closed"]*4 + ["closed"],  # Bb
    ["closed"]*2 + ["open","open","open","open","open"] + ["closed"]*5 + ["closed"],  # B
    ["closed","open","closed","open","open","open","open","open","closed","closed","open","closed","closed"],  # C
    ["open","closed","open","open","open","open","open","closed","open","closed","closed","open","closed"],  # C#
    ["open"]*7 + ["closed"]*5 + ["closed"],  # D
]

print("=== ChatGPT Chart (verified) ===")
for i, (name, row) in enumerate(zip(names, chart_str)):
    pat = "".join("O" if s=="open" else "X" for s in row[:12])
    first_open = next((j+1 for j,s in enumerate(row[:12]) if s=="open"), None)
    print(f"  {name}: {pat}  first_open=H{first_open}")

# Proper initial guess based on reverse-order logic:
# H1 (closest to reed) → H7 (farthest primary) → H12 (farthest overall)
# E2 (~82Hz, first open=H7): L_eff ≈ 1040mm → H7 near bell
# F2 (~87Hz, first open=H6): L_eff ≈ 985mm
# ...
# D3 (~147Hz, first open=H1): L_eff ≈ 583mm → H1 at ~450mm

# Effective length targets (1st register):
# f = c/(4*L_eff) → L_eff = 343000/(4*f) in mm
# But holes are partially effective, so position > L_eff_target
# Use 1.1x multiplier as rough correction for partial venting
L_targets = [343000/(4*t) for t in targets]
# H7 is first open for D#/E (note 1-2), H6 for F (note 3), etc.
# Map: note i has first_open = H(7 - floor(i/2) + ...)
# This is approximate; let the optimizer refine

# Holes from bell-end (H7) toward reed (H1):
# H7 → target for D#/E (avg ~1070mm) → position ~1050mm
# H6 → target for F (~982mm) → position ~960mm
# H5 → target for F#/G (avg ~920mm) → position ~900mm
# H4 → target for G#/A (avg ~800mm) → position ~780mm
# H3 → target for Bb/B (avg ~700mm) → position ~680mm
# H2 → target for C (~585mm) → position ~570mm
# H1 → target for C#/D (avg ~540mm) → position ~520mm
# H8 (corrective): between H7 and bell end → ~1080mm
# H9 (corrective): between H8 and bell → ~1130mm
# H10 (corrective): between H5 and H6 → ~930mm
# H11 (vent): between H2 and H3 → ~620mm
# H12 (vent): past H7 near bell → ~1150mm

hole_positions = [520, 570, 680, 780, 900, 960, 1050, 1080, 1130, 930, 620, 1150]

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
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80,
                      use_de=True, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
positions = result['free_hole_positions']
print(f"Holes: {[f'{p:.0f}' for p in positions]}")
