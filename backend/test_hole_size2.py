"""Test: 7-hole diatonic with 11mm vs 20mm holes - check 1st register."""
import sys, math
import numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii
from optimizer_global import GlobalFingeringOptimizer

# Known working 7-hole positions
pos_7 = [176, 293, 338, 445, 532, 610, 636]
targets = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]
names = ["D2","E2","F#2","G2","A2","B2","C#3","D3"]
FIXED_REGISTER = [(80.0, 2.5, 3.0)]

for hole_label, hole_dia in [("11mm holes", 11.0), ("20mm holes", 20.0)]:
    print(f"\n=== {hole_label} ===")
    positions = [80.0] + pos_7
    diameters = [2.5] + [hole_dia]*7
    lengths = [3.0] + [5.0]*7
    
    radii = np.full(10, 12.5)
    inst = tmm_instrument_from_radii(radii, 1211.3, positions, diameters, lengths, 37.0, closed_top=True, cone_step=0.5)
    
    for ti, (target, name) in enumerate(zip(targets, names)):
        target_wl = 343000 / target
        fingering = ["closed"] * 8
        for j in range(ti):
            fingering[1 + j] = "open"
        fingering[0] = "closed"
        
        prev_phase = None
        found = None
        for wl in np.linspace(6000, 50, 5951):
            phase = inst.resonance_phase(wl, fingering)
            if prev_phase is not None and prev_phase < 1.0 and phase >= 1.0:
                frac = (1.0 - prev_phase) / (phase - prev_phase)
                cross_wl = wl + 1 * frac
                freq = 343000 / cross_wl
                cents = 1200 * math.log2(freq / target)
                print(f"  {name}({target:.1f}Hz): wl={cross_wl:.0f}mm f={freq:.1f}Hz err={cents:+.0f}c")
                found = True
                break
            prev_phase = phase
        if not found:
            print(f"  {name}({target:.1f}Hz): NOT FOUND")
