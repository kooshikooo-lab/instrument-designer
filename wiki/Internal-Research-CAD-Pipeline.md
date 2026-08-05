# Research — 3D Modeling/CAD, AI Tools, and Design-to-Finished-Instrument Pipeline

> Source: `docs/RESEARCH_design_to_finished_instrument.md` (2026-08-05, laptop). Status: REFERENCE — no code changes.

## Key Takeaways

The project's pipeline — TMM optimization → CadQuery solids → STL → SLA print → post-processing → BIAS measurement — **matches the state of the art** for 3D-printed instruments.

## CAD Layer

- **Code-driven parametric CAD (CadQuery/OpenCASCADE)** is the right choice for geometry 100% parameterized from acoustic math. Do not switch the core path to manual GUI CAD (SolidWorks/Fusion reverse-engineering is the Diegel-sax path, not ours).
- **Build123d** (Apache-2.0, OpenCASCADE): actively-maintained successor-style API; top alternative if CadQuery ergonomics are hit. Can coexist incrementally (both emit BRep → same `export_stl`).
- **JSCAD**: preview-only in the Tauri UI (mesh render, never source of truth).
- **FreeCAD**: stays the visualization/STEP handoff layer.
- **OpenSCAD**: excellent LLM-generation target but weaker for revolved/lofted BRep bores.

## Mesh Gap

`stl_export.py` + `stl_verifier.py` use trimesh. **No mesh-repair/heal gate before slicing** — candidates `pymeshlab` / `pymeshfix` / `admesh`. Adoption requires the `docs/TOOLS.md` registry protocol.

## AI Tools

| Tool | Class | Relevance | Verdict |
|------|-------|-----------|---------|
| **ML surrogates** (npj Acoustics 2026, MIT FDTD+ML) | Acoustic solver surrogate | ~10–100× FEM speedup | **Already benchmarked + rejected here** (`topk_polish` + dask won the contract). Do not re-open without a changed contract. |
| **CAD-Coder** (arXiv:2505.14646, MIT) | VLM → CadQuery Python code | Our CAD is already CadQuery | Developer accelerator only (UI scaffolding, mechanism parts), never acoustic bores |
| **CAD-Llama / Text2CAD** (arXiv:2409.17106) | LLM → CAD command sequences | Benchmark / research | Reference only |
| **Zoo.dev Text-to-CAD** | Commercial, OpenSCAD-flavored | UI prototypes | Reference only |
| **Gradient-based geometry optimization** (Szwarcberg 2025) | Analytic TMM sensitivity | Gradient descent on hole positions/diameters | **Most promising new lever**; current optimizer is derivative-free |

## Fabrication

- **SLA** for fixed bores (fine features, smooth interior). **SLS nylon** for mechanisms (Diegel sax: 41 components, keys/springs/pivots, printed + assembled).
- Design-for-AM: print vertically, minimize interior supports, uniform walls, deliberate tonehole chamfers.

## QA / Tuning

- BIAS/impedance measurement is the authoritative feedback signal (`Internal-Research-Measurement`).
- **Acoustic pulse reflectometry (APR)** reconstructs the printed bore from measurement — verifies the print matches the design after reaming. The crux of "finished" quality.
- **OpenWInD** (in stack) is the simulation side; simulation-vs-measurement delta is the QA metric.

## References (key)

- Diegel 3D-printed saxophone (University of Auckland, ~2011)
- Zoran 3D-printed flute (MIT Media Lab, 2010–2011)
- Ernoult et al. one-day design→print→feedback (hal-02479433); OpenWinD (hal-02984478)
- CAD-Coder (arXiv:2505.14646); CAD-Llama/Text2CAD (arXiv:2409.17106); Zoo.dev
- Szwarcberg et al. 2025 gradient woodwind optimization
- 2024MTest..66..705K ABS/PLA impedance-tube materials study
