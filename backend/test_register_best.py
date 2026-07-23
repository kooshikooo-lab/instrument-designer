"""Comprehensive test of best register hole configuration."""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

BORE_LENGTH = 1171.0
BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0
HOLE_POSITIONS = [179.6, 299.5, 345.5, 455.0, 544.7, 624.2, 651.5]

def make_bass_clarinet(register_pos, register_diam=2.5, register_len=3.0):
    all_pos = list(HOLE_POSITIONS) + [register_pos]
    all_dia = [HOLE_DIAMETER] * len(HOLE_POSITIONS) + [register_diam]
    all_len = [HOLE_LENGTH] * len(HOLE_POSITIONS) + [register_len]
    idx = np.argsort(all_pos)
    all_pos_s = [all_pos[i] for i in idx]
    all_dia_s = [all_dia[i] for i in idx]
    all_len_s = [all_len[i] for i in idx]
    reg_idx = all_pos_s.index(register_pos)
    return all_pos_s, all_dia_s, all_len_s, reg_idx

def build_fingering_sets(reg_idx):
    n_total = len(HOLE_POSITIONS) + 1
    reg1_sets, reg2_sets = [], []
    for i in range(len(HOLE_POSITIONS) + 1):
        f1 = ["closed"] * n_total
        if i > 0:
            th_indices = sorted([j for j in range(n_total) if j != reg_idx])
            for j in th_indices[:i]:
                f1[j] = "open"
        f1[reg_idx] = "closed"
        reg1_sets.append(f1)
        f2 = list(f1)
        f2[reg_idx] = "open"
        reg2_sets.append(f2)
    return reg1_sets, reg2_sets

targets_1st = [73.416, 82.407, 92.499, 97.999, 110.000, 123.471, 138.591, 146.832]
targets_2nd = [t * 3 for t in targets_1st]
names = ["D2","E2","F#2","G2","A2","B2","C#3","D3"]
target_wls1 = [SPEED_OF_SOUND / f for f in targets_1st]
target_wls2 = [SPEED_OF_SOUND / f for f in targets_2nd]
radii = np.full(10, BORE_RADIUS)

for pos, label in [(80, "80mm (acoustic best)"), (140, "140mm (practical)"), (279, "279mm (Debut 23.8%)")]:
    all_pos_s, all_dia_s, all_len_s, reg_idx = make_bass_clarinet(pos)
    reg1_fs, reg2_fs = build_fingering_sets(reg_idx)
    inst = tmm_instrument_from_radii(radii, BORE_LENGTH, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
    
    freqs1 = inst.compute_fingered_frequencies(target_wls1, reg1_fs, n_register=1)
    freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)
    
    print(f"\n{'='*70}")
    print(f"REGISTER @ {label}")
    print(f"{'='*70}")
    
    # 1st register
    cents1 = [1200*math.log2(a/t) for t,a in zip(targets_1st, freqs1) if a]
    offset1 = np.median(cents1)
    rms1 = np.sqrt(np.mean((np.array(cents1) - offset1)**2))
    print(f"1st reg: offset={offset1:+.0f}c  RMS(rel)={rms1:.1f}c")
    
    # 2nd register
    cents2 = [1200*math.log2(a/t) for t,a in zip(targets_2nd, freqs2) if a]
    offset2 = np.median(cents2)
    rms2 = np.sqrt(np.mean((np.array(cents2) - offset2)**2))
    print(f"2nd reg: offset={offset2:+.0f}c  RMS(rel)={rms2:.1f}c")
    
    # Twelfths
    twelfths = []
    for n, f1, f2 in zip(names, freqs1, freqs2):
        if f1 and f2:
            r = f2/f1
            e = 1200*math.log2(r/3.0)
            twelfths.append(e)
    rms12 = np.sqrt(np.mean(np.array(twelfths)**2))
    print(f"Twelfths: RMS={rms12:.1f}c  individual: {', '.join(f'{e:+.0f}' for e in twelfths)}")
