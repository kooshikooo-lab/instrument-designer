# Prompt: Claude Expert Advice on Fusion 360 GUI Automation via Local Vision Loop

**Date:** 2026-08-08
**Context:** `scripts/gui_automation/` — screenshot → local gemma4:12b vision → pyautogui actions → deterministic gate verification.

Copy everything below into Claude and ask for a focused review.

---

## Prompt

I run a computational woodwind-instrument-design project (Python, build123d/CadQuery). I have an Autodesk Fusion 360 30-day trial running on Windows. Most of my CAD pipeline is API-scriptable via a Fusion Python add-in (STEP import, measurement, STEP roundtrip, STL export, CAM probe all work headlessly). The one thing the Fusion API does NOT expose is the **mesh-repair command** (Mesh workspace: close hole, erase & fill) — it is GUI-only. I need to prove a non-watertight STL can be healed by Fusion's mesh tools so I can decide whether to keep Fusion as a repair-fallback leg of my mesh gate.

I'm experimenting with a lightweight "computer-use" loop to drive that GUI-only step, and I want your expert critique and recommendations.

### My current architecture (all Windows-native, no external API keys)

1. **Capture:** `mss` screen grab of the primary monitor (1920×1080), downscaled to max edge 1280, PNG bytes. Black-frame detector raises if mean<12 / std<8 (GPU-composited windows can BitBlt black).
2. **Vision:** local `gemma4:12b` via Ollama (`http://127.0.0.1:11434/api/chat`), `temperature 0.1`. System prompt + screenshot in `images: [base64]`. Model must reply with a single strict JSON object from a whitelist:
   - `click` (x,y screenshot-relative), `type` (text), `press` (key), `hotkey` (keys), `wait`, `done` (+ `verified` bool), plus `reason`.
   - I hard-validate the JSON shape and reject any action not in `{click,type,press,hotkey,done,wait}`.
3. **Execution:** `pyautogui` with coordinates clamped to screen bounds and a **human click-gate** (console confirm before every click by default) so the agent can't free-run.
4. **Verification:** the real loop-termination condition is NOT the model's opinion — it's my deterministic `check_mesh_repair_gate(path)` (watertight AND manifold AND single connected component via trimesh) run on the exported STL. Vision decides WHERE to click; numerics decide if it worked.
5. **Flow:** observe → decide → act → screenshot → verify; repeat until gate passes or max_steps (default 15–30).

### Files (in a repo, `scripts/gui_automation/`)

- `gui_driver.py` — mss capture (region/full, black-frame check), pyautogui click/type/press/hotkey, Win32 `activate_window(title)`, click gate.
- `vision_loop.py` — `ask_vision()` (Ollama chat with image), `_parse_action_json()` (extract+validate first JSON object), `execute_action()`, `run_loop(task, verify, run_log, max_steps)` writing a JSONL run log + step screenshots.
- `fusion_mesh_repair_agent.py` — waits for Fusion window, runs the loop with `verify=lambda: gate_passes(out_stl)`, prompts the model to switch to Mesh workspace, repair holes, export STL.
- `make_nonwatertight_target.py` — punches a hole through a known-good STL so the gate fails before repair (verified: `passed: False, watertight: False`).

### What I want from you (be specific, opinionated, prioritize)

1. **Will this reliably click Fusion's Mesh workspace buttons?** Fusion's ribbon is GPU-composited and dialogs are modal/overlayed — what are the concrete failure modes (black frames, wrong monitor DPI scaling, per-monitor DPI on Windows, coordinate-space mismatch between mss pixels and pyautogui?) and the best fixes (e.g. PrintWindow/PW_RENDERFULLCONTENT, monitor-DPI awareness via SetProcessDpiAwareness, `pyautogui`/`mss` coordinate alignment, scaling screenshots to model-native size)?

2. **Is `gemma4:12b` a good enough vision model for dense CAD UI (small buttons, tooltips, ribbon tabs)?** Would you instead: (a) OCR first (Windows `WinRT/OCR`, `pytesseract`, `easyocr`) and pass the text layer to the model, (b) use template/image matching (OpenCV `matchTemplate`) for stable ribbon icons, (c) rely on the accessibility tree (`pywinauto`/UIA) to find buttons by name and skip vision entirely for locatable controls, or (d) something else? Give a concrete recommended hybrid.

3. **Is the strict-JSON action protocol sound?** Critique my whitelist, the `done`+`verified` handling, temperature, and whether I should force the model to emit a confidence/uncertainty field or a "plan" before acting. Any prompt-engineering for UI agents that materially improves reliability?

4. **Safety & loop control:** are the click gate, coordinate clamp, and deterministic gate the right guardrails? What else would you add (max steps, same-state detection = no screen change → back off, hotkey fallback, screenshot hashing to detect loops)?

5. **Fusion-specific pitfalls:** modal dialogs stealing focus mid-loop, the File>Export dialog filename/format handling (STL ASCII vs binary), the Mesh workspace's "Make uniform"/"Close holes" commands actually existing in this build, undo (Ctrl+Z) recovery, and whether the repair can leave the mesh manifold-but-multi-component (which my gate would still reject).

6. **Bigger picture:** is GUI-driving Fusion even the right call versus alternatives — (a) asking a human to do the one-off repair manually, (b) using a headless mesh-healing library (trimesh/`pyMeshFix`/`admesh`) as the repair-fallback instead of Fusion, (c) just regenerating the CAD (build123d) so meshes are always watertight from the source? Where does GUI automation genuinely earn its keep vs. where it's a gimmick?

7. **OpenClaw / general agents:** I declined OpenClaw (heavy Node install, wants an Anthropic key) for this narrow task. Is that the right call, and is there a lightweight Windows-native alternative worth knowing?

Be concrete: name exact APIs, exact commands, and give the highest-leverage 3 changes first. Assume Windows 11, Python 3.14, no GPU preference, offline-first.
