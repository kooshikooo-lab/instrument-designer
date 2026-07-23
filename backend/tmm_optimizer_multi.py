"""
Multi-start bore optimizer for better global convergence.

Runs the Powell+L-BFGS-B optimizer from multiple initial guesses
and returns the best result. Avoids local minima by exploring
different starting points.

Usage:
    from backend.tmm_optimizer_multi import MultiStartOptimizer
    optimizer = MultiStartOptimizer(...)
    result = optimizer.run(verbose=True)
"""

import time
import math
import numpy as np
from typing import List, Optional, Dict

try:
    from .tmm_optimizer_v2 import TMMBoreOptimizerJAX, _pava_isotonic
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from tmm_optimizer_v2 import TMMBoreOptimizerJAX, _pava_isotonic


class MultiStartOptimizer:
    """
    Multi-start bore optimizer.

    Runs Powell+L-BFGS-B from N different initial guesses and returns
    the best result. Initial guesses include:
    1. Cylindrical (uniform radius)
    2. Linear taper (small to large)
    3. Reverse taper (large to small)
    4. Random monotonic profiles
    5. Known-good bore (if provided)
    """

    def __init__(
        self,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_control_points: int = 20,
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
        n_starts: int = 5,
        maxiter_per_start: int = 200,
    ):
        self.n_starts = n_starts
        self.maxiter_per_start = maxiter_per_start

        self.optimizer = TMMBoreOptimizerJAX(
            target_frequencies=target_frequencies,
            fingering_sets=fingering_sets,
            n_control_points=n_control_points,
            bore_length=bore_length,
            min_radius=min_radius,
            max_radius=max_radius,
            temperature=temperature,
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=hole_lengths,
            closed_top=closed_top,
            outer_diameter=outer_diameter,
            n_register=n_register,
        )
        self.n_cp = n_control_points
        self.min_radius = min_radius
        self.max_radius = max_radius

    def _generate_initial_guesses(self, known_good_radii=None):
        """Generate diverse initial guesses for multi-start."""
        guesses = []

        # 1. Cylindrical (uniform)
        guesses.append(np.full(self.n_cp, (self.min_radius + self.max_radius) / 2.0))

        # 2. Linear taper (small -> large)
        guesses.append(np.linspace(self.min_radius + 1, self.max_radius - 1, self.n_cp))

        # 3. Reverse taper (large -> small)
        guesses.append(np.linspace(self.max_radius - 1, self.min_radius + 1, self.n_cp))

        # 4. Random monotonic
        raw = np.random.uniform(self.min_radius, self.max_radius, self.n_cp)
        guesses.append(_pava_isotonic(raw))

        # 5. Another random monotonic
        raw = np.random.uniform(self.min_radius, self.max_radius, self.n_cp)
        guesses.append(_pava_isotonic(raw))

        # 6. Known good (if provided)
        if known_good_radii is not None:
            guesses.insert(0, np.array(known_good_radii, dtype=np.float64))

        return guesses[:self.n_starts]

    def run(self, verbose: bool = True, known_good_radii=None) -> Dict:
        """Run multi-start optimization and return the best result."""
        guesses = self._generate_initial_guesses(known_good_radii)

        if verbose:
            print(f"\n  Multi-Start Optimizer")
            print(f"  Starts: {len(guesses)}")
            print(f"  Max iter/start: {self.maxiter_per_start}")
            print(f"  Control points: {self.n_cp}")

        t_total = time.time()
        best_result = None
        best_obj = float('inf')

        for i, guess in enumerate(guesses):
            if verbose:
                print(f"\n  --- Start {i+1}/{len(guesses)} ---")

            result = self.optimizer.run(
                verbose=verbose,
                maxiter=self.maxiter_per_start,
                known_good_radii=guess,
            )

            if result["final_rms_cents"] < best_obj:
                best_obj = result["final_rms_cents"]
                best_result = result
                if verbose:
                    print(f"    *** New best: {best_obj:.4f} cents ***")

        wall_time = time.time() - t_total

        if verbose:
            print(f"\n  Multi-start complete:")
            print(f"    Best RMS: {best_result['final_rms_cents']:.4f} cents")
            print(f"    Total wall time: {wall_time:.1f}s")

        best_result["wall_time"] = wall_time
        best_result["n_starts"] = len(guesses)
        return best_result
