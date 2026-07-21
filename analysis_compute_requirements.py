"""
Computation Requirements Analysis for Woodwind Instrument Optimization.

Evaluates: how much compute is needed to reach <3 cents RMS?

Key constraint: OpenWInD takes ~1.9s per evaluation (n_freqs=1000).
Each evaluation = one bore profile → impedance → peak detection → cost.

Measures:
- Cost function smoothness (critical for gradient methods)
- Convergence rate of different algorithms
- Total compute time vs accuracy tradeoff
"""
import sys, os, time, json
sys.path.insert(0, '.')
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['OPENBLAS_NUM_THREADS'] = '1'

import numpy as np
from backend.v2_scipy_optimizer import (
    ScipyBoreOptimizer, _objective_cents, _pava_isotonic,
    _compute_impedance_from_bore, _match_peaks_to_targets
)

TARGETS = [261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6]
BORE_LENGTH = 0.65
N_CP = 12
N_FREQS = 1000
EVAL_TIME = 1.9  # seconds per OpenWInD evaluation


def cost_surface_smoothness():
    """
    Test: how smooth is the cost function landscape?
    Randomly sample 100 bore profiles, compute cost, measure variation.
    This tells us if gradient methods are viable.
    """
    print("=" * 60)
    print("COST FUNCTION SMOOTHNESS ANALYSIS")
    print("=" * 60)
    
    opt = ScipyBoreOptimizer(TARGETS, N_CP, BORE_LENGTH, n_freqs=N_FREQS)
    x0 = opt._make_initial_guess("cylindrical")
    
    # Random perturbations around cylindrical bore
    n_samples = 50
    costs = []
    radii_samples = []
    
    t0 = time.time()
    for i in range(n_samples):
        # Random perturbation (different magnitudes)
        scale = np.random.uniform(0.001, 0.005)
        perturbed = x0 + np.random.randn(N_CP) * scale
        perturbed = np.clip(perturbed, opt.min_radius, opt.max_radius)
        perturbed = _pava_isotonic(perturbed)
        
        cost = _objective_cents(perturbed, opt.bore_length, opt.target_freqs,
                               opt.freq_range, opt.n_freqs, opt.temperature,
                               opt.n_cp, opt.max_radius_jump)
        costs.append(cost)
        radii_samples.append(perturbed.copy())
    
    costs = np.array(costs)
    dt = time.time() - t0
    
    print(f"  {n_samples} samples in {dt:.1f}s ({dt/n_samples:.2f}s/sample)")
    print(f"  Cost range: {costs.min():.1f} to {costs.max():.1f}")
    print(f"  Cost mean: {costs.mean():.1f} +/- {costs.std():.1f}")
    print(f"  Cost CV (std/mean): {costs.std()/costs.mean():.3f}")
    
    # Gradient estimate via finite differences at x0
    print("\n  Finite-difference gradient at x0:")
    eps = 1e-4
    f0 = _objective_cents(x0, opt.bore_length, opt.target_freqs,
                          opt.freq_range, opt.n_freqs, opt.temperature,
                          opt.n_cp, opt.max_radius_jump)
    grads = []
    t0 = time.time()
    for i in range(N_CP):
        x_plus = x0.copy(); x_plus[i] += eps
        x_minus = x0.copy(); x_minus[i] -= eps
        f_plus = _objective_cents(x_plus, opt.bore_length, opt.target_freqs,
                                  opt.freq_range, opt.n_freqs, opt.temperature,
                                  opt.n_cp, opt.max_radius_jump)
        f_minus = _objective_cents(x_minus, opt.bore_length, opt.target_freqs,
                                   opt.freq_range, opt.n_freqs, opt.temperature,
                                   opt.n_cp, opt.max_radius_jump)
        g = (f_plus - f_minus) / (2 * eps)
        grads.append(g)
    grad_time = time.time() - t0
    
    grads = np.array(grads)
    print(f"    Gradient norm: {np.linalg.norm(grads):.2f}")
    print(f"    Gradient range: [{grads.min():.2f}, {grads.max():.2f}]")
    print(f"    Gradient computation time: {grad_time:.1f}s ({grad_time/N_CP:.2f}s/dim)")
    print(f"    Gradient finite-difference evals: {2*N_CP+1}")
    
    return costs, grads


