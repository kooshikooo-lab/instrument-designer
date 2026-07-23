# Instrument Designer

3D-printable woodwind instrument design tool with bore optimization, acoustic simulation, and STL generation.

**Vision:** Democratized, low-cost access to musical instruments for everyone regardless of income. Non-technical users access digital instrument design through an easy-to-use GUI.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Tauri Desktop / Web Browser                        │
│  React + TypeScript + Tailwind CSS + Three.js       │
│  - 42 instrument library                            │
│  - Bore optimization UI (NSGA-II)                   │
│  - 3D STL viewer (Three.js)                        │
│  - Acoustic impedance plot (canvas)                 │
│  - Parametric bore generator (JSCAD)               │
│  - Sound preview (Web Audio API)                    │
│  - Microphone pitch analyzer                        │
└──────────────┬──────────────────────────────────────┘
               │ HTTP (localhost:8000)
┌──────────────▼──────────────────────────────────────┐
│  Python Backend (FastAPI)                           │
│  ├── Demakein — bore optimization + STL generation  │
│  ├── OpenWInD — acoustic impedance simulation       │
│  ├── NSGA-II optimizer (pymoo) + PAVA repair        │
│  ├── SQLite shared cache for parallel workers       │
│  └── FreeCAD / OpenSCAD — CAD export                │
└─────────────────────────────────────────────────────┘
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Desktop Shell | Tauri v2 (Rust) |
| Frontend | React 19 + Vite + TypeScript + Tailwind CSS |
| 3D Viewer | Three.js (@react-three/fiber + @react-three/drei) |
| Parametric CAD | JSCAD (browser CSG to STL) |
| Backend | Python + FastAPI + Uvicorn |
| Bore Optimization | pymoo NSGA-II + PAVA monotonicity repair |
| Acoustic Simulation | OpenWInD (1D FEM impedance) |
| Instrument Design | Demakein (v1.1) |

---

## Quick Start

### Option A — Tauri Desktop App

```powershell
# Prerequisites: Rust + MSVC Build Tools + Node.js 18+
cd web
npm install
npx tauri dev
```

### Option B — Web App (browser only)

```powershell
cd web
npm install
npm run dev
# Opens at http://localhost:5173
```

### Option C — Python Backend

```powershell
pip install -e .
python -m woodwind_designer
# FastAPI starts on http://localhost:8000
```

### Running Both Frontend + Backend

```powershell
# Terminal 1: Python backend
cd woodwind-designer
pip install -e .
uvicorn woodwind_designer.engine.design_server:app --host 127.0.0.1 --port 8000

# Terminal 2: Web frontend
cd web
npm install
npm run dev
```

---

## Features

- **42 instruments** in the library (flutes, recorders, ocarinas, whistles, shawms, reedpipes)
- **Bore optimization** — NSGA-II evolutionary algorithm with PAVA monotonicity repair
- **Acoustic impedance** — real-time impedance simulation via OpenWInD
- **3D STL viewer** — Three.js with orbit controls, zoom, pan
- **Parametric generator** — JSCAD-powered adjustable bore with custom binary STL serializer
- **Sound preview** — Web Audio API tone generation with per-note buttons
- **Microphone analyzer** — live pitch detection for tuning comparison
- **Impedance caching** — SQLite shared cache for parallel optimization workers
- **Optimization presets** — correct harmonic series per instrument type (open-open vs closed-open)

---

## Optimizer Accuracy

| Phase | Target | Status |
|-------|--------|--------|
| C1 | <20 cents RMS | DONE |
| C2 | <10 cents RMS | DONE |
| C3 | <5 cents RMS | DONE — 3.11 cents achieved |
| C4 | <3 cents RMS | BORDERLINE — need larger population |

**Benchmark:** Noreland (2013) achieved 0.49 cents RMS on a clarinet using gradient-based optimization.

### How It Works

1. **Design variables:** Bore radius at N control points (default 12)
2. **Objectives:** Frequency accuracy (RMS cents error), scale evenness, impedance projection
3. **Constraints:** Aggregated smoothness (max radius jump between adjacent points)
4. **Repair:** PAVA (Pool Adjacent Violators Algorithm) enforces monotonic bore profile
5. **Targets:** Per-instrument harmonic series — open-open (all harmonics) or closed-open (odd only)

