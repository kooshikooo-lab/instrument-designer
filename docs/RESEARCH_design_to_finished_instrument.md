# RESEARCH — 3D Modeling/CAD, AI Tools, and Design-to-Finished-Instrument Pipeline

Status: **REFERENCE — saved for future work** (no code changes)
Date: 2026-08-05
Author: laptop (opencode)
Sources: live web research (2026-08-05) + existing repo docs
(`docs/ARCHITECTURE.md`, `docs/ARCHITECTURE_DECISIONS.md`, `docs/TOOLS.md`,
`wiki/3D-Printing-Guide.md`, `backend/cadquery_export.py`, `backend/stl_export.py`,
`backend/stl_verifier.py`) + prior research wiki pages (Metamaterials, Measurement, AI).

## Purpose

Capture research on the **design-to-finished-instrument pipeline** for 3D-printed
instruments: 3D modeling / CAD software choices, AI-assisted design tools, and the
full path from parametric bore + tonehole geometry to a physically playable,
acoustically verified instrument. This doc is *ideas and citations only*; it does not
change any code. Tool recommendations are tagged as either **adoptable-now** (already
in `pyproject.toml` or a natural fit for the existing stack) or **reference-only**
(interesting, but require the adopt-a-tool protocol from `docs/TOOLS.md`).

## TL;DR

The pipeline this project already implements — TMM bore/tonehole optimization →
CadQuery solids → STL → SLA print → post-processing → BIAS measurement — matches the
**state of the art** for 3D-printed instruments. Research findings:

1. **CAD layer (already good):** code-driven parametric CAD (CadQuery/OpenCASCADE)
   is the right choice for a design that is 100% parameterized from acoustic math.
   `Build123d` is the actively-maintained successor-style API and is the top
   alternative if we ever hit CadQuery ergonomic limits. **Do not** switch to a
   manual GUI CAD flow for the core path.
2. **Mesh stage (already good, one gap):** `stl_export.py` + `stl_verifier.py` use
   trimesh. The gap is **mesh repair/healing** before slicing — `pymeshlab`,
   `pymeshfix`, or `admesh` — not currently wired into the pipeline.
3. **AI tools (new, maturity varies):**
   - *LLM→CAD code generation* (CAD-Coder, CAD-Llama, Text2CAD, Zoo.dev) is real and
     open-source, but is a **developer accelerator**, not a drop-in generator for our
     acoustic-critical geometry. Our geometry already comes from physics; LLM CAD is
     for scaffolding/UI prototypes.
   - *ML surrogates* for the acoustic solver are the highest-value direction, but the
     project already tested JAX/dask surrogate warm-start on the shared benchmark
     contract and **rejected** it in favor of `topk_polish` + dask parallel eval.
     Reference for future, not a rerun.
   - *Gradient / adjoint geometry optimization* (Szwarcberg et al. 2025) is the
     most promising genuinely-new lever for the design stage.
4. **Fabrication (already good):** SLA resin + careful post-processing is the
   documented choice and matches published instrument-printing practice (MIT flute,
   Diegel saxophone). Small, sometimes-recommended additions: brim/lattice flexure
   hinge patterns, light external supports, bore reaming, and (for final instruments)
   a solvent/vapor or clear-coat seal.
5. **QA/tuning (the weakest link, highest value):** impedance-tube / BIAS
   measurement feedback into the TMM solver is the crux of "finished" quality.
   The project's measurement docs + OpenWInD are ahead of most hobby literature.
   Add **full-waveform inversion (bore reconstruction)** from measured impedance as
   a concrete next step.

## 1. Design stage: how instrument geometry gets defined

Published instrument-printing projects consistently use **parametric code CAD**, not
manual GUI modeling, because the geometry is a mathematical surface:

- **Olaf Diegel's 3D-printed saxophone** (University of Auckland, ~2011): a working
  alto sax printed in SLS nylon with 41 separate components (body, keys, springs,
  pads assembled post-print). The body was reverse-engineered from a real saxophone
  in **SolidWorks** from measured dimensions — the *CAD step was manual*
  (reverse-engineering a reference instrument), then the printed assembly was tuned.
  Demonstrates: multi-part, mechanically-assembled 3D-printed instruments are
  achievable; nylon SLS was chosen for toughness of keys/mechanisms.
