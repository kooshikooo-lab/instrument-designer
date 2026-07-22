import numpy as np, math, sys, os
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
c = SPEED_OF_SOUND

r = np.full(6, 8.5)
L = 556.0
hp = [30.0, 45.0, 60.0, 75.0, 90.0, 105.0]
hd = [7.5]*6; hl = [3.5]*6

inst = tmm_instrument_from_radii(r, L, hp, hd, hl, 26.0, False, 0.5)
targets = [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3]
fingerings = [
    ['closed']*7,
    ['open','closed','closed','closed','closed','closed','closed'],
    ['open','open','closed','closed','closed','closed','closed'],
    ['open','open','open','closed','closed','closed','closed'],
    ['open','open','open','open','closed','closed','closed'],
    ['open','open','open','open','open','closed','closed'],
    ['open','open','open','open','open','open','closed'],
]

# This is what eval_all does (n_register=1)
tw = [c/f for f in targets]
freqs = inst.compute_fingered_frequencies(tw, fingerings, 1)
cents = [1200*math.log2(a/t) if a>0 and math.isfinite(a) else 1e10 for a,t in zip(freqs, targets)]
ca = np.array(cents)
abs_rms = np.sqrt(np.mean(ca**2))
even_rms = np.sqrt(np.mean((ca - np.median(ca))**2))
print(f"eval_all (n_reg=1): Abs RMS={abs_rms:.1f}c, Even RMS={even_rms:.1f}c, Median={np.median(ca):+.1f}c")
print(f"  Per-note: {[f'{x:+.0f}' for x in cents]}")

# Now with n_register=2
freqs2 = inst.compute_fingered_frequencies(tw, fingerings, 2)
cents2 = [1200*math.log2(a/t) if a>0 and math.isfinite(a) else 1e10 for a,t in zip(freqs2, targets)]
ca2 = np.array(cents2)
abs_rms2 = np.sqrt(np.mean(ca2**2))
even_rms2 = np.sqrt(np.mean((ca2 - np.median(ca2))**2))
print(f"\neval_all (n_reg=2): Abs RMS={abs_rms2:.1f}c, Even RMS={even_rms2:.1f}c, Median={np.median(ca2):+.1f}c")
print(f"  Per-note: {[f'{x:+.0f}' for x in cents2]}")
