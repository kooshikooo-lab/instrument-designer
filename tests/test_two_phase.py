import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple test without multiprocessing
from backend.two_phase_optimizer import two_phase_optimize, KeefeLoss
import numpy as np
import math

# Verify imports work
assert two_phase_optimize is not None, "two_phase_optimize import failed"
assert KeefeLoss is not None, "KeefeLoss import failed"

# Simple test: recorder-like instrument
bore_length = 320.0  # mm
hole_lens = [3.5] * 7  # 7 holes, 3.5mm chimney
targets = [523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77]  # C5-D5-E5-F5-G5-A5-B5
fingerings = [
    'OOOOOOO',  # C5
    'OOOOOOc',  # D5
    'OOOOOcc',  # E5
    'OOOOccc',  # F5
    'OOOcccc',  # G5
    'OOccccc',  # A5
    'Occcccc',  # B5
]

print("Testing two-phase optimizer with KeefeLoss...")
result = two_phase_optimize(
    bore_length=320.0,
    n_holes=7,
    hole_lens=hole_lens,
    targets=targets,
    fingerings=fingerings,
    n_register=2,  # open-open
    verbose=True,
    loss_model=KeefeLoss(),
)

# Assert result is a dict with expected keys
assert isinstance(result, dict), f"Expected dict, got {type(result)}"
assert 'bore_radii' in result, "Missing bore_radii in result"
assert 'hole_positions' in result, "Missing hole_positions in result"
assert 'hole_diameters' in result, "Missing hole_diameters in result"
assert 'final_cost' in result, "Missing final_cost in result"
assert 'total_time' in result, "Missing total_time in result"
# Bore length is positive
assert bore_length > 0, "Bore length must be positive"
# Bore radii are positive
for r in result['bore_radii']:
    assert r > 0, f"Bore radius must be positive, got {r}"
# RMS error is finite
assert math.isfinite(result['final_cost']), f"final_cost is not finite: {result['final_cost']}"

print(f"\nResult: final_cost={result['final_cost']:.2f}c")
print(f"Bore radii: {[f'{r:.1f}' for r in result['bore_radii']]}")
print(f"Hole positions: {[f'{p:.1f}' for p in result['hole_positions']]}")
print(f"Hole diameters: {[f'{d:.2f}' for d in result['hole_diameters']]}")
print(f"Registers: {result['detected_registers']}")
print(f"Total time: {result['total_time']:.1f}s")