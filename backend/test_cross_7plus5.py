"""Fix validated 7-hole diatonic, optimize only 5 corrective holes for chromatic notes.

Primary holes (fixed, validated at 0.45c RMS): [176, 293, 338, 445, 532, 610, 636]
Corrective holes (optimized): H8-H12, placed between primary holes.
"""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Primary diatonic holes (validated, FIXED)
PRIMARY = [176, 293, 338, 445, 532, 610, 636]

# Chart: 13 notes x 13 holes (12 free + 1 register)
# Primary holes H1-H7: reed-end-first sequential
# Chromatic notes use corrective holes for cross-fingerings
chart = [
    #           H1 H2 H3 H4 H5 H6 H7  H8 H9 H10 H11 H12  Reg
    [0,0,0,0,0,0,0, 0,0,0,0,0, 0],  # D2
    [1,0,0,0,0,0,0, 0,1,0,0,0, 0],  # D#2: H1+H9 (cross)
    [1,1,0,0,0,0,0, 0,0,0,0,0, 0],  # E2: H1+H2
    [1,1,1,0,0,0,0, 0,0,0,0,0, 0],  # F2: H1+H2+H3
    [1,1,1,0,0,0,0, 1,0,0,0,0, 0],  # F#2: H1+H2+H3+H8 (cross)
    [1,1,1,1,0,0,0, 0,0,0,0,0, 0],  # G2: H1+H2+H3+H4
    [1,1,1,0,1,0,0, 1,0,0,0,0, 0],  # G#2: H1+H2+H3+H5+H8 (cross)
    [1,1,0,0,1,0,0, 0,0,0,0,0, 0],  # A2: H1+H2+H5 (cross from G2)
    [1,0,0,0,1,0,0, 0,0,1,0,0, 0],  # A#2: H1+H5+H10 (cross)
    [1,0,0,0,1,1,0, 0,0,0,0,0, 0],  # B2: H1+H5+H6
    [1,0,0,0,1,1,1, 0,0,0,0,0, 0],  # C3: H1+H5+H6+H7
    [1,0,0,0,1,1,1, 0,0,1,0,0, 0],  # C#3: H1+H5+H6+H7+H10 (cross)
    [1,1,1,1,1,1,1, 0,0,0,0,0, 0],  # D3: all primary
]
chart_str = [["open" if x else "closed" for x in row] for row in chart]

REG_POS = 80.0
REG_DIA = 2.5
REG_LEN = 3.0

def evaluate(corrective_pos):
    """Evaluate 12 holes: 7 fixed primary + 5 corrective."""
    all_12 = sorted(list(PRIMARY) + list(corrective_pos))
    all_pos = sorted(all_12 + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets]
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
    except Exception:
        return 1000.0
    errs = []
    for t, f in zip(targets, freqs):
        c = 1200 * np.log2(f/t) if f > 0 else 1e10
        errs.append(c)
    err_arr = np.array(errs)
    offset = np.median(err_arr)
    rms = np.sqrt(np.mean((err_arr - offset)**2))
    return rms

# Initial: spread corrective holes between primary holes
initial_corr = [240, 390, 490, 570, 650]
print("=== 7+5 cross-fingering optimization ===")
print("Primary (fixed): %s" % PRIMARY)
print("Corrective (initial): %s" % initial_corr)
print("Initial cost: %.2fc" % evaluate(initial_corr))

t0 = time.time()

# Bounds: corrective holes must be between primary holes, no overlap
bounds_corr = [
    (180, 290),   # H8: between H1(176) and H2(293)
    (340, 440),   # H9: between H3(338) and H4(445)
    (450, 530),   # H10: between H4(445) and H5(532)
    (540, 605),   # H11: between H5(532) and H6(610)
    (615, 635),   # H12: between H6(610) and H7(636)
]

# Phase 1: Differential Evolution (small, 5 variables)
print("\nPhase 1: DE (5 variables)")
de_result = differential_evolution(
    evaluate, bounds_corr,
    seed=42, maxiter=30, popsize=15,
    tol=1e-5, mutation=(0.5, 1.0), recombination=0.7,
    polish=False,
)
print("  DE cost: %.2fc" % de_result.fun)
print("  Corrective: %s" % [round(p) for p in de_result.x])

# Phase 2: L-BFGS-B refinement
print("\nPhase 2: L-BFGS-B refinement")
r = minimize(evaluate, de_result.x, method='L-BFGS-B', bounds=bounds_corr,
             options={'maxiter': 200, 'ftol': 1e-8})
dt = time.time() - t0
print("  Final cost: %.2fc (%.0fs)" % (r.fun, dt))

best_corr = r.x
all_12 = sorted(list(PRIMARY) + list(best_corr))
all_pos = sorted(all_12 + [REG_POS])

print("\nHole positions (reed to bell):")
for i, p in enumerate(all_pos[:-1]):
    label = "primary" if p in PRIMARY else "corrective"
    print("  H%02d: %4.0fmm (%s)" % (i+1, p, label))

# Detailed evaluation
inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
    closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]
freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)

print("\n%-6s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 38)
errs = []
for n, t, f in zip(names, targets, freqs):
    c = 1200 * np.log2(f/t) if f > 0 else 0
    errs.append(c)
    print("  %-6s %8.1f %8.1f %+8.1f" % (n, t, f, c))
err_arr = np.array(errs)
off = np.median(err_arr)
rms = np.sqrt(np.mean((err_arr - off)**2))
print()
print("Offset: %+.1fc  RMS(relative): %.2fc" % (off, rms))
print("Max err: %.1fc  Min err: %.1fc" % (max(abs(err_arr - off)), min(abs(err_arr - off))))
