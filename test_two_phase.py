import sys
sys.path.insert(0, r'C:\instrument-designer')

# Simple test without multiprocessing
from backend.two_phase_optimizer import two_phase_optimize, KeefeLoss
import numpy as np

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

print(f"\nResult: final_cost={result['final_cost']:.2f}c")
print(f"Bore radii: {[f'{r:.1f}' for r in result['bore_radii']]}")
print(f"Hole positions: {[f'{p:.1f}' for p in result['hole_positions']]}")
print(f"Hole diameters: {[f'{d:.2f}' for d in result['hole_diameters']]}")
print(f"Registers: {result['detected_registers']}")
print(f"Total time: {result['total_time']:.1f}s")