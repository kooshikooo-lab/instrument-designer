from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.two_phase_optimizer import detect_registers, peak_cost_nearest
import numpy as np
from scipy.optimize import minimize as sp_min
import time


def ml_surrogate_optimize(
    instrument_config,
    target_frequencies,
    fingerings,
    phase_budget=None,
    final_budget=None,
    optimization_method='bayesian',
    verbose=True,
):
    """
    ML surrogate optimization for bore design using phase_cost_with_offset (fast) and peak_cost_nearest (register-correct).

    Args:
        instrument_config (dict): Configuration for TMM instrument creation with keys:
            - bore_length (float): Total bore length in mm
            - hole_positions (list): Position of each tone hole along bore (mm)
            - hole_diameters (list): Diameter of each tone hole (mm)
            - hole_lengths (list): Length of each hole chimney (mm)
            - bore_radii (list): Bore radii at control points (mm)
            - outer_diameter (float): Outer diameter of instrument body (mm)
            - closed_top (bool): Whether bore is closed at mouthpiece end
            - cone_step (float): Maximum step for profile smoothing

        target_frequencies (list): Target frequencies (Hz) to optimize for
        fingerings (list): Fingering patterns as strings of 'O'/'o' (open) and other (closed)
        phase_budget (dict): Phase 1 configuration (fast, register-agnostic optimization)
        final_budget (dict): Phase 2 configuration (accurate, register-aware refinement)
        optimization_method (str): 'bayesian' or 'surrogate' (not implemented yet)
        verbose (bool): Print progress

    Returns:
        dict: Optimization results with the best instrument configuration and cost
    """

    # Extract instrument configuration
    bore_length = instrument_config['bore_length']
    hole_positions = instrument_config['hole_positions']
    hole_diameters = instrument_config['hole_diameters']
    hole_lengths = instrument_config['hole_lengths']
    bore_radii = instrument_config['bore_radii']
    outer_diameter = instrument_config.get('outer_diameter', 22.0)
    closed_top = instrument_config.get('closed_top', False)
    cone_step = instrument_config.get('cone_step', 0.5)
    loss_model = instrument_config.get('loss_model')

    n_holes = len(hole_lengths)
    n_bore_ctrl = len(bore_radii)

    # Prepare data
    targets = np.array(target_frequencies)
    fingerings_parsed = []
    for f in fingerings:
        fl = ['open' if ch in ('O', 'o') else 'closed' for ch in f]
        while len(fl) < n_holes:
            fl.append('open')
        fingerings_parsed.append(fl[:n_holes])

    # Extract optimization parameters
    phase1_popsize = phase_budget.get('popsize', 15) if phase_budget else 15
    phase1_maxiter = phase_budget.get('maxiter', 30) if phase_budget else 30
    phase2_iters = final_budget.get('iters', 500) if final_budget else 500
    phase2_optim_method = final_budget.get('method', 'L-BFGS-B') if final_budget else 'L-BFGS-B'

    # Bounds for optimization variables
    bore_bounds = (instrument_config.get('bore_min', 3.0), instrument_config.get('bore_max', 18.0))
    hd_bounds = (instrument_config.get('hole_diameter_min', 3.0), instrument_config.get('hole_diameter_max', 15.0))
    hp_bounds = (instrument_config.get('hole_position_min', 10.0),
                 instrument_config.get('hole_position_max', bore_length - 10.0))

    # Build initial instrument for register detection
    initial_inst = tmm_instrument_from_radii(
        radii_mm=bore_radii,
        bore_length_mm=bore_length,
        hole_positions_mm=hole_positions,
        hole_diameters_mm=hole_diameters,
        hole_lengths_mm=hole_lengths,
        outer_diameter_mm=outer_diameter,
        closed_top=closed_top,
        cone_step=cone_step,
        loss_model=loss_model,
    )

    # Phase 1: Detect registers for later use in phase 2
    registers = detect_registers(initial_inst, targets, fingerings_parsed, max_reg=5)
    if verbose:
        print(f"Phase 1: Detected registers: {registers}")

    # Phase 1: ML surrogate optimization using phase_cost_with_offset (fast, smooth but register-agnostic)
    if verbose:
        print(f"\nPhase 1: Running ML surrogate optimization with DE")
        print(f"  Objective: phase_cost_with_offset (register-agnostic)")
        print(f"  Parameters: popsize={phase1_popsize}, maxiter={phase1_maxiter}")

    # For now, using the existing DE optimizer from two_phase_optimizer for phase 1
    # This uses phase_cost_with_offset internally
    from backend.two_phase_optimizer import phase1_de_search

    initial_guess = np.array(
        [10.0] * n_bore_ctrl +  # bore radii
        [8.0] * n_holes +       # hole diameters
        sorted([bore_length * (i+1) / (n_holes+1) for i in range(n_holes)])  # hole positions
    )

    # Define the cost function for phase 1 (uses phase_cost_with_offset)
    def phase1_cost(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = sorted(x[n_bore_ctrl + n_holes:])

        # Enforce minimum hole spacing
        for i in range(1, len(hp)):
            if hp[i] <= hp[i-1] + 3:
                return 1e6

        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lengths,
                outer_diameter_mm=outer_diameter, closed_top=closed_top,
                cone_step=cone_step, loss_model=loss_model
            )
            return inst.phase_cost_with_offset(targets, fingerings_parsed,
                                                n_register=1)  # Use register 1 as placeholder
        except:
            return 1e6

    # Bounds for phase 1
    phase1_bounds = (
        [(bore_bounds[0], bore_bounds[1])] * n_bore_ctrl
        + [(hd_bounds[0], hd_bounds[1])] * n_holes
        + [(hp_bounds[0], hp_bounds[1])] * n_holes
    )

    # Run Phase 1: DE optimization (fast, register-agnostic)
    from scipy.optimize import differential_evolution
    t0 = time.time()
    de_result = differential_evolution(
        phase1_cost, phase1_bounds,
        maxiter=phase1_maxiter, popsize=phase1_popsize,
        seed=42, disp=False, tol=1e-6
    )
    t1 = time.time() - t0

    best_phase1_x = de_result.x
    best_phase1_cost = de_result.fun

    if verbose:
        print(f"  Phase 1 result: cost={best_phase1_cost:.6f} ({t1:.1f}s)")

    # Build instrument from Phase 1 result
    radii1 = best_phase1_x[:n_bore_ctrl]
    hd1 = best_phase1_x[n_bore_ctrl:n_bore_ctrl + n_holes]
    hp1 = sorted(best_phase1_x[n_bore_ctrl + n_holes:])
    inst1 = tmm_instrument_from_radii(
        radii1, bore_length, hp1, hd1, hole_lengths,
        outer_diameter_mm=outer_diameter, closed_top=closed_top,
        cone_step=cone_step, loss_model=loss_model
    )

    # Phase 2: ML surrogate refinement using peak_cost_nearest (register-correct)
    if verbose:
        print(f"\nPhase 2: ML surrogate refinement using L-BFGS-B")
        print(f"  Objective: peak_cost_nearest (register-aware)")
        print(f"  Iterations: {phase2_iters}")

    # Build phase 2 cost function (register-aware)
    def phase2_cost(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = sorted(x[n_bore_ctrl + n_holes:])

        # Enforce minimum hole spacing
        for i in range(1, len(hp)):
            if hp[i] <= hp[i-1] + 3:
                return 1e6

        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lengths,
                outer_diameter_mm=outer_diameter, closed_top=closed_top,
                cone_step=cone_step, loss_model=loss_model
            )
            return peak_cost_nearest(inst, targets, fingerings_parsed, registers)
        except:
            return 1e6

    # Bounds for phase 2
    phase2_bounds = (
        [(bore_bounds[0], bore_bounds[1])] * n_bore_ctrl
        + [(hd_bounds[0], hd_bounds[1])] * n_holes
        + [(hp_bounds[0], hp_bounds[1])] * n_holes
    )

    # Run Phase 2: L-BFGS-B optimization (accurate, register-aware)
    t0 = time.time()
    lbfgs_result = sp_min(phase2_cost, best_phase1_x, method=phase2_optim_method,
                         bounds=phase2_bounds, options={'maxiter': phase2_iters, 'ftol': 1e-12})
    t2 = time.time() - t0

    best_phase2_x = lbfgs_result.x
    best_phase2_cost = lbfgs_result.fun

    if verbose:
        print(f"  Phase 2 result: cost={best_phase2_cost:.6f} ({t2:.1f}s)")

    # Build final instrument from Phase 2 result
    radii2 = best_phase2_x[:n_bore_ctrl]
    hd2 = best_phase2_x[n_bore_ctrl:n_bore_ctrl + n_holes]
    hp2 = sorted(best_phase2_x[n_bore_ctrl + n_holes:])
    final_inst = tmm_instrument_from_radii(
        radii2, bore_length, hp2, hd2, hole_lengths,
        outer_diameter_mm=outer_diameter, closed_top=closed_top,
        cone_step=cone_step, loss_model=loss_model
    )

    # Final evaluation with register detection
    final_registers = detect_registers(final_inst, targets, fingerings_parsed)
    final_cost = peak_cost_nearest(final_inst, targets, fingerings_parsed, final_registers)

    # Compile results
    results = {
        'initial_bore_radii': bore_radii,
        'phase1_variables': best_phase1_x,
        'phase1_cost': best_phase1_cost,
        'n_bore_ctrl': n_bore_ctrl,
        'hole_diameters_phase1': hd1,
        'hole_positions_phase1': hp1,
        'instrument_phase1': inst1,
        'phase2_variables': best_phase2_x,
        'phase2_cost': best_phase2_cost,
        'final_cost': final_cost,
        'best_instrument': final_inst,
        'detected_registers': final_registers,
        'bore_radii': radii2,
        'hole_diameters': hd2,
        'hole_positions': hp2,
        'total_time': t1 + t2,
        'optim_method': optimization_method
    }

    if verbose:
        print(f"\nOptimization complete!")
        print(f"  Total time: {results['total_time']:.2f} s")
        print(f"  Phase 1 (fast, register-agnostic): {best_phase1_cost:.6f}")
        print(f"  Phase 2 (accurate, register-aware): {best_phase2_cost:.6f}")
        print(f"  Final cost: {final_cost:.6f}")
        print(f"  Best registers: {final_registers}")

    return results


