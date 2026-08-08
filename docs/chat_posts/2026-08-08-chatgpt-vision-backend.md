[laptop] ChatGPT Desktop vision backend added to PR #68 (commit 120ba18).

The Fusion Phase 0.3 mesh-repair agent now has a working vision path with NO
API keys: capture the Fusion window -> set_clipboard_image (Win32 CF_DIB) ->
paste into ChatGPT Desktop -> Enter -> OCR reply -> parse action JSON.

- gui_driver.set_clipboard_image(): pure Win32 DIB clipboard (no subprocess).
- desktop_chat.send_image(app, png, caption=...): pastes the screenshot into
  the app window and reuses the existing PrintWindow+OCR reply polling.
  CLI: --image file.png [--caption "..."], --app chatgpt.
- vision_loop.ask_vision: VISION_BACKEND=auto|ollama|chatgpt|openrouter.
  auto = ollama -> chatgpt-desktop -> openrouter, tries next only on failure.
- Tests: 19 passed, system_audit ALL PASS, ruff clean on touched files.

Works on laptop (ChatGPT Desktop confirmed) and desktop (also has it). Desktop
needs a copy of the current `scripts/gui_automation/` (120ba18 or PR #68 head).
To run the mesh-repair proof: VISION_BACKEND=chatgpt python -m
scripts.gui_automation.fusion_mesh_repair_agent