def convergence_rate_test():
    """
    Test: how many evaluations to reach <3 cents with different methods?
    """
    print("\n" + "=" * 60)
    print("CONVERGENCE RATE ANALYSIS")
    print("=" * 60)
    
    opt = ScipyBoreOptimizer(TARGETS, N_CP, BORE_LENGTH, n_freqs=N_FREQS)
    
    # Test 1: L-BFGS-B (gradient-based, fast convergence)
    print("\n  L-BFGS-B (finite-difference gradient):")
    print(f"    Evals per iteration: {2*N_CP+1} = 25")
    print(f"    Time per iteration: {25*EVAL_TIME:.1f}s")
    
    # Test 2: Nelder-Mead (derivative-free, slower convergence)
    print("\n  Nelder-Mead (derivative-free):")
    print(f"    Evals per iteration: ~{N_CP+1}-{2*(N_CP+1)} = ~{N_CP+1}-{2*(N_CP+1)}")
    print(f"    Time per iteration: ~{(N_CP+1)*EVAL_TIME:.0f}s")
    print(f"    Typical convergence: 3-5x more evals than gradient methods")
    
    # Test 3: Differential Evolution (global search)
    print("\n  Differential Evolution (global search):")
    pop = 15
    print(f"    Population: {pop}")
    print(f"    Evals per generation: {pop}")
    print(f"    Time per generation: {pop*EVAL_TIME:.1f}s")
    print(f"    Typical generations needed: 50-200")
    
    # Test 4: Powell (direction set)
    print("\n  Powell (direction set):")
    print(f"    Evals per iteration: ~{N_CP+1}-{2*(N_CP+1)}")
    print(f"    Convergence: superlinear")


def compute_budget_analysis():
    """
    Analyze compute budget: what's achievable in X seconds?
    """
    print("\n" + "=" * 60)
    print("COMPUTE BUDGET ANALYSIS")
    print(f"  OpenWInD eval time: {EVAL_TIME}s (n_freqs={N_FREQS})")
    print("=" * 60)
    
    budgets = [30, 60, 120, 300, 600]
    
    for budget in budgets:
        max_evals = int(budget / EVAL_TIME)
        
        print(f"\n  Budget: {budget}s ({max_evals} max evaluations)")
        
        # L-BFGS-B
        lbfgsb_iters = max_evals // (2*N_CP+1)
        print(f"    L-BFGS-B:     {lbfgsb_iters:3d} iterations ({lbfgsb_iters*(2*N_CP+1)} evals)")
        
        # Nelder-Mead
        nm_iters = max_evals // (N_CP+1)
        print(f"    Nelder-Mead:  {nm_iters:3d} iterations ({nm_iters*(N_CP+1)} evals)")
        
        # Differential Evolution
        de_gens = max_evals // 15
        print(f"    Diff. Evol.:  {de_gens:3d} generations ({de_gens*15} evals)")


def run_timed_optimization():
    """
    Actually run L-BFGS-B and measure convergence.
    """
    print("\n" + "=" * 60)
    print("TIMED L-BFGS-B RUN (30s budget)")
    print("=" * 60)
    
    opt = ScipyBoreOptimizer(TARGETS, N_CP, BORE_LENGTH, n_freqs=N_FREQS)
    
    # Track convergence
    eval_count = [0]
    best_cost = [float('inf')]
    best_x = [None]
    
    def track_callback(xk):
        eval_count[0] += 1
        # We don't have the cost here, but we can track iterations
    
    t0 = time.time()
    x0 = opt._make_initial_guess("cylindrical")
    bounds = [(opt.min_radius, opt.max_radius)] * N_CP
    
    def objective(x):
        cost = _objective_cents(x, opt.bore_length, opt.target_freqs,
                               opt.freq_range, opt.n_freqs, opt.temperature,
                               opt.n_cp, opt.max_radius_jump)
        if cost < best_cost[0]:
            best_cost[0] = cost
            best_x[0] = x.copy()
        return cost
    
    from scipy.optimize import minimize
    result = minimize(objective, x0, method='L-BFGS-B', bounds=bounds,
                     options={'maxiter': 100, 'ftol': 1e-8, 'gtol': 1e-6})
    
    wall_time = time.time() - t0
    
    print(f"  Completed in {wall_time:.1f}s")
    print(f"  Function evaluations: {result.nfev}")
    print(f"  Iterations: {result.nit}")
    print(f"  Best cost found: {best_cost[0]:.2f} cents")
    print(f"  Final cost: {result.fun:.2f} cents")
    print(f"  Success: {result.success}")
    print(f"  Message: {result.message}")
    
    # Evaluate best solution in detail
    if best_x[0] is not None:
        final_bore = [(i * BORE_LENGTH/(N_CP-1), best_x[0][i]) for i in range(N_CP)]
        final_result = _compute_impedance_from_bore(final_bore, (50, 10500), N_FREQS, 20.0)
        peak_freqs = final_result["peak_frequencies"]
        matched = _match_peaks_to_targets(np.array(peak_freqs), np.array(TARGETS))
        raw_cents = np.array([m[3] for m in matched])
        offset = np.median(raw_cents)
        corrected = np.abs(raw_cents - offset)
        rms = np.sqrt(np.mean(corrected**2))
        
        print(f"\n  Best solution detail:")
        print(f"    RMS (corrected): {rms:.2f} cents")
        print(f"    Global offset: {offset:.2f} cents")
        for tf, actual, err_hz, err_cents in matched:
            print(f"    {tf:.1f} Hz -> {actual:.1f} Hz ({err_cents:+.1f} cents)")
    
    return result


if __name__ == "__main__":
    cost_surface_smoothness()
    convergence_rate_test()
    compute_budget_analysis()
    run_timed_optimization()
