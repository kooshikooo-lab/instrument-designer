"""Chalumier JSON5 → optimizer config converter.

Reads BbClarinet-parameters.json5 (chalumier output) and converts
it to the benchmark_all.py / jax_optimizer.py config format.

Usage:
    python scripts/convert_chalumier.py
    python scripts/convert_chalumier.py --output C:/tmp/clarinet_config.json
"""
import json
import re
import sys
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CHALUMIER_PARAMS = PROJECT_ROOT / "chalumier" / "output" / "BbClarinet-parameters.json5"


def parse_json5(text):
    def quote_keys(s):
        return re.sub(r'(?<=[{,])\s*([A-Za-z_][A-Za-z_0-9]*)\s*(?=:)', r'"\1"', s)
    text = quote_keys(text)
    return json.loads(text)


def load_chalumier_params(path):
    """Load chalumier JSON5 parameters."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    return parse_json5(text)


def convert_hole_fingering(fingering_str):
    """Convert chalumier 'X'/'O' hole pattern to list of 'closed'/'open'."""
    return ["closed" if c == "X" else "open" for c in fingering_str]


def build_optimizer_config(params_path=None):
    """Build complete optimizer config from chalumier parameters."""
    if params_path is None:
        params_path = CHALUMIER_PARAMS

    params = load_chalumier_params(params_path)

    length_mm = params["length"]
    bore_radius = params["bore"] / 2.0
    n_holes = params["numberOfHoles"]

    hp = params["holePositions"]
    hd = params["holeDiameters"]
    hl = params["holeLengths"]

    note_names = [
        "D3", "Eb3", "E3", "F3", "F#3", "G3", "Ab3", "A3", "Bb3", "B3",
        "C4", "C#4", "D4", "Eb4", "E4", "F4", "F#4", "G4",
        "Ab4", "A4", "Bb4", "B4", "C5", "C#5", "D5",
    ]

    register_map = [1]*21 + [2]*4  # chalumeau (1) through Bb4, clarion (2) for B4-D5

    fingerings = [
        ["closed"]*17,
        ["open","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","open","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","open","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","open","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","open","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","open","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","open","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","open","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","open","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","closed","open"],
        ["closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","open","open","open","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","open","closed","closed","close","open","open","open","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","open","open","open","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","open","open","open","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","open","open","open","closed","closed","closed"],
        ["closed","closed","closed","closed","closed","closed","closed","open","closed","closed","closed","open","open","open","closed","closed","closed"],
    ]

    targets_midi = [
        50, 51, 52, 53, 54, 55, 56, 57, 58, 59,
        60, 61, 62, 63, 64, 65, 66, 67,
        68, 69, 70, 71, 72, 73, 74,
    ]
    targets = [4186.0 / (2 ** ((127 - midi) / 12)) for midi in targets_midi]

    return {
        "instrument_name": "clarinet_Bb",
        "desc": "Bb clarinet (Boehm 17-hole, dual register) — from chalumier",
        "closed_top": True,
        "targets": targets,
        "names": note_names,
        "bore_radius": bore_radius,
        "outer_diameter": 22.0,
        "hole_diameter": hd[0] if hd else 7.0,
        "hole_length": hl[0] if hl else 3.75,
        "hole_positions": hp,
        "hole_diameters": hd,
        "hole_lengths": hl,
        "fingerings": fingerings,
        "n_registers": register_map,
        "bore_profile": {
            "positions_mm": params["inner"]["pos"],
            "inner_diameters_mm": params["inner"]["low"],
            "outer_diameters_mm": params["inner"]["high"],
        },
        "length_mm": length_mm,
        "true_length_mm": params.get("trueLength", length_mm),
        "_chromatic": False,
        "_source": "chalumier",
        "_source_commit": "2bdff4d",
    }


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Convert chalumier JSON5 → optimizer config")
    parser.add_argument("--input", default=str(CHALUMIER_PARAMS))
    parser.add_argument("--output", default=None)
    args = parser.parse_args()

    config = build_optimizer_config(args.input)

    if args.output:
        with open(args.output, "w") as f:
            json.dump(config, f, indent=2)
        print(f"Config written to {args.output}")
    else:
        print(json.dumps(config, indent=2, default=str))


if __name__ == "__main__":
    main()