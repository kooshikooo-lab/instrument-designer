"""Extend validated 7-hole diatonic with 5 corrective holes for cross-fingerings.

The 7-hole diatonic at [176, 293, 338, 445, 532, 610, 636] gives 0.45c RMS
for the natural diatonic scale. Now add H8-H12 for chromatic notes (D#, F#, G#, A#, C, C#).
"""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize

sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets_13 = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
              103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names_13 = ['D2','D#2','E2','F2','F#2','G2','G#2','A2','A#2','B2','C3','C#3','D3']

# Validated 7-hole diatonic primary holes (open from reed end first)
DIA7 = [176, 293, 338, 445, 532, 610, 636]

# ChatGPT cross-fingering chart: 13 notes x 12 holes
# Columns: H1-H7 = primary diatonic (reed to bell)
#          H8-H12 = corrective/auxiliary (for cross-fingerings)
# Row: [H1, H2, H3, H4, H5, H6, H7, H8, H9, H10, H11, H12]
chart_12 = [
    [0,0,0,0,0,0,0,0,0,0,0,0],  # D2 - all closed
    [0,0,0,0,0,0,1,0,1,0,0,0],  # D#2 - H7+H9 (cross)
    [0,0,0,0,0,1,1,0,0,0,0,0],  # E2 - H6+H7 (from 7-hole: just H7)
    [0,0,0,0,1,1,1,0,0,0,0,0],  # F2 - H5+H6+H7 (from 7-hole: H6+H7)
    [0,0,0,0,1,0,1,1,0,0,0,0],  # F#2 - H5+H7+H8 (cross)
    [0,0,0,1,1,1,1,0,0,0,0,0],  # G2 - H4+H5+H6+H7 (from 7-hole: H5+H6+H7)
    [0,0,0,1,0,1,1,1,0,0,0,0],  # G#2 - H4+H6+H7+H8 (cross)
    [0,0,1,1,1,1,1,0,0,0,0,0],  # A2 - H3+H4+H5+H6+H7 (from 7-hole: H4+H5+H6+H7)
    [0,0,1,0,1,1,1,1,0,0,0,0],  # A#2 - H3+H5+H6+H7+H8 (cross)
    [0,1,1,1,1,1,1,0,0,0,0,0],  # B2 - H2+H3+H4+H5+H6+H7 (from 7-hole: H3+H4+H5+H6+H7)
    [1,0,1,1,1,1,1,0,0,0,1,0],  # C3 - H1+H3+H4+H5+H6+H7+H11 (cross)
    [1,0,1,1,1,1,1,0,1,0,0,1],  # C#3 - H1+H3+H4+H5+H6+H7+H9+H12 (cross)
    [1,1,1,1,1,1,1,0,0,0,0,0],  # D3 - all primary (from 7-hole: all 7)
]

# Note: the ChatGPT chart has different primary-hole numbering than our 7-hole.
# Our 7-hole opens from REED end: H1 nearest reed opens first for highest note.
# ChatGpt chart opens H7 first for E2, meaning H7 is nearest reed in primary sequence.
# We need to REVERSE the primary holes to match: H1_chart -> H7_dia, H7_chart -> H1_dia

# Let me build the chart with CORRECTED primary hole mapping to our 7-hole positions:
# Our 7-hole: D2=all closed, E2=H7(636), F2=H6(610)+H7, G2=H5(532)+H6+H7, etc.
# So in the ChatGPT chart convention, our H7=ChatGpt H1, our H6=ChatGpt H2, etc.

# Actually let me just re-map: for our validated 7-hole, the fingering is:
# D2: all closed
# E2: open hole at 636mm (H7 = farthest from reed)
# F2: open holes at 610+636mm (H6+H7)
# G2: open 532+610+636 (H5+H6+H7)
# A2: open 445+532+610+636 (H4+H5+H6+H7)
# B2: open 338+445+532+610+636 (H3+H4+H5+H6+H7)
# C3: open 293+338+445+532+610+636 (H2+H3+H4+H5+H6+H7)
# D3: open all 7 (176+293+338+445+532+610+636)

# Chromatic notes need cross-fingerings with corrective holes.
# Strategy: place H8-H12 between existing primary holes to create
# impedance dips for the missing semitones.

REG_POS = 80.0
REG_DIA = 2.5
REG_LEN = 3.0

