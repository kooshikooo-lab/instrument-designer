"""Test: does phase_cost agree with freq_cost? If not, resonance search is the problem."""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

# Chart 1: Bell-first sequential (12 holes)
chart_bell = []
for i in range(13):
    row = ["closed"] * (12 - i) + ["open"] * i + ["closed"]
    chart_bell.append(row)

# Chart 2: Cross-fingered (reed-first)
chart_cross = [
    [0,0,0,0,0,0,0,0,0,0,0,0, 0],
    [1,0,0,0,0,0,0,0,0,0,0,0, 0],
    [1,1,0,0,0,0,0,0,0,0,0,0, 0],
    [1,1,1,0,0,0,0,0,0,0,0,0, 0],
    [1,1,1,1,0,0,0,0,0,0,0,0, 0],
    [1,1,1,0,1,0,0,0,0,0,0,0, 0],
    [1,1,1,1,1,0,0,0,0,0,0,0, 0],
    [1,1,0,0,1,0,0,0,0,0,0,0, 0],
    [1,0,0,0,1,0,0,1,0,0,0,0, 0],
    [1,0,0,0,1,1,0,0,0,0,0,0, 0],
    [1,0,0,0,1,1,1,0,0,0,0,0, 0],
    [1,0,0,0,1,1,1,1,0,0,0,0, 0],
    [1,1,1,1,1,1,1,1,0,0,0,0, 0],
]

REG_POS = 80.0

for chart_name, chart_raw in [("Bell-first", chart_bell), ("Cross-fingered", chart_cross)]:
    chart_str = [["open" if x else "closed" for x in row] for row in chart_raw]
    
    def eval_phase(x):
        free_pos = sorted(x)
        all_pos = sorted(free_pos + [REG_POS])
        inst = tmm_instrument_from_radii(
            np.full(10, 12.5), 1211.3, all_pos,
            [11.0/2]*12 + [2.5/2], [5.0]*12 + [3.0], 37.0,
            closed_top=True, cone_step=0.5
        )
        return inst.phase_cost_with_offset(targets, chart_str, n_register=1)
    
    def eval_freq(x):
        free_pos = sorted(x)
        all_pos = sorted(free_pos + [REG_POS])
        inst = tmm_instrument_from_radii(
            np.full(10, 12.5), 1211.3, all_pos,
            [11.0/2]*12 + [2.5/2], [5.0]*12 + [3.0], 37.0,
            closed_top=True, cone_step=0.5
        )
        wl = [SPEED_OF_SOUND/t for t in targets]
        try:
            freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
        except:
            return 1000.0
        errs = [1200*np.log2(f/t) if f>0 else 1e10 for t, f in zip(targets, freqs)]
        e = np.array(errs)
        off = np.median(e)
        return np.sqrt(np.mean((e - off)**2))
    
    initial = [176, 293, 338, 445, 532, 610, 636, 700, 780, 860, 940, 1020]
    bounds = [(100, 1180)] * 12
    
    print("=" * 50)
    print("CHART: %s" % chart_name)
    print("=" * 50)
    
    # Optimize with phase cost
    t0 = time.time()
    de = differential_evolution(eval_phase, bounds, seed=42,
                                 maxiter=30, popsize=10, tol=1e-6)
    dt = time.time() - t0
    
    print("Phase cost: %.6f (%.0fs)" % (de.fun, dt))
    print("Freq cost: %.2fc" % eval_freq(de.x))
    print("Holes: %s" % [round(p) for p in sorted(de.x)])
    
    # Also evaluate with freq at initial
    print("Initial freq cost: %.2fc" % eval_freq(initial))
    print()
