"""Test STL export pipeline for SequentialBoreOptimizer (closed-top clarinet)."""
import sys, os, time
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend.archived_optimizers.tmm_optimizer_sequential import SequentialBoreOptimizer
from backend.stl_export import export_optimizer_result, export_bore_only, export_bore_profile_json


def test_stl_export_sequential_clarinet():
    """Test STL export with a realistic closed-top clarinet configuration."""
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

    opt = SequentialBoreOptimizer(
        target_frequencies=target_freqs,
        fingering_sets=fingerings,
        bore_radius=7.25,           # standard clarinet bore
        outer_diameter=22.0,
        closed_top=True,            # clarinet is closed-top
        n_register=1,
        hole_diameter=7.0,
        hole_length=3.75,
        bore_length_bounds=[100.0, 800.0],
        n_bore_cp=6,                # variable bore with 6 control points
        bore_radius_bounds=[4.0, 15.0],
    )
    result = opt.run(verbose=False)

    # Should achieve good intonation (<10c RMS for this configuration)
    assert result['final_rms_cents'] < 10.0, f"RMS too high: {result['final_rms_cents']:.4f}c"
    assert result['bore_length_mm'] > 0
    assert len(result['hole_positions']) == 7

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    stl_path = export_optimizer_result(result, os.path.join(output_dir, "sequential_clarinet.stl"))
    assert os.path.exists(stl_path), f"STL file not found: {stl_path}"
    assert os.path.getsize(stl_path) > 0, f"STL file is empty: {stl_path}"

    bore_path = export_bore_only(result, os.path.join(output_dir, "sequential_clarinet_bore.stl"))
    assert os.path.exists(bore_path), f"Bore STL not found: {bore_path}"
    assert os.path.getsize(bore_path) > 0, f"Bore STL is empty: {bore_path}"

    json_path = export_bore_profile_json(result, os.path.join(output_dir, "sequential_clarinet_profile.json"))
    assert os.path.exists(json_path), f"JSON not found: {json_path}"
    assert os.path.getsize(json_path) > 0, f"JSON is empty: {json_path}"


if __name__ == "__main__":
    test_stl_export_sequential_clarinet()
