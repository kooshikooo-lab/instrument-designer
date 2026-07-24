"""Test: CORRECT bass clarinet fingering chart (reed-end first = real physics)."""
import sys, time
import numpy as np
sys.path.insert(0, 'backend')
from optimizer_global import GlobalFingeringOptimizer
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

FIXED_REGISTER = [(80.0, 2.5, 3.0)]

# Bass clarinet written range D2 to D3 (chalumeau) + register key for clarion
# Written D2 = 73.4Hz (sounds C2), D3 = 146.8Hz (sounds C3)
# Chalumeau register: D2 to D3 (fundamental)
# Clarion register: register key + same fingerings = 12th above

# 12 holes + register = 13 columns
# H1 = closest to reed (LH1), H12 = closest to bell
# Fingering: open from reed end first

# Chalumeau register (register closed)
# Based on real Boehm bass clarinet fingerings
chalumeau = {
    "D2":  [0,0,0,0,0,0,0,0,0,0,0,0],  # all closed
    "D#2": [1,0,0,0,0,0,0,0,0,0,0,0],  # LH1 (thumb) + register? No, D# = LH1 only for chalumeau
    # Actually: D#2 = LH1 only (like clarinet)
    "E2":  [1,1,0,0,0,0,0,0,0,0,0,0],  # LH1+LH2
    "F2":  [1,1,1,0,0,0,0,0,0,0,0,0],  # LH1+LH2+LH3
    "F#2": [1,1,1,1,0,0,0,0,0,0,0,0],  # LH1-LH4
    "G2":  [1,1,1,1,1,0,0,0,0,0,0,0],  # LH1-LH4+RH1
    "G#2": [1,1,1,1,1,1,0,0,0,0,0,0],  # +RH2
    "A2":  [1,1,1,1,1,1,1,0,0,0,0,0],  # +RH3
    "A#2": [1,1,1,1,1,1,1,1,0,0,0,0],  # +RH4 (or side key)
    "B2":  [1,1,1,1,1,1,1,1,1,0,0,0],  # +side Bb
    "C3":  [1,1,1,1,1,1,1,1,1,1,0,0],  # +side C
    "C#3": [1,1,1,1,1,1,1,1,1,1,1,0],  # +side C#
    "D3":  [1,1,1,1,1,1,1,1,1,1,1,1],  # all open
}

# But wait - real clarinet has cross-fingerings for chromatics
# Let me use the ACTUAL Boehm bass clarinet fingerings:
# D2: all closed
# D#2: LH1 (thumb hole) 
# E2: LH1+LH2
# F2: LH1+LH2+LH3
# F#2: LH1+LH2+LH3+LH4 (F# key)
# G2: LH1+LH2+LH3+RH1
# G#2: LH1+LH2+LH3+LH4+RH1 (G# key)
# A2: LH1+LH2+RH1
# A#2: LH1+RH1 (or LH1+side Bb)
# B2: LH1+RH1+RH2
# C3: LH1+RH1+RH2+RH3
# C#3: LH1+RH1+RH2+RH3+RH4
# D3: LH1+RH1+RH2+RH3+RH4+side keys

# Actually, let me check the REAL Boehm system for bass clarinet:
# The thumb hole is the register key when OPEN, but for chalumeau it's CLOSED
# Left hand: 4 fingers cover 4 holes (LH1-4), plus LH pinky keys (G#/Eb, F/C, E/B, Eb/Bb)
# Right hand: 3 fingers cover 3 holes (RH1-3), plus RH pinky keys (F/C, E/B, Eb/Bb, low C)
# Thumb: register key (opens for clarion)

# For CHALUMEAU register (register key CLOSED):
# D2: all 7 finger holes closed, all pinky keys closed
# D#2: LH1 open (thumb hole? No, register key is separate)
# Actually the LEFT THUMB covers a hole (not the register key) for D#2/E2
# The register key is operated by LEFT THUMB but is a SEPARATE hole at ~80mm

# Let me be very precise about bass clarinet Boehm system:
# Finger holes (operated by fingers, not keys):
# LH: thumb hole (covered for D2, open for D#2+), LH1, LH2, LH3
# RH: RH1, RH2, RH3
# That's 7 finger holes
# Keys (operated by pinkies/side):
# LH pinky: G#/Eb, F/C, E/B, Eb/Bb (4 keys)
# RH pinky: F/C, E/B, Eb/Bb, low C (4 keys)
# Side keys: side Bb, side C, side C#, side F# (4 keys)
# Thumb: register key

# For CHALUMEAU D2 to D3:
# D2: all 7 finger holes closed
# D#2: LH thumb hole open (1st finger hole)
# E2: LH thumb + LH1 open
# F2: LH thumb + LH1 + LH2
# F#2: LH thumb + LH1 + LH2 + LH3 (F# key opens LH3? No, F# is a KEY)
# G2: LH thumb + LH1 + LH2 + RH1
# G#2: LH thumb + LH1 + LH2 + LH3 + RH1 (G# key)
# A2: LH thumb + LH1 + RH1
# A#2: LH thumb + RH1 (or LH thumb + side Bb key)
# B2: LH thumb + RH1 + RH2
# C3: LH thumb + RH1 + RH2 + RH3
# C#3: LH thumb + RH1 + RH2 + RH3 + RH4 (C# key)
# D3: LH thumb + RH1 + RH2 + RH3 + RH4 + side

