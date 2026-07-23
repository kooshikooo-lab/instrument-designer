"""Test: Baroque clarinet optimization with 7 holes + 2 keys + register."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# Load baroque clarinet config
import json
with open('config/baroque_clarinet.json') as f:
    config = json.load(f)

# Extract targets and chart
chalumeau_targets = config['targets_hz']['chalumeau']
clarion_targets = config['targets_hz']['clarion']

# Build combined chart (chalumeau + clarion)
chalumeau_chart = config['fingering_chart']['chalumeau']
clarion_chart = config['fingering_chart']['clarion']

all_notes = list(chalumeau_chart.keys()) + list(clarion_chart.keys())
all_targets = chalumeau_targets + clarion_targets

# Chart has 10 columns: 7 finger holes + 2 keys + 1 register
# Fixed holes = register only (1), Free holes = 7 finger + 2 keys = 9
chart_list = []
for note in all_notes:
    if note in chalumeau_chart:
        row = ["open" if x else "closed" for x in chalumeau_chart[note]]
    else:
        row = ["open" if x else "closed" for x in clarion_chart[note]]
    chart_list.append(row)

print(f"=== Baroque Clarinet Test ===")
print(f"Notes: {len(all_notes)}, Free holes: 9 (7 finger + 2 keys), Fixed: 1 (register)")
print(f"Bore: {config['bore_length_mm']}mm x {config['bore_radius_mm']}mm radius")

# Initial positions: 7 finger holes + 2 keys
hole_positions = [h['position_mm'] for h in config['finger_holes']] + [395, 430]
print(f"Initial positions: {[f'{p:.0f}' for p in hole_positions]}")

FIXED_REGISTER = [(45.0, 2.0, 3.0)]

t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=all_targets,
    fingering_chart=chart_list,
    bore_radius=config['bore_radius_mm'],
    outer_diameter=config['outer_diameter_mm'],
    hole_diameter=6.0,  # base
    hole_length=4.0,
    closed_top=True,
    n_register=2,  # clarion = 3rd peak = register 2 in optimizer
    bore_length=config['bore_length_mm'],
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.15, 1.0),  # primary = clarion
    optimize_grad=True,
    grad_bounds=(5.0, 8.0, 9.0, 12.0),
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=40,
                      use_de=False, verbose=True)
t1 = time.time()

print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
if 'graduated_diameters' in result:
    print(f"Diameters: {[f'{d:.1f}' for d in result['graduated_diameters']]}")