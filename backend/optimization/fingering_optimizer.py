"""Fingering optimizer.

Optimizes tonehole positions and diameters for a given bore geometry.
"""
import time
import numpy as np
from scipy.optimize import differential_evolution, minimize
from typing import List, Dict, Any, Optional

from .base import Optimizer, OptimizationResult
from ..core.network import AcousticNetwork
from ..solvers.tmm_solver import TMMSolver


class FingeringOptimizer(Optimizer):
    """Optimize tonehole positions and diameters.

    Optimizes:
    - Hole positions
    - Hole diameters (optional)
    - Hole lengths (optional)
    """

    def __init__(
        self,
        network: AcousticNetwork,
        target_frequencies: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
        solver: TMMSolver = None,
        optimize_diameters: bool = False,
        optimize_lengths: bool = False,
    ):
        self.network = network
        self.targets = target_frequencies
        self.fingering_sets = fingering_sets
        self.n_register = n_register
        self.solver = solver or TMMSolver()
        self.optimize_diameters = optimize_diameters
        self.optimize_lengths = optimize_lengths
        self._n_evaluations = 0

    def evaluate(self, parameters: Dict[str, Any]) -> float:
        """Evaluate cost for given hole parameters."""
        self._n_evaluations += 1

        positions = parameters.get("positions", [])
        diameters = parameters.get("diameters", None)
        lengths = parameters.get("lengths", None)

        temp_network = self._make_network(positions, diameters, lengths)

        target_wavelengths = [self.network.speed_of_sound / f for f in self.targets]
        try:
            freqs = self.solver.compute_frequencies(
                temp_network, target_wavelengths, self.fingering_sets, self.n_register
            )
        except Exception:
            return 1e10

        cents = []
        for target, actual in zip(self.targets, freqs):
            if actual > 0 and np.isfinite(actual):
                cents.append(1200.0 * np.log2(actual / target))
            else:
                cents.append(1e6)

        cents_arr = np.array(cents)
        if np.any(np.abs(cents_arr) > 1e5):
            return 1e10

        offset = np.median(cents_arr)
        return float(np.sqrt(np.mean((cents_arr - offset) ** 2)))

    def _make_network(self, positions, diameters=None, lengths=None) -> AcousticNetwork:
        """Create temporary network with modified holes."""
        import copy
        from ..core.network import Port, NodeType
        net = copy.deepcopy(self.network)

        # Get only tonehole ports (exclude register vent) for default values
        tonehole_ports = [p for p in self.network.ports if p.node_type == NodeType.TONEHOLE]

        n_ports = len(positions)
        new_ports = []
        for i in range(n_ports):
            if diameters:
                rad = diameters[i] / 2.0
            elif i < len(tonehole_ports):
                rad = tonehole_ports[i].radius
            else:
                rad = 7.0  # fallback default

            if lengths:
                ln = lengths[i]
            elif i < len(tonehole_ports):
                ln = tonehole_ports[i].length
            else:
                ln = 5.0  # fallback default

            new_ports.append(Port(
                position=positions[i],
                radius=rad,
                length=ln,
                is_open=True,
                node_type=NodeType.TONEHOLE,
            ))

        # Keep register vent if present
        for p in net.ports:
            if p.node_type == NodeType.REGISTER_VENT:
                new_ports.append(p)

        new_ports.sort(key=lambda p: p.position)
        net.ports = new_ports
        return net

    def optimize(self, initial_positions: List[float] = None, verbose: bool = False) -> OptimizationResult:
        """Run hole position optimization."""
        t0 = time.time()

        n_holes = len([p for p in self.network.ports
                       if p.node_type.value == "tonehole"])

        if initial_positions is None:
            initial_positions = [p.position for p in self.network.ports
                                 if p.node_type.value == "tonehole"]

        # Bounds
        bounds = []
        for i in range(n_holes):
            lo = max(10.0, initial_positions[i] - 100)
            hi = min(self.network.total_length - 10, initial_positions[i] + 100)
            if i > 0:
                lo = max(lo, bounds[-1][0] + 5)
            bounds.append((lo, hi))

        def objective(x):
            return self.evaluate({"positions": sorted(x)})

        result = differential_evolution(
            objective, bounds, seed=42, maxiter=100, tol=1e-6,
            popsize=max(10, n_holes * 2),
        )

        best_positions = sorted(result.x.tolist())
        best_cost = result.fun

        dt = time.time() - t0

        return OptimizationResult(
            success=best_cost < 50.0,
            parameters={"hole_positions": best_positions},
            cost=best_cost,
            n_evaluations=self._n_evaluations,
            wall_time=dt,
        )
