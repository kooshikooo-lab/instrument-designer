import sys
sys.path.insert(0, r'C:\instrument-designer')
import numpy as np
import math
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# Test chalumeau_C from their benchmark
cfg = {
    'closed_top': True,
    'targets': [261.6, 293.7, 329.6, 349.2, 392.0, 440.0],
    'names': ['C4', 'D4', 'E4', 'F4', 'G4', 'A4'],
    'bore_radius': 7.25, 'outer_diameter': 22.0,
    'hole_diameter': 7.0, 'hole_length': 3.75,
    'fingerings': [
        ['closed'] * 6,
        ['open', 'closed', 'closed', 'closed', 'closed', 'closed'],
        ['open', 'open', 'closed', 'closed', 'closed', 'closed'],
        ['open', 'open', 'open', 'closed', 'closed', 'closed'],
        ['open', 'open', 'open', 'open', 'closed', 'closed'],
        ['open', 'open', 'open', 'open', 'open', 'closed'],
    ],
}

bore_r = cfg['bore_radius']
outer_d = cfg['outer_diameter']
hd = cfg['hole_diameter']
hl = cfg['hole_length']

# Initial bore length from fundamental
L = SPEED_OF_SOUND / (4 * cfg['targets'][0])
print('Initial L: %.1fmm' % L)

# Build instrument
inst = tmm_instrument_from_radii(
    [bore_r], L,
    [], [], [], outer_d,
    closed_top=True, cone_step=0.5,
)
print('Instrument length: %.1fmm' % inst.length)

# Test fingerings
freqs = []
for i, fing in enumerate(cfg['fingerings']):
    target_wl = SPEED_OF_SOUND / cfg['targets'][i]
    wl = inst.find_resonance(target_wl, fing, n_register=1)
    freq = SPEED_OF_SOUND / wl
    freqs.append(freq)
    cents = 1200 * math.log2(freq / cfg['targets'][i])
    print('  %s: target=%.1f actual=%.1f cents=%+.1f' % (cfg['names'][i], cfg['targets'][i], freq, cents))

ca = np.array([1200*math.log2(a/t) for a,t in zip(freqs, cfg['targets'])])
rms = math.sqrt(np.mean(ca**2))
print('RMS: %.2fc' % rms)