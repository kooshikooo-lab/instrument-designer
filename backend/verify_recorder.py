import sys, os, math
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND
radii = np.array([8.0, 7.8, 7.8, 7.9, 7.7, 7.9])
bore_length = 325.2
hp = [76.0, 114.0, 126.9, 191.0, 229.0]
hd = [4.8, 4.3, 3.1, 3.2, 4.2]
hl = [4.0] * 5
targets = [523.3, 587.3, 659.3, 698.5, 784.0, 880.0]
names = ['C5', 'D5', 'E5', 'F5', 'G5', 'A5']
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
freqs = inst.compute_fingered_frequencies(tw, fingerings, 2)
print(f"{'Note':<6} {'Target':>8} {'Actual':>8} {'Cents':>8}")
for n, t, a in zip(names, targets, freqs):
    cents = 1200.0 * math.log2(a/t) if a > 0 else 1e10
    print(f"{n:<6} {t:>8.1f} {a:>8.1f} {cents:>+8.1f}")
