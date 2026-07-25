"""Debug alto sax hole placement."""
import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND
targets = [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3]
fundamental = 311.1
L_est = c / (2.0 * fundamental)
print(f"Alto sax: bore estimate = {L_est:.0f}mm")

bore_length = L_est
bore_radii = np.full(8, 8.5)
hp = []
for k, target in enumerate(targets[1:]):
    min_p = hp[-1] + 15 if hp else 30
    max_p = bore_length - 30
    if min_p >= max_p:
        print(f"  Hole {k}: NO ROOM (min_p={min_p:.0f}, max_p={max_p:.0f})")
        break
    best_pos, best_err = 0, 1e10
    for pos in np.linspace(min_p, max_p, 60):
        try:
            inst = tmm_instrument_from_radii(bore_radii, bore_length,
                [pos], [7.5], [3.5], 26.0, False, 0.5)
            wl = inst.find_resonance(c / target, ["open"], 1)
            f = inst.frequency_from_wavelength(wl)
            err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
            if err < best_err:
                best_err, best_pos = err, pos
        except: pass
    hp.append(best_pos)
    print(f"  Hole {k} ({target:.1f} Hz): pos={best_pos:.0f}mm, err={best_err:.1f}c")

print(f"\nTotal holes: {len(hp)}")
print(f"Hole positions: {[f'{p:.0f}' for p in hp]}")
