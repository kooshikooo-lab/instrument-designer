"""Test STL export pipeline."""
import sys, time, os
sys.path.insert(0, r"C:\instrument-designer")
from backend.stl_export import export_optimizer_result, export_bore_only, export_bore_profile_json


def test_stl_export():
    """Test STL export pipeline with mock result."""
    # Mock result dict with required fields for STL export
    result = {
        'final_rms_cents': 0.5,
        'bore_length_mm': 372.5,
        'bore_radii': [7.25] * 12,  # 12 control points
        'hole_positions': [30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0],
        'hole_diameters': [6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5],
        'hole_lengths': [3.0] * 7,
        'outer_diameter': 22.0,
        'bore_radius': 7.25,
        'hole_diameter': 6.5,
        'hole_length': 3.0,
        'bore_length': 372.5,
    }

    print("Using mock result for STL export test...")
    print(f"  RMS: {result['final_rms_cents']:.4f}c | L: {result['bore_length_mm']:.0f}mm")
    print(f"  Holes: {len(result['hole_positions'])}")

    print("\nExporting STL...")
    t0 = time.time()
    os.makedirs(r"C:\instrument-designer\output", exist_ok=True)
    stl_path = export_optimizer_result(result, r"C:\instrument-designer\output\soprano_sax.stl")
    print(f"  STL: {stl_path} ({time.time()-t0:.2f}s)")

    t0 = time.time()
    bore_path = export_bore_only(result, r"C:\instrument-designer\output\soprano_sax_bore.stl")
    print(f"  Bore: {bore_path} ({time.time()-t0:.2f}s)")

    t0 = time.time()
    json_path = export_bore_profile_json(result, r"C:\instrument-designer\output\soprano_sax_profile.json")
    print(f"  JSON: {json_path} ({time.time()-t0:.2f}s)")

    import os
    for p in [stl_path, bore_path, json_path]:
        size = os.path.getsize(p)
        print(f"  {os.path.basename(p)}: {size:,} bytes")
        assert size > 0, f"File {p} should not be empty"


def test_stl_export():
    """Test STL export functions with mock result."""
    import sys, time, os
    sys.path.insert(0, r"C:\instrument-designer")
    from backend.stl_export import export_optimizer_result, export_bore_only, export_bore_profile_json

    # Mock result dict with required fields for STL export
    result = {
        'final_rms_cents': 0.5,
        'bore_length_mm': 372.5,
        'bore_radii': [7.25] * 12,
        'hole_positions': [30.0, 60.0, 90.0, 120.0, 150.0, 180.0, 210.0],
        'hole_diameters': [6.5, 6.5, 6.5, 6.5, 6.5, 6.5, 6.5],
        'hole_lengths': [3.0] * 7,
        'outer_diameter': 22.0,
        'bore_radius': 7.25,
        'hole_diameter': 6.5,
        'hole_length': 3.0,
        'bore_length': 372.5,
    }

    os.makedirs(r"C:\instrument-designer\output", exist_ok=True)
    
    stl_path = export_optimizer_result(result, r"C:\instrument-designer\output\test_soprano_sax.stl")
    assert os.path.exists(stl_path)
    assert os.path.getsize(stl_path) > 0
    
    bore_path = export_bore_only(result, r"C:\instrument-designer\output\test_soprano_sax_bore.stl")
    assert os.path.exists(bore_path)
    assert os.path.getsize(bore_path) > 0
    
    json_path = export_bore_profile_json(result, r"C:\instrument-designer\output\test_soprano_sax_profile.json")
    assert os.path.exists(json_path)
    assert os.path.getsize(json_path) > 0