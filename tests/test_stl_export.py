"""Test STL export pipeline."""
import sys, os, time
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend.archived_optimizers.tmm_optimizer_sequential import SequentialBoreOptimizer
from backend.stl_export import export_optimizer_result, export_bore_only, export_bore_profile_json

target_freqs = [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0]
fingerings = [
    ['closed'] * 7,
    ['open', 'closed', 'closed', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'closed', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'open', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'open', 'open', 'closed'],
]


def test_stl_export():
    opt = SequentialBoreOptimizer(
        target_frequencies=target_freqs,
        fingering_sets=fingerings,
        bore_radius=6.0,
        outer_diameter=20.0,
        closed_top=False,
        n_register=1,
        hole_diameter=6.5,
        hole_length=3.0,
    )
    result = opt.run(verbose=False)
    assert result['final_rms_cents'] < 50.0, f"RMS too high: {result['final_rms_cents']:.4f}c"
    assert result['bore_length_mm'] > 0
    assert len(result['hole_positions']) > 0

    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output")
    os.makedirs(output_dir, exist_ok=True)

    stl_path = export_optimizer_result(result, os.path.join(output_dir, "soprano_sax.stl"))
    assert os.path.exists(stl_path), f"STL file not found: {stl_path}"
    assert os.path.getsize(stl_path) > 0, f"STL file is empty: {stl_path}"

    bore_path = export_bore_only(result, os.path.join(output_dir, "soprano_sax_bore.stl"))
    assert os.path.exists(bore_path), f"Bore STL not found: {bore_path}"
    assert os.path.getsize(bore_path) > 0, f"Bore STL is empty: {bore_path}"

    json_path = export_bore_profile_json(result, os.path.join(output_dir, "soprano_sax_profile.json"))
    assert os.path.exists(json_path), f"JSON not found: {json_path}"
    assert os.path.getsize(json_path) > 0, f"JSON is empty: {json_path}"


if __name__ == "__main__":
    test_stl_export()
