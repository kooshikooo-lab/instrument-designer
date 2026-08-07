"""Fusion 360 trial — laptop-side generators + manifest/result contract tests.

The Fusion GUI steps (STEP import -> measure -> re-export, mesh repair) run
inside Fusion via the `adsk` API and cannot execute headlessly; they are
validated by the human-in-the-loop runbooks in docs/FUSION_360_30day_plan.md.
These tests cover what the laptop CAN verify without Fusion:

- the artifact generators (scripts/make_fusion_smoke_test.py,
  scripts/make_fusion_phase1_artifacts.py),
- the Phase-1 batch manifest contract the Fusion add-in consumes
  ({"files": [{"name", "step", "step_out", "stl_out", "expected_mm3"}, ...]}),
- the result-JSON contract the add-in produces for laptop-side verification
  ({"ok", "files": {name: {name, bodies, volume_mm3, expected_mm3, ok}}}).
"""
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from backend.stl_verifier import check_mesh_repair_gate

FUSION_OUT = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "test_output", "fusion"
)
PHASE1_OUT = os.path.join(FUSION_OUT, "phase1")

# Documented baseline from docs/FUSION_360_30day_plan.md (Phase 0.1).
KONCOVKA_VOLUME_MM3 = 73652.381
PHASE1_PRESETS = [
    "koncovka_C",
    "xaphoon_C",
    "fujara_G",
    "bass_chalumeau_C",
    "glissotar",
]

# Fields the Fusion add-in (phase0_automation.py `_run_phase1`) reads from
# each manifest entry.
MANIFEST_ENTRY_FIELDS = {"name", "step", "step_out", "stl_out", "expected_mm3"}

# Fields the laptop-side verification needs from the add-in's result JSON.
RESULT_FILE_FIELDS = {"name", "bodies", "volume_mm3", "expected_mm3", "ok"}


def _run_smoke():
    sys.path.insert(
        0,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"),
    )
    import make_fusion_smoke_test as smoke

    smoke.main()
    return smoke


def _run_phase1(monkeypatch, *presets):
    sys.path.insert(
        0,
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"),
    )
    import make_fusion_phase1_artifacts as phase1

    monkeypatch.setattr(sys, "argv", ["make_fusion_phase1_artifacts.py", *presets])
    phase1.main()
    return phase1


def _load_manifest():
    path = os.path.join(PHASE1_OUT, "phase1_trigger.json")
    assert os.path.exists(path), f"trigger manifest missing: {path}"
    with open(path, "r") as f:
        return json.load(f)


# --- Phase 0 smoke test generator ------------------------------------------


def test_smoke_generates_expected_artifacts():
    _run_smoke()
    for name in ("koncovka_C.step", "koncovka_C.stl", "xaphoon_C.stl"):
        path = os.path.join(FUSION_OUT, name)
        assert os.path.exists(path), f"missing artifact: {path}"
        assert os.path.getsize(path) > 0, f"empty artifact: {path}"


def test_smoke_koncovka_watertight_with_documented_volume():
    _run_smoke()
    path = os.path.join(FUSION_OUT, "koncovka_C.stl")
    gate = check_mesh_repair_gate(path)
    assert gate["passed"], gate
    assert gate["watertight"] is True
    assert gate["manifold"] is True
    assert gate["component_count"] == 1
    # Doc baseline (Phase 0.1): 73652.381 mm3; Fusion re-import measured
    # +0.04% (73682.914), so the laptop mesh volume is the reference.
    assert abs(gate["volume_mm3"] - KONCOVKA_VOLUME_MM3) / KONCOVKA_VOLUME_MM3 < 0.01


def test_smoke_koncovka_mesh_density_matches_baseline():
    import trimesh

    _run_smoke()
    m = trimesh.load(os.path.join(FUSION_OUT, "koncovka_C.stl"), force="mesh")
    # Doc baseline (Phase 0.1): 504 verts / 1008 faces.
    assert len(m.vertices) == 504
    assert len(m.faces) == 1008


