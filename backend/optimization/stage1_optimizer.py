"""Stage 1 optimizer: bore length + hole positions (register vent closed).

Combines bore length and hole position optimization for Stage 1.
Uses proper cost function (no offset removal).
"""
import time
import numpy as np
from scipy.optimize import differential_evolution
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from ..core.network import AcousticNetwork, Segment
from ..solvers.tmm_solver import TMMSolver


@dataclass
class Stage1Result:
    success: bool
    bore_length: float
    hole_positions: List[float]
    cost: float
    n_evaluations: int
    wall_time: float


def optimize_stage1(
    network: AcousticNetwork,
    target_frequencies: List[float],
    fingering_sets: List[List[str]],
    n_register: int = 1,
    solver: TMMSolver = None,
    bore_length_bounds: Tuple[float, float] = (800, 1600),
    initial_bore_length: float = None,
    initial_hole_positions: List[float] = None,
    min_spacing: float = 20.0,
    maxiter: int = 100,
    popsize: int = None,
    verbose: bool = False,
) -> Stage1Result:
    """
    Stage 1: Optimize bore length + hole positions (register vent closed).
    
    Args:
        network: base acoustic network
        target_frequencies: target frequencies in Hz
        fingering_sets: fingering states for each note
        n_register: register (1=chalumeau)
        solver: TMM solver
        bore_length_bounds: (min, max) bore length in mm
        initial_bore_length: starting bore length (default: network length)
        initial_hole_positions: starting hole positions (default: network tonehole positions)
        min_spacing: minimum spacing between holes (mm)
        maxiter: DE max iterations
        popsize: DE population size
        verbose: print progress
    
    Returns:
        Stage1Result with optimized bore_length and hole_positions
    """
    solver = solver or TMMSolver()
    
    # Get register vent position
    reg_vent_pos = None
    for p in network.ports:
        if p.is_register_vent:
            reg_vent_pos = p.position
            break
    
    # Default initial values
    if initial_bore_length is None:
        initial_bore_length = network.total_length
    if initial_hole_positions is None:
        initial_hole_positions = [p.position for p in network.tonehole_ports]
    
    n_holes = len(initial_hole_positions)
    n_params = 1 + n_holes  # bore_length + hole_positions
    
    # Bounds: [bore_length, hole_0, hole_1, ...]
    bounds = [bore_length_bounds]
    for i in range(n_holes):
        lo = max(reg_vent_pos + 20 if reg_vent_pos else 10.0, initial_hole_positions[i] - 150)
        hi = initial_hole_positions[i] + 150
        if i > 0:
            # Will enforce spacing in objective
            pass
        bounds.append((lo, hi))
    
    def evaluate(params: np.ndarray) -> float:
        """Evaluate cost for given parameters."""
        bore_length = params[0]
        hole_positions = sorted(params[1:])
        
        # Enforce spacing
        penalty = 0.0
        for i in range(1, len(hole_positions)):
            if hole_positions[i] - hole_positions[i-1] < min_spacing:
                penalty += 1e6 * (min_spacing - (hole_positions[i] - hole_positions[i-1])) ** 2
        
        if reg_vent_pos is not None and hole_positions[0] < reg_vent_pos + min_spacing:
            penalty += 1e6 * (reg_vent_pos + min_spacing - hole_positions[0]) ** 2
        
        if penalty > 0:
            return penalty
        
        # Build network with new bore length and hole positions
        temp_net = _make_network(network, bore_length, hole_positions)
        
        target_wavelengths = [network.speed_of_sound / f for f in target_frequencies]
        try:
            freqs = solver.compute_frequencies(
                temp_net, target_wavelengths, fingering_sets, n_register
            )
        except Exception:
            return 1e10
        
        cents = []
        for target, actual in zip(target_frequencies, freqs):
            if actual > 0 and np.isfinite(actual):
                cents.append(1200.0 * np.log2(actual / target))
            else:
                cents.append(1e6)
        
        cents_arr = np.array(cents)
        if np.any(np.abs(cents_arr) > 1e5):
            return 1e10
        
        # Use absolute RMS (no offset removal!)
        return float(np.sqrt(np.mean(cents_arr ** 2))) + penalty
    
    if popsize is None:
        popsize = max(10, n_params * 2)
    
    # Initial guess
    x0 = [initial_bore_length] + initial_hole_positions
    
    # Ensure initial guess is within bounds
    for i, (lo, hi) in enumerate(bounds):
        x0[i] = max(lo, min(hi, x0[i]))
    
    t0 = time.time()
    
    result = differential_evolution(
        evaluate, bounds, seed=42, maxiter=maxiter, tol=1e-6,
        popsize=popsize, init='latinhypercube',
    )
    
    dt = time.time() - t0
    
    best_params = result.x
    best_bore_length = best_params[0]
    best_hole_positions = sorted(best_params[1:].tolist())
    best_cost = result.fun
    
    return Stage1Result(
        success=best_cost < 50.0,
        bore_length=best_bore_length,
        hole_positions=best_hole_positions,
        cost=best_cost,
        n_evaluations=result.nfev,
        wall_time=dt,
    )


def _make_network(network: AcousticNetwork, bore_length: float, hole_positions: List[float]) -> AcousticNetwork:
    """Create temporary network with modified bore and holes."""
    import copy
    from ..core.network import Tonehole
    
    net = copy.deepcopy(network)
    net.segments[0].length = bore_length
    
    # Update tonehole positions
    new_ports = []
    for i, pos in enumerate(hole_positions):
        if i < len(net.tonehole_ports):
            orig = net.tonehole_ports[i]
            new_ports.append(Tonehole(
                position=pos,
                radius=orig.radius,
                length=orig.length,
            ))
        else:
            new_ports.append(Tonehole(
                position=pos,
                radius=7.0,
                length=5.0,
            ))
    
    # Keep register vent
    for p in net.ports:
        if p.is_register_vent:
            new_ports.append(p)
    
    new_ports.sort(key=lambda p: p.position)
    net.ports = new_ports
    net._build_indices()
    return net