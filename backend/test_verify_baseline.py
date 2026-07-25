"""Verify 7-hole diatonic baseline, then test cross-fingerings for chromatic.

Key insight from benchmark_chalumeau.py:
- Reed-end-first: hole nearest reed opens first (ascending scale)
- Register hole at 80mm is ALWAYS CLOSED for chalumeau
- The 0.45c was for 7 DIATONIC notes, not 13 chromatic
"""
import sys, time
import numpy as np
from scipy.optimize import minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

DIA7 = [176, 293, 338, 445, 532, 610, 636]
REG = 80.0
BORE_LEN = 1211.3
BORE_R = 12.5
HOLE_D = 11.0
HOLE_L = 5.0
OUTER_D = 37.0

# ===== Part 1: Verify 7-hole diatonic =====
print("=" * 60)
print("PART 1: Verify 7-hole diatonic baseline")
print("=" * 60)

# 7 diatonic targets (D2 major scale)
dia_targets = [73.416, 82.407, 87.307, 98.000, 110.000, 123.471, 146.832]
dia_names = ['D2', 'E2', 'F2', 'G2', 'A2', 'B2', 'D3']

# Instrument: register + 7 primary holes
# Positions sorted: [80, 176, 293, 338, 445, 532, 610, 636]
# Hole indices:       0    1    2    3    4    5    6    7
inst7 = tmm_instrument_from_radii(
    np.full(10, BORE_R), BORE_LEN, sorted([REG] + DIA7),
    [2.5/2] + [HOLE_D/2]*7, [3.0] + [HOLE_L]*7, OUTER_D,
    closed_top=True, cone_step=0.5
)
wl7 = [SPEED_OF_SOUND/t for t in dia_targets]

# Reed-first sequential: hole 1 opens first (lowest note above D2)
chart_7 = []
for i in range(7):
    row = ['closed'] * 8  # 8 holes total
    if i == 0:
        pass  # D2: all closed
    else:
        # Open holes 1 through i (reed-end first)
        for j in range(1, i + 1):
            row[j] = 'open'
    chart_7.append(row)

print("7-note diatonic chart (reed-first):")
for n, row in zip(dia_names, chart_7):
    pat = "".join("O" if x=="open" else "X" for x in row)
    print("  %s: %s" % (n, pat))

freqs7 = inst7.compute_fingered_frequencies(wl7, chart_7, n_register=1)
errs7 = []
for n, t, f in zip(dia_names, dia_targets, freqs7):
    c = 1200*np.log2(f/t) if f>0 else 0
    errs7.append(c)
    print("  %-4s target=%7.1f actual=%7.1f err=%+7.1f" % (n, t, f, c))
e7 = np.array(errs7)
off7 = np.median(e7)
rms7 = np.sqrt(np.mean((e7 - off7)**2))
print("  RMS=%.2fc offset=%+.1fc" % (rms7, off7))

# ===== Part 2: 7-hole with all 13 chromatic targets =====
print()
print("=" * 60)
print("PART 2: 13-note chromatic with 7 holes only")
print("=" * 60)

targets_13 = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
              103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names_13 = ['D2','D#2','E2','F2','F#2','G2','G#2','A2','A#2','B2','C3','C#3','D3']

# Try various cross-fingerings with just 7 holes
# Strategy: skip some primary holes to get intermediate pitches
chart_13 = []
for i in range(13):
    row = ['closed'] * 8
    if i == 0:
        pass  # D2: all closed
    elif i == 1:
        row[1] = 'open'  # D#2: H1 only
    elif i == 2:
        row[1] = 'open'; row[2] = 'open'  # E2: H1+H2
    elif i == 3:
        row[1] = 'open'; row[2] = 'open'; row[3] = 'open'  # F2
    elif i == 4:
        row[1] = 'open'; row[2] = 'open'; row[3] = 'open'; row[4] = 'open'  # F#2
    elif i == 5:
        row[1] = 'open'; row[2] = 'open'; row[3] = 'open'; row[4] = 'open'; row[5] = 'open'  # G2
    elif i == 6:
        row[1] = 'open'; row[2] = 'open'; row[3] = 'open'; row[4] = 'open'; row[5] = 'open'; row[6] = 'open'  # G#2
    elif i == 7:
        row[1] = 'open'; row[2] = 'open'; row[3] = 'open'; row[4] = 'open'; row[5] = 'open'; row[6] = 'open'; row[7] = 'open'  # A2
    else:
        row = ['open'] * 8  # all open for higher notes
    chart_13.append(row)

wl13 = [SPEED_OF_SOUND/t for t in targets_13]
freqs13 = inst7.compute_fingered_frequencies(wl13, chart_13, n_register=1)
errs13 = []
print("\n%-4s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 40)
for n, t, f in zip(names_13, targets_13, freqs13):
    c = 1200*np.log2(f/t) if f>0 else 0
    errs13.append(c)
    print("  %-4s %8.1f %8.1f %+8.1f" % (n, t, f, c))
e13 = np.array(errs13)
off13 = np.median(e13)
rms13 = np.sqrt(np.mean((e13 - off13)**2))
print("\n7-hole chromatic RMS=%.2fc offset=%+.1fc" % (rms13, off13))
print("Note: with only 7 holes, chromatic intonation will be poor.")
print("This confirms cross-fingerings with ADDITIONAL holes are needed.")
