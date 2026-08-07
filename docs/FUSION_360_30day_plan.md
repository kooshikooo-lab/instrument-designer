# Fusion 360 — 30-Day Evaluation Plan

Status: **ACTIVE** (Phase 0 scriptable PASSED 2026-08-06; Phase 1 batch 5/5 PASS
2026-08-06; Phase-2 API probe 2026-08-06 — CAM scriptable surface confirmed,
Simulation absent; mesh-repair proof 0.3 still needs human GUI + a replacement
non-watertight target since xaphoon_C is watertight; laptop-side generators now
covered by `tests/test_fusion_360.py` 11 tests, 2026-08-07)
Owner: laptop (with human at the Fusion GUI)
Date: 2026-08-05
Related: `docs/RESEARCH_design_to_finished_instrument.md`, `docs/TOOLS.md` (mesh-repair gate), `wiki/3D-Printing-Guide.md`

## Purpose

Evaluate Autodesk Fusion 360 (30-day trial) as a **complementary** tool to the
code-CAD core (CadQuery / build123d). The code-CAD pipeline stays canonical
(parametric, versioned, repeatable); Fusion is evaluated for four jobs:

1. **Mesh repair + STL cleanup** — repair non-watertight preset/instrument
   meshes (e.g. xaphoon_C was 2624 verts / 5264 faces, NOT watertight in
   CadQuery before the audit C1 hole-cutter fix; it now exports watertight, so
   the Phase 0.3 repair-proof needs a genuinely non-watertight sample).
   This plugs directly into the mesh-repair-gate protocol in `docs/TOOLS.md`
   (build123d-first, repair-fallback).
2. **CAM / CNC toolpaths** — lathe/turning for bores + milling for tone holes.
   No machine yet, so this track is feasibility + saved toolpaths only.
3. **Simulation / modal FEA** — cross-check thin-wall body resonances against
   the TMM/acoustic models (which treat walls as rigid). Licensing caveat below.
4. **Manual CAD fallback** — hand-finish folded/paperclip geometries (bells,
   bends) that code-CAD does awkwardly, then export STEP back into the pipeline.

Fabrication equipment: **none yet** (planning only). Primary print path remains
SLA resin per `wiki/3D-Printing-Guide.md`; CNC is a future option.

## Environment

