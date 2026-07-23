"""Test: how do larger holes affect 1st register resonance?"""
import sys, math
import numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii

bore_radius = 12.5
bore_length = 1211.3
outer_diameter = 37.0

# Test with 20mm diameter holes (80% of bore)
hole_dia = 20.0

positions = [80.0, 176.0, 293.0, 338.0, 445.0, 532.0, 610.0, 636.0]
diameters = [2.5, hole_dia, hole_dia, hole_dia, hole_dia, hole_dia, hole_dia, hole_dia]
lengths = [3.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

radii = np.full(10, bore_radius)
inst = tmm_instrument_from_radii(radii, bore_length, positions, diameters, lengths, outer_diameter, closed_top=True, cone_step=0.5)

# Test each note: open i holes sequentially
targets = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]
names = ["D2","E2","F#2","G2","A2","B2","C#3","D3"]

def find_fundamental(inst, fingering):
    """Find fundamental by sweeping from long to short wl, finding first phase<1.0 crossing."""
    prev_phase = None
    for wl in np.linspace(6000, 50, 5951):  # long to short
        phase = inst.resonance_phase(wl, fingering)
        if prev_phase is not None and prev_phase < 1.0 and phase >= 1.0:
            frac = (1.0 - prev_phase) / (phase - prev_phase)
            cross_wl = wl + 1 * frac  # 1mm step
            return cross_wl
        prev_phase = phase
    return None

print("=== 20mm holes on 25mm bore ===")
for ti, (target, name) in enumerate(zip(targets, names)):
    target_wl = 343000 / target
    fingering = ["closed"] * 8
    for j in range(ti):
        fingering[1 + j] = "open"
    fingering[0] = "closed"
    
    wl = find_fundamental(inst, fingering)
    if wl:
        freq = 343000 / wl
        cents = 1200 * math.log2(freq / target)
        print(f"  {name}({target:.1f}Hz): wl={wl:.0f}mm f={freq:.1f}Hz err={cents:+.0f}c")
    else:
        print(f"  {name}({target:.1f}Hz): NOT FOUND")

print("\n=== 20mm holes on 14mm bore ===")
inst2 = tmm_instrument_from_radii(np.full(10, 7.0), bore_length, positions, diameters, lengths, outer_diameter, closed_top=True, cone_step=0.5)

for ti, (target, name) in enumerate(zip(targets, names)):
    target_wl = 343000 / target
    fingering = ["closed"] * 8
    for j in range(ti):
        fingering[1 + j] = "open"
    fingering[0] = "closed"
    
    wl = find_fundamental(inst2, fingering)
    if wl:
        freq = 343000 / wl
        cents = 1200 * math.log2(freq / target)
        print(f"  {name}({target:.1f}Hz): wl={wl:.0f}mm f={freq:.1f}Hz err={cents:+.0f}c")
    else:
        print(f"  {name}({target:.1f}Hz): NOT FOUND")
