"""Headless Blender import test for generated STL files.

Runs Blender in background mode, imports each STL in a batch directory, and
writes a JSON report. No GUI window.

Usage:
    python scripts/test_blender_import.py test_output/desktop_stl_batch
"""
import argparse
import glob
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _find_blender():
    if os.environ.get("BLENDER_EXE"):
        return os.environ["BLENDER_EXE"]
    exe = shutil.which("blender")
    if exe:
        return exe
    found = sorted(glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe"))
    return found[-1] if found else None


def _run_blender(stl_path: str) -> dict:
    blender = _find_blender()
    if not blender:
        return {"ok": False, "error": "Blender not found"}

    script = ROOT / "scripts" / "_blender_import_check.py"
    cmd = [
        blender, "--background", "--python", str(script), "--", stl_path,
    ]
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=120,
        )
        for line in proc.stdout.splitlines():
            marker = "BLENDER_IMPORT_REPORT:"
            if marker in line:
                return json.loads(line.split(marker, 1)[1])
        return {"ok": False, "error": "no report line", "stdout": proc.stdout[-500:], "stderr": proc.stderr[-500:]}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("folder", default="test_output/desktop_stl_batch", nargs="?")
    args = parser.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        print(f"Folder not found: {folder}")
        sys.exit(1)

    results = []
    for stl in sorted(folder.glob("*.stl")):
        print(f"Testing {stl.name} ...")
        report = _run_blender(str(stl))
        report["file"] = stl.name
        results.append(report)
        print(f"  ok={report.get('ok')} verts={report.get('verts')} faces={report.get('faces')} error={report.get('error')}")

    out = folder / "blender_import_report.json"
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nReport written to {out}")


if __name__ == "__main__":
    main()
