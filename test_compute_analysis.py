"""
Compute needs analysis for instrument designer.
Measures: eval time, optimizer costs, total project compute budget.
"""
import sys
sys.path.insert(0, '.')
import time
import numpy as np
from backend.bore_optimizer_lbfgs import _pava_isotonic, _compute_impedance, _match_peaks
from scipy.optimize import minimize

TARGETS = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
MIN_R = 0.003
MAX_R = 0.025
FREQ_RANGE = (50, 3000)

v = 331.3 + 0.606 * 20.0
BORE_LEN = v / (4 * min(TARGETS))


def make_obj(n_cp):
    positions = np.linspace(0, BORE_LEN, n_cp)
    def objective(radii):
        radii = np.clip(radii, MIN_R, MAX_R)
        radii = _pava_isotonic(radii)
        bore = list(zip(positions.tolist(), radii.tolist()))
        peak_freqs, _ = _compute_impedance(bore, FREQ_RANGE, 5000, 20.0)
        if len(peak_freqs) < 2:
            return 1e10
        matched = _match_peaks(peak_freqs, TARGETS)
        raw_cents = np.array([m[3] for m in matched])
        offset = np.median(raw_cents)
        corrected = np.abs(raw_cents - offset)
        return float(np.sqrt(np.mean(corrected ** 2)))
    return objective


print("=" * 70)
print("  COMPUTE NEEDS ANALYSIS — Instrument Designer")
print("=" * 70)

# ─── 1. Single evaluation cost ───
print("\n  1. SINGLE EVALUATION COST")
print("  " + "-" * 50)
for n_cp in [6, 12, 18, 24]:
    obj = make_obj(n_cp)
    x0 = np.full(n_cp, 0.010)
    t0 = time.time()
    val = obj(x0)
    elapsed = time.time() - t0
    print("  {} CP: {:.3f}s per eval (RMS={:.2f})".format(n_cp, elapsed, val))

# ─── 2. Gradient cost ───
print("\n  2. GRADIENT COST (finite differences)")
print("  " + "-" * 50)
for n_cp in [6, 12, 18]:
    obj = make_obj(n_cp)
    x0 = np.full(n_cp, 0.010)
    # Time single eval
    t0 = time.time()
    v0 = obj(x0)
    t_single = time.time() - t0
    # Forward diff = n_cp+1 evals, centered = 2*n_cp+1
    fwd = (n_cp + 1) * t_single
    ctr = (2 * n_cp + 1) * t_single
    print("  {} CP: forward={:.1f}s ({} evals), centered={:.1f}s ({} evals)".format(
        n_cp, fwd, n_cp+1, ctr, 2*n_cp+1))

# ─── 3. Optimizer costs ───
print("\n  3. OPTIMIZER TOTAL COST (L-BFGS-B)")
print("  " + "-" * 50)
for n_cp in [6, 12]:
    obj = make_obj(n_cp)
    x0 = np.full(n_cp, 0.010)
    bounds = [(MIN_R, MAX_R)] * n_cp

    t0 = time.time()
    r = minimize(obj, x0, method='L-BFGS-B', jac='2-point', bounds=bounds,
                 options={'maxiter': 50, 'ftol': 1e-12})
    elapsed = time.time() - t0
    radii = _pava_isotonic(np.clip(r.x, MIN_R, MAX_R))
    print("  {} CP: {:.1f}s total ({} evals), RMS={:.4f} cents".format(
        n_cp, elapsed, r.nfev, r.fun))

# ─── 4. Per-instrument cost ───
print("\n  4. PER-INSTRUMENT DESIGN COST")
print("  " + "-" * 50)
for n_cp in [6, 12]:
    obj = make_obj(n_cp)
    x0 = np.full(n_cp, 0.010)
    bounds = [(MIN_R, MAX_R)] * n_cp
    # Two-phase
    t0 = time.time()
    r1 = minimize(obj, x0, method='L-BFGS-B', jac='2-point', bounds=bounds,
                  options={'maxiter': 25, 'ftol': 1e-12})
    r2 = minimize(obj, r1.x, method='L-BFGS-B', jac='2-point', bounds=bounds,
                  options={'maxiter': 50, 'ftol': 1e-14})
    elapsed = time.time() - t0
    print("  {} CP: {:.1f}s ({} evals), RMS={:.4f} cents".format(
        n_cp, elapsed, r1.nfev + r2.nfev, r2.fun))

