"""Scan register hole position with all toneholes to find optimal 12th."""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

BORE_LENGTH = 1171.0
BORE_RADIUS = 12.5
OUTER_DIAMETER = 37.0
HOLE_DIAMETER = 11.0
HOLE_LENGTH = 5.0
HOLE_POSITIONS = [179.6, 299.5, 345.5, 455.0, 544.7, 624.2, 651.5]

def make_bass_clarinet(register_pos, register_diam, register_len=3.0):
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
target_wls1 = [SPEED_OF_SOUND / f for f in targets_1st]
target_wls2 = [SPEED_OF_SOUND / f for f in targets_2nd]

radii = np.full(10, BORE_RADIUS)

# Scan positions, avoid toneholes
positions = list(range(80, 601, 20))
# Remove positions too close to existing holes
tonehole_set = set(int(p) for p in HOLE_POSITIONS)
positions = [p for p in positions if p not in tonehole_set and not any(abs(p - tp) < 5 for tp in HOLE_POSITIONS)]

diameters = [2.5, 3.0, 3.5, 4.0]

print(f"Scanning {len(positions)} positions × {len(diameters)} diameters = {len(positions)*len(diameters)} configs")
print()

results = []
for dia in diameters:
    for pos in positions:
        # skip positions that collide with toneholes
        all_pos_s, all_dia_s, all_len_s, reg_idx = make_bass_clarinet(pos, dia)
        reg1_fs, reg2_fs = build_fingering_sets(reg_idx)
        
        try:
            inst = tmm_instrument_from_radii(radii, BORE_LENGTH, all_pos_s, all_dia_s, all_len_s, OUTER_DIAMETER, closed_top=True, cone_step=0.5)
        except:
            continue
        
        try:
            freqs1 = inst.compute_fingered_frequencies(target_wls1, reg1_fs, n_register=1)
            freqs2 = inst.compute_fingered_frequencies(target_wls2, reg2_fs, n_register=2)
        except Exception as e:
            print(f"  FAIL pos={pos}, dia={dia}: {e}")
            continue
        
        twelfth_errors = []
        for i in range(8):
            if freqs1[i] and freqs2[i]:
                ratio = freqs2[i] / freqs1[i]
                err = 1200 * math.log2(ratio / 3.0)
                twelfth_errors.append(err)
        
        if not twelfth_errors:
            continue
            
        twelfth_rms = math.sqrt(sum(e*e for e in twelfth_errors) / len(twelfth_errors))
        results.append((pos, dia, twelfth_rms, twelfth_errors))

# Print results table
print(f"\n{'='*80}")
print(f"Register Hole Position Scan (twelfth RMS error in cents)")
print(f"{'='*80}")
print(f"{'Pos':>6} ", end="")
for d in diameters:
    print(f"  {d:>6}mm", end="")
print()
print(f"{'-'*6} ", end="")
for _ in diameters:
    print(f"  {'-'*6}", end="")
print()

for pos in positions:
    print(f"{pos:>6} ", end="")
    for d in diameters:
        matching = [r for r in results if abs(r[0]-pos)<0.1 and abs(r[1]-d)<0.1]
        if matching:
            v = matching[0][2]
            color = "PASS" if v < 40 else "warn" if v < 70 else "FAIL"
            print(f"  {v:>6.1f}", end="")
        else:
            print(f"  {'----':>6}", end="")
    print()

# Find best
best = min(results, key=lambda r: r[2])
print(f"\n{'='*80}")
print(f"BEST: pos={best[0]}mm, dia={best[1]}mm, twelfth RMS={best[2]:.1f}c")
print(f"Individual twelfths: {[f'{e:.1f}' for e in best[3]]}")
