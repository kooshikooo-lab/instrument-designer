"""Fingering optimizer.

Optimizes tonehole positions and diameters for a given bore geometry.
"""
import time
import numpy as np
from scipy.optimize import differential_evolution, minimize
from typing import List, Dict, Any, Optional

from .base import Optimizer, OptimizationResult
from ..core.network import AcousticNetwork
from ..physics.tonehole import SimpleTonehole as Tonehole
from ..solvers.tmm_solver import TMMSolver


class FingeringOptimizer(Optimizer):
    """Optimize tonehole positions and diameters.

    Optimizes:
    - Hole positions
    - Hole diameters (optional)
    - Hole lengths (optional)

    Stage 1: Optimize bore + toneholes (register vent closed)
    Stage 2: Optimize register vent (bore + toneholes fixed)
    Stage 3: Joint optimization (all variables)
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
        min_spacing: float = 20.0,  # mm minimum between holes
    ):
        self.network = network
        self.targets = target_frequencies
        self.fingering_sets = fingering_sets
        self.n_register = n_register
        self.solver = solver or TMMSolver()
        self.optimize_diameters = optimize_diameters
        self.optimize_lengths = optimize_lengths
        self.min_spacing = min_spacing
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

        # Use proper cost function WITHOUT offset removal
        # Offset removal (phase_cost_with_offset) is dangerous - hides register mismatch
        # We use RMS of absolute cents error
        return float(np.sqrt(np.mean(cents_arr ** 2)))

    def _make_network(self, positions, diameters=None, lengths=None) -> AcousticNetwork:
        """Create temporary network with modified holes."""
        import copy
        from ..core.network import Port as Tonehole, Port
        net = copy.deepcopy(self.network)

        # Get only tonehole ports (exclude register vent) for default values
        tonehole_ports = net.tonehole_ports

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

            new_ports.append(Tonehole(
                position=positions[i],
                radius=rad,
                length=ln,
            ))

        # Keep register vent if present
        for p in net.ports:
            if p.is_register_vent:
                new_ports.append(p)

        new_ports.sort(key=lambda p: p.position)
        net.ports = new_ports
        net._build_indices()  # reassign tonehole indices
        return net

    def optimize(self, initial_positions: List[float] = None, verbose: bool = False) -> OptimizationResult:
        """Run hole position optimization."""
        t0 = time.time()

        n_holes = self.network.n_toneholes

        if initial_positions is None:
            initial_positions = [p.position for p in self.network.tonehole_ports]

        # Get register vent position (must be before toneholes in internal coords)
        reg_vent_pos = None
        for p in self.network.ports:
            if p.is_register_vent:
                reg_vent_pos = p.position
                break

        # Bounds with spacing constraints
        bounds = []
        for i in range(n_holes):
            lo = max(10.0, initial_positions[i] - 100)
            hi = min(self.network.total_length - 10, initial_positions[i] + 100)
            
            # Toneholes must be after register vent (further from reed)
            if reg_vent_pos is not None:
                lo = max(lo, reg_vent_pos + self.min_spacing)
            
            if i > 0:
                lo = max(lo, bounds[-1][0] + self.min_spacing)
                hi = min(hi, self.network.total_length - 10 - (n_holes - 1 - i) * self.min_spacing)
            bounds.append((lo, hi))

        def objective(x):
            # Enforce spacing via penalty
            x_sorted = sorted(x)
            penalty = 0.0
            for i in range(1, len(x_sorted)):
                if x_sorted[i] - x_sorted[i-1] < self.min_spacing:
                    penalty += 1e6 * (self.min_spacing - (x_sorted[i] - x_sorted[i-1])) ** 2
            # Ensure after register vent
            if reg_vent_pos is not None and x_sorted[0] < reg_vent_pos + self.min_spacing:
                penalty += 1e6 * (reg_vent_pos + self.min_spacing - x_sorted[0]) ** 2
            return self.evaluate({"positions": x_sorted}) + penalty

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
