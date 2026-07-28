"""Best achievable with physical constraints: 8-16mm holes, proper graduation."""
import sys, time
import numpy as np
from scipy.optimize import differential_evolution, minimize
sys.path.insert(0, '.')
from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

targets = [73.416, 77.782, 82.407, 87.307, 92.499, 97.999,
           103.826, 110.000, 116.541, 123.471, 130.813, 138.591, 146.832]
names = ["D2","D#2","E2","F2","F#2","G2","G#2","A2","A#2","B2","C3","C#3","D3"]

chart_raw = []
for i in range(13):
    row = [0]*12 + [0]
    for j in range(i):
        row[j] = 1
    chart_raw.append(row)
chart_str = [["open" if c else "closed" for c in row] for row in chart_raw]

REG_POS = 80.0
BORE_R = 12.5

def eval_obj(x):
    pos = sorted(x[:12])
    d_min, d_max = x[12], x[13]
    bore_len = x[14]
    hole_dias = [d_min + (d_max - d_min) * i / 11 for i in range(12)]
    
    all_pos = sorted(pos + [REG_POS])
    all_dias = hole_dias + [2.5/2]
    all_lens = [5.0]*12 + [3.0]
    
    inst = tmm_instrument_from_radii(
        np.full(10, BORE_R), bore_len, all_pos,
        all_dias, all_lens, 37.0, closed_top=True, cone_step=0.5
    )
    return inst.phase_cost(targets, chart_str, n_register=1)

def eval_freq(x):
    pos = sorted(x[:12])
    d_min, d_max = x[12], x[13]
    bore_len = x[14]
    hole_dias = [d_min + (d_max - d_min) * i / 11 for i in range(12)]
    
    all_pos = sorted(pos + [REG_POS])
    all_dias = hole_dias + [2.5/2]
    all_lens = [5.0]*12 + [3.0]
    
    inst = tmm_instrument_from_radii(
        np.full(10, BORE_R), bore_len, all_pos,
        all_dias, all_lens, 37.0, closed_top=True, cone_step=0.5
    )
    wl = [SPEED_OF_SOUND/t for t in targets]
    try:
        freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)
    except:
        return 1000.0, []
    errs = [1200*np.log2(f/t) if f>0 else 1e10 for t, f in zip(targets, freqs)]
    e = np.array(errs)
    off = np.median(e)
    return np.sqrt(np.mean((e - off)**2)), errs

# x = [12 positions, d_min, d_max, bore_length]
initial = [208, 255, 312, 364, 412, 459, 493, 541, 581, 618, 654, 1005,
           8.0, 16.0, 1211.3]

bounds = [(100, 1180)] * 12 + [(8.0, 16.0)] + [(10.0, 20.0)] + [(1100, 1300)]

print("=== Physical constraints: 8-16mm holes, bore length optimized ===")
print("Initial freq: %.1fc" % eval_freq(initial)[0])

t0 = time.time()
de = differential_evolution(eval_obj, bounds, seed=42,
                             maxiter=60, popsize=15, tol=1e-6)
dt = time.time() - t0
print("DE: phase=%.6f freq=%.1fc (%.0fs)" % (de.fun, eval_freq(de.x)[0], dt))

r = minimize(eval_obj, de.x, method='L-BFGS-B', bounds=bounds,
             options={'maxiter': 200, 'ftol': 1e-10})
dt2 = time.time() - t0
freq, errs = eval_freq(r.x)
print("Final: phase=%.6f freq=%.1fc (%.0fs)" % (r.fun, freq, dt2))

free_pos = sorted(r.x[:12])
d_min, d_max, bore_len = r.x[12], r.x[13], r.x[14]
grad_d = [d_min + (d_max - d_min) * i / 11 for i in range(12)]
print("Holes: %s" % [round(p) for p in free_pos])
print("Diameters: d_min=%.1f d_max=%.1f" % (d_min, d_max))
print("Bore length: %.1fmm" % bore_len)

all_pos = sorted(free_pos + [REG_POS])
all_dias = grad_d + [2.5/2]
inst = tmm_instrument_from_radii(
    np.full(10, BORE_R), bore_len, all_pos,
    all_dias, [5.0]*12 + [3.0], 37.0, closed_top=True, cone_step=0.5
)
wl = [SPEED_OF_SOUND/t for t in targets]
freqs = inst.compute_fingered_frequencies(wl, chart_str, n_register=1)

print("\n%-4s %9s %9s %9s" % ("Note", "Target", "Actual", "Err(c)"))
print("-" * 40)
errs2 = []
for i, (n, t, f) in enumerate(zip(names, targets, freqs)):
    c = 1200*np.log2(f/t) if f>0 else 0
    errs2.append(c)
    print("  %-4s %8.1f %8.1f %+8.1f" % (n, t, f, c))
e = np.array(errs2)
off = np.median(e)
rms = np.sqrt(np.mean((e - off)**2))
print("\nRMS=%.2fc offset=%+.1fc" % (rms, off))
print("Max err (excl D2): %.1fc" % max(abs(e[1:] - off)))
