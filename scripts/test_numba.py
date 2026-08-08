"""Small test for the numba compiled path.

It prints the Python and numba phases and timings for a representative instrument.
"""
import time
import numpy as np
from backend.tmm_acoustics import tmm_instrument_from_radii, Hole

try:
    from backend.tmm_numba import build_action_arrays, numba_resonance_phase
except Exception as e:
    print("Numba helper not available or numba not installed:", e)
    raise

radii = np.linspace(3.5, 7.0, 50)
inst = tmm_instrument_from_radii(
    radii_mm=radii,
    bore_length_mm=300.0,
    hole_positions_mm=[40,80,120,160,200,240],
    hole_diameters_mm=[7.0]*6,
    hole_lengths_mm=[3.75]*6,
    cone_step=0.5,
)

types,p1,p2,p3,p4,p5 = build_action_arrays(inst.actions)

fingerings = [Hole.OPEN if i%2==0 else Hole.CLOSED for i in range(inst.n_holes)]
mask = np.array([1 if f==Hole.OPEN else 0 for f in fingerings], dtype=np.int32)
wavelength = 400.0

# Python phase
t0 = time.perf_counter()
p_py = inst.resonance_phase(wavelength, fingerings)
t1 = time.perf_counter()

# Numba phase
try:
    t2 = time.perf_counter()
    p_nb = numba_resonance_phase(types,p1,p2,p3,p4,p5,mask,wavelength, closed_top=inst.closed_top)
    t3 = time.perf_counter()
except Exception as e:
    print("Numba call failed:", e)
    raise

print("python phase:", p_py, "time:", (t1-t0))
print("numba phase:", p_nb, "time:", (t3-t2))
print("difference:", abs(p_py - p_nb))
