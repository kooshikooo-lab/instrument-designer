"""Generic JSON Schema validation helper.

Usage:
    python scripts/validate_json_schema.py <schema.json> <file-or-dir>
    python scripts/validate_json_schema.py schemas/design_output.schema.json test_output/unconventional/novel_instruments

Exit codes:
    0 = all files valid
    1 = one or more files invalid
    2 = schema/jsonschema missing or invalid
"""

import json
import subprocess
import sys
from pathlib import Path

try:
    import jsonschema
    from jsonschema import Draft7Validator
except ImportError as e:
    print("ERROR: jsonschema is required. Install with: pip install jsonschema", file=sys.stderr)
    sys.exit(2)


def validate_file(schema: dict, path: Path) -> list[str]:
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
    return errors


def collect_paths(target: Path) -> list[Path]:
    if target.is_file():
        return [target]
    if target.is_dir():
        return sorted(target.glob("*.json"))
    return []


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Validate JSON files against a schema")
    parser.add_argument("schema", type=str, help="path to JSON Schema file")
    parser.add_argument("target", type=str, help="path to JSON file or directory of JSON files")
    args = parser.parse_args()

    schema_path = Path(args.schema)
    target = Path(args.target)

    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except OSError as e:
        print(f"ERROR: cannot read schema {schema_path}: {e}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"ERROR: invalid schema JSON: {e}", file=sys.stderr)
        return 2

    paths = collect_paths(target)
    if not paths:
        print(f"No JSON files found at {target}")
        return 0

    all_errors = []
    for path in paths:
        all_errors.extend(validate_file(schema, path))

    if all_errors:
        print(f"FAILED: {len(all_errors)} error(s) in {len(paths)} file(s):")
        for e in all_errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {len(paths)} JSON file(s) valid against {schema_path.name}.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
