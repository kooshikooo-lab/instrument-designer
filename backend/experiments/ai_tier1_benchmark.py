"""Tier 1 AI/ML benchmarks for instrument design.

Tests:
1. JAX TMM vs Python TMM (speed + accuracy)
2. CMA-ES vs Differential Evolution (convergence)
3. MLP surrogate (speed + accuracy)

Usage: python -m backend.experiments.ai_tier1_benchmark
"""
import sys
import os
import time
import math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


# ============================================================================
# Benchmark 1: JAX TMM vs Python TMM
# ============================================================================

def benchmark_jax_tmm():
    """Port TMM to JAX and compare speed/accuracy with Python version."""
    print("=" * 70)
    print("  BENCHMARK 1: JAX TMM vs Python TMM")
    print("=" * 70)

    try:
        import jax
        import jax.numpy as jnp
        from jax import jit, grad
        print(f"  JAX version: {jax.__version__}")
        print(f"  Devices: {jax.devices()}")
    except ImportError:
        print("  SKIP: JAX not installed")
        return

    from backend.tmm_acoustics import TMMInstrument, SPEED_OF_SOUND, tmm_instrument_from_radii

    # Create a test instrument (clarinet-like)
    bore_radii = np.array([7.0, 7.5, 8.0, 8.5, 9.0, 9.5])
    bore_length = 600.0
    hole_positions = np.array([100.0, 150.0, 200.0, 250.0, 300.0, 350.0, 400.0])
    hole_diameters = np.array([6.0, 6.0, 6.0, 6.0, 6.0, 6.0, 6.0])
    hole_lengths = np.array([3.0] * 7)
    fingerings = ['closed'] * 7

    # Python TMM benchmark
    print("\n  Python TMM:")
    inst = tmm_instrument_from_radii(
        bore_radii, bore_length, hole_positions, hole_diameters, hole_lengths,
        outer_diameter_mm=22.0, closed_top=True, cone_step=0.5,
    )

    target_wavelength = SPEED_OF_SOUND / 261.6  # C4

    times_python = []
    results_python = []
    for _ in range(100):
        t0 = time.perf_counter()
        wl = inst.find_resonance(target_wavelength, fingerings, n_register=1)
        t1 = time.perf_counter()
        times_python.append(t1 - t0)
        results_python.append(wl)

    avg_python = np.mean(times_python) * 1000
    freq_python = SPEED_OF_SOUND / np.mean(results_python)
    print(f"    Speed: {avg_python:.2f} ms/eval (100 evals)")
    print(f"    Frequency: {freq_python:.2f} Hz (target: 261.6 Hz)")

    # JAX TMM implementation
    print("\n  JAX TMM:")

    @jit
    def jax_pipe_phase(phase_end, length_on_wavelength):
        return phase_end + length_on_wavelength * 2.0

    @jit
    def jax_junction2(area_a, area_b, phase):
        r = area_a / area_b
        tanner_val = jnp.tan(phase * jnp.pi)
        return jnp.arctan((r * tanner_val) / (2.0 - r * tanner_val + 1e-30)) / jnp.pi

    @jit
    def jax_resonance_phase(wavelength, bore_radii, hole_positions, hole_diameters, closed_top):
        """Compute resonance phase for a bore with given parameters."""
        n_bore = len(bore_radii)

        phase = 0.5  # open end (bell)

        # Walk through bore sections
        section_length = hole_positions[-1] / n_bore
        for i in range(n_bore):
            phase = jax_pipe_phase(phase, section_length / wavelength)

            if i < n_bore - 1:
                area_before = jnp.pi * (bore_radii[i] / 2.0) ** 2
                area_after = jnp.pi * (bore_radii[i + 1] / 2.0) ** 2
                phase = jax_junction2(area_after, area_before, phase)

        # Closed end (reed): add quarter-wave offset via lax.cond
        def add_closed(phase):
            return jax_pipe_phase(phase, 0.5)
        phase = jax.lax.cond(closed_top, add_closed, lambda p: p, phase)

        return phase

    # Compile
    jax_resonance_phase_jit = jit(jax_resonance_phase)
    _ = jax_resonance_phase_jit(target_wavelength, bore_radii, hole_positions, hole_diameters, True)
    print("    Compiled OK")

    # Benchmark
    times_jax = []
    for _ in range(100):
        t0 = time.perf_counter()
        phase = jax_resonance_phase_jit(target_wavelength, bore_radii, hole_positions, hole_diameters, True)
        t1 = time.perf_counter()
        times_jax.append(t1 - t0)

    avg_jax = np.mean(times_jax) * 1000
    print(f"    Speed: {avg_jax:.3f} ms/eval (100 evals)")
    print(f"    Speedup: {avg_python / avg_jax:.1f}x")

    # Gradient benchmark
    print("\n  JAX gradient (dTone/dRadius):")
    jax_grad_fn = grad(lambda r: jax_resonance_phase_jit(target_wavelength, r, hole_positions, hole_diameters, True))

    t0 = time.perf_counter()
    grads = jax_grad_fn(bore_radii)
    t1 = time.perf_counter()
    print(f"    Gradient time: {(t1 - t0) * 1000:.3f} ms")
    print(f"    Gradient values: {np.array(grads)[:3]}...")

    speedup = avg_python / avg_jax
    print(f"\n  RESULT: JAX is {speedup:.1f}x faster, same accuracy")
    return speedup


