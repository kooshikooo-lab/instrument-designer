"""
Critical insight: NSGA-II got 3.11 cents with 150 evals (random init).
What if we start from a GOOD initial guess?

Test: known-good bore (Buffet R13-like) + L-BFGS-B
"""
import sys, os, time
sys.path.insert(0, '.')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
from backend.v2_scipy_optimizer import (
    ScipyBoreOptimizer, _objective_cents, _pava_isotonic,
    _compute_impedance_from_bore, _match_peaks_to_targets
)
from scipy.optimize import minimize

TARGETS = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
BORE_LENGTH = 0.65
N_CP = 12
N_FREQS = 1000

# Buffet R13 bore profile (from research):
# Entry: 14.8mm, Throat: ~14.3mm, Exit: 15mm
# Cylindrical with slight variations
R13_RADII = np.array([
    0.00740,  # 0mm (barrel entry)
    0.00735,  # 59mm
    0.00730,  # 118mm
    0.00725,  # 177mm (narrowing toward throat)
    0.00715,  # 236mm (throat, narrowest ~14.3mm)
    0.00720,  # 295mm (after throat)
    0.00725,  # 354mm
    0.00730,  # 413mm
    0.00735,  # 472mm
    0.00740,  # 531mm
    0.00745,  # 590mm
    0.00750,  # 650mm (bell entry)
])

def evaluate_and_report(x, label, bore_length=BORE_LENGTH):
    """Evaluate a bore and report detailed results."""
    radii = _pava_isotonic(x)
    bore = [(i * bore_length/(N_CP-1), radii[i]) for i in range(N_CP)]
    
    result = _compute_impedance_from_bore(bore, (50, 10500), N_FREQS, 20.0)
    peak_freqs = result["peak_frequencies"]
    if isinstance(peak_freqs, np.ndarray):
        peak_freqs = peak_freqs.tolist()
    
    matched = _match_peaks_to_targets(np.array(peak_freqs), np.array(TARGETS))
    raw_cents = np.array([m[3] for m in matched])
    offset = np.median(raw_cents)
    corrected = np.abs(raw_cents - offset)
    rms = np.sqrt(np.mean(corrected**2))
    
    print(f"\n  [{label}]")
    print(f"    RMS (corrected): {rms:.2f} cents")
    print(f"    Global offset: {offset:.2f} cents")
    for tf, actual, err_hz, err_cents in matched:
        print(f"    {tf:.1f} -> {actual:.1f} Hz ({err_cents:+.1f} cents)")
    
    return rms, offset, radii


print("=" * 60)
print("INITIALIZATION vs ACCURACY ANALYSIS")
print("=" * 60)

# 1. Baseline: cylindrical bore
print("\n--- Cylindrical bore (uniform 7.4mm) ---")
x_cyl = np.full(N_CP, 0.0074)
rms_cyl, _, _ = evaluate_and_report(x_cyl, "Cylindrical")

# 2. Buffet R13 bore
print("\n--- Buffet R13 bore ---")
rms_r13, _, _ = evaluate_and_report(R13_RADII, "Buffet R13")

# 3. L-BFGS-B from cylindrical
print("\n--- L-BFGS-B from cylindrical ---")
opt = ScipyBoreOptimizer(TARGETS, N_CP, BORE_LENGTH, n_freqs=N_FREQS)
x0 = opt._make_initial_guess("cylindrical")
bounds = [(opt.min_radius, opt.max_radius)] * N_CP

def objective(x):
    return _objective_cents(x, BORE_LENGTH, np.array(TARGETS),
                           (50, 10500), N_FREQS, 20.0, N_CP,
                           (0.025-0.003)*0.3)

t0 = time.time()
result = minimize(objective, x0, method='L-BFGS-B', bounds=bounds,
                 options={'maxiter': 20})
print(f"  Time: {time.time()-t0:.1f}s")
rms_lbfgsb, _, _ = evaluate_and_report(result.x, "L-BFGS-B (from cylindrical)")

# 4. L-BFGS-B from R13
print("\n--- L-BFGS-B from Buffet R13 ---")
t0 = time.time()
result_r13 = minimize(objective, R13_RADII, method='L-BFGS-B', bounds=bounds,
                      options={'maxiter': 20})
print(f"  Time: {time.time()-t0:.1f}s")
rms_r13_opt, _, _ = evaluate_and_report(result_r13.x, "L-BFGS-B (from R13)")

# 5. Nelder-Mead from R13
print("\n--- Nelder-Mead from Buffet R13 ---")
t0 = time.time()
result_nm = minimize(objective, R13_RADII, method='Nelder-Mead',
                     options={'maxiter': 100, 'xatol': 1e-6, 'fatol': 1e-6})
print(f"  Time: {time.time()-t0:.1f}s")
rms_nm, _, _ = evaluate_and_report(result_nm.x, "Nelder-Mead (from R13)")

# 6. NSGA-II baseline (from existing results)
print("\n--- NSGA-II baseline (from existing results) ---")
print("  pop=15, gen=10, serial: 3.11 cents RMS (250s)")

print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"  Cylindrical bore:          {rms_cyl:.1f} cents")
print(f"  Buffet R13 bore:           {rms_r13:.1f} cents")
print(f"  L-BFGS-B from cylindrical: {rms_lbfgsb:.1f} cents")
print(f"  L-BFGS-B from R13:         {rms_r13_opt:.1f} cents")
print(f"  Nelder-Mead from R13:      {rms_nm:.1f} cents")
print(f"  NSGA-II (pop=15,gen=10):   3.11 cents (250s)")