def test_smoke_xaphoon_exists_and_is_valid_mesh():
    import trimesh

    _run_smoke()
    m = trimesh.load(os.path.join(FUSION_OUT, "xaphoon_C.stl"), force="mesh")
    assert len(m.faces) > 0
    assert m.volume > 0


# --- Phase 1 batch generator + manifest contract ----------------------------


def test_phase1_generates_all_presets_watertight(monkeypatch):
    _run_phase1(monkeypatch)
    for name in PHASE1_PRESETS:
        for ext in (".step", ".stl"):
            path = os.path.join(PHASE1_OUT, f"{name}{ext}")
            assert os.path.exists(path), f"missing {path}"
        gate = check_mesh_repair_gate(os.path.join(PHASE1_OUT, f"{name}.stl"))
        assert gate["passed"], f"{name}: {gate}"


def test_phase1_manifest_contract_fields_and_expected_volume(monkeypatch):
    import trimesh

    _run_phase1(monkeypatch)
    manifest = _load_manifest()
    assert set(manifest.keys()) == {"files"}
    files = manifest["files"]
    assert [e["name"] for e in files] == PHASE1_PRESETS
    for entry in files:
        assert set(entry.keys()) == MANIFEST_ENTRY_FIELDS, entry
        assert os.path.exists(entry["step"]), entry["name"]
        # expected_mm3 is the reference STL volume (the generator's own
        # `{name}.stl`); stl_out is where Fusion re-exports (not yet written
        # at manifest-creation time, so we check the reference instead).
        ref_stl = entry["step"].replace(".step", ".stl")
        assert os.path.exists(ref_stl), f"{entry['name']}: reference STL missing"
        m = trimesh.load(ref_stl, force="mesh")
        actual = float(m.volume)
        expected = float(entry["expected_mm3"])
        assert abs(actual - expected) / expected < 0.01, entry["name"]


def test_phase1_subset_presets_restricts_manifest(monkeypatch):
    _run_phase1(monkeypatch, "koncovka_C", "fujara_G")
    manifest = _load_manifest()
    assert [e["name"] for e in manifest["files"]] == ["koncovka_C", "fujara_G"]


def test_phase1_unknown_preset_raises(monkeypatch):
    with pytest.raises(SystemExit) as exc:
        _run_phase1(monkeypatch, "not_a_real_preset")
    assert "not_a_real_preset" in str(exc.value)


# --- Result-JSON contract produced by the Fusion add-in ---------------------


def _valid_result_sample():
    """Shape the add-in actually writes (see phase0_automation._run_phase1)."""
    return {
        "ok": True,
        "files": {
            "koncovka_C": {
                "name": "koncovka_C",
                "bodies": 1,
                "volume_mm3": 73682.914,
                "expected_mm3": 73652.381,
                "step_roundtrip_bytes": 7488,
                "stl_bytes": 10000,
                "mesh_import": {"ok": True, "mesh_bodies": 1},
                "ok": True,
            }
        },
    }


def test_result_contract_valid_sample_passes():
    _assert_result_contract(_valid_result_sample())


def test_result_contract_rejects_missing_file_fields():
    sample = _valid_result_sample()
    del sample["files"]["koncovka_C"]["volume_mm3"]
    with pytest.raises(AssertionError):
        _assert_result_contract(sample)


def test_result_contract_rejects_failed_file():
    sample = _valid_result_sample()
    sample["files"]["koncovka_C"]["ok"] = False
    with pytest.raises(AssertionError):
        _assert_result_contract(sample)


def _assert_result_contract(result):
    assert result["ok"] is True
    assert isinstance(result["files"], dict) and len(result["files"]) > 0
    for name, rec in result["files"].items():
        assert rec.get("name") == name
        assert RESULT_FILE_FIELDS.issubset(set(rec.keys())), rec
        assert rec["ok"] is True, rec
        assert rec["bodies"] == 1, rec
        assert rec["volume_mm3"] > 0, rec
