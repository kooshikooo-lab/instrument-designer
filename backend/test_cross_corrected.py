"""Test: Corrected cross-fingering chart opening from REED end (H1 first)."""
import sys, math, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Corrected chart: [H1..H12, R] - H1 closest to reed, opens FIRST
# D: all closed
# D#: H1 open (cross: H2 closed)
# E:  H1 open
# F:  H1+H2 open
# F#: H1+H3 open (cross: H2 closed)
# G:  H1+H2+H3 open
# G#: H1+H2+H4 open (cross: H3 closed)
# A:  H1+H2+H3+H4 open
# Bb: H1+H3+H4 open (cross: H2 closed)
# B:  H1+H2+H3+H4+H5 open
# C:  H1+H2+H3+H4+H5+H6 open
# C#: H1+H2+H3+H4+H5+H6+H7+H8 open (more holes)
# D:  H1+H2+H3+H4+H5+H6+H7 open

chart_str = [
    ["closed"]*12 + ["closed"],  # D
    ["open"] + ["closed"]*11 + ["closed"],  # D# (H1 only)
    ["open"] + ["closed"]*11 + ["closed"],  # E  (H1 only) - SAME as D#? Need difference
    ["open","open"] + ["closed"]*10 + ["closed"],  # F
    ["open","closed","open"] + ["closed"]*9 + ["closed"],  # F# (cross)
    ["open","open","open"] + ["closed"]*9 + ["closed"],  # G
    ["open","open","closed","open"] + ["closed"]*8 + ["closed"],  # G# (cross)
    ["open","open","open","open"] + ["closed"]*8 + ["closed"],  # A
    ["open","closed","open","open"] + ["closed"]*8 + ["closed"],  # Bb (cross)
    ["open","open","open","open","open"] + ["closed"]*7 + ["closed"],  # B
    ["open"]*6 + ["closed"]*6 + ["closed"],  # C
    ["open"]*8 + ["closed"]*4 + ["closed"],  # C#
    ["open"]*7 + ["closed"]*5 + ["closed"],  # D
]

# But D# and E both have H1 open - that's the problem with cross-fingerings!
# The difference must come from additional holes opened BELOW H1.
# Let me redo with proper cross-fingering structure:

print("=== Corrected Chart (reed-end first) ===")
for i, (name, row) in enumerate(zip(names, chart_str)):
    pat = "".join("O" if s=="open" else "X" for s in row[:12])
    print(f"  {name}: {pat}")

# This still has D# and E identical. Cross-fingerings need additional holes
# opened FURTHER DOWN to create the cavity effect.
# Real clarinet: D# = left thumb + some side keys; E = left thumb only
# The side keys are FURTHER DOWN the bore, creating a cavity.
# Let me try a better pattern:

chart2 = [
    ["closed"]*12 + ["closed"],  # D
    ["open"] + ["closed"]*2 + ["open"] + ["closed"]*8 + ["closed"],  # D#: H1 + H4 (cavity at H2-H3)
    ["open"] + ["closed"]*11 + ["closed"],  # E: H1 only
    ["open","open"] + ["closed"]*10 + ["closed"],  # F: H1+H2
    ["open","closed","open"] + ["closed"]*9 + ["closed"],  # F#: H1+H3 (cavity at H2)
    ["open","open","open"] + ["closed"]*9 + ["closed"],  # G: H1+H2+H3
    ["open","open","closed","open"] + ["closed"]*8 + ["closed"],  # G#: H1+H2+H4
    ["open","open","open","open"] + ["closed"]*8 + ["closed"],  # A: H1+H2+H3+H4
    ["open","closed","open","open","open"] + ["closed"]*7 + ["closed"],  # Bb: H1+H3+H4+H5
    ["open","open","open","open","open"] + ["closed"]*7 + ["closed"],  # B: H1-H5
    ["open"]*6 + ["closed"]*6 + ["closed"],  # C: H1-H6
    ["open"]*8 + ["closed"]*4 + ["closed"],  # C#: H1-H8
    ["open"]*7 + ["closed"]*5 + ["closed"],  # D: H1-H7
]

print("\n=== Chart with cavity cross-fingerings ===")
for i, (name, row) in enumerate(zip(names, chart2)):
    pat = "".join("O" if s=="open" else "X" for s in row[:12])
    print(f"  {name}: {pat}")

# Initial guess: sequential positions from working 7-hole + 5 more
hole_positions = [176, 293, 338, 445, 532, 610, 636, 700, 760, 820, 880, 940]

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart2,
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