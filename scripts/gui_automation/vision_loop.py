"""Vision loop: screenshot -> local vision model -> safe action.

Drives the observe->decide->act->verify cycle using the local Ollama
``gemma4:12b`` model (no external API). The model is asked to reply with a
single JSON object drawn from a strict action schema:

    {"action": "click"|"type"|"press"|"hotkey"|"done"|"wait",
     "x": <int>, "y": <int>, "text": "...", "keys": ["..."],
     "reason": "why", "verified": true|false}

Actions are executed through :mod:`gui_driver` (with its click gate), then
the caller's verification callback (e.g. ``check_mesh_repair_gate``) decides
whether the loop continues. Every step is logged to a JSONL run file.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import sys
import time
import urllib.request
from collections.abc import Callable

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from scripts.gui_automation import gui_driver

OLLAMA_BASE = os.environ.get("OLLAMA_BASE", "http://127.0.0.1:11434")
# gemma3:4b fits in this machine's ~3GB free RAM (12B did not fit and
# swapped at 0.75 tok/s); override with VISION_MODEL if a bigger model runs.
MODEL = os.environ.get("VISION_MODEL", "gemma3:4b")
# Remote vision fallback (OpenRouter). Used when the local Ollama vision path
# is too slow or times out. Default model/free fallbacks are shared with the
# STL verifier so the key + model list live in one place.
REMOTE_MODEL = os.environ.get("REMOTE_VISION_MODEL", "")
# Vision backend order. "auto" = ollama, then chatgpt-desktop, then openrouter.
# Force a specific one with VISION_BACKEND=ollama|chatgpt|openrouter.
VISION_BACKEND = os.environ.get("VISION_BACKEND", "auto")

# Action names the model is allowed to emit; anything else is rejected.
ALLOWED_ACTIONS = {"click", "type", "press", "hotkey", "done", "wait"}

SYSTEM_PROMPT = """You are driving Fusion 360's GUI to repair a non-watertight
mesh. You see one screenshot. Decide the SINGLE next action and reply with
ONLY a JSON object, no prose, no code fences:

{"action": "...", "x": 0, "y": 0, "text": "", "keys": [], "reason": "...", "verified": false}

Allowed actions:
- click: press mouse at (x, y) in screenshot pixel coordinates.
- type: type "text" into the focused field.
- press: press a single key, e.g. "enter", "escape", "tab".
- hotkey: press "keys" together, e.g. ["ctrl", "o"].
- wait: wait a few seconds (dialogs animating, documents loading).
- done: the task is finished; set "verified": true only if you are certain.

