"""Test single-hole evaluation with correct n_register."""
import sys, math
sys.path.insert(0, "C:\\instrument-designer")
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
import numpy as np

c = SPEED_OF_SOUND
bore_radius = 6.0
bore_length = 371.0
od = 20.0

# Single hole at 300mm, target 880 Hz
hole_pos = 300.0
hole_dia = 6.5
hole_len = 3.0
target = 880.0
wl_near = c / target

for nr in range(1, 6):
    try:
        inst = tmm_instrument_from_radii(
            np.full(8, bore_radius), bore_length,
            [hole_pos], [hole_dia], [hole_len],
            od, closed_top=False, cone_step=0.5,
        )
        wl = inst.find_resonance(wl_near, ["open"], n_register=nr)
        f = inst.frequency_from_wavelength(wl)
        err = 1200.0 * math.log2(f / target)
        print(f"  n_register={nr}: f={f:.1f}Hz (err={err:+.1f}c)")
    except Exception as e:
        print(f"  n_register={nr}: ERROR {e}")

print()
print("=== All-closed single hole instrument ===")
for nr in range(1, 6):
    try:
        inst = tmm_instrument_from_radii(
            np.full(8, bore_radius), bore_length,
            [hole_pos], [hole_dia], [hole_len],
            od, closed_top=False, cone_step=0.5,
        )
        wl = inst.find_resonance(wl_near, ["closed"], n_register=nr)
        f = inst.frequency_from_wavelength(wl)
        err = 1200.0 * math.log2(f / target)
        print(f"  n_register={nr}: f={f:.1f}Hz (err={err:+.1f}c)")
    except Exception as e:
        print(f"  n_register={nr}: ERROR {e}")
