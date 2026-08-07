# Autodesk Fusion Personal Use Research - 2026-08-05

## Context
- Goal: evaluate Fusion (free "personal use" edition) as a manual, human-in-the-loop companion to the automated CAD/verification pipeline (build123d -> STL/STEP -> stl_verifier -> openwind/TMM).
- This is research ONLY. No integration work will start without user approval.

## TL;DR
- Fusion personal use is FREE but LIMITED (non-commercial only). Fine for this project (hobby/personal).
- No headless/CLI automation: the Python API runs INSIDE the Fusion GUI (UTILITIES > Add-Ins > Scripts and Add-Ins). Cannot be called from our pipeline.
- Useful as a MANUAL design review + mesh-repair + parametric hand-design tool, feeding STL/STEP back into the repo.
- NOT useful for acoustics/simulation (sim pre-processing locked in personal) - openwind/TMM stays the simulation path.

## License limits (personal use)
- Free, personal, non-commercial only. < $1,000 USD annual. Not for primary employment, company environments, or commercial training.
- No multi-user collaboration, forum support only, single-user data management.
- Limits: 10 active documents (archive to swap), single-sheet 2D drawings, limited CAM, limited electronics/PCB, limited import/export types, cloud rendering needs credits.

## What IS included (relevant)
- Parametric modeling (Design workspace), mesh tools, solid/brep editing.
- Export: STEP, STL, OBJ, 3MF, DXF.
- Import: mesh formats (STL/OBJ/3MF), STEP.
- Manufacturing workspace: 2/2.5/3-axis milling, turning, FFF additive (3D print slicing), water/laser/plasma.
- Local rendering.
- Python/JavaScript API (in-process scripts and add-ins).

## What is NOT included (relevant)
- Simulation pre-processing (locked, needs credits) - so no acoustic FEA in Fusion.
- Generative design (cloud, credits).
- 4/5-axis CAM, probing.
- Headless/command-line execution. Scripts only run from inside the GUI.
- Cloud rendering.

## API notes
- Fusion Python API: `adsk.core` + `adsk.fusion`, runs as an in-process script/add-in inside the open app.
- Example: STL export is scriptable via `adsk.core.exportManager` -> `createSTLExportOptions` -> `execute`.
- No way to drive Fusion from the outside; any script must be run manually by a human in the app. It is a GUI tool with a scripting surface, not an automation target.

## Mesh repair (relevant to our mesh-repair gate)
- Mesh workspace has Prepare > Repair, with repair types:
  - Close Holes
  - Stitch and Remove
  - One Touch Fix
  - Wrap
  - Rebuild
- Mesh > Convert to BRep converts a closed watertight mesh to a parametric solid.
- This gives a manual fallback path: if build123d is unavailable and pymeshlab/pymeshfix is not installed, a human can repair a mesh in Fusion and re-export a watertight STL.

## Suggested roles for this project (manual companion only)
1. Design review + measurement: open exported STEP/STL; Inspect > Measure, Section Analysis for wall thickness / bore dimensions. Complements automated stl_verifier (renders + LLM check).
2. Mesh repair fallback (human-in-the-loop): repair non-watertight meshes, re-export STL; or Convert to BRep.
3. Parametric hand-design of parts the code pipeline cannot easily generate (mouthpieces, keys/mounts, rings, ligatures, bells); export STL/STEP, drop into repo, feed back through pipeline for verification.
4. FFF additive print prep in Manufacturing workspace (optional; our pipeline already exports STL for external slicers).
5. CAM/CNC toolpaths (2/2.5/3-axis) if the project ever moves beyond 3D printing - long term, not needed now.

## What we should NOT use Fusion for
- Headless integration / automated pipeline steps (not possible).
- Acoustic simulation or FEA (locked in personal use; openwind/TMM remains the path).
- Multi-user collaboration or a replacement for the automated CAD flow.

## Open question for user
- Trial: import one of our exported STL parts (e.g. a candidate instrument) into Fusion and run the mesh Repair / measure flow, and export back to STL to confirm round-trip? Or just file this research and leave Fusion as an optional manual tool?

## Sources
- Autodesk: Fusion personal use FAQ/limitations (autodesk.com).
- Fusion API docs: adsk.core.exportManager STL export sample (autodesk.com).
- Fusion Mesh workspace repair documentation.
