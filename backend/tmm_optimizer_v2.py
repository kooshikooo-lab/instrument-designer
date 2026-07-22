"""
L-BFGS-B bore optimizer using JAX-differentiable TMM.

Uses JAX autodiff for exact gradients (no finite differences).
JIT-compiled cost functions with vmap-batched fingering searches.

Usage:
    from backend.tmm_optimizer_v2 import TMMBoreOptimizerJAX

    optimizer = TMMBoreOptimizerJAX(
        target_frequencies=[261.6, 784.8, 1308.0],
        fingering_sets=[['closed']*6, ['open', 'closed']*3, ...],
        n_control_points=12,
        bore_length=650.0,
        hole_positions=[60, 100, 150, ...],
        hole_diameters=[7.0, 7.0, 7.0, ...],
        hole_lengths=[3.75, 3.75, 3.75, ...],
        closed_top=False,
    )
    result = optimizer.run(verbose=True)
"""

import time
import math
import numpy as np
import jax
import jax.numpy as jnp
from scipy.optimize import minimize
from typing import List, Optional, Dict

try:
    from .tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND, end_flange_length_correction
    from .tmm_acoustics_jax import build_action_chain_v2, make_rms_cost, MAX_HOLES
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND, end_flange_length_correction
    from tmm_acoustics_jax import build_action_chain_v2, make_rms_cost, MAX_HOLES


def _pava_isotonic(x: np.ndarray) -> np.ndarray:
    n = len(x)
    vals, sizes = [], []
    for v in x:
        vals.append(float(v))
        sizes.append(1)
        while len(vals) > 1 and vals[-2] > vals[-1]:
            merged = (vals[-2] * sizes[-2] + vals[-1] * sizes[-1]) / (sizes[-2] + sizes[-1])
            vals[-2] = merged
            sizes[-2] += sizes[-1]
            vals.pop()
            sizes.pop()
    result = np.empty(n, dtype=float)
    idx = 0
    for v, s in zip(vals, sizes):
        result[idx:idx + s] = v
        idx += s
    return result


