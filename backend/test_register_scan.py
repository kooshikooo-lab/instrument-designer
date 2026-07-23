"""
Scan register hole position and diameter to find optimal 12th tuning.
Tests the Debut-Kergomard prediction that optimum is near maker's choice.
"""

import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# Bass clarinet (simplified: no toneholes, just register hole)
BORE_LENGTH = 1171.0
BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0

radii = np.full(10, BORE_RADIUS)

# Test: find 1st and 3rd resonances with register hole at various positions
print(f"Scanning register hole position and diameter")
print(f"{'Position':>8} {'Dia':>5} {'1st(Hz)':>10} {'3rd(Hz)':>10} {'Ratio':>8} {'Target':>6} {'Err(c)':>10}")
print(f"{'-'*8} {'-'*5} {'-'*10} {'-'*10} {'-'*8} {'-'*6} {'-'*10}")

best = None
for pos_mm in range(100, 501, 20):
    for dia_mm in [2.5, 3.0, 3.5, 4.0, 5.0]:
        hole_len = 3.0
        all_pos = [pos_mm]
        all_dia = [dia_mm]
        all_len = [hole_len]
        
        inst = tmm_instrument_from_radii(
            radii, BORE_LENGTH, all_pos, all_dia, all_len,
            OUTER_DIAMETER, closed_top=True, cone_step=0.5,
        )
        
        # Find 1st register resonance (register hole closed)
        wl1 = inst.find_resonance(SPEED_OF_SOUND / 73.4, ["closed"], n_register=1)
        f1 = inst.frequency_from_wavelength(wl1) if wl1 else 0
        
        # Find 2nd register resonance (register hole open, 2nd impedance peak = 3rd harmonic)
        wl3 = inst.find_resonance(SPEED_OF_SOUND / (3*73.4), ["open"], n_register=2)
        f3 = inst.frequency_from_wavelength(wl3) if wl3 else 0
        
        if f1 > 0 and f3 > 0:
            ratio = f3 / f1
            target = 3.0
            err = abs(1200.0 * math.log2(ratio / target))
            print(f"{pos_mm:>8} {dia_mm:>5.1f} {f1:>10.1f} {f3:>10.1f} {ratio:>8.3f} {target:>6.1f} {err:>+10.1f}")
            
            if best is None or err < best[0]:
                best = (err, pos_mm, dia_mm, f1, f3, ratio)

if best:
    e, p, d, f1, f3, r = best
    print(f"\nBest: pos={p}mm, dia={d}mm, 1st={f1:.1f}Hz, 3rd={f3:.1f}Hz, ratio={r:.3f}, err={e:.1f}c")
