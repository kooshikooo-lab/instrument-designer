"""local_llm.py — LM Studio local LLM lifecycle (Gemma 4 on the desktop).

Locates the LM Studio ``lms`` CLI, starts the OpenAI-compatible local server
headless, and loads ``google/gemma-4-12b``. Also exposes thin chat helpers so
the vision verifier (stl_verifier) and the advisor (ai_advisor) can prefer the
local model and fall back to OpenRouter when it is unavailable.

Everything here is best-effort and self-contained: no local server, no CLI,
or a model that fails to load all degrade to ``False`` / ``[ERROR]`` instead of
raising, so callers keep working offline.

CLI::
    python -m backend.local_llm status      # report server/model state
    python -m backend.local_llm ensure      # start server + load Gemma 4
    python -m backend.local_llm chat "hi"   # one-shot local chat
"""

from __future__ import annotations

import glob
import json
import os
import shutil
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

LMSTUDIO_BASE = os.environ.get("LMSTUDIO_BASE_URL", "http://localhost:1234")
LMSTUDIO_API = LMSTUDIO_BASE + "/v1"
DEFAULT_MODEL = "google/gemma-4-12b"
LMSTUDIO_MODEL = os.environ.get("LMSTUDIO_MODEL", DEFAULT_MODEL)


def find_lms_cli() -> str | None:
    """Locate the LM Studio ``lms`` CLI executable (Windows first)."""
    env = os.environ.get("LMSTUDIO_BIN", "")
    if env and os.path.isfile(env):
        return env
    home = Path.home()
    candidates = [
        home / ".lmstudio" / "bin" / "lms.exe",
        home / "AppData" / "Local" / "Programs" / "LM Studio" / "lms.exe",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return str(c)
    for pattern in [
        str(home / ".lmstudio" / "bin" / "lms*"),
        str(home / "AppData" / "Local" / "Programs" / "LM Studio" / "lms*"),
    ]:
        for match in glob.glob(pattern):
            if os.path.isfile(match):
                return match
    return shutil.which("lms")


def server_ready(timeout: float = 2.0) -> bool:
    """True when the local OpenAI-compatible endpoint answers /v1/models."""
    try:
        req = urllib.request.Request(f"{LMSTUDIO_API}/models", method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except (urllib.error.URLError, TimeoutError, OSError):
        return False


def list_loaded_models() -> list[str]:
    """Model ids currently loaded by the local server (cached list)."""
    try:
        req = urllib.request.Request(f"{LMSTUDIO_API}/models", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read())
            return [m.get("id", "") for m in data.get("data", [])]
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return []


def _run_lms(args: list[str], timeout: int) -> bool:
    """Run the lms CLI without a console window. Returns exit success."""
    cli = find_lms_cli()
    if not cli:
        return False
    try:
        proc = subprocess.run(
            [cli, *args],
            capture_output=True,
            timeout=timeout,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        return proc.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def start_server() -> bool:
    """Start the LM Studio server headless. True once it answers."""
    if server_ready():
        return True
    _run_lms(["server", "start"], timeout=30)
    for _ in range(40):
        if server_ready():
            return True
        time.sleep(0.5)
    return server_ready()


def load_model(model: str = "") -> bool:
    """Load a model into the local server (idempotent). True when loaded."""
    model = model or LMSTUDIO_MODEL
    if model in list_loaded_models():
        return True
    _run_lms(["load", model], timeout=120)
    for _ in range(120):
        if model in list_loaded_models():
            return True
        time.sleep(0.5)
    return model in list_loaded_models()


def ensure_gemma(model: str = "") -> bool:
    """One-shot bring-up: server started + Gemma 4 loaded. True when ready."""
    model = model or LMSTUDIO_MODEL
    if model in list_loaded_models():
        return True
    if not server_ready():
        if not start_server():
            return False
    return load_model(model)


def chat(prompt: str, model: str = "", system: str = "",
         max_tokens: int = 2048, temperature: float = 0.3,
         timeout: float = 180.0) -> str:
    """Local text completion (OpenAI-compatible). Returns text or '[ERROR]'."""
    import requests

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    payload = {
        "model": model or LMSTUDIO_MODEL,
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        resp = requests.post(f"{LMSTUDIO_API}/chat/completions",
                             json=payload, timeout=timeout)
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        return msg.get("content") or ""
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {type(e).__name__}: {e}"


def chat_vision(images: dict[str, bytes], prompt: str, model: str = "",
                max_tokens: int = 2048, timeout: float = 300.0) -> str:
    """Local vision completion: {label: png_bytes} + prompt. Text or '[ERROR]'."""
    import base64

    import requests

    content = [{"type": "text", "text": prompt}]
    for label, png in images.items():
        b64 = base64.b64encode(png).decode()
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/png;base64,{b64}"},
        })
    payload = {
        "model": model or LMSTUDIO_MODEL,
        "messages": [{"role": "user", "content": content}],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    try:
        resp = requests.post(f"{LMSTUDIO_API}/chat/completions",
                             json=payload, timeout=timeout)
        resp.raise_for_status()
        msg = resp.json()["choices"][0]["message"]
        return msg.get("content") or ""
    except Exception as e:  # noqa: BLE001
        return f"[ERROR] {type(e).__name__}: {e}"


def status_report() -> str:
    """Human-readable one-line status."""
    models = list_loaded_models()
    return (
        f"lms_cli={find_lms_cli()}\n"
        f"api={LMSTUDIO_API}\n"
        f"server_ready={server_ready()}\n"
        f"loaded_models={models}"
    )


def _cli():
    import argparse

    parser = argparse.ArgumentParser(
        description="LM Studio local LLM lifecycle (Gemma 4)."
    )
    parser.add_argument("cmd", choices=["status", "ensure", "chat", "models"],
                        help="status/ensure/chat/models")
    parser.add_argument("args", nargs="*")
    ns = parser.parse_args()

    if ns.cmd == "status":
        print(status_report())
        return 0
    if ns.cmd == "ensure":
        ok = ensure_gemma()
        print("Gemma 4 ready." if ok else "Gemma 4 NOT ready — see status.")
        print(f"loaded_models={list_loaded_models()}")
        return 0 if ok else 1
    if ns.cmd == "models":
        print("models=" + ", ".join(list_loaded_models()) or "(none)")
        return 0
    if ns.cmd == "chat":
        text = " ".join(ns.args)
        if not text:
            print("usage: python -m backend.local_llm chat 'question'")
            return 2
        if not ensure_gemma():
            print("[ERROR] local server/model not available")
            return 1
        print(chat(text))
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(_cli())
