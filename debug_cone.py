"""Fast diagnostic: cone vs cylinder with correct hole sizing"""
import sys, math, numpy as np
from scipy.optimize import minimize as sp_min
sys.path.insert(0, 'backend')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND
targets = [349.2, 392.0, 415.3, 466.2, 523.3, 587.3]
names = ['F4','G4','Ab4','Bb4','C5','D5']
fingerings = [
    ['closed','closed','closed','closed','closed','closed'],
    ['closed','closed','closed','closed','closed','open'],
    ['closed','closed','closed','closed','open','open'],
    ['closed','closed','closed','open','open','open'],
    ['closed','closed','open','open','open','open'],
    ['closed','open','open','open','open','open'],
]
N_REG = 3; L = 965.2; OD = 120.0; CHIMNEY = 0.7

def eval_inst(inst, label):
    cents = []
    for fing, tgt in zip(fingerings, targets):
        wl = inst.find_resonance(c/tgt, fing, n_register=N_REG)
        f = inst.frequency_from_wavelength(wl)
        cents.append(1200*math.log2(f/tgt) if f>0 and math.isfinite(f) else 1e10)
    ca = np.array(cents)
    if np.any(np.abs(ca)>1e5):
        print(f"  {label}: FAIL"); return 999
    even = float(np.sqrt(np.mean((ca-np.median(ca))**2)))
    absr = float(np.sqrt(np.mean(ca**2)))
    print(f"  {label}: Even={even:.1f}c  Abs={absr:.1f}c  Off={np.median(ca):+.1f}c")
    for n,fr,ct in zip(names,targets,cents):
        print(f"    {n:>5} ({fr:.0f}Hz): {ct:>+7.1f}c")
    return even

# Lefebvre cone
r_in, angle = 6.25, 3.0
radii_cone = np.linspace(r_in, r_in + L*math.tan(math.radians(angle)), 12)

# 1: Cone, tiny holes (old test)
print("=== 1: Cone, HD=7.5mm fixed, c/(2*t) positions (OLD) ===")
hp1 = sorted([c/(2.0*t) for t in reversed(targets)])
inst1 = tmm_instrument_from_radii(radii_cone, L, hp1, [7.5]*6, [3.5]*6, OD, False, 0.5)
eval_inst(inst1, "OLD")

# 2: Cone, 54% holes, c/t positions
print("\n=== 2: Cone, 54% bore holes, c/t positions ===")
hp2 = sorted([min(c/t, L-20) for t in reversed(targets)])
def hd_at(pos):
    r = r_in + pos * math.tan(math.radians(angle))
    return 0.54 * 2 * r
hd2 = [hd_at(p) for p in hp2]
inst2 = tmm_instrument_from_radii(radii_cone, L, hp2, hd2, [CHIMNEY]*6, OD, False, 0.5)
eval_inst(inst2, "54% holes")

# 3: Cone, L-BFGS-B optimize holes (54% sizing)
print("\n=== 3: Cone, L-BFGS-B optimize holes (54%) ===")
def obj3(x):
    hp = sorted(x)
    for i in range(1, len(hp)):
        if hp[i] <= hp[i-1]+5: return 1e6
    if hp[0]<50 or hp[-1]>L-20: return 1e6
    hd = [hd_at(p) for p in hp]
    inst = tmm_instrument_from_radii(radii_cone, L, hp, hd, [CHIMNEY]*6, OD, False, 0.5)
    cents = []
    for fing, tgt in zip(fingerings, targets):
        wl = inst.find_resonance(c/tgt, fing, n_register=N_REG)
        f = inst.frequency_from_wavelength(wl)
        cents.append(1200*math.log2(f/tgt) if f>0 and math.isfinite(f) else 1e10)
    ca = np.array(cents)
    if np.any(np.abs(ca)>1e5): return 1e10
    med = float(np.median(ca))
    return float(np.sqrt(np.mean((ca-med)**2))) + 0.05*float(np.sqrt(np.mean(ca**2)))

res3 = sp_min(obj3, np.array(hp2), method='L-BFGS-B',
              bounds=[(50,L-20)]*6, options={"maxiter":300})
print(f"  cost={res3.fun:.1f}")
inst3 = tmm_instrument_from_radii(radii_cone, L, sorted(res3.x),
    [hd_at(p) for p in sorted(res3.x)], [CHIMNEY]*6, OD, False, 0.5)
eval_inst(inst3, "Cone 54% opt")

# 4: Cylinder for comparison
print("\n=== 4: Cylinder (r=12.5mm), 7.5mm holes, c/t positions ===")
radii_cyl = np.full(12, 12.5)
hp4 = sorted([min(c/t, L-20) for t in reversed(targets)])
inst4 = tmm_instrument_from_radii(radii_cyl, L, hp4, [7.5]*6, [CHIMNEY]*6, OD, False, 0.5)
eval_inst(inst4, "Cylinder")

# 5: Cylinder L-BFGS-B optimize
print("\n=== 5: Cylinder, L-BFGS-B optimize holes ===")
def obj5(x):
    hp = sorted(x)
    for i in range(1, len(hp)):
        if hp[i] <= hp[i-1]+5: return 1e6
    if hp[0]<50 or hp[-1]>L-20: return 1e6
    inst = tmm_instrument_from_radii(radii_cyl, L, hp, [7.5]*6, [CHIMNEY]*6, OD, False, 0.5)
    cents = []
    for fing, tgt in zip(fingerings, targets):
        wl = inst.find_resonance(c/tgt, fing, n_register=N_REG)
        f = inst.frequency_from_wavelength(wl)
        cents.append(1200*math.log2(f/tgt) if f>0 and math.isfinite(f) else 1e10)
    ca = np.array(cents)
    if np.any(np.abs(ca)>1e5): return 1e10
    med = float(np.median(ca))
    return float(np.sqrt(np.mean((ca-med)**2))) + 0.05*float(np.sqrt(np.mean(ca**2)))

res5 = sp_min(obj5, np.array(hp4), method='L-BFGS-B',
              bounds=[(50,L-20)]*6, options={"maxiter":300})
print(f"  cost={res5.fun:.1f}")
inst5 = tmm_instrument_from_radii(radii_cyl, L, sorted(res5.x),
    [7.5]*6, [CHIMNEY]*6, OD, False, 0.5)
eval_inst(inst5, "Cylinder opt")

# 6: What does a REAL sax hole pattern look like?
# Postma/Selmer: holes grow from ~10mm (C) to ~38mm (Bb/B)
# Bore at those positions: ~13mm (near reed) to ~60mm (near bell)
print("\n=== 6: Cone with REALISTIC sax hole sizes ===")
# Real alto sax hole positions from Postma (approximate, from bell):
# Bb/B: ~100mm from bell, d=~38mm
# C#: ~150mm from bell, d=~34mm
# Eb: ~200mm from bell, d=~33mm
# F: ~300mm from bell, d=~28mm
# G: ~350mm from bell, d=~24mm
# A: ~400mm from bell, d=~20mm
# Convert to from-reed positions:
real_hp = [L - x for x in [100, 150, 200, 300, 350, 400]]
real_hd = [38, 34, 33, 28, 24, 20]
print(f"  Positions from reed: {[round(p) for p in real_hp]}")
print(f"  Diameters: {real_hd}")
inst6 = tmm_instrument_from_radii(radii_cone, L, real_hp, real_hd, [CHIMNEY]*6, OD, False, 0.5)
eval_inst(inst6, "Real sax holes")
