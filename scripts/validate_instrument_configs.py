"""Validate instrument config JSON files against schemas/instrument_config.schema.json.

Usage:
    python scripts/validate_instrument_configs.py
    python scripts/validate_instrument_configs.py --path config/my_instrument.json

Exit codes:
    0 = all configs valid
    1 = one or more configs invalid
"""

import json
import sys
from pathlib import Path


try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError as e:
    print("ERROR: jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(2)


REPO_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_PATH = REPO_ROOT / "schemas" / "instrument_config.schema.json"
CONFIG_DIR = REPO_ROOT / "config"


def load_schema():
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_file(path: Path, schema: dict) -> list[str]:
    """Return a list of error messages for the given config file."""
    errors = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"{path.name}: invalid JSON — {e}"]
    except OSError as e:
        return [f"{path.name}: cannot read file — {e}"]

    validator = Draft7Validator(schema)
    for err in validator.iter_errors(data):
        errors.append(f"{path.name}: {err.message} (at {list(err.path)})")

    # Cross-check: fingering chart bit length must match tonehole count (if both present).
    if "toneholes" in data and "fingering_chart" in data:
        n_holes = len(data["toneholes"])
        for chart_name, chart in data["fingering_chart"].items():
            for note, bits in chart.items():
                if len(bits) != n_holes:
                    errors.append(
                        f"{path.name}: fingering_chart.{chart_name}.{note} has "
                        f"{len(bits)} bits but toneholes has {n_holes} entries"
                    )

    return errors


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate instrument config files")
    parser.add_argument("--path", type=str, help="validate a single file instead of config/")
    args = parser.parse_args()

    schema = load_schema()

    if args.path:
        paths = [Path(args.path)]
    else:
        paths = sorted(CONFIG_DIR.glob("*.json"))

    if not paths:
        print("No config files found.")
        return 0

    all_errors = []
    for path in paths:
        all_errors.extend(validate_file(path, schema))

    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s) in {len(paths)} file(s):")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(paths)} instrument config file(s) valid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
