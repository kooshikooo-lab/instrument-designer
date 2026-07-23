# API Integration Options for Instrument Designer

## Research Date: 2026-07-11

---

## 1. CAD Software

### FreeCAD (Python API / OCC)
- **Call**: `import FreeCAD; import Part` or CLI `freecadcmd script.py`
- **Use**: Programmatic bore profiles, finger hole cutting, STEP/STL export
- **Gotcha**: Large install (~500MB); headless mode requires exact module paths

### OpenSCAD (CLI)
- **Call**: `openscad -o output.stl input.scad -D 'var=value'`
- **Use**: Simple bore cross-sections, parametric CSG tubes
- **Gotcha**: No STEP export (mesh only); slow for complex models

### Build123d (Python, WASM-capable)
- **Call**: `pip install build123d` or browser via Pyodide + OCP.wasm
- **Use**: **Best Python CAD for instrument design** — bore profiles, splines, sweeps, booleans
- **Gotcha**: WASM initial load ~15MB; VTK removed in WASM build

### CadQuery (Python)
- **Call**: `pip install cadquery`
- **Use**: Fluent parametric BREP CAD, same OpenCascade kernel as Build123d
- **Gotcha**: Less actively maintained than Build123d

### OpenCascade.js / occt-wasm (WASM)
- **Call**: `npm install occt-wasm`
- **Use**: STEP/STL/BREP I/O in browser; ~4MB brotli
- **Gotcha**: Firefox unsupported (no WASM tail calls); single-threaded per kernel

### Blender (Python API)
- **Call**: `blender --background --python script.py` or `pip install bpy`
- **Use**: Visualization, rendering, mesh cleanup (NOT precision CAD)
- **Gotcha**: Mesh-only — no parametric BREP

---

## 2. 3D Printing / Slicing

### PrusaSlicer
- **Call**: `prusa-slicer-console.exe --export-gcode -o output.gcode model.stl`
- **Use**: Batch-slice instrument segments; INI profile injection
- **Gotcha**: CLI only, no REST API

### OrcaSlicer
- **Call**: `orca-slicer --slice 1 --load-settings "machine.json;process.json" --export-3mf output.gcode.3mf input.3mf`
- **Use**: **Best CLI for automated slicing**; JSON profiles; `--pipe` for live progress streaming
- **Gotcha**: Undocumented CLI; version-dependent flags

### CuraEngine (Docker Microservice)
- **Call**: `CuraEngine slice -j printer.def.json -l model.stl -o output.gcode`
- **Use**: FastAPI + Docker wrapper for REST microservice
- **Gotcha**: Community-maintained; requires JSON definition files

---

## 3. Acoustic Simulation

### Demakein (v1.1)
- **Call**: `demakein design-folk-flute: myflute --transpose 12` or `import demakein`
- **Use**: **Core tool** — bore optimization, hole placement, STL generation
- **Gotcha**: Requires `nesoni` for design; CGAL + g++ for make stage

### OpenWInD (v0.12.4)
- **Call**: `pip install openwind; import openwind`
- **Use**: **Complementary to Demakein** — impedance validation, bore shape optimization
- **Gotcha**: Academic docs; 1D FEM only

---

## 4. File Format Interop

### Python
| Library | Formats | Notes |
|---------|---------|-------|
| trimesh | STL, OBJ, PLY, GLTF, 3MF | Best general mesh library; watertight check, boolean ops |
| numpy-stl | STL | Fast STL read/write |
| pythonocc-core | STEP, IGES, STL, OBJ, PLY, GLTF | Full OCCT format support |
| stl2step | STL → STEP | Intelligent mesh-to-BREP conversion |

### JavaScript/WASM
| Library | Formats | Notes |
|---------|---------|-------|
| occt-wasm | STEP, STL, glTF, BREP | ~4MB brotli; TypeScript-first |
| three.js | GLTF, OBJ, STL | Rendering + loader ecosystem |

---

## 5. Recommended Architecture

```
┌──────────────────────────────────────────────────┐
│  Web UI (React + Three.js + JSCAD)               │
│  - Parametric bore input                         │
│  - Acoustic preview (OpenWInD impedance)         │
│  - 3D STL viewer                                 │
└──────────────┬───────────────────────────────────┘
               │ Tauri IPC / REST API
┌──────────────▼───────────────────────────────────┐
│  Backend (Rust Tauri / FastAPI Python)           │
│  ├── Demakein (bore optimization)                │
│  ├── OpenWInD (acoustic validation)              │
│  ├── Build123d / pythonocc (STEP generation)     │
│  ├── trimesh (STL manipulation/repair)           │
│  └── OpenSCAD (simple CSG bores)                 │
└──────────────┬───────────────────────────────────┘
               │ CLI subprocess
┌──────────────▼───────────────────────────────────┐
│  Slicing Service                                 │
│  └── OrcaSlicer CLI or PrusaSlicer CLI           │
│      → G-code / .gcode.3mf                      │
└──────────────────────────────────────────────────┘
```

## 6. Quick Decision Matrix

| Need | Best Option |
|------|-------------|
| Programmatic bore generation (Python) | **Build123d** + pythonocc |
| Acoustic optimization | **Demakein** (design) + **OpenWInD** (validate) |
| Browser-based CAD | **JSCAD** (existing) + **OCP.wasm** (WASM) |
| Automated slicing | **OrcaSlicer CLI** |
| File format conversion | **trimesh** (mesh) + **pythonocc** (BREP) |
| Microservice slicing | **CuraEngine Slicer API** (Docker) |
