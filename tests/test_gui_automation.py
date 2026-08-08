"""Contract tests for the Fusion GUI automation package (scripts/gui_automation/).

These run headlessly - no Fusion, no clicks, no display interaction. They
cover the parts that are safe to verify without a GUI session:

- the non-watertight target generator must produce a mesh whose
  check_mesh_repair_gate fails (so the repair proof has something to fix),
- the action-JSON parser must accept valid model replies and reject malformed
  / disallowed actions,
- the black-frame detector must reject an all-black image and accept a
  normal one,
- gui_driver must clamp out-of-bounds coordinates to the screen.

The live screenshot->vision->click loop is NOT covered here (it needs the
human + Fusion at the GUI); that is exercised by fusion_mesh_repair_agent.py.
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.stl_verifier import check_mesh_repair_gate
from scripts.gui_automation import gui_driver
from scripts.gui_automation.make_nonwatertight_target import punch_hole
from scripts.gui_automation.vision_loop import (
    _ask_vision_remote,
    _parse_action_json,
    ask_vision,
    execute_action,
)

FUSION_OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "test_output", "fusion")
SOURCE_STL = os.path.join(FUSION_OUT, "koncovka_C.stl")


# --- action JSON parsing -------------------------------------------------


def test_parse_action_accepts_valid_click():
    obj = _parse_action_json('{"action":"click","x":100,"y":200,"reason":"hit export","verified":false}')
    assert obj["action"] == "click"
    assert obj["x"] == 100 and obj["y"] == 200


def test_parse_action_accepts_code_fenced_json():
    obj = _parse_action_json('```json\n{"action":"wait","reason":"dialog","verified":false}\n```')
    assert obj["action"] == "wait"


def test_parse_action_rejects_disallowed_action():
    with pytest.raises(ValueError):
        _parse_action_json('{"action":"rm_rf","reason":"nope","verified":false}')


def test_parse_action_rejects_non_json_reply():
    with pytest.raises(ValueError):
        _parse_action_json("sure, I'll click the button")


def test_parse_action_rejects_missing_required_types():
    # text must be a string; keys must be a list
    with pytest.raises(TypeError):
        _parse_action_json('{"action":"type","text":123,"reason":"bad","verified":false}')
    with pytest.raises(TypeError):
        _parse_action_json('{"action":"hotkey","keys":"ctrl","reason":"bad","verified":false}')


def test_parse_action_fills_defaults():
    obj = _parse_action_json('{"action":"done","reason":"all good"}')
    assert obj["verified"] is False
    assert obj["keys"] == []


# --- execute_action routing (no real clicks) ------------------------------


def test_execute_action_done_returns_true():
    assert execute_action({"action": "done", "reason": "x", "verified": False})


def test_execute_action_click_gate_can_veto(monkeypatch):
    gui_driver.set_click_gate(lambda _prompt: False)
    try:
        assert execute_action({"action": "click", "x": 10, "y": 10,
                               "reason": "x", "verified": False}) is False
    finally:
        gui_driver.set_click_gate(lambda _p: True)


# --- vision remote fallback -----------------------------------------------


def test_ask_vision_falls_back_to_remote_on_local_failure(monkeypatch):
    # Local Ollama request raises (timeout/refused) -> remote OpenRouter used.
    monkeypatch.setattr("urllib.request.urlopen", lambda *a, **k: (_ for _ in ()).throw(TimeoutError("local timed out")))

    def fake_remote(images, prompt, model=""):
        assert "screen" in images
        return '{"action":"wait","reason":"remote ok","verified":false}'

    monkeypatch.setattr("backend.stl_verifier.ask_vision", fake_remote)
    obj = ask_vision(b"pngbytes", "task")
    assert obj["action"] == "wait"


def test_ask_vision_remote_passes_through_errors(monkeypatch):
    def fake_remote(images, prompt, model=""):
        return "[ERROR] all vision models rate-limited or unavailable"

    monkeypatch.setattr("backend.stl_verifier.ask_vision", fake_remote)
    with pytest.raises(ValueError, match="rate-limited"):
        _ask_vision_remote(b"png", "task")


def test_ask_vision_remote_parses_action(monkeypatch):
    def fake_remote(images, prompt, model=""):
        return '{"action":"press","text":"enter","reason":"ok","verified":true}'

    monkeypatch.setattr("backend.stl_verifier.ask_vision", fake_remote)
    obj = _ask_vision_remote(b"png", "task")
    assert obj["action"] == "press"
    assert obj["text"] == "enter"


# --- gui_driver bounds clamping -------------------------------------------


def test_clamp_keeps_in_screen():
    w, h = gui_driver.screen_size()
    x, y = gui_driver._clamp(w * 10, h * 10)
    assert x < w and y < h
    x, y = gui_driver._clamp(-50, -50)
    assert x == 0 and y == 0


def test_capture_region_black_frame_detected():
    from PIL import Image
    img = Image.new("RGB", (200, 200), (0, 0, 0))
    with pytest.raises(RuntimeError):
        gui_driver._check_not_black(img)


def test_capture_region_accepts_normal_frame():
    from PIL import Image
    img = Image.new("RGB", (200, 200), (120, 120, 120))
    gui_driver._check_not_black(img)  # must not raise


# --- non-watertight target generator --------------------------------------

import numpy as np


def test_punch_hole_creates_nonwatertight_mesh():
    import trimesh

    src = trimesh.load(SOURCE_STL, force="mesh")
    fc = src.triangles_center
    bands = np.unique(np.round(fc[:, 2], 1))
    mid = float(bands[len(bands) // 2])
    wall_r = float(np.median(np.linalg.norm(fc[:, :2], axis=1)))
    punched = punch_hole(src, np.array([wall_r, 0.0, mid]), radius=12.0)
    assert len(punched.faces) < len(src.faces)
    assert punched.is_watertight is False


def test_target_gate_fails_as_intended():
    path = os.path.join(FUSION_OUT, "nonwatertight_target.stl")
    if not os.path.exists(path):
        pytest.skip("target not generated yet")
    gate = check_mesh_repair_gate(path)
    assert gate["passed"] is False
    assert gate["watertight"] is False
