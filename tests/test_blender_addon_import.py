"""Headless Blender addon smoke test.

Skips entirely when Blender's `bpy` is not importable (the normal host-Python
case). When the tests are run inside Blender's bundled Python (or with a bpy
module on the path), verifies the addon registers and unregisters cleanly.
"""
import os
import sys

import pytest

_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _root)

bpy = pytest.importorskip("bpy")


def test_register_unregister_round_trip():
    import blender_addon

    blender_addon.register()
    try:
        assert hasattr(bpy.types.Scene, "id_server_url")
        assert hasattr(bpy.types.Scene, "id_preset")
        assert hasattr(bpy.types.Scene, "id_status")
        assert blender_addon.DEFAULT_PRESETS
    finally:
        blender_addon.unregister()
    assert not hasattr(bpy.types.Scene, "id_server_url")
    assert not hasattr(bpy.types.Scene, "id_preset")
    assert not hasattr(bpy.types.Scene, "id_status")


def test_operators_declared():
    import blender_addon

    ids = {cls.bl_idname for cls in blender_addon.CLASSES}
    assert "designer.check_health" in ids
    assert "designer.refresh_presets" in ids
    assert "designer.import_instrument" in ids
    assert "VIEW3D_PT_instrument_designer" in {cls.bl_idname for cls in blender_addon.CLASSES}
