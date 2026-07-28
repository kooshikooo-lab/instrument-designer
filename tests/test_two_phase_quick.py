import sys
sys.path.insert(0, r'C:\instrument-designer')

from backend.two_phase_optimizer import two_phase_optimize
from backend.physics.losses import KeefeLoss
import numpy as np

# Minimal test with fewer iterations
bore_length = 320.0
hole_lens = [3.5] * 7
targets = [523.25, 587.33, 659.25, 698.46, 783.99, 880.00, 987.77]
fingerings = [
    'OOOOOOO', 'OOOOOOc', 'OOOOOcc', 'OOOOccc', 'OOOcccc', 'OOccccc', 'Occcccc',
]

print("Quick test (reduced iterations)...")
result = two_phase_optimize(
    bore_length=320.0,
    n_holes=7,
    hole_lens=hole_lens,
    targets=targets,
    fingerings=fingerings,
    n_register=2,
    verbose=True,
    loss_model=KeefeLoss(),
    popsize=8,
    maxiter=10,
    n_iters=100,
)

print(f"\nResult: final_cost={result['final_cost']:.2f}c")
print(f"Bore radii: {[f'{r:.1f}' for r in result['bore_radii']]}")
print(f"Hole positions: {[f'{p:.1f}' for r in result['hole_positions']]}")
print(f"Hole diameters: {[f'{d:.2f}' for d in result['hole_diameters']]}")
print(f"Registers: {result['detected_registers']}")
print(f"Total time: {result['total_time']:.1f}s")