- **MIT 3D-Printed Flute** (Amit Zoran, 2010–2011): a concert flute printed in one
  piece including its key mechanism; iterative re-prints adjusted hole geometry and
  wall thickness. Demonstrates: monolithic printing + **rapid acoustic iteration** —
  print → test → modify → reprint is a valid design loop, exactly our workflow.
- **Ernoult et al.** (hal-02479433): a **one-day design → 3D-print → musician
  feedback** loop for a clarinet mouthpiece/chamber, powered by impedance simulation.
  Demonstrates the tight loop we already run (TMM + print + BIAS).
- **CT-scan replica workflow** (MIT + MFA, 2026): CT-scan a historic instrument →
  reconstruct digital twin → reprint. Relevant for reproducing reference instruments
  the same way Diegel reverse-engineered the sax.

**Conclusion for the project:** keep the physics-first parametric approach. The CAD
question is *which code-CAD library*, not *whether to use CAD*.

## 2. 3D modeling / CAD software options

### 2.1 Code-driven (scripted, parametric) — fits this project

| Tool | Kernel | License | Verdict |
|---|---|---|---|
| **CadQuery** (current) | OpenCASCADE (BRep) | Apache-2.0 | Already in use (`backend/cadquery_export.py`). Solid, battle-tested. |
| **Build123d** | OpenCASCADE (BRep) | Apache-2.0 | Active successor-style API; more ergonomic (`Location`, `Align`, context builders). Top alternative. |
| **pythonOCC** | OpenCASCADE | LGPL | Lower-level; more boilerplate than CadQuery. Not recommended as a replacement. |
| **OpenSCAD** | CGAL mesh | GPL | Declarative CSG; excellent LLM target (see §3.3) but weaker for revolved/lofted BRep bores. |
| **JSCAD** | in-browser mesh | MIT | Already a candidate for the Tauri/UI arch; web-native but geometry is mesh (loses BRep precision). |
| **FreeCAD** | OpenCASCADE | LGPL | Already in stack (`freecad_backend.py`); GUI + scripting. Heavy; used for export/visualization. |
| **SolidWorks / Fusion 360** | proprietary | commercial | The Diegel path (manual reverse-engineering). Not for the core parametric path. |

Notes:
- **CadQuery vs Build123d:** both target OpenCASCADE. Build123d's `Location` model
  and context managers reduce a class of the transform bugs we already work around in
  `cadquery_export.py` (e.g. `.rotate().translate()` in `_cut_single_hole`). If we
  adopt Build123d it should be *incremental* — the two can coexist (both produce BRep
  → same `export_stl` path). CadQuery is still maintained.
- **FreeCAD** remains valuable as a **visualization / STEP handoff** layer (already
  used), not as the generator.
- For a **UI**, the existing architecture decision (Tauri + in-browser preview)
  favors **JSCAD for preview only** — render the exported mesh, never the source of
  truth.

### 2.2 Mesh and repair layer (pre-slicing)

STL is the handoff to slicing. The gap: STL from BRep can have
degenerate/non-manifold faces. Standards-track tools:

- **trimesh** (already used in `stl_export.py` / `stl_verifier.py`): load, inspect,
  boolean ops, watertight checks.
- **pymeshlab** (PyMeshLab): full mesh-processing pipeline (decimation, fairing,
  hole filling, cleaning) — same engine as MeshLab. **adoptable-now.**
- **pymeshfix**: fast hole-filling / intersection repair on top of
  libigl/TetGen. **adoptable-now.**
- **admesh**: classic STL repair utility, simple and battle-tested.
- **MeshLib / MeshLib Python**: industrial healing incl. self-intersections;
  heavier dependency.

Recommendation: add a **mesh-repair gate** (e.g. `pymeshlab` or `pymeshfix`) that runs
after `export_stl` and before slicing, so `stl_verifier` always sees a watertight,
manifold mesh. This is a *new tool → requires the adopt-a-tool protocol*
(`docs/TOOLS.md`: declare in `pyproject.toml`, import in live pipeline, test).

## 3. AI tools for instrument design

### 3.1 ML surrogates for the acoustic solver — HIGH VALUE but already evaluated

- **Ernoult et al. (hal-02479433)** and **Chabassier/Ernoult OpenWInD**
  (hal-02984478): iterative maker + numerical optimization loop; OpenWInD already in
  our stack for acoustic simulation.
