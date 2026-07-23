"""Test: ChatGPT cross-fingering chart (bell-end first = correct physics)."""
import sys, math, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# ChatGPT chart: H1=reed end, H12=bell end
# Opens from BELL end (H7) toward REED end (H1) as pitch rises
chart = [
    ["closed"]*12 + ["closed"],  # D: all closed
    ["closed"]*6 + ["open","closed","open"] + ["closed"]*3 + ["closed"],  # D#: H7+H9
    ["closed"]*6 + ["open"] + ["closed"]*5 + ["closed"],  # E: H7
    ["closed"]*5 + ["open","open"] + ["closed"]*5 + ["closed"],  # F: H6+H7
    ["closed"]*4 + ["open","closed","open","open"] + ["closed"]*4 + ["closed"],  # F#: H5+H7+H8
    ["closed"]*4 + ["open","open","open"] + ["closed"]*5 + ["closed"],  # G: H5+H6+H7
    ["closed"]*3 + ["open","closed","open","open","open"] + ["closed"]*4 + ["closed"],  # G#: H4+H6+H7+H8
    ["closed"]*3 + ["open","open","open","open"] + ["closed"]*5 + ["closed"],  # A: H4+H5+H6+H7
    ["closed"]*2 + ["open","closed","open","open","open","open"] + ["closed"]*4 + ["closed"],  # Bb: H3+H5+H6+H7+H8
    ["closed"]*2 + ["open","open","open","open","open"] + ["closed"]*5 + ["closed"],  # B: H3+H4+H5+H6+H7
    ["closed","open","closed","open","open","open","open","open","closed","closed","open","closed","closed"],  # C: H2+H4-H8+H11
    ["open","closed","open","open","open","open","open","closed","open","closed","closed","open","closed"],  # C#: H1+H3-H7+H9+H12
    ["open"]*7 + ["closed"]*5 + ["closed"],  # D: H1-H7
]

print("=== ChatGPT Chart (verified - bell-end first) ===")
for i, (name, row) in enumerate(zip(names, chart)):
    pat = "".join("O" if s=="open" else "X" for s in row[:12])
    first_open = next((j+1 for j,s in enumerate(row[:12]) if s=="open"), None)
    print(f"  {name}: {pat}  first_open=H{first_open}")

# Correct initial guess: holes NEAR BELL END for low notes
# H7 (first open for D#/E) should be ~1000-1100mm for ~80Hz
# H6 (first open for F) ~950mm
# H5 ~900mm, H4 ~800mm, H3 ~700mm, H2 ~600mm, H1 ~500mm
# H8,H9,H10 (corrective): between H7 and bell ~1100-1180mm
# H11 (vent): ~650mm
# H12 (vent): ~1180mm
hole_positions = [500, 600, 700, 800, 900, 950, 1050, 1100, 1150, 1120, 650, 1180]

print(f"\nInitial: {[f'{p:.0f}' for p in hole_positions]}")

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
    register_weights=(0.0, 1.0),
    optimize_grad=True,
    grad_bounds=(6.0, 12.0, 14.0, 22.0),
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