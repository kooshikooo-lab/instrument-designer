"""Determine correct fingering direction for 7-hole clarinet."""
import sys
import numpy as np
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

DIA7 = [176, 293, 338, 445, 532, 610, 636]
REG = 80.0
targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ['D2','D#2','E2','F2','F#2','G2','G#2','A2','A#2','B2','C3','C#3','D3']

# Instrument: register at 80mm, then 7 primary holes
# Sorted by position: [80, 176, 293, 338, 445, 532, 610, 636]
# Hole indices:        0    1    2    3    4    5    6    7
all_pos = sorted([REG] + DIA7)
inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [2.5/2] + [11.0/2]*7, [3.0] + [5.0]*7, 37.0,
    closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]

print("Hole positions (sorted):", all_pos)
print("Hole 0 = register at 80mm (always closed for chalumeau)")
print("Holes 1-7 = primary diatonic")

def eval_chart(chart_str, label):
    freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
    errs = []
    for n, t, f in zip(names, targets, freqs):
        c = 1200*np.log2(f/t) if f>0 else 0
        errs.append(c)
    e = np.array(errs)
    off = np.median(e)
    rms = np.sqrt(np.mean((e - off)**2))
    print("\n=== %s ===" % label)
    for n, t, f, c in zip(names, targets, freqs, errs):
        print("  %-4s target=%7.1f actual=%7.1f err=%+7.1f" % (n, t, f, c))
    print("  RMS=%.2fc offset=%+.1fc" % (rms, off))
    return rms

# Bell-first: hole 7 (636mm) opens first for E2, then 6+7, 5+6+7, etc.
# Register (hole 0) always closed
chart_bell = []
for i in range(13):
    row = ['closed'] * 8  # 8 holes total
    if i == 0:
        pass  # D2: all closed
    elif i <= 7:
        # Diatonic: open from bell end (high index) toward reed
        for j in range(8 - i, 8):
            row[j] = 'open'
    else:
        row = ['open'] * 8
    chart_bell.append(row)

# Reed-first: hole 1 (176mm) opens first for E2, then 1+2, 1+2+3, etc.
chart_reed = []
for i in range(13):
    row = ['closed'] * 8
    if i == 0:
        pass
    elif i <= 7:
        # Open from reed end (low index) toward bell
        for j in range(1, 1 + i):
            row[j] = 'open'
    else:
        row = ['open'] * 8
    chart_reed.append(row)

eval_chart(chart_bell, "BELL-FIRST: hole7(636) opens first")
eval_chart(chart_reed, "REED-FIRST: hole1(176) opens first")