class TMMBoreOptimizerJAX:
    """
    JAX-accelerated bore optimizer using TMM phase resonance + L-BFGS-B.

    Key difference from tmm_optimizer.py: uses JAX autodiff instead of
    finite differences for gradient computation.

    Performance (20 control points, 5 fingerings):
      Baseline FD:  63ms per gradient
      JAX grad:     19ms per gradient
    """

    def __init__(
        self,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_control_points: int = 12,
        bore_length: Optional[float] = None,
        min_radius: float = 1.0,
        max_radius: float = 15.0,
        temperature: float = 20.0,
        hole_positions: Optional[List[float]] = None,
        hole_diameters: Optional[List[float]] = None,
        hole_lengths: Optional[List[float]] = None,
        closed_top: bool = False,
        outer_diameter: float = 22.0,
        n_register: int = 1,
    ):
        self.target_freqs = sorted(target_frequencies)
        self.fingering_sets = fingering_sets
        self.n_cp = n_control_points
        self.min_radius = min_radius
        self.max_radius = max_radius
        self.closed_top = closed_top
        self.outer_diameter = outer_diameter
        self.n_register = n_register

        self.speed_of_sound = 331300.0 + 606.0 * temperature

        if bore_length is None:
            fundamental = min(target_frequencies)
            if closed_top:
                self.bore_length = self.speed_of_sound / (4.0 * fundamental)
            else:
                self.bore_length = self.speed_of_sound / (2.0 * fundamental)
        else:
            self.bore_length = bore_length

        self.hole_positions = list(hole_positions or [])
        self.hole_diameters = list(hole_diameters or [])
        self.hole_lengths = list(hole_lengths or [])

        # Compute initial wavelength guesses
        self._target_wavelengths = self._compute_initial_wavelengths()

        # Build JAX cost function (JIT-compiled)
        self._jax_cost_fn = None

    def _compute_initial_wavelengths(self):
        return np.array([self.speed_of_sound / f for f in self.target_freqs])

    def _build_jax_cost(self, bore_positions):
        """Build JIT-compiled cost function for given bore positions."""
        bore_radii_template = [7.25] * len(bore_positions)
        chain = build_action_chain_v2(
            bore_positions, bore_radii_template, self.outer_diameter,
            self.hole_positions, self.hole_diameters, self.hole_lengths,
            self.closed_top,
        )
        target_freqs_jax = jnp.array(self.target_freqs[:len(self.fingering_sets)])
        target_wavelengths_jax = jnp.array(self._target_wavelengths[:len(self.fingering_sets)])
        fingering_sets_float = []
        for fs in self.fingering_sets:
            arr = jnp.zeros(MAX_HOLES)
            for i, h in enumerate(fs):
                if i < MAX_HOLES:
                    arr = arr.at[i].set(1.0 if h == 'open' else 0.0)
            fingering_sets_float.append(arr)

        self._jax_cost_fn = make_rms_cost(
            chain, target_freqs_jax, fingering_sets_float, target_wavelengths_jax,
        )
        return self._jax_cost_fn

    def _make_initial_guess(self, method="cylindrical"):
        if method == "flat":
            return np.full(self.n_cp, (self.min_radius + self.max_radius) / 2.0)
        elif method == "cylindrical":
            return np.full(self.n_cp, 7.25)
        elif method == "random":
            raw = np.random.uniform(self.min_radius, self.max_radius, self.n_cp)
            return _pava_isotonic(raw)
        raise ValueError(f"Unknown: {method}")

    def run(
        self,
        verbose: bool = True,
        maxiter: int = 300,
        initial_guess: str = "cylindrical",
        known_good_radii: Optional[np.ndarray] = None,
    ) -> Dict:
        bore_positions = np.linspace(0, self.bore_length, self.n_cp).tolist()
        cost_fn = self._build_jax_cost(bore_positions)
        grad_fn = jax.grad(cost_fn)

        if known_good_radii is not None:
            x0 = np.array(known_good_radii, dtype=np.float64)
        else:
            x0 = self._make_initial_guess(initial_guess)

        bounds = [(self.min_radius, self.max_radius)] * self.n_cp

        # Convert JAX grad to numpy for scipy
        iteration_count = [0]
        best_val = [float('inf')]
        grad_eval_count = [0]

        if verbose:
            print(f"  JAX TMM Bore Optimizer")
            print(f"  Control points: {self.n_cp}")
            print(f"  Bore length: {self.bore_length:.1f} mm")
            print(f"  Holes: {len(self.hole_positions)}")
            print(f"  Fingerings: {len(self.fingering_sets)}")
            print(f"  Starting optimization...")

        def objective_and_grad(x):
            radii_jax = jnp.array(x, dtype=jnp.float32)
            cost = cost_fn(radii_jax)
            grad = grad_fn(radii_jax)
            grad_eval_count[0] += 1
            return float(cost), np.array(grad, dtype=np.float64)

        def callback(xk):
            iteration_count[0] += 1
            if iteration_count[0] % 10 == 0:
                cost = float(cost_fn(jnp.array(xk, dtype=jnp.float32)))
                if cost < best_val[0]:
                    best_val[0] = cost
                print(f"    iter {iteration_count[0]:4d}: obj={cost:.4f} (best={best_val[0]:.4f})")

        t0 = time.time()

        # Warmup JIT
        if verbose:
            print("  JIT compiling...")
        _ = cost_fn(jnp.array(x0, dtype=jnp.float32)).block_until_ready()
        _ = grad_fn(jnp.array(x0, dtype=jnp.float32)).block_until_ready()
        if verbose:
            print(f"  JIT compiled in {time.time()-t0:.2f}s")

        t_opt = time.time()
        result = minimize(
            lambda x: objective_and_grad(x)[0],
            x0,
            method='L-BFGS-B',
            jac=lambda x: objective_and_grad(x)[1],
            bounds=bounds,
            callback=callback if verbose else None,
            options={"maxiter": maxiter, "ftol": 1e-6, "gtol": 1e-4},
        )

        wall_time = time.time() - t_opt

        final_radii = _pava_isotonic(result.x)
        final_radii = np.maximum(final_radii, self.min_radius)

        # Evaluate final result using baseline for accuracy
        inst = tmm_instrument_from_radii(
            final_radii, self.bore_length,
            self.hole_positions, self.hole_diameters, self.hole_lengths,
            self.outer_diameter, self.closed_top, 0.5,
        )

        matched = []
        all_errors = []
        for i, (fingerings, target_freq) in enumerate(zip(self.fingering_sets, self.target_freqs)):
            try:
                wl = inst.find_resonance(self._target_wavelengths[i], fingerings, self.n_register)
                actual_freq = inst.frequency_from_wavelength(wl)
                cents = 1200.0 * math.log2(actual_freq / target_freq) if actual_freq > 0 else 1e10
                matched.append({"target": target_freq, "actual": actual_freq, "error_cents": cents})
                all_errors.append(cents)
            except Exception:
                matched.append({"target": target_freq, "actual": 0.0, "error_cents": 1e10})
                all_errors.append(1e10)

        all_errors = np.array(all_errors)
        global_offset = float(np.median(all_errors))
        corrected_errors = np.abs(all_errors - global_offset)
        final_rms = float(np.sqrt(np.mean(corrected_errors ** 2)))

        if verbose:
            print(f"\n  Optimization complete:")
            print(f"    RMS cents error: {final_rms:.4f}")
            print(f"    Global offset: {global_offset:.2f} cents")
            print(f"    Wall time: {wall_time:.1f}s")
            print(f"    Gradient evaluations: {grad_eval_count[0]}")
            print(f"\n  Per-note errors (cents):")
            for m in matched:
                print(f"    {m['target']:8.1f} Hz -> {m['actual']:8.1f} Hz  ({m['error_cents']:+.2f})")

        return {
            "success": result.success,
            "message": str(result.message),
            "best_radii": final_radii.tolist(),
            "best_objective": float(result.fun),
            "final_rms_cents": final_rms,
            "global_offset_cents": global_offset,
            "matched_frequencies": matched,
            "iterations": result.nit,
            "gradient_evaluations": grad_eval_count[0],
            "wall_time": wall_time,
            "bore_length_mm": self.bore_length,
        }
