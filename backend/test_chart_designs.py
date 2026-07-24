"""Try fundamentally different chart designs for 13-note chromatic.

The problem: current charts have too much pattern overlap, causing hole collapse.
New approach: maximize acoustic diversity — each note gets a unique hole pattern.
"""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

REG_POS = 80.0

# Chart A: Bell-first primary + corrective holes for chromatics
# Primary H1-H7: sequential from bell (H7=1st to open)
# Corrective H8-H12: specific cross-fingerings
chart_a_raw = [
    # H1 H2 H3 H4 H5 H6 H7  H8 H9 H10 H11 H12  Reg
    [0, 0, 0, 0, 0, 0, 0,  0, 0, 0,  0,  0,   0],  # D2
    [0, 0, 0, 0, 0, 0, 1,  1, 0, 0,  0,  0,   0],  # D#2: H7+H8 cross
    [0, 0, 0, 0, 0, 1, 1,  0, 0, 0,  0,  0,   0],  # E2: H6+H7
    [0, 0, 0, 0, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # F2: H5+H6+H7
    [0, 0, 0, 1, 0, 1, 1,  0, 1, 0,  0,  0,   0],  # F#2: H4+H6+H7+H9 cross
    [0, 0, 0, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # G2: H4-H7
    [0, 0, 1, 0, 1, 1, 1,  0, 0, 1,  0,  0,   0],  # G#2: H3+H5+H6+H7+H10 cross
    [0, 0, 1, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # A2: H3-H7
    [0, 1, 0, 1, 1, 1, 1,  0, 0, 0,  1,  0,   0],  # A#2: H2+H4-H7+H11 cross
    [0, 1, 1, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # B2: H2-H7
    [1, 0, 1, 1, 1, 1, 1,  0, 0, 0,  0,  1,   0],  # C3: H1+H3-H7+H12 cross
    [1, 1, 1, 1, 1, 1, 1,  0, 1, 0,  0,  1,   0],  # C#3: all primary+H9+H12
    [1, 1, 1, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # D3: all primary
]

# Chart B: Reed-first primary + corrective holes
# Primary H1-H7: sequential from reed (H1=1st to open)
# Corrective H8-H12: specific cross-fingerings
chart_b_raw = [
    [0, 0, 0, 0, 0, 0, 0,  0, 0, 0,  0,  0,   0],  # D2
    [1, 0, 0, 0, 0, 0, 0,  1, 0, 0,  0,  0,   0],  # D#2: H1+H8 cross
    [1, 1, 0, 0, 0, 0, 0,  0, 0, 0,  0,  0,   0],  # E2: H1+H2
    [1, 1, 1, 0, 0, 0, 0,  0, 0, 0,  0,  0,   0],  # F2: H1+H2+H3
    [1, 1, 0, 0, 0, 0, 0,  0, 1, 0,  0,  0,   0],  # F#2: H1+H2+H9 cross
    [1, 1, 1, 1, 0, 0, 0,  0, 0, 0,  0,  0,   0],  # G2: H1-H4
    [1, 1, 1, 0, 0, 0, 0,  0, 0, 1,  0,  0,   0],  # G#2: H1-H3+H10 cross
    [1, 1, 1, 1, 1, 0, 0,  0, 0, 0,  0,  0,   0],  # A2: H1-H5
    [1, 1, 1, 0, 0, 0, 0,  0, 0, 0,  1,  0,   0],  # A#2: H1-H3+H11 cross
    [1, 1, 1, 1, 1, 1, 0,  0, 0, 0,  0,  0,   0],  # B2: H1-H6
    [1, 1, 1, 1, 0, 0, 0,  0, 0, 0,  0,  1,   0],  # C3: H1-H4+H12 cross
    [1, 1, 1, 1, 1, 1, 0,  0, 1, 0,  0,  1,   0],  # C#3: H1-H6+H9+H12 cross
    [1, 1, 1, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # D3: all primary
]

# Chart C: Alternating primary pattern (skip-one pattern)
# This gives more diverse impedance patterns
chart_c_raw = [
    [0, 0, 0, 0, 0, 0, 0,  0, 0, 0,  0,  0,   0],  # D2: all closed
    [0, 0, 0, 0, 0, 0, 1,  1, 0, 0,  0,  0,   0],  # D#2: H7+H8
    [0, 0, 0, 0, 0, 1, 1,  0, 0, 0,  0,  0,   0],  # E2: H6+H7
    [0, 0, 0, 0, 0, 1, 1,  1, 0, 0,  0,  0,   0],  # F2: H6+H7+H8
    [0, 0, 0, 0, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # F#2: H5+H6+H7
    [0, 0, 0, 0, 1, 1, 1,  1, 0, 0,  0,  0,   0],  # G2: H5-H7+H8
    [0, 0, 0, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # G#2: H4-H7
    [0, 0, 0, 1, 1, 1, 1,  1, 0, 0,  0,  0,   0],  # A2: H4-H7+H8
    [0, 0, 1, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # A#2: H3-H7
    [0, 0, 1, 1, 1, 1, 1,  1, 0, 0,  0,  0,   0],  # B2: H3-H7+H8
    [0, 1, 1, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # C3: H2-H7
    [0, 1, 1, 1, 1, 1, 1,  1, 0, 0,  0,  0,   0],  # C#3: H2-H7+H8
    [1, 1, 1, 1, 1, 1, 1,  0, 0, 0,  0,  0,   0],  # D3: all primary
]

REG_DIA = 2.5
REG_LEN = 3.0

def evaluate(x, chart_raw):
    chart_str = [["open" if c else "closed" for c in row] for row in chart_raw]
    free_pos = sorted(x)
    all_pos = sorted(free_pos + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )
    return inst.phase_cost_with_offset(targets, chart_str, n_register=1)

initial = [176, 293, 338, 445, 532, 610, 636, 700, 780, 860, 940, 1020]
bounds = [(100, 1180)] * 12

for name, chart_raw in [("A: bell-primary+corrective", chart_a_raw),
                         ("B: reed-primary+corrective", chart_b_raw),
                         ("C: alternating+H8", chart_c_raw)]:
    t0 = time.time()
    de = differential_evolution(
        lambda x: evaluate(x, chart_raw),
        bounds, seed=42, maxiter=30, popsize=10, tol=1e-6,
    )
    dt = time.time() - t0
    
    # Freq evaluation
    chart_str = [["open" if c else "closed" for c in row] for row in chart_raw]
    free_pos = sorted(de.x)
    all_pos = sorted(free_pos + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets]
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
        errs = [1200*np.log2(f/t) if f>0 else 1e10 for t, f in zip(targets, freqs)]
        e = np.array(errs)
        off = np.median(e)
        rms = np.sqrt(np.mean((e - off)**2))
    except:
        rms = 999
    
    print("%s: phase=%.6f freq=%.1fc (%.0fs) holes=%s" % (
        name, de.fun, rms, dt, [round(p) for p in sorted(de.x)]))
