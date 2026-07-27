import numpy as np
from backend.two_phase_optimizer import two_phase_optimize

# Test on a simple recorder-like instrument
bore_length = 350.0  # mm
hole_positions = [60, 100, 140, 180, 220, 260, 300]  # mm
hole_diameters = [5.0, 5.5, 5.5, 6.0, 6.0, 6.5, 6.5]  # mm
hole_lengths = [3.0] * 7  # mm

# Target frequencies for recorder in C (approx)
target_frequencies = np.array([261.6, 293.7, 329.6, 349.2, 392.0, 440.0, 493.9, 523.3])

# Fingering patterns (all open = fundamental, then sequential closing)
fingering_lists = [
    [True, True, True, True, True, True, True],   # C
    [True, True, True, True, True, True, False],  # D
    [True, True, True, True, True, False, False], # E
    [True, True, True, True, False, False, False], # F
    [True, True, True, False, False, False, False], # G
    [True, True, False, False, False, False, False], # A
    [True, False, False, False, False, False, False], # B
    [False, False, False, False, False, False, False], # C
]

# Run two-phase optimization
print("Running two-phase optimization...")
result = two_phase_optimize(
    bore_length=bore_length,
    hole_positions=hole_positions,
    hole_diameters=hole_diameters,
    hole_lengths=hole_lengths,
    target_frequencies=target_frequencies,
    fingering_lists=fingering_lists,
    n_register=2,
    verbose=True,
)

print(f"\nResult:")
print(f"  Phase 1 cost: {result.get('phase1_cost')}")
print(f"  Phase 2 cost: {result.get('phase2_cost')}")
print(f"  Bore radii: {result.get('bore_radii')}")
print(f"  Hole diameters: {result.get('hole_diameters')}")
print(f"  Hole positions: {result.get('hole_positions')}")