- **MIT FDTD + ML** (thesis, 2021): 3D FDTD simulation + ML surrogate for wind
  instrument shape/tonehole placement.
- **Brass instrument ML + physics-based sound optimization** (hal-05529863,
  hal-05529717): ML proxy for brass tone.
- **npj Acoustics surrogate benchmarks** (2026): NN surrogates give ~10–100× speedup
  over FEM with training cost amortized over the optimization.

**Project status (from BOOT_STATE / REMINDERS):** the JAX TMM + dask surrogate
warm-start idea was **implemented and benchmarked on the shared contract, then
rejected** — `topk_polish` + parallel evaluation won on the contract metric. Do **not**
re-litigate this in a future session; treat ML surrogates as a *reference-only* idea
unless the contract changes.

### 3.2 LLM → CAD code generation — REAL, opensource, a developer accelerator

- **CAD-Coder** (Nafie et al., arXiv:2505.14646, MIT license): VLM fine-tuned to
  produce **CadQuery Python code** from images + text. Directly relevant because our
  CAD is already CadQuery Python.
- **CAD-Llama** (UPenn, 2025): LLM that outputs CAD command sequences for a custom
  kernel. Provenance/cad-dataset is the original CAD-code dataset.
- **Text2CAD** (arXiv:2409.17106): text → CAD commands with grounding; used by
  CAD-Llama.
- **Zoo.dev Text-to-CAD** (2025): commercial; OpenSCAD-flavored; tested against
  public benchmarks, OpenSCAD historically wins for LLM generation.
- **CAD-Genesis / multimodal CAD generation** (2025–2026): neural meshes + LLM
  layouts; research stage.

Honest read: these models generate *plausible* CAD for furniture/objects, not
acoustically-correct bores. For this project they are useful to **scaffold UI widgets
or test fixtures**, or to draft a new mechanism part (keys, brackets) for review —
never to generate the acoustically-critical bore. Treat as **reference / developer
accelerator**.

### 3.3 Gradient-based geometry optimization — most promising new lever

- **Szwarcberg, Vázquez, Chaigne et al.** (2025, grad-instrument): analytic
  sensitivity of a woodwind TMM model with respect to geometry → **gradient descent
  on hole positions/diameters directly**. This is *exactly* the shape of our
  problem (TMM → geometry → impedance → fitness). Our current optimizer is
  derivative-free (CMA-ES / topk_polish). Analytic gradients (or AD through the TMM,
  JAX already in repo) could converge faster. **High-value future work.**
- Sells the same message as §1: the acoustic model *is* the driver; the CAD is the
  downstream render.

### 3.4 Generative design / commercial

- **Autodesk Fusion generative design**: topology optimization; applies to
  *structural* parts (key mechanisms, mounts), not bores. Reference-only.

## 4. Fabrication stage

### 4.1 Technology choice — SLA confirmed

`wiki/3D-Printing-Guide.md` already specifies: SLA resin (25–50 µm layers),
vertical orientation, light external supports, bore reaming/sealing. Published
practice agrees:

- **SLA** gives the fine features + smooth bore needed for acoustics (and internal
  bores are hard to post-finish, so layer quality matters most there).
- **SLS nylon** (Diegel sax) is the choice when *mechanism toughness* dominates —
  keys, springs, pivots. For a fully-printed instrument with moving parts, SLS/MJF
  beats SLA; for a fixed-bore instrument, SLA wins.
- **FDM** is for prototyping only (layer steps in the bore are acoustically
  measurable and hard to smooth).

### 4.2 Design-for-AM rules that recur in the literature

- Print **vertically** (bore axis vertical) so tonehole interior surfaces get the
  cleanest layer orientation.
- Add **tonehole chamfers/undercuts** deliberately — an acoustic decision, not just
  cosmetic (published flute/recorder reprints tune hole edges).
- Support the bore interior minimally; **leave support-free air columns** where
  possible.
- For **leak-prone joints** (Diegel sax assembly): print mating parts with tight
  tolerance, use flexure-style detents, and ream bore joints after assembly.
- Wall thickness: published flutes/sax use ~1.5–3 mm walls — our default 3 mm is
  reasonable; die-wall compliance changes tone, so keep it uniform.

### 4.3 Post-processing / finishing

Current guide already covers washing, curing, reaming, sealing. Additions from
research:

- **Acetone/IPA smoothing** (FDM) — only for non-acoustic surfaces.
- **Clear UV coating / epoxy bore seal** on SLA bores to close micro-porosity and
  improve moisture resistance (flutes get wet); reduces surface-loss change after
  tuning.
- **Bore reaming with a tapered reamer + gauge** is the single highest-leverage
  finishing step: measured bore radius vs. design radius is what the acoustics
  assumes.

## 5. QA / tuning — the "finished" step

- **BIAS / impedance measurement** already in `wiki/Internal-Research-Measurement.md`.
  This is the authoritative feedback signal.
- **Acoustic pulse reflectometry (APR)**: reconstruct bore profile from an
  impedance/pressure measurement; used in flute/sax restoration; *also* the natural
  way to verify a print matches the design bore after reaming.
- **OpenWInD** (already in stack) provides the simulation side for the same
  impedance quantity — simulation-vs-measurement delta is the QA metric.
- **Tuning loop:** measure impedance → compare to target (TMM) → adjust hole
  geometry → re-print. MIT flute and Diegel sax both converged this way; our
  `topk_polish` + dask loop is the computational version of it.

## 6. Tool mapping to this repo

| Pipeline stage | Current repo tool | Candidate addition | Status |
|---|---|---|---|
| Geometry (math) | `backend/core/network.py` TMM | gradient/AD (Szwarcberg-style) | reference/future |
| CAD solid | `backend/cadquery_export.py` (CadQuery) | Build123d (optional, incremental) | optional |
| Mesh/handoff | `backend/stl_export.py` (trimesh) | — | done |
| Mesh repair | none (gap) | pymeshlab / pymeshfix | **adoptable-now** |
| STL verify | `backend/stl_verifier.py` (trimesh) | — | done |
| Slicing | external (PrusaSlicer / slicer) | — | external |
| Fabrication | SLA per `wiki/3D-Printing-Guide.md` | SLS/MJF for mechanisms | reference |
| Finishing | ream/seal per guide | APR bore verification | reference |
| Acoustic sim | OpenWInD | — | done |
| Tuning/opt | `topk_polish` + dask | gradient methods | reference/future |
| QA | BIAS impedance | APR bore reconstruction | reference |

## 7. Guardrails

- **Tool registry:** any *adopted* candidate (e.g. `pymeshlab`, `pymeshfix`) must be
  declared in `pyproject.toml`, imported by the live pipeline, and covered by tests
  (`scripts/toolcheck.py`, `tests/test_tool_registry.py`). Until then it is
  **reference-only**.
- **No regenerable artifacts committed** (STLs, mesh dumps, logs) — same rule as
  `test_output/`.
- **Do not re-open the surrogate-warm-start question** without a changed contract;
  the decision is recorded in `docs/session-logs/BOOT_STATE.md` / Discussion #23.
- This doc is ideas/citations; it changes no code. Adopting any tool is a separate
  task with its own tests.

## 8. References

- Olaf Diegel, 3D-printed saxophone project (University of Auckland, ~2011),
  https://www.olafdiegel.com
- A. Zoran, "The 3D Printed Flute" (MIT Media Lab, 2010–2011),
  https://www.media.mit.edu
- A. Ernoult et al., one-day design→print→feedback clarinet loop,
  https://hal.science/hal-02479433
- J. Chabassier, A. Ernoult, "Virtual Workshop OpenWinD",
  https://hal.science/hal-02984478
- E. Nafie et al., CAD-Coder, arXiv:2505.14646 (MIT license)
- CAD-Llama / Text2CAD, arXiv:2409.17106
- Zoo.dev Text-to-CAD, https://zoo.dev (OpenSCAD-flavored)
- Szwarcberg, Vázquez, Chaigne et al. (2025), gradient-based woodwind geometry
  optimization (grad-instrument project)
- MIT + MFA CT-scan instrument replica project (2026)
- npj Acoustics ML-surrogate benchmarks (2026)
- MIT FDTD + ML wind-instrument thesis (2021)
- hal-05529863 / hal-05529717: brass instrument ML + physics-based sound optimization
- 2024MTest..66..705K: ABS/PLA infill/cell-shape impedance-tube study (materials)
- Repo-internal: `docs/ARCHITECTURE.md`, `docs/TOOLS.md`,
  `wiki/3D-Printing-Guide.md`, `wiki/Internal-Research-Measurement.md`,
  `docs/session-logs/BOOT_STATE.md`