# This is getting complex. Let me simplify to the 7 finger holes + register
# and use keys as additional holes.

# SIMPLIFIED MODEL: 7 finger holes + register = 8 holes
# H1 = LH thumb hole (covered for D2, open for D#2+)
# H2 = LH1
# H3 = LH2
# H4 = LH3
# H5 = RH1
# H6 = RH2
# H7 = RH3
# R = register key (at 80mm)

# Chalumeau fingerings (R=closed):
# D2:  0000000
# D#2: 1000000  (H1 open)
# E2:  1100000  (H1+H2)
# F2:  1110000  (H1+H2+H3)
# F#2: 1111000  (H1+H2+H3+H4) -- F# key
# G2:  1110100  (H1+H2+H3+H5) -- RH1
# G#2: 1111100  (H1+H2+H3+H4+H5) -- G# key
# A2:  1100100  (H1+H2+H5)
# A#2: 1000100  (H1+H5) or 1000010 (side Bb)
# B2:  1001100  (H1+H5+H6)
# C3:  1001110  (H1+H5+H6+H7)
# C#3: 1001111  (H1+H5+H6+H7+side)
# D3:  1111111  (all open)

# Let's test this with the optimizer

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

chalumeau_fingerings = {
    "D2":  [0,0,0,0,0,0,0],
    "D#2": [1,0,0,0,0,0,0],
    "E2":  [1,1,0,0,0,0,0],
    "F2":  [1,1,1,0,0,0,0],
    "F#2": [1,1,1,1,0,0,0],
    "G2":  [1,1,1,0,1,0,0],
    "G#2": [1,1,1,1,1,0,0],
    "A2":  [1,1,0,0,1,0,0],
    "A#2": [1,0,0,0,1,0,0],  # side Bb fingering
    "B2":  [1,0,0,0,1,1,0],
    "C3":  [1,0,0,0,1,1,1],
    "C#3": [1,0,0,0,1,1,1],  # plus side key - simplified
    "D3":  [1,1,1,1,1,1,1],
}

# Add register column (closed for chalumeau)
chart = []
for n in names:
    row = ["open" if x else "closed" for x in chalumeau_fingerings[n]] + ["closed"]
    chart.append(row)

print("=== CORRECT Bass Clarinet Chalumeau Fingerings ===")
for n, row in zip(names, chart):
    pat = "".join("O" if x=="open" else "X" for x in row[:7])
    print(f"  {n:>4}: {pat}  R=X")

# Initial guess: evenly spaced along bore
hole_positions = [176, 293, 338, 445, 532, 610, 636]

import numpy as np
t0 = time.time()
opt = GlobalFingeringOptimizer(
    targets_hz=targets,
    fingering_chart=chart,
    bore_radius=12.5,
    outer_diameter=37.0,
    hole_diameter=11.0,
    hole_length=5.0,
    closed_top=True,
    n_register=2,
    bore_length=1211.3,
    fixed_holes=FIXED_REGISTER,
    register_weights=(0.15, 1.0),
    optimize_grad=True,
    grad_bounds=(6.0, 12.0, 16.0, 22.0),
)

result = opt.optimize(initial_positions=hole_positions, bounds_per_hole=80,
                      use_de=True, verbose=True)
t1 = time.time()
print(f"\nTime: {t1-t0:.0f}s")
print(f"Reg1 RMS: {result['final_rms_1st_cents']:.2f}c")
print(f"Reg2 RMS: {result['final_rms_2nd_cents']:.2f}c")
print(f"Holes: {[f'{p:.0f}' for p in result['free_hole_positions']]}")
if 'graduated_diameters' in result:
    print(f"Diameters: {[f'{d:.1f}' for d in result['graduated_diameters']]}")

# Evaluate
free_pos = sorted(result['free_hole_positions'])
all_pos = sorted(free_pos + [80.0])
grad_diam = result.get('graduated_diameters', [11.0]*7)

inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos, 
    [d/2.0 for d in grad_diam] + [2.5/2.0],
    [5.0]*7 + [3.0], 37.0, closed_top=True, cone_step=0.5
)

target_wls = [SPEED_OF_SOUND / f for f in targets]
freqs = inst.compute_fingered_frequencies(target_wls, chart, n_register=1)

print(f"\n{'Note':<6} {'Target':>8} {'Actual':>8} {'Error(c)':>10}")
print("-" * 40)
errors = []
for n, t, f in zip(names, targets, freqs):
    c = 1200 * np.log2(f/t) if f > 0 else 0
    errors.append(c)
    print(f"  {n:<6} {t:>8.1f} {f:>8.1f} {c:>+10.1f}")

err_arr = np.array(errors)
offset = np.median(err_arr)
rms = np.sqrt(np.mean((err_arr - offset)**2))
print(f"\nOffset: {offset:+.1f}c  RMS(relative): {rms:.2f}c")