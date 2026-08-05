# Instrument Designer — Blender Addon

Imports wind instruments from the Instrument Designer `design_server`
(default `http://127.0.0.1:8000`) directly into Blender as STL meshes.
Standard-library only — no pip dependencies inside Blender.

## Install

1. Blender > Edit > Preferences > Add-ons > Install from Disk
2. Select the `blender_addon` folder (or the repo root so it installs the package)
3. Enable **Import-Export: Instrument Designer**

If installing the folder fails, zip the `blender_addon` folder and install the zip.

## Usage

1. Start the design server: `python -m uvicorn woodwind_designer.engine.design_server:app --host 0.0.0.0 --port 8000`
2. In Blender's 3D Viewport open the Sidebar (**N**) > **Instrument Designer**
3. Leave the server URL as `http://127.0.0.1:8000` (or the laptop's Tailscale IP)
4. **Check Server** — verify connectivity
5. **Refresh Presets** — pull the instrument list from the server
6. Pick a preset and hit **Import Instrument**

Each import runs `POST /export/cadquery` and loads the returned STL mesh.

## Notes

- Uses `urllib`, so it works in Blender's bundled Python without installing `requests`.
- STL import uses `bpy.ops.wm.stl_import` (Blender 4.1+) with a fallback to
  `bpy.ops.import_mesh.stl` for older builds.
- Mesh-based (STL), not parametric — for dimensioned parametric editing use the
  FreeCAD workbench track instead.
