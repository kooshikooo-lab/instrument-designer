"""Test STL export for Two-Phase Optimizer."""
import sys, os
import numpy as np
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend.two_phase_optimizer import two_phase_optimize
from backend.stl_export import export_optimizer_result, export_bore_only, export_bore_profile_json


def test_stl_export_two_phase():
    """Test STL export using two-phase optimizer result via stl_export."""
    # C4-C5 diatonic scale (8 notes, 7 holes) for a Bb clarinet
    target_freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]
    fingerings = [
        ['closed'] * 7,
        ['open', 'closed', 'closed', 'closed', 'closed', 'closed', 'closed'],
        ['open', 'open', 'closed', 'closed', 'closed', 'closed', 'closed'],
        ['open', 'open', 'open', 'closed', 'closed', 'closed', 'closed'],
        ['open', 'open', 'open', 'open', 'closed', 'closed', 'closed'],
        ['open', 'open', 'open', 'open', 'open', 'closed', 'closed'],
        ['open', 'open', 'open', 'open', 'open', 'open', 'closed'],
        ['open', 'open', 'open', 'open', 'open', 'open', 'open'],
    ]

# Run two-phase optimizer
    result = two_phase_optimize(
        330.0,                    # bore_length
        7,                        # n_holes
        [3.75] * 7,              # hole_lens
        target_freqs,            # targets
        fingerings,              # fingerings
        n_register=1,
        bore_bounds_range=(4.0, 15.0),
        hole_pos_bounds_range=(10.0, 320.0),
        loss_model=None,
        verbose=False,
    )

    # Verify optimization succeeded
    assert 'phase2' in result
    assert 'variables' in result['phase2']
    x2 = result['phase2']['variables']
    assert x2 is not None

    # Extract bore radii, hole positions, diameters from result
    # x2 format: [6 bore radii] + [7 hole diameters] + [7 hole positions]
    n_bore_ctrl = 6
    n_holes = 7
    bore_radii = list(x2[:n_bore_ctrl])
    hole_diameters = list(x2[n_bore_ctrl:n_bore_ctrl + n_holes])
    hole_positions = sorted(list(x2[n_bore_ctrl + n_holes:]))

    # Convert to format expected by export_optimizer_result
    export_result = {
        'success': True,
        'bore_length_mm': 330.0,
        'bore_radii': bore_radii,
        'hole_positions': hole_positions,
        'hole_diameters': hole_diameters,
        'hole_lengths': [3.75] * n_holes,
        'final_rms_cents': result['phase2'].get('cost', 0.0),
        'scale_rms_cents': 0.0,
        'median_offset_cents': 0.0,
        'peak_error_cents': 0.0,
        'wall_time': result.get('total_time', 0.0),
        'matched_frequencies': [],
    }

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output")
    os.makedirs(output_dir, exist_ok=True)

    stl_path = export_optimizer_result(export_result, os.path.join(output_dir, "two_phase_clarinet.stl"))
    assert os.path.exists(stl_path), f"STL file not found: {stl_path}"
    assert os.path.getsize(stl_path) > 0, f"STL file is empty: {stl_path}"

    bore_path = export_bore_only(export_result, os.path.join(output_dir, "two_phase_clarinet_bore.stl"))
    assert os.path.exists(bore_path), f"Bore STL not found: {bore_path}"
    assert os.path.getsize(bore_path) > 0, f"Bore STL is empty: {bore_path}"

    json_path = export_bore_profile_json(export_result, os.path.join(output_dir, "two_phase_clarinet_profile.json"))
    assert os.path.exists(json_path), f"JSON not found: {json_path}"
    assert os.path.getsize(json_path) > 0, f"JSON is empty: {json_path}"


if __name__ == "__main__":
    test_stl_export_two_phase()