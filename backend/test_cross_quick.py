"""Quick 12-hole cross-fingering test with ChatGPT chart — L-BFGS-B only."""
import sys, time
import numpy as np
from scipy.optimize import minimize

sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ['D2','D#2','E2','F2','F#2','G2','G#2','A2','A#2','B2','C3','C#3','D3']

chart_binary = [
    [0,0,0,0,0,0,0,0,0,0,0,0,0],
    [0,0,0,0,0,0,1,0,1,0,0,0,0],
    [0,0,0,0,0,0,1,0,0,0,0,0,0],
    [0,0,0,0,0,1,1,0,0,0,0,0,0],
    [0,0,0,0,1,0,1,1,0,0,0,0,0],
    [0,0,0,0,1,1,1,0,0,0,0,0,0],
    [0,0,0,1,0,1,1,1,0,0,0,0,0],
    [0,0,0,1,1,1,1,0,0,0,0,0,0],
    [0,0,1,0,1,1,1,1,0,0,0,0,0],
    [0,0,1,1,1,1,1,0,0,0,0,0,0],
    [0,1,0,1,1,1,1,1,0,0,1,0,0],
    [1,0,1,1,1,1,1,0,1,0,0,1,0],
    [1,1,1,1,1,1,1,0,0,0,0,0,0],
]
chart_str = [['open' if x else 'closed' for x in row] for row in chart_binary]

REG_POS = 80.0
REG_DIA = 2.5
REG_LEN = 3.0

def evaluate(pos_vec):
    free_pos = sorted(pos_vec)
    all_pos = sorted(free_pos + [REG_POS])
    inst = tmm_instrument_from_radii(
        np.full(10, 12.5), 1211.3, all_pos,
        [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
        closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets]
    freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
    errs = []
    for t, f in zip(targets, freqs):
        c = 1200 * np.log2(f/t) if f > 0 else 1e10
        errs.append(c)
    err_arr = np.array(errs)
    offset = np.median(err_arr)
    rms = np.sqrt(np.mean((err_arr - offset)**2))
    return rms

# Initial guess: H1-H7 primary (reed to bell), H8-H12 auxiliary (near bell)
initial = [
    200, 350, 500, 650, 780, 900, 1000,
    850, 950, 1050, 1100, 1150
]

print("=== Quick L-BFGS-B test (12 holes, ChatGPT chart) ===")
print("Initial cost: %.2fc" % evaluate(initial))

t0 = time.time()
bounds = [(100, 1180)] * 12
for i in range(11):
    bounds[i] = (max(100, initial[i]-100), min(1180, initial[i]+100))

r = minimize(evaluate, initial, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 150, 'ftol': 1e-6})
dt = time.time() - t0

print("Optimized cost: %.2fc (%.0fs)" % (r.fun, dt))
print("Holes: %s" % [round(p) for p in sorted(r.x)])

# Detailed eval
free_pos = sorted(r.x)
all_pos = sorted(free_pos + [REG_POS])
inst = tmm_instrument_from_radii(
    np.full(10, 12.5), 1211.3, all_pos,
    [11.0/2]*12 + [REG_DIA/2], [5.0]*12 + [REG_LEN], 37.0,
    closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]
freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)

print()
print("%-6s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
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
