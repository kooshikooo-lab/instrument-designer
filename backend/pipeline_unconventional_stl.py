"""Generate STL files from unconventional bore optimization results.

Usage:
    python backend/pipeline_unconventional_stl.py [--input INPUT_JSON] [--output DIR]

Reads the benchmark report (or a single optimization result JSON),
generates bore profiles from optimized parameters, and exports STL files.
"""

import sys, os, json, time, argparse

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.physics.bore_generators import bore_profile_to_diameter
from backend.physics.bore_optimizer import _generate_radii
from backend.cadquery_export import generate_variable_bore_instrument, export_stl


def build_hole_positions(length_mm: float, n_holes: int, offsets: list[float] | None = None) -> list[float]:
    if n_holes == 0:
        return []
    spacing = length_mm / (n_holes + 1)
    positions = [spacing * (i + 1) for i in range(n_holes)]
    if offsets and len(offsets) == 2:
        offset_a, offset_b = offsets
        for i in range(n_holes):
            t = (i + 1) / (n_holes + 1)
            positions[i] += offset_a * t + offset_b * t ** 2
        positions = [max(2.0, min(length_mm - 2.0, p)) for p in positions]
    return positions


def generate_stl_from_opt_result(result: dict, output_dir: str) -> dict:
    bore_type = result.get("bore_type", "unknown")
    length = result.get("bore_length_mm", 600.0)
    params = result.get("optimized_params", {})
    n_holes = result.get("n_holes", 7)
    hole_diameters = result.get("hole_diameters") or [7.0] * n_holes
    closed_top = result.get("closed_top", True) if result.get("closed_top") is not None else True
    hole_offsets = result.get("hole_offsets", None)

    hole_positions = build_hole_positions(length, n_holes, hole_offsets)
    holes = list(zip(hole_positions, hole_diameters))

    t0 = time.time()
    radii = _generate_radii(bore_type, length, params)
    gen_time = time.time() - t0

    t1 = time.time()
    profile = bore_profile_to_diameter(radii, n_samples=64)
    prof_time = time.time() - t1

    t2 = time.time()
    solid = generate_variable_bore_instrument(
        bore_profile=profile, wall_thickness=3.0,
        bore_length=length, holes=holes, closed_top=closed_top,
    )
    stl_path = os.path.join(output_dir, f"optimized_{bore_type}.stl")
    stl_time = export_stl(solid, stl_path)
    size_kb = round(os.path.getsize(stl_path) / 1024, 1)

    return {
        "bore_type": bore_type,
        "stl_path": stl_path,
        "size_kb": size_kb,
        "time_s": round(time.time() - t0, 3),
        "n_holes": n_holes,
        "n_radii": len(radii),
        "hole_positions_mm": [round(p, 1) for p in hole_positions],
    }


def main():
    parser = argparse.ArgumentParser(description="Generate STLs from optimization results")
    parser.add_argument("--input", default=None,
                        help="Path to benchmark report JSON (default: test_output/unconventional/benchmark_report.json)")
    parser.add_argument("--output", default=None,
                        help="Output directory for STL files (default: test_output/unconventional)")
    args = parser.parse_args()

    base = os.path.join(os.path.dirname(__file__), "..")
    input_path = args.input or os.path.join(base, "test_output", "unconventional", "benchmark_report.json")
    output_dir = args.output or os.path.join(base, "test_output", "unconventional")
    os.makedirs(output_dir, exist_ok=True)

    with open(input_path, "r") as f:
        report = json.load(f)

    opt_results = report.get("optimization_results", [])
    if not opt_results:
        print(f"No optimization results found in {input_path}")
        sys.exit(1)

    print(f"Generating STLs for {len(opt_results)} optimized instruments...")
    print(f"{'Type':<20} {'Holes':>5} {'Size':>8} {'Time':>7}")
    print("-" * 45)

    manifest = []
    for r in opt_results:
        info = generate_stl_from_opt_result(r, output_dir)
        manifest.append(info)
        print(f"{info['bore_type']:<20} {info['n_holes']:>5} {info['size_kb']:>7}KB {info['time_s']:>6.2f}s")

    manifest_path = os.path.join(output_dir, "stl_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest saved: {manifest_path}")
    print(f"STL files in: {output_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
