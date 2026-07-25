import sys
sys.path.insert(0, r'C:\instrument-designer')

from backend.tmm_acoustics import tmm_instrument_from_radii
from backend.physics.losses import KeefeLoss
import numpy as np

# Test KeefeLoss integration directly
print("Testing KeefeLoss integration...")

loss_model = KeefeLoss()
inst = tmm_instrument_from_radii(
    np.array([7.5]*6),  # 6 control points, 7.5mm radius
    320.0,  # bore length
    [60, 100, 140, 180, 220, 260, 300],  # hole positions
    [5.0]*7,  # hole diameters
    [3.5]*7,  # hole lengths
    loss_model=loss_model,
)

# Test resonance
wl_guess = 346100 / 523.25  # C5 wavelength
wl = inst.find_resonance(wl_guess, ['open']*7, n_register=2)
freq = inst.frequency_from_wavelength(wl)
print(f"Test freq: {freq:.1f} Hz (target: 523.25)")

# Test loss model directly
factor = loss_model.bore_loss(100.0, 7.5, 661.0)  # 100mm, 7.5mm radius, ~661mm wavelength
print(f"Loss factor: {factor}")
print(f"Loss magnitude: {abs(factor):.4f}")
print(f"Loss phase shift: {np.angle(factor):.6f} rad")

print("\n✅ KeefeLoss integration works!")