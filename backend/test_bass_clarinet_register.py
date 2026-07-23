"""
Bass clarinet with register hole: test both registers.

1st register (chalumeau): all holes + register hole closed
2nd register (clarino): register hole open, fingered with same tonehole pattern
   Each 2nd register note = 12th above the 1st register note

Uses Debut-Kergomard Eq. 19 for register hole placement.
"""

import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND


def make_bass_clarinet(bore_length, bore_radius, hole_positions, hole_diameters,
                       hole_lengths, register_pos, register_diam, register_len,
                       outer_diameter=37.0):
    """Build a bass clarinet TMM instrument with register hole.
    
    The register hole is included in the tonehole list but always fingered 
    'closed' for 1st register, 'open' for 2nd register.
    """
    all_pos = list(hole_positions) + [register_pos]
    all_dia = list(hole_diameters) + [register_diam]
    all_len = list(hole_lengths) + [register_len]
    
    # Sort by position
    idx = np.argsort(all_pos)
    all_pos = [all_pos[i] for i in idx]
    all_dia = [all_dia[i] for i in idx]
    all_len = [all_len[i] for i in idx]
    
    # Determine register hole index after sorting
    reg_idx = list(all_pos).index(register_pos)
    
    return all_pos, all_dia, all_len, reg_idx


def build_fingering_sets(n_toneholes, reg_idx):
    """Build fingering sets for both registers.
    
    1st register: register hole CLOSED, toneholes follow standard pattern
    2nd register: register hole OPEN, toneholes same pattern
    """
    n_total = n_toneholes + 1  # +1 for register hole
    
    # Each list: [tonehole_0, tonehole_1, ..., register_hole, ...]
    # Sorted by position
    
    # 1st register fingering (all with register hole closed)
    reg1_sets = []
    for i in range(n_toneholes + 1):
        fingering = ["closed"] * n_total
        if i > 0:
            # First i toneholes open (using Bordeaux method: opened top-to-bottom)
            # Actually, for the diatonic scale: lowest note = all closed,
            # then open one more hole from the TOP each step
            # We need to find which holes are the first i (by position, from reed end)
            tonehole_indices = [j for j in range(n_total) if j != reg_idx]
            # Holes sorted by position ascending. The first i (from reed) should be open
            sorted_th = sorted(tonehole_indices)
            for j in sorted_th[:i]:
                fingering[j] = "open"
        fingering[reg_idx] = "closed"
        reg1_sets.append(fingering)
    
    # 2nd register: same but register hole open
    reg2_sets = []
    for fs in reg1_sets:
        f2 = list(fs)
        f2[reg_idx] = "open"
        reg2_sets.append(f2)
    
    return reg1_sets, reg2_sets


# ============================================================================
# Main test
# ============================================================================

# Bass clarinet dimensions (from benchmark)
BORE_LENGTH = 1171.0  # Phase 1 optimized for D2=73.4 Hz
BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0

# Tonehole positions from uniform bore optimizer (after Phase 2, before Phase 3)
HOLE_POSITIONS = [179.6, 299.5, 345.5, 455.0, 544.7, 624.2, 651.5]

# Register hole: Debut-Kergomard position at ~23.8% of L
REGISTER_POS = 0.238 * BORE_LENGTH  # ~279mm
REGISTER_DIAM = 3.5  # mm (midpoint of 3.2-3.8mm recommendation)
REGISTER_LENGTH = 3.0  # mm (chimney height, per ChatGPT ~2.5-4mm)

print(f"Bass Clarinet with Register Hole")
print(f"  Bore: {BORE_LENGTH:.0f}mm x {BORE_RADIUS:.1f}mm radius")
print(f"  Toneholes: {len(HOLE_POSITIONS)} at {[f'{p:.0f}' for p in HOLE_POSITIONS]}mm")
print(f"  Register hole: pos={REGISTER_POS:.0f}mm, dia={REGISTER_DIAM:.1f}mm, len={REGISTER_LENGTH:.1f}mm")
print()

# Build the instrument
all_pos, all_dia, all_len, reg_idx = make_bass_clarinet(
    BORE_LENGTH, BORE_RADIUS, HOLE_POSITIONS,
    [HOLE_DIAMETER] * len(HOLE_POSITIONS),
    [HOLE_LENGTH] * len(HOLE_POSITIONS),
    REGISTER_POS, REGISTER_DIAM, REGISTER_LENGTH,
    OUTER_DIAMETER,
)

print(f"  All holes by position:")
for i, (p, d, l) in enumerate(zip(all_pos, all_dia, all_len)):
    tag = "REGISTER" if i == reg_idx else "TONEHOLE"
    print(f"    {i}: {p:.1f}mm, dia={d:.1f}mm, len={l:.1f}mm [{tag}]")

# 1st register targets (from benchmark)
targets_reg1 = [73.4, 82.4, 92.5, 98.0, 110.0, 123.5, 138.6, 146.8]
names_reg1 = ["D2", "E2", "F#2", "G2", "A2", "B2", "C#3", "D3"]

# 2nd register targets: 12th above each 1st register note (x3 frequency for closed-open)
targets_reg2 = [f * 3 for f in targets_reg1]
names_reg2 = [f"{n} (12th)" for n in names_reg1]

# Build fingering sets
reg1_fs, reg2_fs = build_fingering_sets(len(HOLE_POSITIONS), reg_idx)

