"""Complete bass clarinet test: both registers validated with optimized config."""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

# OPTIMIZED CONFIGURATION (from test_refine_with_register.py)
BORE_LENGTH = 1211.3
BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0
HOLE_POSITIONS = [175.9, 292.9, 337.5, 444.6, 532.0, 609.8, 636.4]
REGISTER_POS = 80.0
REGISTER_DIAM = 2.5
REGISTER_LENGTH = 3.0

targets_1st = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]
names = ["D2","E2","F#2","G2","A2","B2","C#3","D3"]

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

reg1_fs = make_fingerings("closed")
reg2_fs = make_fingerings("open")
targets_2nd = [t * 3 for t in targets_1st]

radii = np.full(10, BORE_RADIUS)
inst = tmm_instrument_from_radii(radii, BORE_LENGTH, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)

# 1st register
target_wls1 = [SPEED_OF_SOUND / f for f in targets_1st]
freqs1 = inst.compute_fingered_frequencies(target_wls1, reg1_fs, n_register=1)

# 2nd register
target_wls2 = [SPEED_OF_SOUND / f for f in targets_2nd]
freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)

print(f"{'='*80}")
print(f"BASS CLARINET FINAL CONFIGURATION")
print(f"{'='*80}")
print(f"\n  Bore: {BORE_LENGTH:.1f}mm × {BORE_RADIUS}mm radius")
print(f"  Register: pos={REGISTER_POS}mm, dia={REGISTER_DIAM}mm")
print(f"  Toneholes: {[f'{p:.0f}' for p in HOLE_POSITIONS]}")
print(f"\n  Model: uniform cylinder, closed-top (Bordeaux method)")
print(f"  Systematic offset: -63c (correctable by mouthpiece pull)")
print()

print(f"  {'Note':<8} {'1st(Hz)':>10} {'1st err':>10} {'2nd(Hz)':>10} {'2nd err':>10} {'12th(c)':>10}")
print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
c1_all, c2_all, c12_all = [], [], []
for n, t1, t2, f1, f2 in zip(names, targets_1st, targets_2nd, freqs1, freqs2):
    c1 = 1200*math.log2(f1/t1) if f1 > 0 else 0
    c2 = 1200*math.log2(f2/t2) if f2 > 0 else 0
    c12 = 1200*math.log2((f2/f1)/3.0) if f1 > 0 and f2 > 0 else 0
    c1_all.append(c1); c2_all.append(c2); c12_all.append(c12)
    print(f"  {n:<8} {f1:>10.1f} {c1:>+10.0f} {f2:>10.1f} {c2:>+10.0f} {c12:>+10.0f}")

c1_arr = np.array(c1_all); c2_arr = np.array(c2_all); c12_arr = np.array(c12_all)
off1 = np.median(c1_arr); off2 = np.median(c2_arr)
rms1 = np.sqrt(np.mean((c1_arr - off1)**2))
rms2 = np.sqrt(np.mean((c2_arr - off2)**2))
rms12 = np.sqrt(np.mean(c12_arr**2))

print(f"\n  {'':8} {'':10} {'':10} {'':10} {'':10} {rms12:>10.1f}")
print(f"\n  1st register: offset={off1:+.0f}c RMS(rel)={rms1:.2f}c")
print(f"  2nd register: offset={off2:+.0f}c RMS(rel)={rms2:.2f}c")
print(f"  Twelfths: RMS={rms12:.1f}c")
print(f"\n  Status: {'PASS' if rms12 < 20 else 'CHECK'}")
