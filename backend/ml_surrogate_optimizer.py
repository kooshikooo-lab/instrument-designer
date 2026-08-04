# Phase 1 optimizer - fast global search using phase_cost_with_offset
# Based on backend/two_phase_optimizer.py:phase1_de_search()
import time
import numpy as np
from scipy.optimize import differential_evolution
from backend.tmm_acoustics import tmm_instrument_from_radii

def ml_phase1_optimizer(bore_length, hole_positions, hole_diameters, hole_lengths,
                         target_frequencies, fingerings, n_register,
                         bore_bounds_range, hole_pos_bounds_range,
                         popsize=15, maxiter=30, seed=42, verbose=True):
    """
    Fast global search using phase_cost_with_offset (register-agnostic).

    Args:
        bore_length: Total bore length in mm
        hole_positions: List of hole positions along bore (mm)
        hole_diameters: List of hole diameters (mm)
        hole_lengths: List of hole chimney lengths (mm)
        target_frequencies: Target frequencies (Hz)
        fingerings: Fingering patterns (list of 'open'/'closed' strings)
        n_register: Register number for resonance search
        bore_bounds_range: (min, max) bore radius bounds (mm)
        hole_pos_bounds_range: (min, max) hole position bounds (mm)
        popsize: DE population size
        maxiter: DE max iterations
        seed: Random seed
        verbose: Print progress

    Returns:
        dict with keys: 'variables' (array), 'cost' (float), 'time' (float), 'instrument'
    """
    if verbose:
        print("=== Phase 1: ML surrogate optimization (global search) ===")
        print(f"  DE DE popsize={popsize}, maxiter={maxiter}")

    n_holes = len(hole_lengths)
    n_bore_ctrl = 6
    bore_min, bore_max = bore_bounds_range
    hp_min, hp_max = hole_pos_bounds_range
    hd_min, hd_max = 3.0, 15.0

    targets = np.array(target_frequencies)
    fingerings_parsed = []
    for f in fingerings:
        fl = ['open' if ch in ('O', 'o') else 'closed' for ch in f]
        while len(fl) < n_holes:
            fl.append('open')
        fingerings_parsed.append(fl[:n_holes])

    def cost(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = sorted(x[n_bore_ctrl + n_holes:])

        for i in range(1, len(hp)):
            if hp[i] <= hp[i-1] + 3:
                return 1e6

        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lengths,
                outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
            )
            return inst.phase_cost_with_offset(targets, fingerings_parsed,
                                                n_register=1)
        except:
            return 1e6

    bounds = (
        [(bore_min, bore_max)] * n_bore_ctrl
        + [(hd_min, hd_max)] * n_holes
        + [(hp_min, hp_max)] * n_holes
    )

    t0 = time.time()
    result = differential_evolution(
        cost, bounds, seed=seed, maxiter=maxiter, popsize=popsize,
        tol=1e-6, mutation=(0.5, 1.0), recombination=0.7,
        disp=False, polish=False
    )
    elapsed = time.time() - t0

    radii = result.x[:n_bore_ctrl]
    hd = result.x[n_bore_ctrl:n_bore_ctrl + n_holes]
    hp = sorted(result.x[n_bore_ctrl + n_holes:])

    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hole_lengths,
        outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
    )

    if verbose:
        print(f"  Phase 1 result: cost={result.fun:.6f} ({elapsed:.1f}s)")

    return {
        'variables': result.x,
        'cost': result.fun,
        'time': elapsed,
        'instrument': inst,
        'bore_radii': radii,
        'hole_diameters': hd,
        'hole_positions': hp,
        'n_holes': n_holes,
    }

# Phase 2 optimizer - local refinement using peak_cost_nearest (register-correct)
# Based on backend/two_phase_optimizer.py:phase2_lbfgsb_refine()
from scipy.optimize import minimize as sp_min

