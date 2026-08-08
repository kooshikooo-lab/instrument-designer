"""Generate the Fusion 360 Phase 0 smoke-test artifacts.

Produces (all under ``test_output/fusion/``, gitignored):
- koncovka_C.step  : clean no-hole solid for the STEP round-trip test
- koncovka_C.stl   : watertight STL reference (504 verts / 1008 faces)
- xaphoon_C.stl    : 7-hole mesh (NOTE: watertight since the audit C1 hole-cutter
                     fix — no longer a NON-watertight repair proof target)

Then prints a baseline summary (watertight + volume per file) so the Fusion
GUI steps in ``docs/FUSION_360_30day_plan.md`` have expected values to check.

Run:
    python scripts/make_fusion_smoke_test.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.cadquery_export import export_step, export_stl, generate_instrument

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output", "fusion")

KONCOVKA = {
    "bore_length": 651.5, "bore_diameter": 16.0, "wall_thickness": 2.0,
    "closed_top": False, "holes": [],
}
XAPHOON = {
    "bore_length": 300.0, "bore_diameter": 14.0, "wall_thickness": 3.0,
    "closed_top": False,
    "holes": [(40, 6.5), (80, 6.5), (120, 6.5), (160, 6.5),
              (200, 6.5), (240, 6.5), (280, 6.5)],
}


def mesh_stats(path):
    import trimesh
    m = trimesh.load(path, force="mesh")
    status = "watertight" if (m.is_watertight and m.is_winding_consistent) else "NOT watertight"
    return len(m.vertices), len(m.faces), float(m.volume), status


def main():
    os.makedirs(OUT, exist_ok=True)

    k_step = os.path.join(OUT, "koncovka_C.step")
    k_stl = os.path.join(OUT, "koncovka_C.stl")
    x_stl = os.path.join(OUT, "xaphoon_C.stl")

    print("generating koncovka_C STEP/STL ...")
    koncovka = generate_instrument(**KONCOVKA)
    export_step(koncovka, k_step)
    export_stl(koncovka, k_stl)

    print("generating xaphoon_C STL ...")
    xaphoon = generate_instrument(**XAPHOON)
    export_stl(xaphoon, x_stl)

    print("\n=== baseline (expected values for the Fusion checks) ===")
    for path, label in ((k_step, "koncovka_C.step (STEP)"),
                        (k_stl, "koncovka_C.stl"),
                        (x_stl, "xaphoon_C.stl")):
        if path.endswith(".step"):
            print(f"  {label}: {os.path.getsize(path)} bytes")
            continue
        nv, nf, vol, status = mesh_stats(path)
        print(f"  {label}: verts={nv} faces={nf} volume={vol:.3f} mm3 [{status}]")

    print(f"\nartifacts in {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
