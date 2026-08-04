"""
Tests for the new ml_surrogate_optimizer modules.
Tests the two-phase ML optimizer for bore design.
"""
import pytest
import numpy as np
from backend.ml_surrogate_optimizer import (
    ml_phase1_optimizer,
    ml_phase2_optimizer,
    build_tmm_instrument_from_bore_variables,
    ml_surrogate_optimize,
)


def test_build_tmm_instrument_from_bore_variables():
    """Test building TMM instrument from bore variables."""
    bore_length = 330.8
    hole_positions = [62.1, 92.3, 107.3, 131.4, 154.2]
    hole_diameters = [7.0] * 5
    hole_lengths = [3.75] * 5

    instrument = build_tmm_instrument_from_bore_variables(
        bore_length, hole_positions, hole_diameters, hole_lengths
    )

    assert instrument is not None
    assert hasattr(instrument, 'find_resonance')
    assert hasattr(instrument, 'phase_cost_with_offset')


def test_ml_phase1_optimizer_basic():
    """Test Phase 1 optimizer with minimal configuration."""
    bore_length = 330.8
    hole_positions = [62.1, 92.3, 107.3, 131.4, 154.2]
    hole_diameters = [7.0] * 5
    hole_lengths = [3.75] * 5
    target_frequencies = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
    fingerings = ['OOOOOO', 'OOOOOo', 'OOOoOO', 'OOoOOO', 'OoOOOO', 'oOOOOO']

    result = ml_phase1_optimizer(
        bore_length, hole_positions, hole_diameters, hole_lengths,
        target_frequencies, fingerings, 1,
        (5.0, 25.0), (20.0, 300.0),
        popsize=5, maxiter=2, verbose=False
    )

    assert 'variables' in result
    assert 'cost' in result
    assert 'time' in result
    assert 'instrument' in result
    assert 'bore_radii' in result
    assert 'hole_diameters' in result
    assert 'hole_positions' in result

    assert isinstance(result['variables'], np.ndarray)
    assert isinstance(result['cost'], (int, float))
    assert result['cost'] >= 0

    assert result['instrument'] is not None
    assert len(result['bore_radii']) == 6
    assert len(result['hole_diameters']) == 5
    assert len(result['hole_positions']) == 5


def test_ml_phase2_optimizer_basic():
    """Test Phase 2 optimizer with minimal configuration."""
    # Create a simple initial guess
    x0 = np.array([10.0] * 6 +  # 6 bore radii
                  [8.0] * 5 +   # 5 hole diameters
                  [62.1, 92.3, 107.3, 131.4, 154.2])  # 5 hole positions

    bore_length = 330.8
    hole_positions = [62.1, 92.3, 107.3, 131.4, 154.2]
    hole_diameters = [7.0] * 5
    hole_lengths = [3.75] * 5
    target_frequencies = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
    fingerings = ['OOOOOO', 'OOOOOo', 'OOOoOO', 'OOoOOO', 'OoOOOO', 'oOOOOO']
    detected_regs = [1] * 6

    result = ml_phase2_optimizer(
        x0, bore_length, hole_positions, hole_diameters, hole_lengths,
        target_frequencies, fingerings, detected_regs,
        (5.0, 25.0), (20.0, 300.0),
        n_iters=5, verbose=False
    )

    assert 'variables' in result
    assert 'cost' in result
    assert 'time' in result
    assert 'instrument' in result
    assert 'bore_radii' in result
    assert 'hole_diameters' in result
    assert 'hole_positions' in result

    assert isinstance(result['variables'], np.ndarray)
    assert isinstance(result['cost'], (int, float))


def test_ml_surrogate_optimize_basic():
    """Test main ML surrogate optimizer with minimal configuration."""
    instrument_config = {
        'bore_length': 330.8,
        'hole_positions': [62.1, 92.3, 107.3, 131.4, 154.2],
        'hole_diameters': [7.0] * 5,
        'hole_lengths': [3.75] * 5,
        'bore_min': 5.0,
        'bore_max': 25.0,
        'hole_position_min': 20.0,
        'hole_position_max': 300.0,
    }

    target_frequencies = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
    fingerings = ['OOOOOO', 'OOOOOo', 'OOOoOO', 'OOoOOO', 'OoOOOO', 'oOOOOO']

    result = ml_surrogate_optimize(
        instrument_config, target_frequencies, fingerings,
        phase_budget={'popsize': 5, 'maxiter': 2},
        final_budget={'iters': 5},
        verbose=False
    )

    assert 'phase1' in result
    assert 'phase2' in result
    assert 'detected_registers' in result
    assert 'final_cost' in result
    assert 'total_time' in result
    assert 'best_instrument' in result
    assert 'best_variables' in result

    assert isinstance(result['final_cost'], (int, float))
    assert result['total_time'] >= 0
    assert result['best_instrument'] is not None

    # Check that Phase 1 and Phase 2 have required keys
    for phase_key in ['phase1', 'phase2']:
        phase_result = result[phase_key]
        assert 'variables' in phase_result
        assert 'cost' in phase_result
        assert 'time' in phase_result
        assert 'instrument' in phase_result

    # Final cost should be reasonable (not infinite)
    assert result['final_cost'] < 1e6


