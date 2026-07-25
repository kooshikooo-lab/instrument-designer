import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND
radii = [8.0, 7.8, 7.8, 7.9, 7.7, 7.9]
bore_length = 325.2
hp = [76.0, 114.0, 126.9, 191.0, 229.0]
hd = [4.8, 4.3, 3.1, 3.2, 4.2]
hl = [4.0] * 5
targets = [523.3, 587.3, 659.3, 698.5, 784.0, 880.0]
fingerings = [
    ['X','X','X','X','X','X'],
    ['O','X','X','X','X','X'],
    ['O','O','X','X','X','X'],
    ['O','O','O','X','X','X'],
    ['O','O','O','O','X','X'],
    ['O','O','O','O','O','X'],
]
inst = tmm_instrument_from_radii(radii, bore_length, hp, hd, hl, 24.0, closed_top=False, cone_step=0.5)
tw = [c/f for f in targets]

for nreg in [1, 2, 3, 4]:
    freqs = inst.compute_fingered_frequencies(tw, fingerings, nreg)
    cents_arr = [1200*math.log2(a/t) if a > 0 else 1e10 for a, t in zip(freqs, targets)]
    ca = np.array(cents_arr)
    rms_abs = np.sqrt(np.mean(ca**2))
    rms_med = np.sqrt(np.mean((ca - np.median(ca))**2))
    print(f"n_reg={nreg}: abs_rms={rms_abs:.2f}c  med_rms={rms_med:.2f}c  freqs={[f'{a:.0f}' for a in freqs]}")
