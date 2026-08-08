"""Test STL/STEP export via cadquery_export (cylindrical/conical bore)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend.cadquery_export import generate_instrument, export_stl, export_step


def test_cadquery_cylindrical_clarinet():
    """Test STL/STEP export for a cylindrical bore clarinet."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    # Cylindrical bore clarinet
    solid = generate_instrument(
        bore_length=600.0,
        bore_diameter=15.0,
        wall_thickness=3.0,
        holes=[(100, 8.0), (200, 8.5), (300, 9.0), (350, 8.0), (400, 7.5), (450, 7.0), (500, 6.5)],
        closed_top=True,
    )

    stl_path = os.path.join(output_dir, "cadquery_cylindrical_clarinet.stl")
    export_stl(solid, stl_path)
    assert os.path.exists(stl_path), f"STL file not found: {stl_path}"
    assert os.path.getsize(stl_path) > 0, f"STL file is empty: {stl_path}"

    step_path = os.path.join(output_dir, "cadquery_cylindrical_clarinet.step")
    export_step(solid, step_path)
    assert os.path.exists(step_path), f"STEP file not found: {step_path}"
    assert os.path.getsize(step_path) > 0, f"STEP file is empty: {step_path}"


def test_cadquery_conical_soprano_sax():
    """Test STL/STEP export for a conical bore soprano saxophone."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    # Conical bore soprano sax (open-open)
    solid = generate_instrument(
        bore_length=650.0,
        bore_diameter=(16.0, 36.0),  # (small_end, large_end) diameters
        wall_thickness=2.0,
        holes=[(80, 4.0), (200, 3.0), (400, 3.0), (450, 4.0), (500, 5.0), (550, 6.0), (580, 7.0)],
        closed_top=False,  # saxophone is open-open
    )

    stl_path = os.path.join(output_dir, "cadquery_conical_soprano_sax.stl")
    export_stl(solid, stl_path)
    assert os.path.exists(stl_path), f"STL file not found: {stl_path}"
    assert os.path.getsize(stl_path) > 0, f"STL file is empty: {stl_path}"

    step_path = os.path.join(output_dir, "cadquery_conical_soprano_sax.step")
    export_step(solid, step_path)
    assert os.path.exists(step_path), f"STEP file not found: {step_path}"
    assert os.path.getsize(step_path) > 0, f"STEP file is empty: {step_path}"


def test_cadquery_flute_open_open():
    """Test STL export for an open-open cylindrical flute."""
    output_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "output")
    os.makedirs(output_dir, exist_ok=True)

    solid = generate_instrument(
        bore_length=600.0,
        bore_diameter=19.0,
        wall_thickness=2.5,
        holes=[(150, 8.0), (200, 8.0), (250, 8.0), (300, 8.0), (350, 8.0), (400, 8.0)],
        closed_top=False,
    )

    stl_path = os.path.join(output_dir, "cadquery_flute.stl")
    export_stl(solid, stl_path)
    assert os.path.exists(stl_path), f"STL file not found: {stl_path}"
    assert os.path.getsize(stl_path) > 0, f"STL file is empty: {stl_path}"


if __name__ == "__main__":
    test_cadquery_cylindrical_clarinet()
    test_cadquery_conical_soprano_sax()
    test_cadquery_flute_open_open()
    print("All cadquery STL tests passed!")