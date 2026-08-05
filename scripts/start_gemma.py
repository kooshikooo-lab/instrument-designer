"""One-click: start the local LM Studio server headless and load Gemma 4.

Usage:
    python scripts/start_gemma.py            # ensure server + model ready
    python scripts/start_gemma.py --status   # report only, don't change state
    python scripts/start_gemma.py --chat "question"   # one-shot local chat
"""

import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from backend.local_llm import (  # noqa: E402
    chat,
    ensure_gemma,
    find_lms_cli,
    list_loaded_models,
    server_ready,
)


def main() -> int:
    if "--status" in sys.argv:
        print(f"lms CLI: {find_lms_cli()}")
        print(f"server ready: {server_ready()}")
        print(f"loaded models: {list_loaded_models()}")
        return 0

    if "--chat" in sys.argv:
        i = sys.argv.index("--chat")
        if i + 1 >= len(sys.argv):
            print("usage: start_gemma.py --chat 'question'")
            return 2
        if not ensure_gemma():
            print("Gemma 4 not ready (server or model load failed).")
            return 1
        print(chat(sys.argv[i + 1]))
        return 0

    if ensure_gemma():
        print("Gemma 4 ready.")
        print(f"loaded models: {list_loaded_models()}")
        return 0
    print("Failed to start local Gemma. Check the LM Studio install.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