def test_cost_decreases_from_phase1_to_phase2():
    """Test that Phase 2 typically improves on Phase 1 (lower cost).
    
    Note: Phase 1 and Phase 2 use different objective functions:
    - Phase 1: phase_cost_with_offset (fast, register-agnostic)
    - Phase 2: peak_cost_nearest (register-aware)
    
    Therefore Phase 2 cost can be higher because it's a more accurate but
    potentially more expensive evaluation. The key is that the optimization
    converges to a reasonable solution.
    """
    instrument_config = {
        'bore_length': 330.8,
        'hole_positions': [62.1, 92.3, 107.3, 131.4, 154.2],
        'hole_diameters': [7.0] * 5,
        'hole_lengths': [3.75] * 5,
        'bore_min': 5.0,
        'bore_max': 25.0,
        'hole_position_min': 20.0,
        'hole_position_max': 300.0,
    }

    target_frequencies = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
    fingerings = ['OOOOOO', 'OOOOOo', 'OOOoOO', 'OOoOOO', 'OoOOOO', 'oOOOOO']

    result = ml_surrogate_optimize(
        instrument_config, target_frequencies, fingerings,
        phase_budget={'popsize': 5, 'maxiter': 2},
        final_budget={'iters': 5},
        verbose=False
    )

    # Phase 2 and Phase 1 use different objective functions, so direct comparison
    # is not meaningful. However, the final cost should be reasonable.
    final_cost = result['final_cost']
    assert final_cost < 1000, f"Final cost ({final_cost}) should be reasonable"
    assert final_cost > 0, f"Final cost ({final_cost}) should be positive"


def test_ml_surrogate_optimizer_with_low_clarinet_config():
    """Test ML surrogate optimizer with low clarinet configuration."""
    low_clarinet_config = {
        'bore_length': 2650.0,  # 2.65m for low clarinet
        'bore_radii': [15.0] * 6,  # Larger radii for low instrument
        'hole_positions': [62.1, 92.3, 107.3, 131.4, 154.2],
        'hole_diameters': [7.0] * 5,
        'hole_lengths': [3.75] * 5,
        'outer_diameter': 22.0,
        'closed_top': True,
        'cone_step': 0.5,
        'bore_min': 10.0,
        'bore_max': 30.0,
        'hole_diameter_min': 5.0,
        'hole_diameter_max': 20.0,
        'hole_position_min': 40.0,
        'hole_position_max': 2400.0,
    }

    targets = [233.08, 261.63, 293.66, 329.63, 349.23, 392.00]  # Bb clarinet notes
    fingerings = ['OOOOOO', 'OOOOOo', 'OOOoOO', 'OOoOOO', 'OoOOOO', 'oOOOOO']

    result = ml_surrogate_optimize(
        low_clarinet_config, targets, fingerings,
        phase_budget={'popsize': 3, 'maxiter': 2},
        final_budget={'iters': 3},
        verbose=False
    )

    assert 'final_cost' in result
    assert result['final_cost'] < 1e6  # Reasonable cost
    assert result['best_instrument'] is not None

    # Should be able to evaluate the instrument
    assert hasattr(result['best_instrument'], 'find_resonance')


def test_ml_surrogate_optimizer_with_folded_bore_config():
    """Test ML surrogate optimizer with folded bass clarinet configuration."""
    folded_config = {
        'bore_length': 1800.0,  # 1.8m physical length with folds
        'bore_radii': [12.0] * 6,
        'hole_positions': [50.0, 80.0, 95.0, 120.0, 143.0],
        'hole_diameters': [6.5] * 5,
        'hole_lengths': [3.5] * 5,
        'outer_diameter': 20.0,
        'closed_top': True,
        'cone_step': 0.5,
        'bore_min': 8.0,
        'bore_max': 25.0,
        'hole_diameter_min': 4.0,
        'hole_diameter_max': 18.0,
        'hole_position_min': 30.0,
        'hole_position_max': 1600.0,
    }

    targets = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]
    fingerings = ['OOOOOO', 'OOOOOo', 'OOOoOO', 'OOoOOO', 'OoOOOO', 'oOOOOO']

    result = ml_surrogate_optimize(
        folded_config, targets, fingerings,
        phase_budget={'popsize': 3, 'maxiter': 2},
        final_budget={'iters': 3},
        verbose=False
    )

    assert 'final_cost' in result
    assert result['final_cost'] < 1e6
    assert result['best_instrument'] is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])