print(f"\n  Fingering sets (1st register, {len(reg1_fs)} notes):")
for i, fs in enumerate(reg1_fs):
    has_open = any(fs[j] == "open" for j in range(len(fs)) if j != reg_idx)
    marker = "[O]" if has_open else "[*]"
    reg_mark = "R" if fs[reg_idx] == "open" else "r"
    print(f"    {i}: {''.join('O' if f == 'open' else '.' for f in fs)} {marker} reg={reg_mark}")

# Test 1st register
print(f"\n{'='*70}")
print(f"1ST REGISTER (chalumeau, register hole CLOSED)")
print(f"{'='*70}")
radii = np.full(10, BORE_RADIUS)
inst = tmm_instrument_from_radii(
    radii, BORE_LENGTH, all_pos, all_dia, all_len,
    OUTER_DIAMETER, closed_top=True, cone_step=0.5,
)

target_wls = [SPEED_OF_SOUND / f for f in targets_reg1]
freqs1 = inst.compute_fingered_frequencies(target_wls, reg1_fs, n_register=1)

print(f"\n  {'Note':<16} {'Target':>10} {'Actual':>10} {'Err(c)':>10}")
print(f"  {'-'*16} {'-'*10} {'-'*10} {'-'*10}")
cents1 = []
for name, t, a in zip(names_reg1, targets_reg1, freqs1):
    c = 1200.0 * math.log2(a / t) if a > 0 else 1e10
    cents1.append(c)
    print(f"  {name:<16} {t:>10.1f} {a:>10.1f} {c:>+10.1f}")

c1 = np.array(cents1)
offset1 = np.median(c1)
rms1 = float(np.sqrt(np.mean((c1 - offset1) ** 2)))
print(f"\n  Median offset: {offset1:+.1f}c")
print(f"  RMS (relative): {rms1:.2f}c")

# Test 2nd register: n_register=3 (3rd harmonic = 12th for closed-open)
# The register hole vents the fundamental, so the 3rd harmonic plays
print(f"\n{'='*70}")
print(f"2ND REGISTER (clarino, register hole OPEN, n_register=2 = 3rd harmonic)")
print(f"{'='*70}")
target_wls2 = [SPEED_OF_SOUND / f for f in targets_reg2]
freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)

print(f"\n  {'Note':<16} {'Target':>10} {'Actual':>10} {'Err(c)':>10}")
print(f"  {'-'*16} {'-'*10} {'-'*10} {'-'*10}")
cents2 = []
for name, t, a in zip(names_reg2, targets_reg2, freqs2):
    c = 1200.0 * math.log2(a / t) if a > 0 else 1e10
    cents2.append(c)
    print(f"  {name:<16} {t:>10.1f} {a:>10.1f} {c:>+10.1f}")

c2 = np.array(cents2)
offset2 = np.median(c2)
rms2 = float(np.sqrt(np.mean((c2 - offset2) ** 2)))
print(f"\n  Median offset: {offset2:+.1f}c")
print(f"  RMS (relative): {rms2:.2f}c")

# Twelfths test: for each fingering, the 12th interval between 1st and 2nd register
print(f"\n{'='*70}")
print(f"TWELFTHS (interval between 1st and 2nd register for each fingering)")
print(f"{'='*70}")
print(f"\n  {'Fing':<6} {'1st(Hz)':>10} {'2nd(Hz)':>10} {'Ratio':>8} {'Target':>8} {'Err(c)':>10}")
print(f"  {'-'*6} {'-'*10} {'-'*10} {'-'*8} {'-'*8} {'-'*10}")
twelfth_errors = []
for i, (f1, f2) in enumerate(zip(freqs1, freqs2)):
    ratio = f2 / f1
    target_ratio = 3.0  # 12th = 3:1 for closed-open
    c = 1200.0 * math.log2(ratio / target_ratio)
    twelfth_errors.append(c)
    print(f"  {i:<6} {f1:>10.1f} {f2:>10.1f} {ratio:>8.3f} {target_ratio:>8.1f} {c:>+10.1f}")

twelfth_arr = np.array(twelfth_errors)
twelfth_rms = float(np.sqrt(np.mean(twelfth_arr ** 2)))
print(f"\n  Twelfth RMS error: {twelfth_rms:.1f}c")
print(f"  Debut et al. report: 20-30c error at register extremes")
print(f"  {'PASS' if twelfth_rms < 30 else 'CHECK'}")

# Also test register hole diameter sensitivity
print(f"\n{'='*70}")
print(f"SENSITIVITY: Register hole diameter")
print(f"{'='*70}")
for dia in [2.5, 3.0, 3.5, 4.0, 5.0, 6.0]:
    all_pos_t, all_dia_t, all_len_t, _ = make_bass_clarinet(
        BORE_LENGTH, BORE_RADIUS, HOLE_POSITIONS,
        [HOLE_DIAMETER] * len(HOLE_POSITIONS),
        [HOLE_LENGTH] * len(HOLE_POSITIONS),
        REGISTER_POS, dia, REGISTER_LENGTH, OUTER_DIAMETER,
    )
    inst_t = tmm_instrument_from_radii(
        radii, BORE_LENGTH, all_pos_t, all_dia_t, all_len_t,
        OUTER_DIAMETER, closed_top=True, cone_step=0.5,
    )
    f2_t = inst_t.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)
    twelfths_t = []
    for f1, f2v in zip(freqs1, f2_t):
        if f1 > 0 and f2v > 0:
            twelfths_t.append(1200.0 * math.log2((f2v / f1) / 3.0))
    if twelfths_t:
        print(f"  dia={dia:.1f}mm: twelfth RMS={np.sqrt(np.mean(np.array(twelfths_t)**2)):.1f}c")
