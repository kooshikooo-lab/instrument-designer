"""Add Bessel bell to bass clarinet and test both registers."""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# Current optimized parameters
BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0
HOLE_POSITIONS = [175.9, 292.9, 337.5, 444.6, 532.0, 609.8, 636.4]
REGISTER_POS = 80.0
REGISTER_DIAM = 2.5
REGISTER_LENGTH = 3.0

# Bell parameters (from ChatGPT research)
BELL_LENGTH = 220.0
BELL_END_RADIUS = 26.0  # 52mm ID
BELL_GAP = 60.0  # gap after last tonehole before bell starts
n_bessel = math.log2(BELL_END_RADIUS / BORE_RADIUS)  # ~1.057

# Total length from bell test
L_cyl = 696.4  # HOLE_POSITIONS[-1] + BELL_GAP = 636.4 + 60
L_total = 916.4  # L_cyl + BELL_LENGTH

def build_profile():
    n_seg = 200
    radii = np.zeros(n_seg)
    for i in range(n_seg):
        x = i * L_total / n_seg
        if x < L_cyl:
            radii[i] = BORE_RADIUS
        else:
            xi = (x - L_cyl) / BELL_LENGTH
            radii[i] = BORE_RADIUS * (1 + xi)**n_bessel
    return radii

# Build all holes
all_pos = list(HOLE_POSITIONS) + [REGISTER_POS]
all_dia = [HOLE_DIAMETER] * len(HOLE_POSITIONS) + [REGISTER_DIAM]
all_len = [HOLE_LENGTH] * len(HOLE_POSITIONS) + [REGISTER_LENGTH]
idx_s = np.argsort(all_pos)
all_pos_s = [all_pos[i] for i in idx_s]
all_dia_s = [all_dia[i] for i in idx_s]
all_len_s = [all_len[i] for i in idx_s]
reg_idx = all_pos_s.index(REGISTER_POS)

n_total = len(all_pos_s)
tonehole_indices = sorted([j for j in range(n_total) if j != reg_idx])

def make_fingerings(register_state):
    fingerings = []
    for i in range(8):
        f = ["closed"] * n_total
        if i > 0:
            for j in tonehole_indices[:i]:
                f[j] = "open"
        f[reg_idx] = register_state
        fingerings.append(f)
    return fingerings

targets_1st = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]
targets_2nd = [t * 3 for t in targets_1st]
names = ["D2","E2","F#2","G2","A2","B2","C#3","D3"]

radii = build_profile()
print(f"Bore profile:")
print(f"  Cylinder: 0-{L_cyl:.0f}mm ({BORE_RADIUS}mm radius)")
print(f"  Bell: {L_cyl:.0f}-{L_total:.0f}mm (Bessel n={n_bessel:.3f})")
print(f"  Total: {L_total:.0f}mm")
print(f"  End radius: {radii[-1]:.1f}mm ({radii[-1]*2:.0f}mm dia)")
print(f"  Register: {REGISTER_POS}mm, 2.5mm dia")
print(f"  Toneholes: {HOLE_POSITIONS}")

inst = tmm_instrument_from_radii(radii, L_total, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)

reg1_fs = make_fingerings("closed")
reg2_fs = make_fingerings("open")

target_wls1 = [SPEED_OF_SOUND / f for f in targets_1st]
target_wls2 = [SPEED_OF_SOUND / f for f in targets_2nd]

freqs1 = inst.compute_fingered_frequencies(target_wls1, reg1_fs, n_register=1)
freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)

print(f"\n{'='*70}")
print(f"1ST REGISTER (register closed)")
print(f"{'='*70}")
print(f"  {'Note':<8} {'Target':>8} {'Actual':>8} {'Err(c)':>8}")
c1_all = []
for n, t, a in zip(names, targets_1st, freqs1):
    c = 1200*math.log2(a/t) if a > 0 else 0
    c1_all.append(c)
    print(f"  {n:<8} {t:>8.1f} {a:>8.1f} {c:>+8.0f}")
c1_arr = np.array(c1_all)
off1 = np.median(c1_arr)
rms1 = np.sqrt(np.mean((c1_arr - off1)**2))
print(f"  {'':8} {'':8} {'':8} {'':8}")
print(f"  Offset: {off1:+.0f}c  RMS(rel): {rms1:.1f}c")

print(f"\n{'='*70}")
print(f"2ND REGISTER (register open)")
print(f"{'='*70}")
print(f"  {'Note':<8} {'Target':>8} {'Actual':>8} {'Err(c)':>8}")
c2_all = []
for n, t, a in zip(names, targets_2nd, freqs2):
    c = 1200*math.log2(a/t) if a > 0 else 0
    c2_all.append(c)
    print(f"  {n:<8} {t:>8.1f} {a:>8.1f} {c:>+8.0f}")
c2_arr = np.array(c2_all)
off2 = np.median(c2_arr)
rms2 = np.sqrt(np.mean((c2_arr - off2)**2))
print(f"  {'':8} {'':8} {'':8} {'':8}")
print(f"  Offset: {off2:+.0f}c  RMS(rel): {rms2:.1f}c")

print(f"\n{'='*70}")
print(f"TWELFTHS")
print(f"{'='*70}")
print(f"  {'Note':<8} {'1st':>8} {'2nd':>8} {'Ratio':>7} {'Err(c)':>8}")
c12_all = []
for n, f1, f2 in zip(names, freqs1, freqs2):
    r = f2/f1
    c = 1200*math.log2(r/3.0)
    c12_all.append(c)
    print(f"  {n:<8} {f1:>8.1f} {f2:>8.1f} {r:>7.3f} {c:>+8.0f}")
c12_arr = np.array(c12_all)
rms12 = np.sqrt(np.mean(c12_arr**2))
print(f"  RMS: {rms12:.1f}c")
print(f"  Status: {'PASS' if rms12 < 20 else 'CHECK'}")
