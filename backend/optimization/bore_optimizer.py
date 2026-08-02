"""
Bore optimizer — Absolute RMS primary metric.

Optimizes bore geometry (length, profile) for a given fingering chart.
Uses absolute RMS cents as the cost function (no median correction).

Methodology:
- Two-phase approach (Noreland 2013): Phase 1 DE global search, Phase 2 L-BFGS-B refinement
- Cost function: absolute RMS cents deviation from target frequencies
- Median correction (evenness) is reported separately, NOT used for optimization

References:
- Noreland et al. (2013) "The Logical Clarinet" — two-phase optimization essential
- Ernoult et al. (2020) JASA — phase-based resonance tracking (to implement)
- Petiot et al. (2025) — NSGA-II Pareto front (intonation vs timbre)
"""
import time
import numpy as np
from scipy.optimize import differential_evolution, minimize
from typing import List, Dict, Any, Optional

from .base import Optimizer, OptimizationResult
from ..core.network import AcousticNetwork
from ..solvers.tmm_solver import TMMSolver


class BoreOptimizer(Optimizer):
    """Optimize bore geometry for a set of target notes.

    Optimizes:
    - Bore length
    - Bore profile (radii at control points)
    - Hole positions (optional)
    """

    def __init__(
        self,
        network: AcousticNetwork,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
        solver: TMMSolver = None,
        bore_length_bounds: tuple = (800, 1600),
        n_bore_cp: int = 0,
    ):
        """
        Args:
            network: initial acoustic network
            target_frequencies: target frequencies in Hz
            fingering_sets: fingering states for each note
            n_register: register to optimize (1=fundamental, 2=first overtone)
            solver: TMM solver instance
            bore_length_bounds: (min, max) bore length in mm
            n_bore_cp: number of bore control points (0=uniform)
        """
        self.network = network
        self.targets = target_frequencies
        self.fingering_sets = fingering_sets
        self.n_register = n_register
        self.solver = solver or TMMSolver()
        self.bore_length_bounds = bore_length_bounds
        self.n_bore_cp = n_bore_cp
        self._n_evaluations = 0

    def evaluate(self, parameters: Dict[str, Any]) -> float:
        """Evaluate cost for given bore parameters."""
        self._n_evaluations += 1

        bore_length = parameters.get("bore_length", self.network.total_length)
        bore_radii = parameters.get("bore_radii", None)

        # Create temporary network with new bore
        temp_network = self._make_network(bore_length, bore_radii)

        # Compute frequencies
        target_wavelengths = [self.network.speed_of_sound / f for f in self.targets]
        try:
            freqs = self.solver.compute_frequencies(
                temp_network, target_wavelengths, self.fingering_sets, self.n_register
            )
        except Exception:
            return 1e10

        # Compute cents error
        cents = []
        for target, actual in zip(self.targets, freqs):
            if actual > 0 and np.isfinite(actual):
                cents.append(1200.0 * np.log2(actual / target))
            else:
                cents.append(1e6)

        cents_arr = np.array(cents)
        if np.any(np.abs(cents_arr) > 1e5):
            return 1e10

        return float(np.sqrt(np.mean(cents_arr ** 2)))

    def _make_network(self, bore_length: float, bore_radii=None) -> AcousticNetwork:
        """Create a temporary network with modified bore."""
        import copy
        net = copy.deepcopy(self.network)

        if bore_radii is not None:
            net.segments[0] = Segment(
                length=bore_length,
                radius_in=bore_radii[0],
                radius_out=bore_radii[-1],
            )
        else:
            net.segments[0].length = bore_length

        net.boundary_bell.position = 0.0
        return net

    def optimize(self, verbose: bool = False) -> OptimizationResult:
        """Run bore optimization."""
        from ..core.network import Segment
        t0 = time.time()

        # Initial guess
        initial_length = self.network.total_length

        if self.n_bore_cp == 0:
            # Optimize only bore length
            bounds = [self.bore_length_bounds]

            result = differential_evolution(
                lambda x: self.evaluate({"bore_length": x[0]}),
                bounds, seed=42, maxiter=50, tol=1e-6,
            )

            best_length = result.x[0]
            best_cost = result.fun
        else:
            # Optimize bore length + control points
            bounds = [self.bore_length_bounds]
            for _ in range(self.n_bore_cp):
                bounds.append((5.0, 25.0))

            def objective(x):
                length = x[0]
                radii = x[1:]
                return self.evaluate({"bore_length": length, "bore_radii": radii})

            result = differential_evolution(
                objective, bounds, seed=42, maxiter=50, tol=1e-6,
            )

            best_length = result.x[0]
            best_cost = result.fun

        dt = time.time() - t0

        # Compute final metrics — absolute RMS is primary, median-corrected is secondary
        temp_net = self._make_network(best_length)
        target_wavelengths = [self.network.speed_of_sound / f for f in self.targets]
        try:
            freqs = self.solver.compute_frequencies(
                temp_net, target_wavelengths, self.fingering_sets, self.n_register
            )
            cents = []
            for target, actual in zip(self.targets, freqs):
                if actual > 0 and np.isfinite(actual):
                    cents.append(1200.0 * np.log2(actual / target))
                else:
                    cents.append(1e6)
            cents_arr = np.array(cents)
            rms_cents_abs = float(np.sqrt(np.mean(cents_arr ** 2)))
            offset = np.median(cents_arr)
            rms_cents_median = float(np.sqrt(np.mean((cents_arr - offset) ** 2)))
            peak_cents = float(np.max(np.abs(cents_arr - offset)))
            # Primary metric is absolute RMS (accuracy), median-corrected is evenness
            rms_cents = rms_cents_abs
        except Exception:
            rms_cents = best_cost
            rms_cents_median = 0.0
            peak_cents = 0.0

        return OptimizationResult(
            success=best_cost < 50.0,
            parameters={"bore_length": best_length},
            cost=best_cost,
            rms_cents=rms_cents,           # absolute RMS — primary (accuracy)
            rms_cents_median=rms_cents_median,  # median-corrected — secondary (evenness)
            peak_cents=peak_cents,
            n_evaluations=self._n_evaluations,
            wall_time=dt,
        )


# Import Segment at module level for _make_network
from ..core.network import Segment
