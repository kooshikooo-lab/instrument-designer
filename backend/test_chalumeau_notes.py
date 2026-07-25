import sys, os, math, numpy as np
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from benchmark_all import INSTRUMENTS

cfg = INSTRUMENTS['chalumeau_C']
c = SPEED_OF_SOUND

inst = tmm_instrument_from_radii(
    [6.4/2, 6.3/2, 5.3/2, 6.2/2, 6.0/2]*2,  # bore_radii_list needs >len(holes)
    330.8,
    [64.7, 94.6, 106.8, 135.6, 159.3],
    [6.4, 6.3, 5.3, 6.2, 6.0],
    [3.75]*5,
    22.0, closed_top=True, cone_step=0.5,
)
tw = [c/f for f in cfg["targets"]]
freqs = inst.compute_fingered_frequencies(tw, cfg["fingerings"], 1)
print("Chalumeau individual notes:")
for name, target, actual in zip(cfg["names"], cfg["targets"], freqs):
    cents = 1200 * math.log2(actual/target)
    print("  %s: target=%.1f actual=%.1f cents=%+.4f" % (name, target, actual, cents))
