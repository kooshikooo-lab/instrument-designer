"""Test: Can global optimizer solve 12-hole chromatic (sequential fingerings)?"""
import sys, math
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

# Chromatic targets D2-D3 (13 notes)
targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

N_FREE = 12
N_FIXED = 1

# Sequential fingerings
chart = []
for i in range(13):
    row = ["closed"] * (N_FREE + N_FIXED)
    for j in range(i):
        row[j] = "open"
    row[N_FREE] = "closed"
    chart.append(row)

print(f"Testing: {N_FREE} free holes + register, {len(chart)} notes")
print(f"Sequential fingering chart: each note +1 open hole from top")

# Initial guess: interpolate from known 7-hole positions
known = np.array([176, 293, 338, 445, 532, 610, 636])
known_note_indices = [1, 2, 4, 5, 7, 9, 11]  # positions in 13-note array for D#=1, E=2, F#=4, G=5, A=7, B=9, C#=11
# Map: E2(82Hz)=index1, F#2(92.5Hz)=index2, G2(98Hz)=... 
# Actually the 7-hole diatonic targets were [73, 82, 92, 98, 110, 123, 139, 147] at indices [0,2,4,5,7,9,11,12]
# D2=0, E2=2, F#2=4, G2=5, A2=7, B2=9, C#3=11, D3=12
dia_indices = [0, 2, 4, 5, 7, 9, 11, 12]
dia_positions = [0, 176, 293, 338, 445, 532, 610, 636]
# Interpolate for all 12 hole positions
hole_positions = []
for hi in range(12):
    # Find where hole hi lies in the diatonic indices
    note_idx = hi + 1  # hole hi opens at note hi+1
    # Find surrounding diatonic notes
    for di in range(len(dia_indices)-1):
        if dia_indices[di] <= note_idx <= dia_indices[di+1]:
            frac = (note_idx - dia_indices[di]) / (dia_indices[di+1] - dia_indices[di])
            pos = dia_positions[di] + frac * (dia_positions[di+1] - dia_positions[di])
            hole_positions.append(pos)
            break
print(f"Initial holes: {[f'{p:.0f}' for p in hole_positions]}")

opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=1,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=60, use_de=False, verbose=True)
print(f"\nResult: RMS={result['final_rms_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
