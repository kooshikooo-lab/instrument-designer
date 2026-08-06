"""Generate the Fusion 360 Phase-1 batch artifacts.

Produces STEP + reference STL for the 5 representative presets (under
``test_output/fusion/phase1/``, gitignored) and writes the batch trigger
manifest ``phase1_trigger.json`` the Fusion add-in consumes:

- koncovka_C       : cylindrical, open-open, no holes (Phase-0 baseline)
- xaphoon_C        : cylindrical, open-open, 7 holes
- fujara_G         : cylindrical, closed-top cap, no holes
- bass_chalumeau_C : cylindrical, closed-top, 8 holes
- glissotar        : conical (16 -> 36 mm), 9 holes

Prints a baseline summary (watertight + volume per file) so the Fusion
batch results in ``phase1_result.json`` have expected values to compare.

Run:
    python scripts/make_fusion_phase1_artifacts.py
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.cadquery_export import INSTRUMENTS, export_step, export_stl, generate_instrument

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output", "fusion", "phase1")

PHASE1_PRESETS = [
    "koncovka_C",
    "xaphoon_C",
    "fujara_G",
    "bass_chalumeau_C",
    "glissotar",
]

_PARAMS = ("bore_length", "bore_diameter", "wall_thickness", "holes", "closed_top")


def mesh_stats(path):
    import trimesh

    m = trimesh.load(path, force="mesh")
    status = "watertight" if (m.is_watertight and m.is_winding_consistent) else "NOT watertight"
    return len(m.vertices), len(m.faces), float(m.volume), status


def main():
    os.makedirs(OUT, exist_ok=True)
    manifest = []
    baseline = {}

    for name in PHASE1_PRESETS:
        spec = INSTRUMENTS[name]
        kwargs = {k: spec[k] for k in _PARAMS if k in spec}

        step = os.path.join(OUT, f"{name}.step")
        stl = os.path.join(OUT, f"{name}.stl")
        step_out = os.path.join(OUT, f"{name}_roundtrip.step")
        stl_out = os.path.join(OUT, f"{name}_from_fusion.stl")

        print(f"generating {name} ...")
        solid = generate_instrument(**kwargs)
        export_step(solid, step)
        export_stl(solid, stl)

        nv, nf, vol, status = mesh_stats(stl)
        baseline[name] = {
            "verts": nv, "faces": nf, "volume_mm3": round(vol, 3), "status": status,
        }
        manifest.append({
            "name": name,
            "step": step,
            "step_out": step_out,
            "stl_out": stl_out,
            "expected_mm3": round(vol, 3),
        })

    trigger = os.path.join(OUT, "phase1_trigger.json")
    with open(trigger, "w") as f:
        json.dump({"files": manifest}, f, indent=2)

    print("\n=== baseline (expected values for the Fusion batch) ===")
    for name in PHASE1_PRESETS:
        b = baseline[name]
        print(f"  {name}: verts={b['verts']} faces={b['faces']} "
              f"volume={b['volume_mm3']:.3f} mm3 [{b['status']}]")
    print(f"\nartifacts + trigger in {os.path.abspath(OUT)}")


if __name__ == "__main__":
    main()
