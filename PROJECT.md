# Instrument Designer — Project Summary

> 3D-printable woodwind instrument design tool using Demakein (bore optimization) + OpenWInD (acoustic simulation).

## What Is This?

A tool to design, simulate, and 3D-print playable woodwind instruments (flutes, recorders, ocarinas, whistles, didgeridoos). Originally Python + PySide6 desktop app, now evolving to web-based architecture.

**Core tools** (unchanged, no better alternatives exist):
- **Demakein** (v1.1) — Bore optimization, hole placement, STL generation
- **OpenWInD** (v0.12.4) — Acoustic impedance simulation and validation

---

## Architecture Options

### Option A — Tauri Desktop App ✅ Built
| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| 3D Viewer | Three.js (@react-three/fiber + @react-three/drei) |
| Parametric CAD | JSCAD (in-browser CSG → STL) |
| Desktop Shell | Tauri v2 (Rust backend) |
| Backend Commands | Rust (Demakein, OpenWInD, FreeCAD, OpenSCAD, PrusaSlicer CLI) |
| Build Size | ~5-10MB (Tauri) vs ~100MB (PySide6) |

### Option B — Pure Web App ✅ Built
| Layer | Technology |
|-------|-----------|
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| 3D Viewer | Three.js (@react-three/fiber + @react-three/drei) |
| Parametric CAD | JSCAD (in-browser CSG → STL) |
| Backend | Existing FastAPI server (Demakein + OpenWInD) |
| Runs in | Any modern browser |

### Option C — Original (Still Available on `main`)
| Layer | Technology |
|-------|-----------|
| Desktop | Python + PySide6 |
| Bore Design | Demakein |
| Acoustics | OpenWInD |
| CAD Export | FreeCAD |
| Backend | FastAPI |

---

## Key Features

- **42 instruments** in library (flutes, recorders, ocarinas, whistles, didgeridoos, etc.)
- **3D STL viewer** — Three.js with orbit controls, zoom, pan, auto-rotating demo bore when no STL loaded
- **Parametric generator** — JSCAD-powered adjustable bore length, diameter, wall thickness with custom binary STL serializer
- **Demakein integration** — preset selector with 12 presets, transposition, bore generation with job polling
- **OpenWInD integration** — acoustic impedance plot (canvas-based visualization with resonance peaks)
- **Sound playback** — Web Audio API tone generation with per-note buttons, scale playback
- **Filterable instrument browser** — search + 4 dropdown filters (subcategory, type, difficulty, tags)
- **Preset wiring** — select instrument from library, auto-loads preset into design tab
- **Slicer integration** — PrusaSlicer/OrcaSlicer CLI for automated G-code generation (Tauri backend)

---

## API Integrations Available

| Tool | How Called | Purpose |
|------|-----------|---------|
| Demakein | Python CLI / `import demakein` | Bore optimization |
| OpenWInD | Python import | Acoustic simulation |
| FreeCAD | `freecadcmd` CLI | STEP/STL export, BREP modeling |
| OpenSCAD | CLI (`openscad -o output.stl`) | Simple CSG parametric models |
| Build123d | Python import (WASM-capable) | Best Python CAD for bore generation |
| PrusaSlicer | CLI | FDM slicing → G-code |
| OrcaSlicer | CLI (undocumented) | Headless slicing with JSON profiles |
| CuraEngine | CLI / Docker | Slicing microservice |
| trimesh | Python import | STL repair, boolean ops, format conversion |
| occt-wasm | npm (WASM) | STEP/STL/BREP in browser |

Full research: `chat-logs/api-integration-research.md`

---

## Git Branches

| Branch | Description | Build Status |
|--------|-------------|-------------|
| `main` | Original Python + PySide6 | ✅ |
| `option-b-web-app` | Pure Web App (React + Three.js) | ✅ TS + Vite |
| `option-a-tauri` | Tauri Desktop (Rust + React) | ✅ TS + Vite + Rust |

---

## Project Structure