def ml_phase2_optimizer(x0, bore_length, hole_positions, hole_diameters, hole_lengths,
                        target_frequencies, fingerings, detected_regs,
                        bore_bounds_range, hole_pos_bounds_range,
                        n_iters=500, verbose=True):
    """
    Local refinement using peak_cost_nearest (register-aware).

    Args:
        x0: Initial guess (array of bore radii, hole diameters, hole positions)
        bore_length: Total bore length in mm
        hole_positions: List of hole positions along bore (mm)
        hole_diameters: List of hole diameters (mm)
        hole_lengths: List of hole chimney lengths (mm)
        target_frequencies: Target frequencies (Hz)
        fingerings: Fingering patterns (list of 'open'/'closed' strings)
        detected_regs: Detected registers for each fingering
        bore_bounds_range: (min, max) bore radius bounds (mm)
        hole_pos_bounds_range: (min, max) hole position bounds (mm)
        n_iters: L-BFGS-B max iterations
        verbose: Print progress

    Returns:
        dict with keys: 'variables' (array), 'cost' (float), 'time' (float), 'instrument'
    """
    if verbose:
        print("=== Phase 2: ML surrogate refinement (local search) ===")
        print(f"  L-BFGS-B iters={n_iters}")

    n_holes = len(hole_lengths)
    n_bore_ctrl = 6
    bore_min, bore_max = bore_bounds_range
    hp_min, hp_max = hole_pos_bounds_range
    hd_min, hd_max = 3.0, 15.0

    targets = np.array(target_frequencies)
    fingerings_parsed = []
    for f in fingerings:
        fl = ['open' if ch in ('O', 'o') else 'closed' for ch in f]
        while len(fl) < n_holes:
            fl.append('open')
        fingerings_parsed.append(fl[:n_holes])

    def cost(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = sorted(x[n_bore_ctrl + n_holes:])

        for i in range(1, len(hp)):
            if hp[i] <= hp[i-1] + 3:
                return 1e6

        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lengths,
                outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
            )
            from backend.two_phase_optimizer import peak_cost_nearest
            return peak_cost_nearest(inst, targets, fingerings_parsed, detected_regs)
        except:
            return 1e6

    bounds = (
        [(bore_min, bore_max)] * n_bore_ctrl
        + [(hd_min, hd_max)] * n_holes
        + [(hp_min, hp_max)] * n_holes
    )

    t0 = time.time()
    result = sp_min(cost, x0, method='L-BFGS-B', bounds=bounds,
                    options={'maxiter': n_iters, 'ftol': 1e-12})
    elapsed = time.time() - t0

    radii = result.x[:n_bore_ctrl]
    hd = result.x[n_bore_ctrl:n_bore_ctrl + n_holes]
    hp = sorted(result.x[n_bore_ctrl + n_holes:])

    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hole_lengths,
        outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
    )

    if verbose:
        print(f"  Phase 2 result: cost={result.fun:.6f} ({elapsed:.1f}s)")

    return {
        'variables': result.x,
        'cost': result.fun,
        'time': elapsed,
        'instrument': inst,
        'bore_radii': radii,
        'hole_diameters': hd,
        'hole_positions': hp,
    }

# Bore builder - converts variables to instrument

def build_tmm_instrument_from_bore_variables(bore_length, hole_positions, hole_diameters,
                                              hole_lengths, outer_diameter=22.0,
                                              closed_top=False, cone_step=0.5):
    """
    Build TMM instrument from bore design variables.

    Args:
        bore_length: Total bore length in mm
        hole_positions: List of hole positions along bore (mm)
        hole_diameters: List of hole diameters (mm)
        hole_lengths: List of hole chimney lengths (mm)
        outer_diameter: Outer diameter of instrument body (mm)
        closed_top: Whether bore is closed at mouthpiece end
        cone_step: Maximum step for profile smoothing

    Returns:
        TMMInstrument object
    """
    from backend.tmm_acoustics import tmm_instrument_from_radii
    # Default bore radii (10mm)
    radii = [10.0] * 6

    return tmm_instrument_from_radii(
        radii, bore_length, hole_positions, hole_diameters, hole_lengths,
        outer_diameter_mm=outer_diameter, closed_top=closed_top,
        cone_step=cone_step,
    )

