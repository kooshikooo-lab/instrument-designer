"""
Generate test STL files for promising / successful metamaterial low-clarinet
models.

For every family member (bass, contra-alto, contra-bass, octocontras):
  1. The folded paperclip body (from the repo's folded-instrument presets).
  2. The metamaterial low-register section: a straight bore carrying the
     tuned Helmholtz-resonator array (neck + cavity bulbs) that extends the
     all-closed note to the family's target.

Designs come from the L1 explicit-array tuner in
``backend/metamaterial_low_clarinets.py`` (same code the benchmark reports),
so the STLs and the acoustics always agree.

Regenerable artifacts (STLs) are deliberately NOT committed.

Run: python scripts/export_metamaterial_low_clarinets_stl.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.cadquery_export import (
    INSTRUMENTS,
    export_stl,
    generate_folded_bore_instrument,
    generate_metamaterial_section,
    instrument_info,
)
from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    cavity_volume_for_f0,
    tune_f0_to_fundamental_l1,
)

NECK_RADIUS_MM = 4.0
NECK_LENGTH_MM = 8.0

OUT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "designs", "metamaterial_low_clarinets")

# cadquery_export preset name for each folded low-clarinet body
FOLDED_PRESET = {
    "bass": "bass_clarinet_7hole_folded",
    "contra_alto": "contra_alto_clarinet_Eb",
    "contra_bass": "contra_bass_clarinet_Bb",
    "octocontra_alto": "octo_contra_alto_clarinet_EEb",
    "octocontrabass": "octo_contra_bass_clarinet_BBB",
}


def cavity_dims(volume_mm3):
    """Cylindrical cavity bulb: length = 2 * radius, volume matches target."""
    radius = (volume_mm3 / (2.0 * math.pi)) ** (1.0 / 3.0)
    return radius, 2.0 * radius


def folded_body(key):
    preset = FOLDED_PRESET[key]
    spec = {k: v for k, v in INSTRUMENTS[preset].items() if k != "_meta"}
    return generate_folded_bore_instrument(**spec)


def metamaterial_section(key):
    """Straight bore section carrying the tuned HR array for the family."""
    spec = LOW_CLARINETS[key]
    target = spec["extension_target_hz"]
    spacing = 30.0 if key == "bass" else 40.0
    f0, n, achieved, _ = tune_f0_to_fundamental_l1(key, target, spacing_mm=spacing)
    v = cavity_volume_for_f0(f0, NECK_RADIUS_MM, NECK_LENGTH_MM)
    cav_r, cav_l = cavity_dims(v)
    seg_len = spec["bore_length_mm"] * 0.1  # [0.9L, L] segment from the tuner
    resonators = []
    for i in range(n):
        pos = seg_len * (i + 0.5) / n
        resonators.append((pos, NECK_RADIUS_MM, NECK_LENGTH_MM, cav_r, cav_l))
    return generate_metamaterial_section(
        bore_length=seg_len,
        bore_diameter=spec["bore_diameter_mm"],
        wall_thickness=spec["wall_thickness_mm"],
        resonators=resonators,
        closed_end=True,
    ), {"f0_hz": f0, "n": n, "cavity_v_mm3": v, "cavity_r_mm": cav_r,
        "cavity_l_mm": cav_l, "spacing_mm": spacing, "achieved_f1": achieved,
        "target_hz": target}


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    manifest = {}
    for key in sorted(LOW_CLARINETS):
        entry = {"key": key, "name": LOW_CLARINETS[key]["name"]}

        body = folded_body(key)
        body_path = os.path.join(OUT_DIR, f"{key}_folded_body.stl")
        dt = export_stl(body, body_path)
        entry["folded_body_stl"] = body_path
        entry["folded_body_info"] = instrument_info(body)
        entry["folded_body_export_s"] = round(dt, 2)

        section, meta = metamaterial_section(key)
        sec_path = os.path.join(OUT_DIR, f"{key}_metamaterial_section.stl")
        dt = export_stl(section, sec_path)
        entry["metamaterial_section_stl"] = sec_path
        entry["metamaterial_section_info"] = instrument_info(section)
        entry["metamaterial_section_export_s"] = round(dt, 2)
        entry["design"] = meta

        manifest[key] = entry
        print(f"{key:<16} body {entry['folded_body_stl'].split(chr(92))[-1]} "
              f"{entry['folded_body_info']} | section "
              f"{entry['metamaterial_section_stl'].split(chr(92))[-1]} "
              f"{entry['metamaterial_section_info']} | "
              f"f0={meta['f0_hz']:.0f} Hz N={meta['n']} "
              f"cav={meta['cavity_r_mm']:.0f}x{meta['cavity_l_mm']:.0f} mm")

    manifest_path = os.path.join(OUT_DIR, "manifest.json")
    with open(manifest_path, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(f"\n  STLs + manifest -> {OUT_DIR}")
    print("  (regenerable artifacts: not committed, per AGENTS.md)")


if __name__ == "__main__":
    main()