```
instrument-designer/
├── chat-logs/
│   ├── 2026-07-11-initial-web-app-build.md    # Session summary
│   ├── 2026-07-11-problems-report.md           # All problems encountered
│   └── api-integration-research.md              # API research doc
├── web/                                         # Shared React frontend
│   ├── src/
│   │   ├── components/
│   │   │   ├── Sidebar.tsx                      # Navigation
│   │   │   ├── InstrumentBrowser.tsx            # Library search + filters
│   │   │   ├── InstrumentDetail.tsx             # Instrument detail view
│   │   │   ├── DesignTab.tsx                    # Design + parametric gen
│   │   │   ├── ResourcesTab.tsx                 # Tips + tools + links
│   │   │   ├── STLViewer.tsx                    # Three.js 3D viewer
│   │   │   └── ParametricGenerator.tsx          # JSCAD bore generator
│   │   ├── data/instruments.ts                  # 42 instruments metadata
│   │   ├── utils/
│   │   │   ├── api.ts                           # FastAPI client
│   │   │   └── filters.ts                       # Instrument filtering
│   │   ├── App.tsx                              # Main layout
│   │   ├── main.tsx                             # Entry point
│   │   └── index.css                            # Tailwind + brand theme
│   ├── src-tauri/                               # Tauri Rust backend (Option A)
│   │   ├── src/
│   │   │   ├── commands.rs                      # All Rust commands
│   │   │   ├── lib.rs                           # Tauri builder
│   │   │   └── main.rs                          # Entry point
│   │   ├── Cargo.toml                           # Rust dependencies
│   │   └── tauri.conf.json                      # Tauri config
│   ├── vite.config.ts
│   └── package.json
├── woodwind_designer/                            # Original Python code
│   ├── engine/
│   │   ├── instrument_library.py                 # Source instrument data
│   │   ├── demakein_wrapper.py                   # Demakein wrapper
│   │   └── design_server.py                      # FastAPI server
│   └── ...
├── ROADMAP.md
└── pyproject.toml
```

---

## Components

| Component | File | Description |
|-----------|------|-------------|
| ImpedancePlot | `ImpedancePlot.tsx` | Canvas-based acoustic impedance visualization with resonance peaks |
| TonePlayer | `TonePlayer.tsx` | Web Audio API tone generation, per-note buttons, scale playback |
| STLViewer | `STLViewer.tsx` | Three.js 3D viewer with demo bore geometry fallback |
| ParametricGenerator | `ParametricGenerator.tsx` | JSCAD bore generator with custom `geometryToSTL()` |
| DesignTab | `DesignTab.tsx` | Wires preset → Demakein controls → ImpedancePlot → TonePlayer → Generator |
| InstrumentBrowser | `InstrumentBrowser.tsx` | Library search + 4 filter dropdowns |
| InstrumentDetail | `InstrumentDetail.tsx` | Instrument detail with TonePlayer embedded |

---

## How to Run

### Option B — Web App
```powershell
cd C:\instrument-designer\web
npm install
npm run dev        # → http://localhost:5173
```

### Option A — Tauri Desktop
```powershell
cd C:\instrument-designer\web
npm install
npx tauri dev      # Launches desktop app
```
*Requires: Rust + MSVC Build Tools + Node.js*

### Option C — Original Python
```powershell
cd C:\instrument-designer
pip install -e .
python -m woodwind_designer
```

---

## Next Steps

1. **Push branches to GitHub** (run `gh auth login` in terminal)
2. **Integrate Build123d** for STEP export (best Python CAD for bore generation)
3. **Add OpenSCAD** as alternative parametric backend
4. **Slicer integration** — auto-slice after STL generation
5. **User accounts** — save designs, share with community
6. **Connect real OpenWInD data** to impedance plot (currently demo data)
7. **Test Tauri release build** — `npx tauri build` for distributable .exe

---

## Problems Solved

13 issues encountered and resolved during development. Full report: `chat-logs/2026-07-11-problems-report.md`

Key gotchas:
- JSCAD v2 removed STL serialization — wrote custom binary STL serializer
- Tauri `#[tauri::command]` conflicts with multiple `crate-types` — separate into `commands.rs` module
- Rust requires MSVC Build Tools + `vcvarsall.bat` environment for Windows compilation
- PowerShell blocks `npm.ps1` — always use `npm.cmd`
- Git push requires manual auth setup (HTTPS → token or SSH key)
