"""Test: 2-register optimization with full fingering chart (chalumeau + clarion)."""
import sys, math, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from fingering_reference import (
    FINGERING_CHART_CHALUMEAU, FINGERING_CHART_CLARION,
    written_pitches, GRADUATED_DIAMETERS, EXTENDED_HOLE_POSITIONS
)

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

# Combine both registers
all_notes = {**FINGERING_CHART_CHALUMEAU, **FINGERING_CHART_CLARION}
targets = [written_pitches[n] for n in sorted(all_notes.keys(), key=lambda k: written_pitches[k])]
chart_str = []
for note in sorted(all_notes.keys(), key=lambda k: written_pitches[k]):
    row = ["open" if x else "closed" for x in all_notes[note]]
    chart_str.append(row)

print("=== Full 2-Register Fingering Chart ===")
for i, (note, row) in enumerate(zip(sorted(all_notes.keys(), key=lambda k: written_pitches[k]), chart_str)):
    pat = "".join("O" if s=="open" else "X" for s in row[:12])
    reg = "O" if row[12]=="open" else "X"
    print(f"  {note:>4} ({targets[i]:>7.2f} Hz): {pat}  R={reg}")

# Initial positions
hole_positions = EXTENDED_HOLE_POSITIONS

print(f"\nInitial positions: {[f'{p:.0f}' for p in hole_positions]}")

# Targets for register 2 (clarion) - the notes with register hole OPEN
clarion_notes = [n for n in FINGERING_CHART_CLARION.keys()]
chalumeau_notes = [n for n in FINGERING_CHART_CHALUMEAU.keys()]

# We'll optimize for both registers using 2-register mode (n_register=2 means 2nd impedance peak)
# Chalumeau uses 1st peak, clarion uses 2nd peak (with register hole open)

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart_str,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,              # optimize for 2nd impedance peak (clarion)
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.15, 1.0),  # 1st reg as regularizer, 2nd reg primary
    optimize_grad=True,
    grad_bounds=(8.0, 12.0, 16.0, 22.0),
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80,
                      use_de=False, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
if 'graduated_diameters' in result:
    print(f"Diameters: {[f'{d:.1f}' for d in result['graduated_diameters']]}")