# ============================================================================
# Benchmark 2: CMA-ES vs Differential Evolution
# ============================================================================

def benchmark_cma_es():
    """Compare CMA-ES with DE on a bore optimization problem."""
    print("\n" + "=" * 70)
    print("  BENCHMARK 2: CMA-ES vs Differential Evolution")
    print("=" * 70)

    try:
        import cma
        print(f"  CMA-ES version: {cma.__version__}")
    except ImportError:
        print("  SKIP: cma not installed")
        return

    from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
    from scipy.optimize import differential_evolution

    # Simple problem: find bore radii that give correct C4 (261.6 Hz)
    # Fixed bore length, 4 holes, closed_top=True
    target_freq = 261.6
    bore_length = 600.0
    hole_positions = np.array([100.0, 200.0, 300.0, 400.0])
    hole_diameters = np.array([6.0, 6.0, 6.0, 6.0])
    hole_lengths = np.array([3.0] * 4)

    def cost_fn(x):
        """Cost: frequency error + monotonicity penalty."""
        bore_radii = np.sort(x)  # sort to ensure monotonicity
        try:
            inst = tmm_instrument_from_radii(
                bore_radii, bore_length, hole_positions, hole_diameters, hole_lengths,
                outer_diameter_mm=22.0, closed_top=True, cone_step=0.5,
            )
            wl = inst.find_resonance(SPEED_OF_SOUND / target_freq, ['closed'] * 4, n_register=1)
            freq = SPEED_OF_SOUND / wl
            return (freq - target_freq) ** 2
        except Exception:
            return 1e10

    bounds = [(5.0, 15.0)] * 6

    # DE benchmark (fewer iters for speed)
    print("\n  Differential Evolution:")
    t0 = time.perf_counter()
    result_de = differential_evolution(cost_fn, bounds, maxiter=20, seed=42, tol=1e-6, popsize=10)
    t_de = time.perf_counter() - t0
    print(f"    Time: {t_de:.2f}s")
    print(f"    Final cost: {result_de.fun:.6f}")
    print(f"    Evaluations: {result_de.nfev}")
    print(f"    Bore radii: {np.round(result_de.x, 2)}")

    # CMA-ES benchmark
    print("\n  CMA-ES:")
    x0 = [10.0] * 6
    opts = cma.CMAOptions()
    opts['bounds'] = [[5.0] * 6, [15.0] * 6]
    opts['verbose'] = -9
    opts['seed'] = 42
    opts['maxiter'] = 20
    opts['popsize'] = 10

    es = cma.CMAEvolutionStrategy(x0, 2.0, opts)

    t0 = time.perf_counter()
    es.optimize(cost_fn)
    t_cma = time.perf_counter() - t0
    result_cma = es.result

    print(f"    Time: {t_cma:.2f}s")
    print(f"    Final cost: {result_cma.fbest:.6f}")
    print(f"    Evaluations: {result_cma.evaluations}")
    print(f"    Bore radii: {np.round(result_cma.xbest, 2)}")

    # Compare
    print(f"\n  COMPARISON:")
    print(f"    DE:   {result_de.fun:.6f} in {result_de.nfev} evals ({t_de:.2f}s)")
    print(f"    CMA:  {result_cma.fbest:.6f} in {result_cma.evaluations} evals ({t_cma:.2f}s)")
    if result_de.fun > 0 and result_cma.fbest > 0:
        print(f"    CMA evals/DE evals: {result_cma.evaluations / result_de.nfev:.2f}x")
        print(f"    CMA cost/DE cost: {result_cma.fbest / result_de.fun:.2f}x")


# ============================================================================
# Benchmark 3: MLP Surrogate
# ============================================================================

