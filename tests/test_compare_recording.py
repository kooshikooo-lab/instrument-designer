"""Tests for scripts/compare_recording.py (WAV vs TMM synthesis comparison).

Loaded standalone via importlib because scripts/ is not a package.
"""

import importlib.util
import json
import os
import sys

import pytest

_SCRIPT = os.path.join(os.path.dirname(__file__), "..", "scripts", "compare_recording.py")
_spec = importlib.util.spec_from_file_location("compare_recording", _SCRIPT)
compare_recording = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(compare_recording)

REPO_ROOT = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)


def _write_design(tmp_path, closed_top=False):
    design = {
        "inner_positions": [0.0, 600.0],
        "inner_diameters": [17.0, 17.0],
        "outer_diameter_mm": 22.0,
        "hole_positions": [],
        "hole_diameters": [],
        "hole_lengths": [],
        "closed_top": closed_top,
    }
    path = tmp_path / "design.json"
    path.write_text(json.dumps(design))
    return str(path)


def test_fingering_for():
    assert compare_recording.fingering_for(4, []) == ["closed"] * 4
    assert compare_recording.fingering_for(3, [0, 2]) == ["open", "closed", "open"]


def test_predict_pitch_open_pipe(tmp_path):
    inst = compare_recording.build_instrument(json.loads(open(_write_design(tmp_path)).read()))
    f0 = compare_recording.predict_pitch(inst, [])
    # 600mm open-open pipe -> c/2L ~= 286 Hz
    assert 270.0 < f0 < 300.0


def test_predict_pitch_closed_top(tmp_path):
    inst = compare_recording.build_instrument(
        json.loads(open(_write_design(tmp_path, closed_top=True)).read())
    )
    f0 = compare_recording.predict_pitch(inst, [])
    # 600mm closed-open -> c/4L ~= 143 Hz
    assert 125.0 < f0 < 160.0


def test_closed_loop_synth_then_compare(tmp_path):
    design = _write_design(tmp_path)
    wav = str(tmp_path / "pred.wav")
    out = str(tmp_path / "report.json")
    rc = compare_recording.main(
        ["--design", design, "--synthesize", wav, "--out", out]
    )
    assert rc == 0
    assert os.path.exists(wav)

    rc = compare_recording.main(
        ["--design", design, "--wav", wav, "--out", out]
    )
    assert rc == 0
    report = json.loads(open(out).read())
    assert 270.0 < report["predicted_f0_hz"] < 300.0
    assert report["measured_f0_hz"] is not None
    assert abs(report["pitch_cents_error"]) < 20.0
    assert report["harmonic_envelope_corr"] > 0.9
    assert report["harmonic_envelope_rmse"] < 0.05


def test_missing_inputs_rejected(tmp_path):
    design = _write_design(tmp_path)
    with pytest.raises(SystemExit):
        compare_recording.main(["--design", design])


def test_bad_design_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text(json.dumps({"bore_length_mm": 600.0}))
    with pytest.raises(ValueError):
        compare_recording.build_instrument(json.loads(bad.read_text()))
