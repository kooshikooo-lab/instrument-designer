"""Test STL export for Legacy BoreOptimizer (NSGA-II)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend.archived_optimizers.bore_optimizer import BoreOptimizer
from backend.stl_export import export_optimizer_result, export_bore_only, export_bore_profile_json


def test_stl_export_legacy_bore_optimizer():
    """Test STL export using legacy BoreOptimizer result."""
    # C4-C5 diatonic scale (8 notes)
    target_freqs = [261.63, 293.66, 329.63, 349.23, 392.00, 440.00, 493.88, 523.25]

    optimizer = BoreOptimizer(
        target_frequencies=target_freqs,
        n_control_points=6,
        bore_length=None,
        min_radius=4.0,
        max_radius=15.0,
        pop_size=20,
        n_generations=10,
        temperature=20.0,
        n_workers=1,  # single-threaded for test
    )

    # Run optimization
    result = optimizer.run(verbose=False, callback=None)

    # Verify optimization produced designs
    assert 'designs' in result
    assert len(result['designs']) > 0

    # Take the best design
    best_design = result['designs'][0]
    bore_profile = best_design['bore_profile']  # list of {"position": p, "radius": r}

    # Convert to format expected by export_optimizer_result
    bore_radii = [p['radius'] for p in bore_profile]
    bore_positions = [p['position'] for p in bore_profile]
    bore_length = bore_positions[-1]

    # Legacy optimizer doesn't optimize holes directly - use placeholder
    n_holes = 7
    hole_positions = [bore_length * (i + 1) / (n_holes + 1) for i in range(n_holes)]
    hole_diameters = [7.0] * n_holes

    export_result = {
        'success': True,
        'bore_length_mm': float(bore_length),
        'bore_radii': bore_radii,
        'hole_positions': hole_positions,
        'hole_diameters': hole_diameters,
        'hole_lengths': [3.75] * n_holes,
        'final_rms_cents': best_design['objectives']['frequency_accuracy'],
        'scale_rms_cents': best_design['objectives']['scale_evenness'],
        'median_offset_cents': 0.0,
        'peak_error_cents': 0.0,
        'wall_time': result.get('wall_time', 0.0),
        'matched_frequencies': best_design.get('matched_frequencies', []),
    }

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output")
    os.makedirs(output_dir, exist_ok=True)

    stl_path = export_optimizer_result(export_result, os.path.join(output_dir, "legacy_clarinet.stl"))
    assert os.path.exists(stl_path), f"STL file not found: {stl_path}"
    assert os.path.getsize(stl_path) > 0, f"STL file is empty: {stl_path}"

    bore_path = export_bore_only(export_result, os.path.join(output_dir, "legacy_clarinet_bore.stl"))
    assert os.path.exists(bore_path), f"Bore STL not found: {bore_path}"
    assert os.path.getsize(bore_path) > 0, f"Bore STL is empty: {bore_path}"

    json_path = export_bore_profile_json(export_result, os.path.join(output_dir, "legacy_clarinet_profile.json"))
    assert os.path.exists(json_path), f"JSON not found: {json_path}"
    assert os.path.getsize(json_path) > 0, f"JSON is empty: {json_path}"


if __name__ == "__main__":
    test_stl_export_legacy_bore_optimizer()