# Main ML surrogate optimizer function combining phases 1 and 2
def ml_surrogate_optimize(instrument_config, target_frequencies, fingerings,
                           phase_budget=None, final_budget=None,
                           verbose=True):
    """
    ML surrogate optimizer for bore design using two-phase approach.

    Phase 1: Fast global search using phase_cost_with_offset (register-agnostic)
    Phase 2: Local refinement using peak_cost_nearest (register-aware)

    Args:
        instrument_config: Dictionary with instrument configuration
        target_frequencies: Target frequencies (Hz)
        fingerings: Fingering patterns (list of strings)
        phase_budget: Phase 1 budget parameters
        final_budget: Phase 2 budget parameters
        verbose: Print progress

    Returns:
        dict with optimization results
    """
    # Extract configuration
    bore_length = instrument_config['bore_length']
    hole_positions = instrument_config['hole_positions']
    hole_diameters = instrument_config['hole_diameters']
    hole_lengths = instrument_config['hole_lengths']
    outer_diameter = instrument_config.get('outer_diameter', 22.0)
    closed_top = instrument_config.get('closed_top', False)
    cone_step = instrument_config.get('cone_step', 0.5)

    # Set defaults
    if phase_budget is None:
        phase_budget = {'popsize': 15, 'maxiter': 30}
    if final_budget is None:
        final_budget = {'iters': 500, 'method': 'L-BFGS-B'}

    # Phase 1: Global search
    phase1_result = ml_phase1_optimizer(
        bore_length, hole_positions, hole_diameters, hole_lengths,
        target_frequencies, fingerings, 1,
        (instrument_config.get('bore_min', 3.0), instrument_config.get('bore_max', 18.0)),
        (instrument_config.get('hole_position_min', 10.0),
         instrument_config.get('hole_position_max', bore_length - 10.0)),
        popsize=phase_budget.get('popsize', 15),
        maxiter=phase_budget.get('maxiter', 30),
        verbose=verbose
    )

    # Get detected registers from Phase 1 instrument
    from backend.two_phase_optimizer import detect_registers
    detected_regs = detect_registers(
        phase1_result['instrument'],
        target_frequencies,
        fingerings,
        max_reg=5
    )

    # Phase 2: Local refinement
    phase2_result = ml_phase2_optimizer(
        phase1_result['variables'],
        bore_length, hole_positions, hole_diameters, hole_lengths,
        target_frequencies, fingerings, detected_regs,
        (instrument_config.get('bore_min', 3.0), instrument_config.get('bore_max', 18.0)),
        (instrument_config.get('hole_position_min', 10.0),
         instrument_config.get('hole_position_max', bore_length - 10.0)),
        n_iters=final_budget.get('iters', 500),
        verbose=verbose
    )

    # Final evaluation
    from backend.two_phase_optimizer import peak_cost_nearest
    final_cost = peak_cost_nearest(
        phase2_result['instrument'],
        target_frequencies,
        fingerings,
        detected_regs
    )

    total_time = phase1_result['time'] + phase2_result['time']

    if verbose:
        print("\n=== ML Surrogate Optimization Complete ===")
        print(f"  Phase 1 cost: {phase1_result['cost']:.6f}")
        print(f"  Phase 2 cost: {phase2_result['cost']:.6f}")
        print(f"  Final cost: {final_cost:.6f}")
        print(f"  Total time: {total_time:.2f}s")

    return {
        'phase1': {
            'variables': phase1_result['variables'],
            'cost': phase1_result['cost'],
            'time': phase1_result['time'],
            'instrument': phase1_result['instrument'],
            'bore_radii': phase1_result['bore_radii'],
            'hole_diameters': phase1_result['hole_diameters'],
            'hole_positions': phase1_result['hole_positions'],
        },
        'phase2': {
            'variables': phase2_result['variables'],
            'cost': phase2_result['cost'],
            'time': phase2_result['time'],
            'instrument': phase2_result['instrument'],
            'bore_radii': phase2_result['bore_radii'],
            'hole_diameters': phase2_result['hole_diameters'],
            'hole_positions': phase2_result['hole_positions'],
        },
        'detected_registers': detected_regs,
        'final_cost': final_cost,
        'total_time': total_time,
        'best_instrument': phase2_result['instrument'],
        'best_variables': phase2_result['variables'],
    }

if __name__ == "__main__":
    # Example usage
    example_config = {
        'bore_length': 330.8,
        'hole_positions': [62.1, 92.3, 107.3, 131.4, 154.2],
        'hole_diameters': [7.0] * 5,
        'hole_lengths': [3.75] * 5,
        'bore_min': 5.0,
        'bore_max': 25.0,
        'hole_position_min': 20.0,
        'hole_position_max': 300.0,
    }

    targets = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
    fingerings = ['OOOOOO', 'OOOOOo', 'OOOoOO', 'OOoOOO', 'OoOOOO', 'oOOOOO']

    result = ml_surrogate_optimize(example_config, targets, fingerings, verbose=True)
    print("\n=== Optimization Results ===")
    print(f"Phase 1 cost: {result['phase1']['cost']:.6f}")
    print(f"Phase 2 cost: {result['phase2']['cost']:.6f}")
    print(f"Final cost: {result['final_cost']:.6f}")
    print(f"Detected registers: {result['detected_registers']}")