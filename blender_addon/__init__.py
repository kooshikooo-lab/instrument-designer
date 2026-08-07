"""
Instrument Designer Blender addon.

Imports wind instruments from the Instrument Designer design_server
(http://127.0.0.1:8000 by default) directly into Blender as STL meshes.

Install: Blender > Edit > Preferences > Add-ons > Install from Disk > select
this folder's parent (blender_addon/). Enable "Import-Export: Instrument Designer".

Dependencies: none (standard library only).
"""

bl_info = {
    "name": "Instrument Designer",
    "author": "kooshikooo-lab",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > Sidebar > Instrument Designer",
    "description": "Import woodwind instruments from the design_server",
    "category": "Import-Export",
}

import os
import tempfile

import bpy

from . import server_client

PRESET_CACHE = {}
DEFAULT_PRESETS = [
    ("koncovka_C", "Koncovka in C (Overtone Flute)", ""),
    ("glissotar", "Glissotar (Glissando Reed)", ""),
    ("soprano_sax", "Soprano Saxophone Bb (Template)", ""),
]


def _status(context, text: str):
    context.scene.id_status = text
    print("[Instrument Designer]", text)


def preset_items(self, context):
    if PRESET_CACHE:
        return [
            (key, f"{display} ({key})", "")
            for key, display in PRESET_CACHE.items()
        ]
    return list(DEFAULT_PRESETS)


class DESIGNER_OT_check_health(bpy.types.Operator):
    bl_idname = "designer.check_health"
    bl_label = "Check Server"
    bl_description = "Ping the design_server /health endpoint"

    def execute(self, context):
        url = context.scene.id_server_url
        try:
            info = server_client.health(url)
            _status(context, f"OK: {info.get('status')} v{info.get('version')}")
            self.report({"INFO"}, f"Server healthy: {info}")
        except server_client.ServerError as e:
            _status(context, f"FAIL: {e}")
            self.report({"ERROR"}, str(e))
        return {"FINISHED"}


class DESIGNER_OT_refresh_presets(bpy.types.Operator):
    bl_idname = "designer.refresh_presets"
    bl_label = "Refresh Presets"
    bl_description = "Pull the instrument list from /export/cadquery/instruments"

    def execute(self, context):
        url = context.scene.id_server_url
        try:
            data = server_client.list_cadquery_instruments(url)
            PRESET_CACHE.clear()
            for key, meta in data.items():
                PRESET_CACHE[key] = meta.get("display_name", key)
            _status(context, f"Loaded {len(PRESET_CACHE)} presets")
            self.report({"INFO"}, f"{len(PRESET_CACHE)} presets loaded")
        except server_client.ServerError as e:
            _status(context, f"FAIL: {e}")
            self.report({"ERROR"}, str(e))
        return {"FINISHED"}


class DESIGNER_OT_import_instrument(bpy.types.Operator):
    bl_idname = "designer.import_instrument"
    bl_label = "Import Instrument"
    bl_description = "POST the selected preset to /export/cadquery and import the STL"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        url = context.scene.id_server_url
        preset = context.scene.id_preset
        if not preset:
            _status(context, "No preset selected")
            self.report({"ERROR"}, "Select a preset first")
            return {"CANCELLED"}

        try:
            stl_bytes = server_client.fetch_instrument_stl(url, preset)
        except server_client.ServerError as e:
            _status(context, f"FAIL: {e}")
            self.report({"ERROR"}, str(e))
            return {"CANCELLED"}

        if not stl_bytes:
            _status(context, "Server returned an empty STL")
            self.report({"ERROR"}, "Empty STL from server")
            return {"CANCELLED"}

        fd, tmp_path = tempfile.mkstemp(suffix=".stl", prefix=f"{preset}_")
        with os.fdopen(fd, "wb") as f:
            f.write(stl_bytes)

        before = set(bpy.data.objects)
        try:
            if hasattr(bpy.ops.wm, "stl_import"):
                bpy.ops.wm.stl_import(filepath=tmp_path)
            else:
                bpy.ops.import_mesh.stl(filepath=tmp_path)
        finally:
            try:
                os.remove(tmp_path)
            except OSError:
                pass

        new_objects = [o for o in bpy.data.objects if o not in before]
        if new_objects:
            bpy.ops.object.select_all(action="DESELECT")
            for o in new_objects:
                o.select_set(True)
            if context.view_layer.objects.active not in new_objects:
                context.view_layer.objects.active = new_objects[0]
            _status(context, f"Imported {preset}: {len(new_objects)} object(s)")
            self.report({"INFO"}, f"Imported {preset}")
        else:
            _status(context, f"Imported {preset} but no new objects found")
            self.report({"WARNING"}, "Import produced no objects")
        return {"FINISHED"}


class VIEW3D_PT_instrument_designer(bpy.types.Panel):
    bl_label = "Instrument Designer"
    bl_idname = "VIEW3D_PT_instrument_designer"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Instrument Designer"

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        layout.prop(scene, "id_server_url")
        row = layout.row(align=True)
        row.operator("designer.check_health")
        row.operator("designer.refresh_presets")
        layout.prop(scene, "id_preset")
        layout.operator("designer.import_instrument", icon="IMPORT")
        layout.separator()
        layout.label(text="Status: " + scene.id_status)


CLASSES = [
    DESIGNER_OT_check_health,
    DESIGNER_OT_refresh_presets,
    DESIGNER_OT_import_instrument,
    VIEW3D_PT_instrument_designer,
]


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.id_server_url = bpy.props.StringProperty(
        name="Server URL",
        default="http://127.0.0.1:8000",
    )
    bpy.types.Scene.id_preset = bpy.props.EnumProperty(
        name="Preset",
        description="Instrument preset to import",
        items=preset_items,
    )
    bpy.types.Scene.id_status = bpy.props.StringProperty(
        name="Status",
        default="Not connected",
    )


def unregister():
    del bpy.types.Scene.id_status
    del bpy.types.Scene.id_preset
    del bpy.types.Scene.id_server_url
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
