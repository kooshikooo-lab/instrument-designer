"""Pipeline for driving desktop chat apps (Claude Desktop, ChatGPT Desktop)
by clipboard+paste automation, and reading responses back with Windows OCR.

No API keys are needed: we focus the app window, paste a prompt into the
input box, press Enter, wait for the reply to finish, screenshot the last
message region, and OCR it back to text.

Session limits (Claude, researched 2026-08):
  - Free  ~20-30 msgs/day
  - Pro   ~45 msgs per rolling 5h window (~200/day)
  - Max5  ~225 msgs / 5h
  - Max20 ~900 msgs / 5h
  Counting is TOKEN-based not message-count, so long prompts/history consume
  more. A rolling-window tracker (see RollingWindow) records every send and
  refuses to fire past a configurable cap so we don't waste quota.

Usage:
    python -m scripts.gui_automation.desktop_chat --app claude --prompt "..." [--out dir]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))

from scripts.gui_automation import gui_driver  # noqa: E402

APP_TITLES = {
    "claude": "Claude",
    "chatgpt": "ChatGPT",
}
# Window subtitle used to disambiguate the main window from installers etc.
APP_EXCLUDE = {
    "chatgpt": "Installer",
}

OCR_PS1 = os.path.join(os.path.dirname(os.path.abspath(__file__)), "win_ocr.ps1")
STATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "test_output", "desktop_chat")


class RollingWindow:
    """Track sends in a rolling time window (e.g. 5h) to respect session caps."""

    def __init__(self, state_file: str, window_h: float, cap: int):
        self.state_file = state_file
        self.window_h = window_h
        self.cap = cap
        self.events = self._load()

    def _load(self) -> list[float]:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return [float(x) for x in json.load(f)]
            except (ValueError, OSError):
                return []
        return []

    def _save(self) -> None:
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)
        with open(self.state_file, "w") as f:
            json.dump(self.events, f)

    def prune(self, now: float) -> None:
        cutoff = now - self.window_h * 3600
        self.events = [t for t in self.events if t >= cutoff]
        self._save()

    def remaining(self) -> int:
        now = time.time()
        self.prune(now)
        return max(0, self.cap - len(self.events))

    def record(self) -> None:
        self.events.append(time.time())
        self._save()


def ocr_png(path: str) -> str:
    """OCR a PNG via Windows WinRT engine. Returns joined text."""
    if not os.path.exists(path):
        return ""
    try:
        out = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", OCR_PS1, path],
            capture_output=True, text=True, timeout=60,
        )
    except subprocess.TimeoutExpired:
        return ""
    lines = []
    for line in out.stdout.splitlines():
        if line.startswith("OCR|"):
            lines.append(line[len("OCR|"):])
    return "\n".join(lines)


def find_app_window(app: str) -> bool:
    title = APP_TITLES.get(app, app)
    exclude = APP_EXCLUDE.get(app, "")
    # enumerate all top-level windows, filter by title, reject exclusions
    import ctypes
    from ctypes import wintypes
    user32 = ctypes.windll.user32
    found = []

    @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    def _cb(hwnd, lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length == 0:
            return True
        buf = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buf, length + 1)
        t = buf.value
        if title.lower() in t.lower() and (not exclude or exclude.lower() not in t.lower()):
            found.append((hwnd, t))
        return True

    user32.EnumWindows(_cb, 0)
    if not found:
        return False
    # activate the most recent / largest main window
    gui_driver.activate_window(found[0][1])
    return True


def send_prompt(
    app: str,
    prompt: str,
    wait_s: float = 60.0,
    poll_s: float = 3.0,
    min_stable_s: float = 8.0,
    out_dir: Optional[str] = None,
) -> dict:
    """Send one prompt to the app and OCR the response.

    Returns {"prompt", "response", "shots": [...], "sent": bool}.
    The click gate is auto-approved only for the *input box* of the target
    app - we never approve arbitrary clicks.
    """
    out_dir = os.path.abspath(out_dir or os.path.join(STATE_DIR, app))
    os.makedirs(out_dir, exist_ok=True)

    if not find_app_window(app):
        return {"sent": False, "error": f"{app} window not found; is it running?"}

    # Put the prompt on the clipboard, focus input, paste, send.
    gui_driver.set_clipboard_text(prompt)

    gui_driver.activate_window(APP_TITLES[app])
    time.sleep(1.5)
    gui_driver.hotkey("ctrl", "v")
    time.sleep(0.5)
    gui_driver.press("enter")
    print(f"[{app}] sent prompt ({len(prompt)} chars)")

    # Poll the window until the reply is stable. We capture the app window via
    # PrintWindow (window_hwnd), which renders the window itself and so works
    # even when the terminal occludes it on screen.
    exclude = APP_EXCLUDE.get(app, "")
    hwnd = gui_driver.window_hwnd(APP_TITLES[app], exclude=exclude)
    if hwnd is None:
        return {"sent": True, "response": "", "shots": [],
                "error": f"{app} window disappeared after send"}
    last_text = ""
    stable_for = 0.0
    deadline = time.time() + wait_s
    shot_paths = []
    texts = []
    while time.time() < deadline:
        try:
            png = gui_driver.capture_window_png(hwnd)
        except RuntimeError:
            time.sleep(poll_s)
            continue
        shot = os.path.join(out_dir, f"shot_{len(shot_paths):03d}.png")
        gui_driver.save_png(png, shot)
        shot_paths.append(shot)
        text = ocr_png(shot)
        texts.append(text)
        if text == last_text and text.strip():
            stable_for += poll_s
            if stable_for >= min_stable_s:
                print(f"[{app}] response stable after {len(shot_paths)} polls")
                break
        else:
            stable_for = 0.0
        last_text = text
        time.sleep(poll_s)

    # Authoritative response: OCR of the last capture (loop exit may have hit
    # a transient empty read at deadline).
    if shot_paths:
        final = ocr_png(shot_paths[-1])
        if final.strip():
            last_text = final
    return {"sent": True, "response": last_text, "shots": shot_paths}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--app", choices=list(APP_TITLES), default="claude")
    ap.add_argument("--prompt", default="")
    ap.add_argument("--prompt-file", default=None)
    ap.add_argument("--wait", type=float, default=60.0)
    ap.add_argument("--min-stable", type=float, default=8.0)
    ap.add_argument("--out", default=None)
    ap.add_argument("--cap", type=int, default=40, help="max sends per rolling window")
    ap.add_argument("--window-h", type=float, default=5.0, help="rolling window hours")
    args = ap.parse_args()

    prompt = args.prompt
    if args.prompt_file:
        with open(args.prompt_file, "r", encoding="utf-8") as f:
            prompt = f.read()
    if not prompt.strip():
        print("no prompt")
        return 2

    window = RollingWindow(
        os.path.join(STATE_DIR, args.app, "window.json"),
        window_h=args.window_h,
        cap=args.cap,
    )
    print(f"[{args.app}] sends remaining in window: {window.remaining()}")
    if window.remaining() <= 0:
        print("session cap reached - stopping")
        return 1

    result = send_prompt(args.app, prompt, wait_s=args.wait, min_stable_s=args.min_stable, out_dir=args.out)
    result["model"] = args.app
    log_path = os.path.join(STATE_DIR, args.app, "log.jsonl")
    os.makedirs(os.path.dirname(log_path), exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(result) + "\n")
    if result.get("sent"):
        window.record()
    print(f"[{args.app}] response:\n{result.get('response', '')[:400]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
