"""Debug: what wavelength does find_resonance return for open holes?"""
import sys, math
import numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii

# Build a simple 12-hole instrument with register hole at 80mm
bore_radius = 12.5
bore_length = 1211.3
outer_diameter = 37.0

# Hole positions (from optimizer output)
positions = [80.0, 98.0, 166.0, 225.0, 283.0, 335.0, 386.0, 435.0, 478.0, 522.0, 561.0, 616.0, 646.0]
diameters = [2.5, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0]
lengths = [3.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

radii = np.full(10, bore_radius)

inst = tmm_instrument_from_radii(
    radii, bore_length, positions, diameters, lengths,
    outer_diameter, closed_top=True, cone_step=0.5,
)

# D2-D3 targets
targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]

for ti, target in enumerate(targets):
    target_wl = 343.0 / target * 1000  # in mm
    # All closed first
    all_closed = ["closed"] * 13
    # Alternative: open first N holes
    N_open = ti
    fingering = ["closed"] * 13
    for j in range(N_open):
        fingering[j] = "open"
    fingering[12] = "closed"  # register always closed in 1st register
    
    # Wait - positions[0] is the register hole! We need to map correctly.
    # The register hole at 80mm must always be closed.
    # Fingering[0] corresponds to position 80mm (register)
    # Fingering[1] corresponds to position 98mm (first free hole)
    
    # Correct mapping:
    fingering2 = ["closed"] * 13
    # fingering2[0] = register hole at 80mm (always closed for 1st reg)
    # fingering2[1..12] = free holes
    for j in range(N_open):
        fingering2[1 + j] = "open"
    fingering2[0] = "closed"
    
    try:
        wl = inst.find_resonance(target_wl, fingering2, n_register=1, max_steps=200)
        actual_freq = 343.0 / (wl / 1000)
        cents = 1200 * math.log2(actual_freq / target)
        print(f"N{ti} ({target:.1f}Hz): target_wl={target_wl:.0f}mm, found_wl={wl:.0f}mm, freq={actual_freq:.1f}Hz, err={cents:+.0f}c")
    except Exception as e:
        print(f"N{ti} ({target:.1f}Hz): ERROR: {e}")