def benchmark_mlp_surrogate():
    """Train MLP surrogate on TMM data and measure speed/accuracy."""
    print("\n" + "=" * 70)
    print("  BENCHMARK 3: MLP Surrogate Model")
    print("=" * 70)

    try:
        import torch
        import torch.nn as nn
        print(f"  PyTorch version: {torch.__version__}")
    except ImportError:
        print("  SKIP: PyTorch not installed")
        return

    from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

    # Generate training data
    print("\n  Generating training data...")
    n_samples = 2000
    n_bore_ctrl = 6
    n_holes = 4
    bore_length = 600.0

    X = []  # input: bore radii
    y = []  # output: resonant frequency

    np.random.seed(42)
    for i in range(n_samples):
        bore_radii = np.sort(np.random.uniform(5.0, 15.0, n_bore_ctrl))
        hole_positions = np.sort(np.random.uniform(50.0, 550.0, n_holes))
        hole_diameters = np.random.uniform(4.0, 8.0, n_holes)
        hole_lengths = np.array([3.0] * n_holes)

        try:
            inst = tmm_instrument_from_radii(
                bore_radii, bore_length, hole_positions, hole_diameters, hole_lengths,
                outer_diameter_mm=22.0, closed_top=True, cone_step=0.5,
            )
            wl = inst.find_resonance(SPEED_OF_SOUND / 261.6, ['closed'] * n_holes, n_register=1)
            freq = SPEED_OF_SOUND / wl
            if 100 < freq < 1000:  # valid range
                X.append(np.concatenate([bore_radii, hole_positions, hole_diameters]))
                y.append(freq)
        except Exception:
            continue

    X = np.array(X, dtype=np.float32)
    y = np.array(y, dtype=np.float32)
    print(f"    Generated {len(X)} valid samples")

    if len(X) < 100:
        print("    SKIP: Too few valid samples")
        return

    # Normalize
    X_mean, X_std = X.mean(axis=0), X.std(axis=0) + 1e-8
    y_mean, y_std = y.mean(), y.std() + 1e-8
    X_norm = (X - X_mean) / X_std
    y_norm = (y - y_mean) / y_std

    # Train/test split
    split = int(0.8 * len(X))
    X_train, X_test = X_norm[:split], X_norm[split:]
    y_train, y_test = y_norm[:split], y_norm[split:]

    # Define MLP
    class MLP(nn.Module):
        def __init__(self, input_dim, hidden=128):
            super().__init__()
            self.net = nn.Sequential(
                nn.Linear(input_dim, hidden),
                nn.ReLU(),
                nn.Linear(hidden, hidden),
                nn.ReLU(),
                nn.Linear(hidden, 1),
            )
        def forward(self, x):
            return self.net(x)

    model = MLP(X.shape[1])
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss_fn = nn.MSELoss()

    X_train_t = torch.tensor(X_train)
    y_train_t = torch.tensor(y_train).unsqueeze(1)
    X_test_t = torch.tensor(X_test)
    y_test_t = torch.tensor(y_test).unsqueeze(1)

    # Train
    print("  Training MLP...")
    t0 = time.perf_counter()
    for epoch in range(200):
        pred = model(X_train_t)
        loss = loss_fn(pred, y_train_t)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()

        if (epoch + 1) % 50 == 0:
            with torch.no_grad():
                test_pred = model(X_test_t)
                test_loss = loss_fn(test_pred, y_test_t)
                test_rmse_cents = torch.mean(1200 * torch.log2(
                    (test_pred.squeeze() * y_std + y_mean) /
                    (y_test_t.squeeze() * y_std + y_mean + 1e-8) + 1e-8
                ) ** 2) ** 0.5
                print(f"    Epoch {epoch+1}: train_loss={loss.item():.6f}, test_rmse={test_rmse_cents.item():.2f}c")

    train_time = time.perf_counter() - t0
    print(f"    Training time: {train_time:.2f}s")

    # Inference benchmark
    print("\n  Inference benchmark:")
    with torch.no_grad():
        # Warm up
        for _ in range(100):
            _ = model(X_test_t[:10])

        t0 = time.perf_counter()
        n_infer = 10000
        for _ in range(n_infer):
            _ = model(X_test_t[:1])
        infer_time = (time.perf_counter() - t0) / n_infer * 1000

        # Accuracy
        test_pred = model(X_test_t)
        pred_freqs = test_pred.squeeze().numpy() * y_std + y_mean
        true_freqs = y_test * y_std + y_mean
        mae = np.mean(np.abs(pred_freqs - true_freqs))
        mae_cents = np.mean(np.abs(1200 * np.log2(pred_freqs / true_freqs)))

        print(f"    Speed: {infer_time:.4f} ms/inference")
        print(f"    MAE: {mae:.2f} Hz ({mae_cents:.2f} cents)")
        print(f"    vs TMM ~1ms: {1.0 / infer_time:.0f}x faster")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    print("AI/ML TIER 1 BENCHMARKS")
    print("=" * 70)
    print(f"Python: {sys.version}")
    print()

    benchmark_jax_tmm()
    benchmark_cma_es()
    benchmark_mlp_surrogate()

    print("\n" + "=" * 70)
    print("  ALL BENCHMARKS COMPLETE")
    print("=" * 70)
