"""One-click: open an instrument in the three.js web preview.

Usage: python scripts/view_browser.py [preset]
With no argument it prompts: Enter = koncovka_C, 'list' = show all presets.

Starts design_server if it isn't running, then opens the default browser at
http://127.0.0.1:8000/preview?preset=<preset>
"""

import os
import subprocess
import sys
import time
import urllib.parse
import urllib.request
import webbrowser

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

SERVER_URL = "http://127.0.0.1:8000"
DEFAULT_PRESET = "koncovka_C"


def server_up():
    try:
        with urllib.request.urlopen(SERVER_URL + "/health", timeout=2) as r:
            return r.status == 200
    except Exception:
        return False


def start_server():
    print("design_server not running — starting it...")
    py = sys.executable
    log = os.path.join(ROOT, "scripts", "design_server.log")
    with open(log, "a") as f:
        subprocess.Popen(
            [py, "-m", "uvicorn", "woodwind_designer.engine.design_server:app",
             "--host", "0.0.0.0", "--port", "8000"],
            cwd=ROOT,
            stdout=f,
            stderr=subprocess.STDOUT,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    for _ in range(30):
        time.sleep(0.5)
        if server_up():
            return True
    return False


def list_presets():
    try:
        from blender_addon import server_client
        data = server_client.list_cadquery_instruments(SERVER_URL)
        return {k: v.get("display_name", k) for k, v in data.items()}
    except Exception:
        from backend.cadquery_export import INSTRUMENTS
        return {k: k for k in INSTRUMENTS}


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

    if not server_up():
        if not start_server():
            print("Failed to start design_server. Start it manually:")
            print(
                "  python -m uvicorn woodwind_designer.engine.design_server:app "
                "--host 0.0.0.0 --port 8000"
            )
            sys.exit(1)

    url = f"{SERVER_URL}/preview?preset={urllib.parse.quote(preset)}"
    print(f"Opening {preset} in browser...")
    webbrowser.open(url)
    print("Close the browser tab when finished.")


if __name__ == "__main__":
    main()
