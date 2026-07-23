"""Test: ChatGPT cross-fingering chart with graduated hole sizes."""
import sys, math, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

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

# Initial guess: H1 near reed, H7 near bell, others distributed
# H1: ~450mm, H2: ~550mm, H3: ~650mm, H4: ~750mm, H5: ~850mm, H6: ~950mm, H7: ~1050mm
# H8-H10 (corrective): between H7 and bell ~1100-1150mm
# H11 (vent): between H2-H3 ~600mm
# H12 (vent): near bell ~1150mm
hole_positions = [450, 550, 650, 750, 850, 950, 1050, 1100, 1150, 1120, 600, 1180]

print("=== ChatGPT Cross-Fingering Chart with Graduated Diameters ===")
print(f"Initial positions: {[f'{p:.0f}' for p in hole_positions]}")

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart_str,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,  # base (ignored when optimize_grad=True)
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.0, 1.0),        # only optimize 2nd register
    optimize_grad=True,              # enable graduated diameters
    grad_bounds=(6.0, 12.0, 14.0, 22.0),  # d_min range, d_max range
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