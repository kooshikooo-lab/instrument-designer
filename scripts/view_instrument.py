"""One-click: open an instrument in Blender without touching the GUI panel.

Usage: python scripts/view_instrument.py [preset]
With no argument it prompts: Enter = koncovka_C, 'list' = show all presets.

Fetches the STL from the running design_server (127.0.0.1:8000); if the server
is down it generates the STL locally with backend.cadquery_export.
"""

import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SERVER_URL = "http://127.0.0.1:8000"
DEFAULT_PRESET = "koncovka_C"


def _find_blender():
    if os.environ.get("BLENDER_EXE"):
        return os.environ["BLENDER_EXE"]
    exe = shutil.which("blender")
    if exe:
        return exe
    found = glob.glob(r"C:\Program Files\Blender Foundation\Blender*\blender.exe")
    return sorted(found)[-1] if found else None


BLENDER_EXE = _find_blender()


def list_presets():
    try:
        from blender_addon import server_client
        data = server_client.list_cadquery_instruments(SERVER_URL)
        return {k: v.get("display_name", k) for k, v in data.items()}
    except Exception:
        from backend.cadquery_export import INSTRUMENTS
        return {k: k for k in INSTRUMENTS}


def fetch_stl(preset, out_path):
    try:
        from blender_addon import server_client
        stl = server_client.fetch_instrument_stl(SERVER_URL, preset)
        with open(out_path, "wb") as f:
            f.write(stl)
        print(f"  via design_server ({len(stl):,} bytes)")
        return
    except Exception:
        pass

    print("  design_server not reachable, generating locally...")
    from backend.cadquery_export import (
        INSTRUMENTS,
        generate_folded_bore_instrument,
        generate_instrument,
    )
    from cadquery import exporters

    spec = {k: v for k, v in INSTRUMENTS[preset].items() if k != "_meta"}
    solid = (
        generate_folded_bore_instrument(**spec)
        if "bend_radius_mm" in spec
        else generate_instrument(**spec)
    )
    exporters.export(solid, out_path)


def main():
    presets = list_presets()

    preset = sys.argv[1] if len(sys.argv) > 1 else ""
    if not preset:
        answer = input(
            f"Preset (Enter for {DEFAULT_PRESET}, 'list' for all, 'q' to quit): "
        ).strip()
        if answer.lower() in ("q", "quit"):
            return
        if answer.lower() in ("list", "l", "?"):
            for i, (key, display) in enumerate(sorted(presets.items()), 1):
                print(f"  {i:3d}. {display} ({key})")
            sel = input("Enter number or name: ").strip()
            if sel.isdigit():
                preset = sorted(presets.keys())[int(sel) - 1]
            else:
                preset = sel
        elif answer:
            preset = answer
        else:
            preset = DEFAULT_PRESET

    if preset not in presets:
        print(f"Unknown preset: {preset}")
        sys.exit(1)

    out_dir = os.path.join(ROOT, "output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, f"{preset}.stl")

    print(f"Fetching {preset} ({presets[preset]})...")
    fetch_stl(preset, out_path)
    print(f"STL ready: {out_path} ({os.path.getsize(out_path):,} bytes)")

    if not BLENDER_EXE or not os.path.exists(BLENDER_EXE):
        print(f"Blender not found at {BLENDER_EXE or '<none>'} (set BLENDER_EXE to override)")
        sys.exit(1)

    view_script = os.path.join(ROOT, "scripts", "blender_view.py")
    print("Opening Blender...")
    subprocess.run([
        BLENDER_EXE,
        "--window-geometry", "60", "60", "1280", "800",
        "--python", view_script, "--", out_path,
    ])
    print("Done. Close the Blender window when finished.")


if __name__ == "__main__":
    main()