if __name__ == "__main__":
    # Example: Test with a low clarinet configuration
    print("Testing ML surrogate optimizer on low clarinet configuration")
    print("=" * 60)

    # Low clarinet configuration (e.g., contrabass clarinet)
    low_clarinet_config = {
        'bore_length': 2650.0,  # 2.65m total length
        'bore_radii': [15.0] * 6,  # Start with larger radii for low instrument
        'hole_positions': [62.1, 92.3, 107.3, 131.4, 154.2],  # Bb clarinet holes, scaled
        'hole_diameters': [7.0] * 5,  # Open holes
        'hole_lengths': [3.75] * 5,  # Standard hole lengths
        'outer_diameter': 22.0,
        'closed_top': True,
        'cone_step': 0.5,
        'bore_min': 5.0,
        'bore_max': 25.0,
        'hole_diameter_min': 3.0,
        'hole_diameter_max': 20.0,
        'hole_position_min': 20.0,
        'hole_position_max': 2400.0,
    }

    # Target frequencies for Bb clarinet (lowest 6 notes)
    targets = [233.08, 261.63, 293.66, 329.63, 349.23, 392.00]  # B♭3, B♭4, E♭5, F5, G5, A♭5

    # Fingering patterns (all holes open for lowest register, partial for others)
    fingerings = [
        'OOOOOO',  # All holes open (lowest register)
        'OOOOOo',  # One hole closed
        'OOOoOO',  # Two holes closed
        'OOoOOO',  # Three holes closed
        'OoOOOO',  # Four holes closed
        'oOOOOO',  # Five holes closed
    ]

    # Phase budgets
    phase1_budget = {'popsize': 10, 'maxiter': 20}
    phase2_budget = {'iters': 300, 'method': 'L-BFGS-B'}

    # Run ML surrogate optimization
    results = ml_surrogate_optimize(
        low_clarinet_config,
        targets,
        fingerings,
        phase_budget=phase1_budget,
        final_budget=phase2_budget,
        verbose=True
    )

    print(f"\nOptimization Summary:")
    print(f"  Initial RMS cents: Not calculated")
    print(f"  Phase 1 cost: {results['phase1_cost']:.6f}")
    print(f"  Phase 2 cost: {results['phase2_cost']:.6f}")
    print(f"  Final cost: {results['final_cost']:.6f}")
    print(f"  Detected registers: {results['detected_registers']}")

    # Test folded bass clarinet configuration
    print(f"\n{'='*60}")
    print(f"Testing ML surrogate optimizer on folded bass clarinet")
    print(f"{'='*60}")

    folded_bass_config = {
        'bore_length': 1800.0,  # 1.8m physical length with folds
        'bore_radii': [12.0] * 6,
        'hole_positions': [50.0, 80.0, 95.0, 120.0, 143.0],  # Different hole placement for folded bore
        'hole_diameters': [6.5] * 5,
        'hole_lengths': [3.5] * 5,
        'outer_diameter': 20.0,
        'closed_top': True,
        'cone_step': 0.5,
        'bore_min': 4.0,
        'bore_max': 22.0,
        'hole_diameter_min': 3.0,
        'hole_diameter_max': 18.0,
        'hole_position_min': 15.0,
        'hole_position_max': 1600.0,
    }

    results_folded = ml_surrogate_optimize(
        folded_bass_config,
        targets,
        fingerings,
        phase_budget=phase1_budget,
        final_budget=phase2_budget,
        verbose=True
    )

    print(f"\nFolded Instrument Summary:")
    print(f"  Phase 1 cost: {results_folded['phase1_cost']:.6f}")
    print(f"  Phase 2 cost: {results_folded['phase2_cost']:.6f}")
    print(f"  Final cost: {results_folded['final_cost']:.6f}")
    print(f"  Detected registers: {results_folded['detected_registers']}")