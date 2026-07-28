"""Compare CMA-ES, DE, and L-BFGS-B for bore optimization."""
import sys
sys.path.insert(0, '.')
import time
import numpy as np
from backend.bore_optimizer_lbfgs import LBFGSBoreOptimizer, _pava_isotonic, _compute_impedance, _match_peaks


TARGETS = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
N_CP = 12
MIN_R = 0.003
MAX_R = 0.025
FREQ_RANGE = (50, 3000)


def make_evaluator(bore_len=None, n_cp=N_CP):
    """Return a function: radii -> RMS cents."""
    if bore_len is None:
        v = 331.3 + 0.606 * 20.0
        bore_len = v / (4 * min(TARGETS))
    positions = np.linspace(0, bore_len, n_cp)

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


def test_cma_es():
    import cma

    obj = make_evaluator()
    x0 = [0.010] * N_CP  # uniform bore
    sigma0 = 0.003  # step size ~3mm

    print("=" * 60)
    print("  CMA-ES")
    print("=" * 60)

    t0 = time.time()
    options = {
        'bounds': [MIN_R, MAX_R],
        'verbose': -9,
        'maxfevals': 1500,
        'tolfun': 1e-10,
        'tolx': 1e-10,
        'popsize': 16,
    }

    res = cma.fmin2(obj, x0, sigma0, options)
    x_best = np.array(res[0])
    f_best = res[1].fbest
    n_evals = res[1].countevals
    elapsed = time.time() - t0

    radii = _pava_isotonic(np.clip(x_best, MIN_R, MAX_R))
    print("  CMA-ES: {:.4f} cents, {} evals, {:.1f}s".format(f_best, n_evals, elapsed))
    print("  Bore: entry={:.2f}mm, exit={:.2f}mm".format(radii[0]*1000, radii[-1]*1000))
    return f_best, elapsed, radii


def test_de():
    from scipy.optimize import differential_evolution

    obj = make_evaluator()
    bounds = [(MIN_R, MAX_R)] * N_CP

    print("=" * 60)
    print("  Differential Evolution + L-BFGS-B polish")
    print("=" * 60)

    t0 = time.time()
    result = differential_evolution(
        obj, bounds,
        strategy='best1bin',
        maxiter=100,
        popsize=15,
        tol=1e-10,
        seed=42,
        polish=True,
    )
    elapsed = time.time() - t0
    radii = _pava_isotonic(np.clip(result.x, MIN_R, MAX_R))
    print(f"  DE: {result.fun:.4f} cents, {result.nfev} evals, {elapsed:.1f}s")
    print(f"  Bore: entry={radii[0]*1000:.2f}mm, exit={radii[-1]*1000:.2f}mm")
    return result.fun, elapsed, radii


def test_lbfgs_with_known_init():
    """L-BFGS-B starting from known clarinet dimensions."""
    obj = make_evaluator()
    bounds = [(MIN_R, MAX_R)] * N_CP

    # Starting from uniform 10mm (close to clarinet)
    x0_clarinet = np.full(N_CP, 0.010)

    print("=" * 60)
    print("  L-BFGS-B (uniform 10mm init)")
    print("=" * 60)

    t0 = time.time()
    from scipy.optimize import minimize
    result = minimize(obj, x0_clarinet, method='L-BFGS-B', jac='2-point',
                      bounds=bounds, options={'maxiter': 200, 'ftol': 1e-12})
    elapsed = time.time() - t0
    radii = _pava_isotonic(np.clip(result.x, MIN_R, MAX_R))
    print("  L-BFGS-B: {:.4f} cents, {} evals, {:.1f}s".format(result.fun, result.nfev, elapsed))
    print("  Bore: entry={:.2f}mm, exit={:.2f}mm".format(radii[0]*1000, radii[-1]*1000))
    return result.fun, elapsed, radii


def test_de_then_lbfgs():
    """DE for global search, then L-BFGS-B to polish the best."""
    obj = make_evaluator()
    bounds = [(MIN_R, MAX_R)] * N_CP

    print("=" * 60)
    print("  DE (global) -> L-BFGS-B (polish)")
    print("=" * 60)

    t0 = time.time()
    # DE without polish
    result_de = differential_evolution(
        obj, bounds,
        strategy='best1bin',
        maxiter=80,
        popsize=15,
        tol=1e-8,
        seed=42,
        polish=False,
    )
    t_de = time.time() - t0
    print(f"  DE phase: {result_de.fun:.4f} cents, {result_de.nfev} evals, {t_de:.1f}s")

    # L-BFGS-B polish from DE best
    t1 = time.time()
    result_lb = minimize(
        obj, result_de.x, method='L-BFGS-B', jac='2-point',
        bounds=bounds, options={'maxiter': 200, 'ftol': 1e-12},
    )
    t_lb = time.time() - t1
    elapsed = t_de + t_lb

    radii = _pava_isotonic(np.clip(result_lb.x, MIN_R, MAX_R))
    print(f"  L-BFGS-B polish: {result_lb.fun:.4f} cents, {result_lb.nfev} evals, {t_lb:.1f}s")
    print(f"  Total: {result_lb.fun:.4f} cents, {result_de.nfev + result_lb.nfev} evals, {elapsed:.1f}s")
    print(f"  Bore: entry={radii[0]*1000:.2f}mm, exit={radii[-1]*1000:.2f}mm")
    return result_lb.fun, elapsed, radii


if __name__ == "__main__":
    results = {}

    for name, test_fn in [
        ("CMA-ES", test_cma_es),
        ("DE+polish", test_de),
        ("L-BFGS-B (clarinet init)", test_lbfgs_with_known_init),
        ("DE->L-BFGS-B", test_de_then_lbfgs),
    ]:
        print()
        try:
            rms, time_s, radii = test_fn()
            results[name] = (rms, time_s)
        except Exception as e:
            print(f"  FAILED: {e}")
            results[name] = (None, None)

    print()
    print("=" * 60)
    print("  COMPARISON SUMMARY")
    print("=" * 60)
    print(f"  {'Method':<30} {'RMS (cents)':>12} {'Time (s)':>10}")
    print(f"  {'-'*30} {'-'*12} {'-'*10}")
    for name, (rms, t) in sorted(results.items(), key=lambda x: x[1][0] if x[1][0] else 999):
        if rms is not None:
            print(f"  {name:<30} {rms:>12.4f} {t:>10.1f}")
        else:
            print(f"  {name:<30} {'FAILED':>12}")