- Install: `Autodesk Fusion 360` v2704.1.36 (trial)
  - `C:\Users\koosh\AppData\Local\Autodesk\Autodesk Fusion 360\`
  - `C:\Users\koosh\AppData\Roaming\Autodesk\Autodesk Fusion 360\`
- Trial scope: full CAD + CAM + CAE + PCB access for 30 days.
- Python API (`adsk` module): add-ins/scripts run **inside** Fusion (app must be
  open). **Mesh repair is NOT exposed in the API** (Autodesk forum, 2023) —
  repair is a manual Mesh-workspace action; text-command workaround exists but
  is not scriptable via Python. Expect a manual/GUI-assisted batch workflow.
- Simulation: base-trial simulation studies may require the Simulation
  Extension or Flex tokens; verify included scope before investing in 2c.
- **Phase-2 API probe (2026-08-06, automated via the add-in, `phase2_result.json`):**
  both `adsk.cam` and `adsk.sim` modules exist in this build. **CAM**:
  `CAMManager.get()` returns a valid manager (post engine + library manager
  present); the `CAM` product exposes `setups`, `generateAllToolpaths`,
  `getMachiningTime`, `generateSetupSheet` → toolpath automation is scriptable in
  principle. **Simulation**: no `SimulationProductType` product in the document →
  not available in this trial without extension activation (2c stays
  license-gated). API notes: this build's `Products` has no `itemById` and
  `Product` has no `.name` — enumerate via `.count`/`.item(i)` + `productType`.

## Phase 0 — Smoke test (days 1–2) — gates deeper Fusion investment

Goal: prove the two highest-value flows in ~30 minutes of GUI time, then hand
results back to the laptop for the A/B/C workstreams.

### 0.1 Generate smoke-test artifacts (laptop — done)

```
python scripts/make_fusion_smoke_test.py
```

Writes to `test_output/fusion/` (gitignored):
- `koncovka_C.step`  — clean no-hole solid (volume reference, STEP round-trip)
- `koncovka_C.stl`   — watertight STL reference (504 verts / 1008 faces)
- `xaphoon_C.stl`  — 7-hole mesh; watertight since the audit C1 hole-cutter fix
  (2993 verts / 6014 faces). NOT a repair proof target anymore.

Baseline (laptop-verified, 2026-08-06): koncovka_C watertight (504v/1008f,
volume 73652.381 mm³); xaphoon_C NOT watertight (2624v/5264f).
**2026-08-07 update:** the audit C1 fix (centered hole cutter) made xaphoon_C
watertight (2993v/6014f, mesh-repair gate PASS). The Phase 0.3 repair-proof
target must be a different, genuinely non-watertight sample (see below).

**Automation (2026-08-06):** scriptable parts of Phase 0 are automated in
`test_output/fusion/fusion_phase0_smoke.py` (staged in Fusion as
`phase0_smoke_test` under MyScripts/ManuallyInstalled). It imports the STEP,
reports body count + volume, and re-exports STEP + STL round-trip artifacts.
Mesh repair (xaphoon) remains manual (not in the Fusion API).

### 0.2 STEP round-trip (automated 2026-08-06 — PASS)

Fully automated via the `phase0_automation` add-in (no GUI steps needed):

1. File > Open, select `test_output/fusion/koncovka_C.step`. (add-in import)
2. Measure volume via the API (`BRepBody.volume`, returned in **cm³**).
3. Save As STEP → `test_output/fusion/koncovka_C_roundtrip.step`.
4. Export STL → `test_output/fusion/koncovka_C_from_fusion.stl`.
5. **Result (PASS):** 1 body, 73682.914 mm³ vs expected 73652.381 mm³
   (+0.04%); round-trip STEP 7488 B; re-exported STL 696v/1392f watertight AND
   manifold (`check_mesh_repair_gate` PASS), bbox 20×20×651.5 mm unchanged;
   mesh volume 72844.11 mm³ (~1.1% tessellation loss at default refinement).

### 0.3 Mesh repair proof (human in Fusion GUI — still open)

**Status 2026-08-07:** xaphoon_C is now watertight (C1 fix), so it can no longer
serve as the repair proof target. Pick a replacement sample: one of the ~57
gitignored output STLs that is genuinely non-watertight (find via
`python -m backend.stl_verifier --all` / the Phase-2a sweep), or deliberately
degrade a clean STL (e.g. delete a face in a mesh editor). Then:

1. Insert the chosen STL (File > Insert > Mesh).
2. Mesh workspace > Modify > Repair (Close Holes / Stitch-and-Remove; enable
   "Close holes" at default tolerance, then "Rebuild" if needed).
3. Export as STL → `test_output/fusion/<name>_repaired.stl`.
4. Save the repaired mesh also as a component to measure volume.
5. Pass criteria: repaired STL passes the laptop verification step below.

### 0.4 Verify repaired/exported STLs (laptop — runs on the files you save)

```
python -m backend.stl_verifier test_output/fusion/koncovka_C_from_fusion.stl --no-vision
python -m backend.stl_verifier test_output/fusion/<name>_repaired.stl --no-vision
```

Report the `watertight=...` and `volume_mm3` lines back to #23.

2026-08-06 automated check: `koncovka_C_from_fusion.stl` — watertight=true,
manifold=true, 72844.11 mm³ → **PASS** (posted as `discussioncomment-17919778`).

### 0.5 Exit criteria for Phase 0

- One STEP round-trips (0.2) with volume intact. — **DONE (automated, +0.04%).**
- One non-watertight mesh becomes watertight via Fusion (0.3) and passes `verify_stl`. — **OPEN (human GUI; needs a replacement non-watertight target since xaphoon_C is now watertight).**
- Automation posture recorded (what can be scripted vs manual). — **DONE (below).**
- Findings appended to this doc; status post to #23; then proceed to Phase 1.

**Automation posture (2026-08-06):** scriptable = STEP import, body/volume
measure, STEP/STL export, mesh import, CAM manager + toolpath-generation API
surface (CAM product activation probe pending). Not scriptable = mesh repair
(GUI-only, not exposed in the Fusion Python API), simulation (product absent in
this trial — license/extension-gated), manual CAD (human). Mechanism =
`phase0_automation` add-in in `%APPDATA%\Autodesk\Autodesk Fusion 360\API\AddIns\`
(JSON manifest `"type":"addin"`, `runOnStartup:true`) triggered by a file watch;
work runs on a background thread after a 15 s startup delay (synchronous work in
the startup `run()` crashes Fusion).

## Phase 1 — A/B/C code workstreams (laptop; not gated on Fusion outcome)

Runs in parallel with the trial; these are needed regardless of the Fusion
verdict. See `docs/session-logs/BOOT_STATE.md` for details.

- **A. Check-only mesh gate** — watertight + manifold checks in
  `backend/stl_verifier.py`, called from `backend/cadquery_export.export_stl`;
  new whitelisted test `tests/test_mesh_repair_gate.py`.
- **B. build123d backend module** — `backend/build123d_export.py` mirroring
  `generate_instrument` (cylindrical + tone-hole path) using build123d 0.11
  `Pos(...) * part`; parity tests vs CadQuery (koncovka_C / fujara_G / xaphoon_C).
- **C. Metamaterial test gap** — whitelist the 8 `tests/test_metamaterial*.py`
  files in `pyproject.toml`; run; fix real bugs only.
- **L2-vs-L1 parity sweep** — `test_level1_vs_level2_fundamental_parity` across
  all `LOW_CLARINETS` keys; report deviations.

## Phase 2 — Deeper Fusion evaluation (trial weeks 2–4, background)

- **2a. Mesh-repair library sweep** — batch-repair the ~57 gitignored STLs
  across `output/`, `test_output/`, `instrument-designer/`,
  `metamaterial_low_clarinets/`; re-verify each with `verify_stl`; commit only
  the report (repaired STLs stay regenerable/untracked). Feeds the
  repair-fallback leg of the mesh-repair gate.
  **Status (2026-08-06):** repair itself is GUI-only. But the **STEP→Fusion→STL
  re-export path is fully scriptable (Phase 1, 5/5 gate PASS)** and heals meshes
  for STEP-source artifacts; STL-source artifacts (no STEP) still need the GUI
  Mesh workspace. Phase 1's batch add-in already does the scriptable leg.
- **2b. CAM / CNC feasibility** — import STEP, set up lathe/turning for the bore
  + milling/drilling for tone holes, post-process to a generic post, save CAM
  files; document feeds/speeds and machine constraints for resin/wood/POM.
  Deliverable is a feasibility file + toolpath plan (no machine to run it).
  **Status (2026-08-06):** `CAMManager` reachable via API + `CAM` product has
  `setups`/`generateAllToolpaths`/`getMachiningTime`/`generateSetupSheet` → a
  headless CAM probe (create setup → generate toolpath → post) is the next
  scriptable test; needs a CAM-product activation probe before committing to
  the sweep.
  **Status (2026-08-07):** add-in now dispatches `phase2b_trigger.json` →
  `_run_phase2b` (defensive probe: finds `CAMProductType`, enumerates
  setups/operations, probes `createInput`; records everything in
  `phase2b_result.json`, never crashes Fusion). Toolpath generation itself still
  needs confirmed stock/CS/tooling params from the human at the GUI. The
  result-JSON contract is covered by `tests/test_fusion_360.py`
  (`test_cam_probe_*`, 4 tests). **Next:** human creates `phase2b_trigger.json`
  and runs a Fusion session; laptop verifies `phase2b_result.json`.
- **2c. Simulation / modal FEA** — modal analysis on a thin-wall tube body;
  compare body resonances vs the rigid-wall TMM assumption. Bounded effort:
  verify trial licensing first (Simulation Extension / Flex tokens).
  **Status (2026-08-06):** **BLOCKED — no `SimulationProductType` product in
  the document** (probe confirmed). Do not invest until the Simulation
  Extension is confirmed available; revisit before trial end.
- **2d. Manual CAD fallback proof** — hand-model one folded/paperclip geometry
  (bells, bends) in Fusion; STEP-export back; document when to use the manual
  path over code-CAD. **Status (2026-08-06):** inherently manual (human), but
  STEP export back into the pipeline is scriptable (proven in Phase 0/1).

## Phase 3 — Checkpoints & decision (end of trial)

- Weekly status posts to #23 (smoke-test results, A/B/C completion, sweep
  results, Fusion track progress).
- End-of-trial decision write-up in this doc: keep SLA code-CAD pipeline as
  core; adopt Fusion for mesh repair + future CAM once equipment exists;
  document trial/extension costs.

## Constraints

- Work on `opencode/build123d/laptop` (or a side branch); AUDIT-tag exploratory
  commits. No pushes to `main` while desktop is offline (PR #62, team_chat.py
  fixes D are desktop's / held).
- Repaired STLs, STEPs, CAM files, and reports-under-test are regenerable and
  **never committed** (`*.stl`, `output/`, `test_output/*.stl` are gitignored).
  Only docs/decisions are tracked.
- New pytest files must be whitelisted in `pyproject.toml` `python_files`.
- `scripts/toolcheck.py` must stay clean; no secrets in commits.

## Research findings log

- 2026-08-05: Fusion 30-day trial = full CAD/CAM/CAE/PCB access (Autodesk).
- 2026-08-05: Fusion Python API does not expose the mesh-repair command
  (Autodesk forum 2023); repair is manual Mesh-workspace work. STEP import and
  STL export are scriptable.
- 2026-08-05: v2704.1.36 installed; trial began.
- 2026-08-06: Add-in auto-load requires `%APPDATA%\...\API\AddIns\<name>\` with a
  **JSON** manifest (`"type":"addin"`, `runOnStartup:true`); `MyScripts\Autorun`
  alone does not load and XML manifests are rejected on this build.
- 2026-08-06: Synchronous import/export inside the add-in's startup `run()`
  crashes Fusion (Qt6WebEngineCore); a background thread + ~15 s startup delay is
  stable.
- 2026-08-06: `app.exportManager` does not exist; `exportManager` is exposed on
  `Design` (adsk/fusion.py:48042). `app.importManager` is on `Application`.
- 2026-08-06: `BRepBody.volume` returns cm³ (×1000 → mm³); there is no `Timer`
  class in this build's API.
- 2026-08-06: Fusion re-exports a watertight/manifold STL from an imported STEP
  solid (696v/1392f, gate PASS). STEP is confirmed as the interchange format.
- 2026-08-06: Phase 1 batch add-in proves the STEP→Fusion→STL heal generalizes:
  all five geometry families (cylindrical, open-open holed, closed-top cap,
  8-hole closed-open, conical) re-export watertight + manifold + single
  component (gate PASS); Fusion volumes +0.03–0.19% vs cadquery solids; Fusion
  STL tessellation volume loss 0.3–1.1%.
- 2026-08-06: Fusion accepts non-watertight STL as a mesh import without warning;
  mesh repair is GUI-only (not API-exposed).
- 2026-08-06: Phase-2 probe — `adsk.cam` + `adsk.sim` modules present;
  `CAMManager.get()` works (post engine + library manager); `CAM` product has
  toolpath API (`setups`, `generateAllToolpaths`, `getMachiningTime`).
  Simulation product **absent** from the document (license-gated). `Products`
  has no `itemById` (iterate `.count`/`.item(i)`); `Product` has no `.name`.
- 2026-08-06: `CAMManager.manufacturingModels` does not exist on this build —
  `ManufacturingModels` is accessed via the `CAM` product (defs line 8024).
- 2026-08-07: xaphoon_C now exports watertight (audit C1 hole-cutter fix) —
  the Phase 0.3 mesh-repair proof needs a genuinely non-watertight sample.
- 2026-08-07: `tests/test_fusion_360.py` (whitelisted) covers the laptop-side
  generators: smoke artifacts + baseline, Phase-1 manifest contract (fields the
  add-in consumes), subset/unknown-preset handling, and the add-in result-JSON
  contract for laptop verification (11 tests).
- 2026-08-07: Phase 2b CAM probe automation staged in the add-in:
  `phase2b_trigger.json` → `_run_phase2b` (defensive capability probe — CAM
  product activation, setups/operations enumeration, `createInput` probe;
  result → `phase2b_result.json`, never raises into Fusion). Contract covered
  by 4 `test_cam_probe_*` tests (15 total in the module).
