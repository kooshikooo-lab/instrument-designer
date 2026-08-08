"""Phase 0.3 mesh-repair proof agent: drives Fusion's Mesh workspace GUI to
repair a non-watertight STL and verifies the result with
``check_mesh_repair_gate``.

Workflow (Fusion GUI, automated via screenshot + local vision model):
    1. ensure Fusion is running and the target mesh is open,
    2. switch to the Mesh workspace,
    3. tell the vision agent to repair the mesh (close hole, erase & fill),
    4. export the repaired mesh as STL,
    5. run check_mesh_repair_gate on the exported file -> PASS required.

The vision loop is the same one in :mod:`vision_loop`; verification here is
the deterministic numeric gate, not the model's opinion.

Usage:
    python scripts/gui_automation/fusion_mesh_repair_agent.py \
        --stl test_output/fusion/nonwatertight_target.stl \
        --out test_output/fusion/repaired.stl \
        --max-steps 30
"""
from __future__ import annotations

import argparse
import os
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from backend.stl_verifier import check_mesh_repair_gate
from scripts.gui_automation import gui_driver
from scripts.gui_automation.vision_loop import run_loop

DEFAULT_STL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "test_output", "fusion", "nonwatertight_target.stl",
)
DEFAULT_OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "..",
    "test_output", "fusion", "repaired_from_gui.stl",
)

TASK_PROMPT = (
    "The current document contains a mesh with a hole (non-watertight). "
    "Work in the Mesh workspace: open the Repair dialog, close the hole(s), "
    "make the mesh watertight and manifold, then export it as an STL file. "
    "You may use the File > Export or right-click export commands. "
    "Proceed in small verified steps. When the export dialog asks for a "
    "filename, the target path is {out}. When you have exported, report done."
)


def _mesh_gate_passes(path: str) -> bool:
    if not os.path.exists(path):
        return False
    gate = check_mesh_repair_gate(path)
    ok = bool(gate.get("passed"))
    print(f"  gate: passed={ok} watertight={gate.get('watertight')} "
          f"manifold={gate.get('manifold')} components={gate.get('component_count')}")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stl", default=DEFAULT_STL)
    ap.add_argument("--out", default=DEFAULT_OUT)
    ap.add_argument("--max-steps", type=int, default=30)
    ap.add_argument("--skip-launch-check", action="store_true",
                    help="skip the wait-for-Fusion window check (tests)")
    args = ap.parse_args()

    if not args.skip_launch_check:
        print("Waiting for Fusion 360 window (start Fusion and open the mesh now)...")
        for _ in range(60):
            if gui_driver.activate_window("Fusion"):
                break
            time.sleep(2)
        else:
            print("ERROR: Fusion 360 window not found. Open the mesh in Fusion and retry.")
            return 2
        print("Fusion window found; starting repair loop.")
        time.sleep(2.0)

    prompt = TASK_PROMPT.format(out=args.out.replace("\\", "/"))
    run_log = os.path.join("test_output", "gui_agent", "fusion_mesh_repair.jsonl")
    code = run_loop(
        task_prompt=prompt,
        verify=lambda: _mesh_gate_passes(args.out),
        run_log=run_log,
        max_steps=args.max_steps,
        screenshot_dir=os.path.join("test_output", "gui_agent", "fusion_shots"),
    )
    final = check_mesh_repair_gate(args.out) if os.path.exists(args.out) else None
    print(f"\nfinal gate: {final}")
    return 0 if (final and final.get("passed")) else code


if __name__ == "__main__":
    sys.exit(main())