---

## Project Structure

```
woodwind-designer/
├── web/                          # React frontend + Tauri desktop
│   ├── src/
│   │   ├── components/           # React components
│   │   │   ├── DesignTab.tsx     # Design + optimization UI
│   │   │   ├── ImpedancePlot.tsx # Canvas impedance visualization
│   │   │   ├── STLViewer.tsx     # Three.js 3D viewer
│   │   │   ├── ParametricGenerator.tsx  # JSCAD bore generator
│   │   │   ├── TonePlayer.tsx    # Web Audio tone generation
│   │   │   ├── InstrumentBrowser.tsx    # Library search + filters
│   │   │   └── wiki/             # Wiki/knowledge base components
│   │   ├── data/
│   │   │   ├── instruments.ts    # 42 instruments metadata
│   │   │   ├── impedance-data.ts # Pre-computed impedance data
│   │   │   └── wiki-articles.ts  # Knowledge base content
│   │   └── utils/
│   │       ├── api.ts            # FastAPI client
│   │       └── tauri.ts          # Tauri IPC bridge
│   └── src-tauri/                # Tauri Rust backend
│       ├── src/commands.rs       # Rust commands (server, dialogs, I/O)
│       └── tauri.conf.json
├── backend/                      # Python optimization backend
│   ├── bore_optimizer.py         # NSGA-II + PAVA + constraints
│   ├── mp_cache.py               # SQLite shared cache
│   ├── target_frequencies.py     # Per-instrument harmonic targets
│   └── validate_optimizer.py     # Benchmark script
├── woodwind_designer/            # Original Python GUI + engine
│   ├── engine/
│   │   ├── design_server.py      # FastAPI server
│   │   ├── demakein_wrapper.py   # Demakein integration
│   │   └── instrument_library.py # Instrument data
│   └── gui/                      # PySide6 desktop GUI
├── chat-logs/                    # Session logs + research
├── ROADMAP.md                    # Development roadmap
└── PROJECT.md                    # Project summary
```

---

## Git Branches

| Branch | Description |
|--------|-------------|
| `main` | Original Python + PySide6 desktop app |
| `option-a-tauri` | **Active** — Tauri desktop (Rust + React) |
| `option-b-web-app` | Pure web app (React, no Tauri) |
| `scipy-prototype` | Backup — Python scipy optimizer (abandoned) |

---

## Instrument Types

| Type | Acoustic Model | Examples |
|------|---------------|----------|
| Open-open pipe | All harmonics (f, 2f, 3f...) | Flute, recorder, whistle |
| Closed-open pipe | Odd harmonics (f, 3f, 5f...) | Clarinet, reedpipe |
| Conical bore | All harmonics (acts open-open) | Shawm, oboe, saxophone |

---

## Development

### Linting

```powershell
cd web
npm run lint        # oxlint
```

### Building Tauri Release

```powershell
$env:CARGO_TARGET_DIR = "C:\instrument-designer\.cargo-target"
npx tauri build --no-bundle
```

### Running Optimizer Tests

```powershell
python -c "from backend.bore_optimizer import BoreOptimizer; opt = BoreOptimizer([261.6, 784.8, 1308.0, 1831.2, 2354.4, 2877.6], n_control_points=6, pop_size=10, n_generations=5); r = opt.run(); print(r['best_candidates'][0]['objectives'])"
```

---

## Research Foundation

This project builds on published research in computational acoustics:

- **Noreland et al. (2013)** — "The logical clarinet" — 0.49 cents RMS via gradient optimization
- **Ernoult et al. (2020)** — Regularized reflection function for smoother optimization landscapes
- **Szwarcberg et al. (2025)** — Geometric sensitivity analysis for wind instrument intonation
- **Demakein** (Paul Harrison) — Open-source bore optimization + STL generation

See `chat-logs/` for detailed research summaries on acoustic simulation, 3D printing tolerances, and AI-assisted instrument design.

---

## License

GPL-3.0
