"""Test: cross-fingerings for 12-hole chromatic."""
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

# Cross-fingering chart based on clarinet acoustics:
# Each row = ["hole_1", ..., "hole_12", "register"]
# Holes are arranged from reed (1) to bell (12)
# Register hole is last entry
# Cross-fingerings: opening a hole AND closing the next creates intermediate effective lengths
chart = [
    # D2  (all closed)
    ["closed"]*12 + ["closed"],
    # D#2 (open hole 1 only - sequential, closest to reed)
    ["open"] + ["closed"]*11 + ["closed"],
    # E2  (open holes 1-2 = sequential, skip hole as cross: open holes 2-3)
    ["closed", "open", "open"] + ["closed"]*9 + ["closed"],
    # F2  (open holes 1-4, close hole 3 = forked: creates intermediate length)
    ["open", "open", "closed", "open"] + ["closed"]*8 + ["closed"],
    # F#2 (open holes 1-4, sequential)
    ["open"]*4 + ["closed"]*8 + ["closed"],
    # G2  (open holes 1-5, sequential)
    ["open"]*5 + ["closed"]*7 + ["closed"],
    # G#2 (forked: open 1-6, close 5)
    ["open"]*4 + ["closed", "open", "open"] + ["closed"]*5 + ["closed"],
    # A2  (open holes 1-7, sequential)
    ["open"]*7 + ["closed"]*5 + ["closed"],
    # A#2 (forked between 7-8: open 1-8, close 7)
    ["open"]*6 + ["closed", "open", "open"] + ["closed"]*3 + ["closed"],
    # B2  (open holes 1-9, sequential)
    ["open"]*9 + ["closed"]*3 + ["closed"],
    # C3  (open holes 1-10, sequential)
    ["open"]*10 + ["closed"]*2 + ["closed"],
    # C#3 (open holes 1-11, sequential)
    ["open"]*11 + ["closed"]*1 + ["closed"],
    # D3  (open all 12, sequential)
    ["open"]*12 + ["closed"],
]

# Initial guess from 7-hole interpolation
hole_positions = [88, 176, 234, 293, 338, 392, 445, 488, 532, 571, 610, 636]

print("=== Cross-fingering chart ===")
for i, (name, row) in enumerate(zip(names, chart)):
    open_count = sum(1 for s in row[:12] if s == "open")
    pattern = "".join("O" if s=="open" else "X" for s in row[:12])
    print(f"  {name}: {open_count} open  {pattern}")

print("\n=== 2nd register optimization with cross-fingerings ===")
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
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80, 
                      use_de=False, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
positions = result['free_hole_positions']
print(f"Holes: {[f'{p:.0f}' for p in positions]}")