def make_chart(primary_7, corrective_5):
    """Build 13-note chart for 12 holes.
    primary_7 = positions of the 7 diatonic holes (reed to bell).
    corrective_5 = positions of 5 corrective holes.
    """
    all_holes = sorted(primary_7 + corrective_5)
    # Map primary holes to their new indices
    prim_idx = {p: i for i, p in enumerate(sorted(primary_7))}
    corr_idx = {p: i+7 for i, p in enumerate(sorted(corrective_5))}
    
    # Build chart using our validated 7-hole logic + corrective holes
    # For diatonic notes: open primary holes from bell end (high index) toward reed
    # For chromatic notes: add specific corrective holes
    chart = []
    for note_idx in range(13):
        row = [0] * 12
        # Primary holes: open from H7 (bell end) toward H1 (reed end)
        n_primary_open = note_idx  # 0 for D2, 1 for D#2->wrong, ...
        # Actually: D2=0, E2=1(primary H7), F2=2(H6+H7), etc.
        # D#2,F#2,G#2,A#2,C3,C#3 are chromatic - need different logic
        chart.append(row)
    return chart

# Simpler approach: just test adding 5 corrective holes to the 7-hole layout
# and optimize their positions while keeping primary holes fixed.

def evaluate_12(all_12_pos):
    """Evaluate 12-hole cross-fingering chart."""
    all_pos = sorted(list(all_12_pos) + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets_13]
    
    # Use our validated 7-hole fingering logic for diatonic,
    # test various chromatic patterns with corrective holes
    freqs = inst.compute_fingered_frequencies(wl, chart_12_str, n_register=1)
    errs = []
    for t, f in zip(targets_13, freqs):
        c = 1200 * np.log2(f/t) if f > 0 else 1e10
        errs.append(c)
    err_arr = np.array(errs)
    offset = np.median(err_arr)
    rms = np.sqrt(np.mean((err_arr - offset)**2))
    return rms

# First: verify 7-hole baseline by adding dummy holes at same positions
print("=== Step 1: Verify 7-hole baseline ===")
baseline = DIA7 + [636, 636, 636, 636, 636]  # corrective holes overlap with H7

# Actually, let's just run the 7-hole test first with the validated config
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

inst7 = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, sorted(DIA7 + [REG_POS]),
    [11.0/2]*7 + [REG_DIA/2], [5.0]*7 + [REG_LEN], 37.0,
    closed_top=True, cone_step=0.5
)
wl7 = [SPEED_OF_SOUND/t for t in targets_13]

# 7-hole diatonic chart: D2-D3 chromatic (7 holes only)
chart_7 = []
for i in range(13):
    row = [0]*7
    if i == 0:
        pass  # D2: all closed
    elif i == 1:
        row[6] = 1  # D#2: open H7 only (closest to bell)
    elif i == 2:
        row[5] = 1; row[6] = 1  # E2: H6+H7
    elif i == 3:
        row[4] = 1; row[5] = 1; row[6] = 1  # F2
    elif i == 4:
        row[3] = 1; row[5] = 1; row[6] = 1  # F#2: cross (skip H4)
    elif i == 5:
        row[3] = 1; row[4] = 1; row[5] = 1; row[6] = 1  # G2
    elif i == 6:
        row[2] = 1; row[4] = 1; row[5] = 1; row[6] = 1  # G#2: cross (skip H3)
    elif i == 7:
        row[2] = 1; row[3] = 1; row[4] = 1; row[5] = 1; row[6] = 1  # A2
    elif i == 8:
        row[1] = 1; row[3] = 1; row[4] = 1; row[5] = 1; row[6] = 1  # A#2: cross
    elif i == 9:
        row[1] = 1; row[2] = 1; row[3] = 1; row[4] = 1; row[5] = 1; row[6] = 1  # B2
    elif i == 10:
        row[0] = 1; row[2] = 1; row[3] = 1; row[4] = 1; row[5] = 1; row[6] = 1  # C3: cross
    elif i == 11:
        row[0] = 1; row[1] = 1; row[2] = 1; row[3] = 1; row[4] = 1; row[5] = 1; row[6] = 1  # C#3: all primary
    elif i == 12:
        row = [1]*7  # D3: all open
    chart_7.append(['open' if x else 'closed' for x in row])

chart_7_str = chart_7
freqs7 = inst7.compute_fingered_frequencies(wl7, chart_7_str, n_register=1)

print("%-6s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 38)
errs7 = []
for n, t, f in zip(names_13, targets_13, freqs7):
    c = 1200 * np.log2(f/t) if f > 0 else 0
    errs7.append(c)
    print("  %-6s %8.1f %8.1f %+8.1f" % (n, t, f, c))
err_arr7 = np.array(errs7)
off7 = np.median(err_arr7)
rms7 = np.sqrt(np.mean((err_arr7 - off7)**2))
print()
print("7-hole cross-fingering only:")
print("  Offset: %+.1fc  RMS(relative): %.2fc" % (off7, rms7))
print("  Max err: %.1fc" % max(abs(err_arr7 - off7)))
