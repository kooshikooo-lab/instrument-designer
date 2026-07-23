"""Evaluate known working 7-hole configuration."""
import sys, numpy as np
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# Known working config from bass_clarinet_full_test.py
BORE_LENGTH = 1211.3
BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0
HOLE_POSITIONS = [175.9, 292.9, 337.5, 444.6, 532.0, 609.8, 636.4]
REGISTER_POS = 80.0
REGISTER_DIAM = 2.5
REGISTER_LENGTH = 3.0

targets_1st = [73.416, 82.407, 97.999, 110.000, 130.813, 146.832, 164.814, 195.998]
names = ["D2","E2","G2","A2","C3","D3","E3","G3"]

all_pos = list(HOLE_POSITIONS) + [REGISTER_POS]
all_dia = [HOLE_DIAMETER] * len(HOLE_POSITIONS) + [REGISTER_DIAM]
all_len = [HOLE_LENGTH] * len(HOLE_POSITIONS) + [REGISTER_LENGTH]
idx = np.argsort(all_pos)
all_pos_s = [all_pos[i] for i in idx]
all_dia_s = [all_dia[i] for i in idx]
all_len_s = [all_len[i] for i in idx]
reg_idx = all_pos_s.index(REGISTER_POS)

n_total = len(all_pos_s)
tonehole_indices = sorted([j for j in range(n_total) if j != reg_idx])

radii = np.full(10, BORE_RADIUS)
inst = tmm_instrument_from_radii(
    radii, BORE_LENGTH, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, 
    closed_top=True, cone_step=0.5
)

# 1st register fingerings
reg1_fs = []
for i in range(8):
    f = ["closed"] * n_total
    for j in tonehole_indices[:i]:
        f[j] = "open"
    f[reg_idx] = "closed"
    reg1_fs.append(f)

# 2nd register fingerings
reg2_fs = []
for i in range(8):
    f = ["closed"] * n_total
    for j in tonehole_indices[:i]:
        f[j] = "open"
    f[reg_idx] = "open"
    reg2_fs.append(f)

target_wls1 = [SPEED_OF_SOUND / f for f in targets_1st]
target_wls2 = [SPEED_OF_SOUND / (f * 3) for f in targets_1st]
freqs1 = inst.compute_fingered_frequencies(target_wls1, reg1_fs, n_register=1)
freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)

print(f"{'='*80}")
print(f"KNOWN WORKING 7-HOLE CONFIG EVALUATION")
print(f"{'='*80}")
print(f"  Bore: {BORE_LENGTH:.1f}mm x {BORE_RADIUS}mm")
print(f"  Register: {REGISTER_POS}mm, {REGISTER_DIAM}mm")
print(f"  Holes: {[f'{p:.0f}' for p in HOLE_POSITIONS]}")
print(f"  Model: uniform cylinder, 11mm holes")
print()

c1_all, c2_all, c12_all = [], [], []
for n, t1, f1, f2 in zip(names, targets_1st, freqs1, freqs2):
    c1 = 1200*np.log2(f1/t1) if f1 > 0 else 0
    c2 = 1200*np.log2(f2/(t1*3)) if f2 > 0 else 0
    c12 = 1200*np.log2((f2/f1)/3.0) if f1 > 0 and f2 > 0 else 0
    c1_all.append(c1); c2_all.append(c2); c12_all.append(c12)
    print(f"  {n:<4} 1st={f1:>7.1f}Hz {c1:>+7.1f}c   2nd={f2:>7.1f}Hz {c2:>+7.1f}c   12th={c12:>+7.1f}c")

c1_arr = np.array(c1_all); c2_arr = np.array(c2_all); c12_arr = np.array(c12_all)
off1 = np.median(c1_arr); off2 = np.median(c2_arr)
rms1 = np.sqrt(np.mean((c1_arr - off1)**2))
rms2 = np.sqrt(np.mean((c2_arr - off2)**2))
rms12 = np.sqrt(np.mean(c12_arr**2))
print(f"\n  1st register: offset={off1:+.1f}c RMS={rms1:.2f}c")
print(f"  2nd register: offset={off2:+.1f}c RMS={rms2:.2f}c")
print(f"  Twelfths: RMS={rms12:.1f}c")
print(f"  Status: {'PASS' if rms12 < 20 else 'CHECK'}")