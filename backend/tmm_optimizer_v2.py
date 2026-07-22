"""
Bore optimizer using TMM phase resonance.

Two-phase approach:
  Phase 1: Powell (gradient-free) with root-finding cost for global search
  Phase 2: L-BFGS-B (scipy FD) with same root-finding cost for local polish

Both phases optimize the same objective, so comparison is fair.

Usage:
    from backend.tmm_optimizer_v2 import TMMBoreOptimizerJAX
    optimizer = TMMBoreOptimizerJAX(...)
    result = optimizer.run(verbose=True)
"""

import time
import math
import numpy as np
from scipy.optimize import minimize
from typing import List, Optional, Dict

try:
    from .tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.dirname(__file__))
    from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND


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
    Two-phase bore optimizer (root-finding based).

    Phase 1: Powell (gradient-free, no FD overhead) — global search
    Phase 2: L-BFGS-B (scipy FD gradients) — local polish

    Both phases optimize the same root-finding objective.
    JAX is not used here — the root-finding cost has discontinuous gradients
    that break JAX autodiff. Powell avoids this by being gradient-free.
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
            fundamental = min(target_freqs)
            if closed_top:
                self.bore_length = self.speed_of_sound / (4.0 * fundamental)
            else:
                self.bore_length = self.speed_of_sound / (2.0 * fundamental)
        else:
            self.bore_length = bore_length

        self.hole_positions = list(hole_positions or [])
        self.hole_diameters = list(hole_diameters or [])
        self.hole_lengths = list(hole_lengths or [])

        self._target_wavelengths = np.array([
            self.speed_of_sound / f for f in self.target_freqs
        ])

    def _objective(self, x: np.ndarray) -> float:
        """Root-finding based objective: RMS cents error after median offset correction."""
        radii = _pava_isotonic(x)
        radii = np.maximum(radii, self.min_radius)
        try:
            inst = tmm_instrument_from_radii(
                radii, self.bore_length,
                self.hole_positions, self.hole_diameters, self.hole_lengths,
                self.outer_diameter, self.closed_top, 0.5,
            )
        except Exception:
            return 1e10

        errors = []
        for i, (fingerings, target_freq) in enumerate(zip(self.fingering_sets, self.target_freqs)):
            try:
                wl = inst.find_resonance(
                    self._target_wavelengths[i], fingerings, self.n_register,
                )
                actual_freq = inst.frequency_from_wavelength(wl)
                if actual_freq <= 0 or not math.isfinite(actual_freq):
                    errors.append(1e6)
                else:
                    errors.append(1200.0 * math.log2(actual_freq / target_freq))
            except Exception:
                errors.append(1e6)

        errors = np.array(errors)
        if np.any(np.abs(errors) > 1e5):
            return 1e10
        global_offset = np.median(errors)
        corrected = errors - global_offset
        return float(np.sqrt(np.mean(corrected ** 2)))

    def _make_initial_guess(self, method="cylindrical"):
        if method == "cylindrical":
            return np.full(self.n_cp, 7.25)
        elif method == "flat":
            return np.full(self.n_cp, (self.min_radius + self.max_radius) / 2.0)
        elif method == "random":
            raw = np.random.uniform(self.min_radius, self.max_radius, self.n_cp)
            return _pava_isotonic(raw)
        raise ValueError(f"Unknown method: {method}")

    def run(
        self,
        verbose: bool = True,
        maxiter: int = 300,
        initial_guess: str = "cylindrical",
        known_good_radii: Optional[np.ndarray] = None,
    ) -> Dict:
        if known_good_radii is not None:
            x0 = np.array(known_good_radii, dtype=np.float64)
        else:
            x0 = self._make_initial_guess(initial_guess)

        bounds = [(self.min_radius, self.max_radius)] * self.n_cp

        if verbose:
            print(f"  TMM Bore Optimizer (root-finding)")
            print(f"  Control points: {self.n_cp}")
            print(f"  Bore length: {self.bore_length:.1f} mm")
            print(f"  Holes: {len(self.hole_positions)}")
            print(f"  Fingerings: {len(self.fingering_sets)}")

        t_opt = time.time()

        # Phase 1: Powell (gradient-free, no FD cost)
        powell_budget = maxiter * 2 // 3
        if verbose:
            print(f"  Phase 1: Powell ({powell_budget} maxiter)...")
        result_powell = minimize(
            self._objective,
            x0,
            method='Powell',
            bounds=bounds,
            options={"maxiter": powell_budget, "ftol": 1e-8},
        )
        if verbose:
            print(f"    Powell: {result_powell.fun:.4f} cents ({result_powell.nit} iters, {result_powell.nfev} evals)")

        # Phase 2: L-BFGS-B (scipy FD gradients, same objective)
        lbfgs_budget = maxiter - powell_budget
        if verbose:
            print(f"  Phase 2: L-BFGS-B ({lbfgs_budget} maxiter, FD gradients)...")
        result_lbfgs = minimize(
            self._objective,
            result_powell.x,
            method='L-BFGS-B',
            bounds=bounds,
            options={"maxiter": lbfgs_budget, "ftol": 1e-10, "gtol": 1e-6},
        )
        if verbose:
            print(f"    L-BFGS-B: {result_lbfgs.fun:.4f} cents ({result_lbfgs.nit} iters, {result_lbfgs.nfev} evals)")

        wall_time = time.time() - t_opt

        # Select best
        if result_powell.fun <= result_lbfgs.fun:
            best_x = result_powell.x
            best_obj = result_powell.fun
            if verbose:
                print(f"    -> Using Powell result")
        else:
            best_x = result_lbfgs.x
            best_obj = result_lbfgs.fun
            if verbose:
                print(f"    -> Using L-BFGS-B result")

        final_radii = _pava_isotonic(best_x)
        final_radii = np.maximum(final_radii, self.min_radius)

        # Final verification with root-finding
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
            print(f"\n  Per-note errors (cents):")
            for m in matched:
                print(f"    {m['target']:8.1f} Hz -> {m['actual']:8.1f} Hz  ({m['error_cents']:+.2f})")

        return {
            "success": True,
            "best_radii": final_radii.tolist(),
            "best_objective": best_obj,
            "final_rms_cents": final_rms,
            "global_offset_cents": global_offset,
            "matched_frequencies": matched,
            "wall_time": wall_time,
            "bore_length_mm": self.bore_length,
        }
