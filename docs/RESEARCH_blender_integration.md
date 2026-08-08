# Blender Integration — Research (instrument-designer)

> Reference doc consolidating the existing Blender work and the integration
> options going forward. Status: REFERENCE, 2026-08-08 (desktop).

## 1. What already exists (do not rebuild)

| Piece | Location | Notes |
| --- | --- | --- |
| Blender addon (sidebar panel) | `blender_addon/` (`__init__.py`, `server_client.py`) | Imports instruments from `design_server` over HTTP as STL meshes. stdlib-only (`urllib`), so it runs in Blender's bundled Python with zero pip installs. Blender 4.0+; STL import handles 4.1+ and older builds. |
| One-click viewer | `scripts/view_instrument.py` (+ `launchers/view_instrument.bat`) | Auto-detects Blender (`BLENDER_EXE`, PATH, `C:\Program Files\Blender Foundation\*`). Commit `84b393e6`. |
| Headless import checker | `scripts/test_blender_import.py`, `scripts/_blender_import_check.py` | `blender -b` batch STL import validation. Commit `2e9d8174`. |
| Render-compare pipeline | `scripts/compare_stl_renders.py`, `tests/test_stl_render_compare.py` | STL render diffs; pillow declared in `cad` extra. Commit `fbb1ebae`. |
| Client tests | `tests/test_blender_server_client.py` (8) | bpy-free, monkeypatched urllib — run on host Python. |
| Addon tests | `tests/test_blender_addon_import.py` (2) | register/unregister round trip; skip-guarded on `bpy` (run only inside Blender). |
| Registry + tier | `docs/TOOLS.md` L100, `docs/TEST_MATRIX.md` §blender | Tier: **low**. Pass criteria defined. |

Design-server endpoints used: `GET /health`, `GET /export/cadquery/instruments`,
`POST /export/cadquery` (returns STL bytes). Server URL can be a Tailscale IP,
so a Blender session on one machine can pull from the other machine's server.

## 2. Integration options

### A. Current addon + design_server (mesh/STL) — KEEP
- Works today, zero deps, network-transparent (Tailscale).
- Mesh-based, not parametric — parametric editing remains the FreeCAD workbench
  track (per `blender_addon/README.md` note). That split stays.

### B. Headless CLI (`blender -b -P script.py`) — EXTEND
- Already proven by the import checker. Best fit for automated gates because it
  needs no GUI and no new Python deps.
- Candidate uses:
  1. **Mesh print-validation gate**: Blender ships the bundled *3D Print Toolbox*
     addon (`bpy.ops.mesh.print3d_check_all`) — non-manifold / watertight /
     overhang checks. This maps directly onto the mesh-repair gate decision in
     `docs/TOOLS.md` (2026-08-05: build123d-first + repair fallback; check-only
     gate "wireable with zero new deps"). Blender is already an adopted tool, so
     a headless print-check is a zero-new-dependency gate alongside
     `backend/stl_verifier.py` (trimesh). Repair itself stays pymeshlab/pymeshfix
     (declared, not adopted) — Blender's repair tools are manual/GUI-oriented.
  2. **Doc/wiki renders** of finalized instruments (off the render-compare base).

### C. `bpy` as a pip module (in-process Blender API) — NOT NOW
- Verified against PyPI (2026-08-08): `bpy` 4.2/4.5/5.0 require **Python ==3.11**;
  5.1/5.2 require **==3.13**. There is **no wheel for Python 3.12** — our desktop
  env (`py3.12`, repo `requires-python >=3.10`).
- Adopting it would mean a pinned side-venv (3.11 or 3.13) just for Blender calls
  — env complexity for no functional gain over (A)+(B). Revisit only if we need
  heavy in-process Blender scripting (we don't currently).

### D. glTF/STEP exchange — FUTURE, optional
- STL is lossy mesh. If we later want materials/colors/scene hierarchy in Blender,
  export glTF (CadQuery/build123d both export it) and add a glTF path to the addon.
- STEP import into Blender requires an importer addon (not bundled) — skip.

## 3. CI / risk notes

- Blender is **not** in CI (and shouldn't be — 300MB+ download, GUI-licensed
  binaries). All Blender-dependent tests stay skip-guarded; host-Python tests
  (`test_blender_server_client.py`) are the CI coverage.
- `bpy` import must never leak into host-Python modules outside `blender_addon/`
  (it only exists inside Blender). The import checker pattern (`-b -P`) is the
  sanctioned way to run bpy code.
- Blender is installed on desktop (`C:\Program Files\Blender Foundation`).
  Laptop WSL2 would need a Linux Blender build for headless use — trivial via apt.

## 4. Recommended next steps (small, in order)

1. **Headless print-check gate script** (`scripts/blender_print_check.py`):
   `blender -b -P blender_print_check.py -- file.stl` → exit 1 on
   non-watertight/non-manifold. Wires into the TOOLS.md mesh-repair gate as the
   zero-dep "check-only" option. Add a skip-guarded test + TEST_MATRIX row.
2. **Docs render target**: one-command "render this preset to PNG for the wiki"
   on top of the existing render pipeline.
3. Evaluate laptop-WSL2 headless Blender for compute-side render/check jobs.
4. (Only if a real need appears) glTF export path in the addon.

## 5. Non-goals

- No `bpy` pip dependency in the main env (version lock, see §2C).
- No parametric CAD inside Blender (FreeCAD workbench owns that).
- No Blender in CI runners.