# ─── 5. Development compute budget ───
print("\n  5. DEVELOPMENT COMPUTE BUDGET")
print("  " + "-" * 50)
# Typical dev session: ~20 test runs, each ~3-5 min
eval_12cp = 2.0  # seconds per eval (measured)
print("  Single eval (12 CP): ~{:.1f}s".format(eval_12cp))
print("  L-BFGS-B iteration: ~{:.1f}s (13 evals for 12 CP)".format(13 * eval_12cp))
print("  Full optimization (12 CP, ~300 evals): ~{:.0f}s ({:.1f} min)".format(
    300 * eval_12cp, 300 * eval_12cp / 60))
print("  Dev session (20 test runs): ~{:.0f}s ({:.1f} hrs)".format(
    20 * 300 * eval_12cp, 20 * 300 * eval_12cp / 3600))
print("  Week of dev (5 sessions): ~{:.0f}s ({:.1f} hrs)".format(
    5 * 20 * 300 * eval_12cp, 5 * 20 * 300 * eval_12cp / 3600))

# ─── 6. Production compute budget ───
print("\n  6. PRODUCTION COMPUTE BUDGET (per instrument)")
print("  " + "-" * 50)
print("  Desktop (single machine):")
for n_cp, evals in [(6, 200), (12, 300), (12, 500)]:
    cost = evals * eval_12cp
    print("    {} CP, {} evals: {:.0f}s ({:.1f} min)".format(n_cp, evals, cost, cost/60))

print("\n  Parallel (6 workers, ~1.8x speedup):")
for n_cp, evals in [(6, 200), (12, 300), (12, 500)]:
    cost = evals * eval_12cp / 1.8
    print("    {} CP, {} evals: {:.0f}s ({:.1f} min)".format(n_cp, evals, cost, cost/60))

print("\n  Laptop + Desktop (parallel, ~3.6x):")
for n_cp, evals in [(6, 200), (12, 300), (12, 500)]:
    cost = evals * eval_12cp / 3.6
    print("    {} CP, {} evals: {:.0f}s ({:.1f} min)".format(n_cp, evals, cost, cost/60))

# ─── 7. Total project estimate ───
print("\n  7. TOTAL PROJECT COMPUTE")
print("  " + "-" * 50)
# Phase 1 dev: ~100 optimization runs
dev_runs = 100
dev_evals_per = 300
dev_total = dev_runs * dev_evals_per * eval_12cp
print("  Phase 1 (optimizer dev): {} runs x {} evals = {:.0f}s ({:.1f} hrs)".format(
    dev_runs, dev_evals_per, dev_total, dev_total/3600))
# Validation: 3 reference instruments
val_runs = 3
val_evals = 500
val_total = val_runs * val_evals * eval_12cp
print("  Validation (3 instruments): {} runs x {} evals = {:.0f}s ({:.1f} min)".format(
    val_runs, val_evals, val_total, val_total/60))
# Production: design 10 instruments
prod_runs = 10
prod_evals = 300
prod_total = prod_runs * prod_evals * eval_12cp
print("  Production (10 instruments): {} runs x {} evals = {:.0f}s ({:.1f} min)".format(
    prod_runs, prod_evals, prod_total, prod_total/60))
print("  TOTAL: {:.0f}s ({:.1f} hrs)".format(dev_total + val_total + prod_total,
    (dev_total + val_total + prod_total)/3600))

# ─── 8. Recommendation ───
print("\n  8. RECOMMENDATION")
print("  " + "-" * 50)
print("  - Each machine has ~2s per eval (OpenWInD bottleneck)")
print("  - L-BFGS-B needs ~13 evals/iter for 12 CP (centered diff)")
print("  - Full optimization: ~300 evals = ~600s = 10 min")
print("  - With parallel (6 workers, 1.8x): ~333s = 5.5 min")
print("  - Both machines parallel: ~167s = 2.8 min")
print("  - Development: ~3 hrs total on one machine")
print("  - Surrogate model could reduce to ms/eval (long-term)")