Rules: coordinates are relative to the screenshot you were shown. Prefer
small, verifiable steps. If you cannot see a target, choose "wait" or
"done". Never invent coordinates for something that is not visible."""

# The JSON the model must produce, plus a free-form summary for the log.
ACTION_KEYS = {"action", "reason", "verified"}
ACTION_JSON_FIELDS = {
    "action": str,
    "x": (int, type(None)),
    "y": (int, type(None)),
    "text": str,
    "keys": list,
    "reason": str,
    "verified": bool,
}


def _image_payload(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode("ascii")


def ask_vision(png_bytes: bytes, user_prompt: str, timeout: int = 120) -> dict:
    """Send screenshot + prompt to the vision model, return parsed JSON.

    Backends, in order (override with ``VISION_BACKEND``):
      1. ollama     - local Ollama model (no API key). Fast when the model is
                      already warm; times out when it is not loaded.
      2. chatgpt    - ChatGPT Desktop via clipboard+paste+OCR. No API key, but
                      needs the app installed and running on this machine.
      3. openrouter - OpenRouter free models (needs ``OPENROUTER_API_KEY``);
                      reuses :func:`backend.stl_verifier.ask_vision`, which
                      retries 429/5xx across a small free-model list.

    In "auto" mode the next backend is tried only if the current one raises.
    """
    order = {
        "ollama": (_ask_vision_ollama, timeout),
        "chatgpt": (_ask_vision_chatgpt, 180),
        "openrouter": (_ask_vision_remote, timeout),
    }
    if VISION_BACKEND == "auto":
        chain = ["ollama", "chatgpt", "openrouter"]
    elif VISION_BACKEND in order:
        chain = [VISION_BACKEND]
    else:
        raise ValueError(f"unknown VISION_BACKEND {VISION_BACKEND!r}")
    errors = []
    for name in chain:
        fn, t = order[name]
        try:
            return fn(png_bytes, user_prompt, timeout=t)
        except Exception as e:  # noqa: BLE001  (backend fallthrough)
            errors.append(f"{name}: {e}")
    raise ValueError("all vision backends failed: " + "; ".join(errors))


def _ask_vision_ollama(png_bytes: bytes, user_prompt: str, timeout: int = 120) -> dict:
    """Local Ollama vision path (see :func:`ask_vision`)."""
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": user_prompt,
                "images": [_image_payload(png_bytes)],
            },
        ],
        "stream": False,
        "options": {"temperature": 0.1},
    }
    req = urllib.request.Request(
        f"{OLLAMA_BASE}/api/chat",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    text = data["message"]["content"]
    return _parse_action_json(text)


def _ask_vision_remote(png_bytes: bytes, user_prompt: str, timeout: int = 120) -> dict:
    """OpenRouter fallback: screenshot + prompt -> parsed JSON action."""
    try:
        from backend.stl_verifier import ask_vision as remote_ask
    except Exception as e:
        raise ValueError(f"remote vision unavailable: {e}") from e
    text = remote_ask({"screen": png_bytes}, user_prompt, model=REMOTE_MODEL)
    if text.startswith("[ERROR]"):
        raise ValueError(text)
    return _parse_action_json(text)


def _ask_vision_chatgpt(png_bytes: bytes, user_prompt: str, timeout: int = 180) -> dict:
    """ChatGPT Desktop backend: paste the screenshot into the chat app, OCR
    the reply, and parse it as the action JSON.

    No API key needed - drives the installed desktop app via clipboard+paste
    (``desktop_chat.send_image``). Works on any machine with ChatGPT Desktop
    installed. Falls back to :func:`_ask_vision_remote` if the app window is
    not available.
    """
    from scripts.gui_automation import desktop_chat

    result = desktop_chat.send_image(
        "chatgpt",
        png_bytes,
        caption=user_prompt,
        wait_s=float(timeout),
    )
    if not result.get("sent"):
        raise ValueError(result.get("error", "chatgpt send failed"))
    text = result.get("response", "").strip()
    if not text:
        raise ValueError("chatgpt replied with empty OCR text")
    return _parse_action_json(text)


def _parse_action_json(text: str) -> dict:
    """Extract the first JSON object from the model reply and validate it."""
    # Strip code fences if the model added them despite instructions.
    text = re.sub(r"```(?:json)?", "", text).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError(f"no JSON object in model reply: {text[:200]!r}")
    try:
        obj = json.loads(text[start : end + 1])
    except json.JSONDecodeError as e:
        raise ValueError(f"model reply not valid JSON: {e}") from e
    if not isinstance(obj, dict):
        raise TypeError("model reply JSON is not an object")
    if obj.get("action") not in ALLOWED_ACTIONS:
        raise ValueError(f"disallowed action {obj.get('action')!r}")
    for key, typ in ACTION_JSON_FIELDS.items():
        if key not in obj:
            if key in ("text", "reason"):
                obj[key] = ""
            elif key == "verified":
                obj[key] = False
            elif key == "keys":
                obj[key] = []
            else:
                obj[key] = None
        if not isinstance(obj[key], typ):
            raise TypeError(f"bad type for {key}: {obj[key]!r}")
    return obj


def execute_action(action: dict) -> bool:
    """Run a parsed action via gui_driver. Returns True if it ran (or was done)."""
    name = action["action"]
    if name == "click":
        return gui_driver.click(float(action["x"]), float(action["y"]))
    if name == "type":
        gui_driver.type_text(action.get("text") or "")
        return True
    if name == "press":
        gui_driver.press(action.get("text") or action.get("keys") or "enter")
        return True
    if name == "hotkey":
        gui_driver.hotkey(*action.get("keys") or ["ctrl"])
        return True
    if name == "wait":
        time.sleep(3.0)
        return True
    return name == "done"


def _write_log(run_log: str, entry: dict) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(run_log)), exist_ok=True)
    with open(run_log, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def run_loop(
    task_prompt: str,
    verify: Callable[[], bool],
    run_log: str,
    max_steps: int = 15,
    screenshot_dir: str | None = None,
    region: tuple[int, int, int, int] | None = None,
) -> int:
    """Run the observe->decide->act->verify loop until verify() passes.

    Returns 0 on verified success, 1 if the model said done without
    verification, 2 if max_steps exhausted.
    """
    screenshot_dir = screenshot_dir or os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "test_output", "gui_agent"
    )
    for step in range(1, max_steps + 1):
        png = (
            gui_driver.capture_region_png(*region)
            if region
            else gui_driver.capture_png(downscale=1280)
        )
        shot_path = os.path.join(screenshot_dir, f"step{step:02d}.png")
        gui_driver.save_png(png, shot_path)

        prompt = (
            f"Task: {task_prompt}\nThis is step {step}. Decide the next single action. "
            "Reply with ONLY the JSON object."
        )
        action = ask_vision(png, prompt)
        _write_log(
            run_log,
            {"step": step, "shot": shot_path, "action": action},
        )
        print(f"[{step}] {action['action']} {action.get('reason', '')}")

        if action["action"] == "done":
            if action.get("verified") or verify():
                print("done (verified)")
                return 0
            print("model claims done but verification failed - forcing continue")
            continue

        if not execute_action(action):
            print("action vetoed by click gate - stopping")
            return 3

        time.sleep(1.0)
        if verify():
            print(f"verification PASSED after step {step}")
            return 0
    print("max steps exhausted")
    return 2


def main() -> int:
    ap = argparse.ArgumentParser(description="Local vision GUI agent (Fusion mesh repair).")
    ap.add_argument("--task", default="Repair the non-watertight mesh and export it as STL.")
    ap.add_argument("--max-steps", type=int, default=15)
    ap.add_argument("--log", default="test_output/gui_agent/run.jsonl")
    ap.add_argument("--shots", default=None, help="dir to save step screenshots")
    args = ap.parse_args()

    # Demo verify callback: place a file to signal manual success.
    def _verify() -> bool:
        return os.path.exists(os.path.join("test_output", "gui_agent", "done.txt"))

    return run_loop(args.task, _verify, args.log, max_steps=args.max_steps, screenshot_dir=args.shots)


if __name__ == "__main__":
    sys.exit(main())
