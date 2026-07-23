"""Sweep wavelength to see resonance phase for open-hole configurations."""
import sys, math
import numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii

bore_radius = 12.5
bore_length = 1211.3
outer_diameter = 37.0

# 12 holes + 1 register
positions = [80.0, 98.0, 166.0, 225.0, 283.0, 335.0, 386.0, 435.0, 478.0, 522.0, 561.0, 616.0, 646.0]
diameters = [2.5, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0, 11.0]
lengths = [3.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]

radii = np.full(10, bore_radius)
inst = tmm_instrument_from_radii(radii, bore_length, positions, diameters, lengths, outer_diameter, closed_top=True, cone_step=0.5)

# Test two configurations: all closed, and hole 1 open
for name, fingering in [
    ("ALL CLOSED", ["closed"] * 13),
    ("HOLE 1 OPEN (98mm)", ["closed"] + ["open"] + ["closed"] * 11),
    ("HOLE 7 OPEN (98-435mm)", ["closed"] + ["open"]*7 + ["closed"]*5),
    ("ALL OPEN (98-646mm)", ["closed"] + ["open"]*12),
]:
    print(f"\n=== {name} ===")
    phases = []
    wavelengths = list(np.linspace(200, 6000, 581))
    for wl in wavelengths:
        phase = inst.resonance_phase(wl, fingering)
        phases.append(phase)
    
    print(f"  Phase at wl=200mm: {phases[0]:.2f}")
    print(f"  Phase at wl=6000mm: {phases[-1]:.2f}")
    print(f"  Min phase: {min(phases):.2f} at wl={wavelengths[phases.index(min(phases))]:.0f}mm")
    print(f"  Max phase: {max(phases):.2f} at wl={wavelengths[phases.index(max(phases))]:.0f}mm")
    
    # Find all phase crossings of 1.0
    for i in range(len(phases)-1):
        if phases[i] < 1.0 and phases[i+1] >= 1.0:
            frac = (1.0 - phases[i]) / (phases[i+1] - phases[i])
            cross_wl = wavelengths[i] + 10 * frac
            freq = 343000 / cross_wl
            print(f"  wl~={cross_wl:.0f}mm  f~={freq:.1f}Hz  (cross+1)")
        elif phases[i] > 1.0 and phases[i+1] <= 1.0:
            frac = (phases[i] - 1.0) / (phases[i] - phases[i+1])
            cross_wl = wavelengths[i] + 10 * frac
            freq = 343000 / cross_wl
            print(f"  wl~={cross_wl:.0f}mm  f~={freq:.1f}Hz  (cross-1)")
