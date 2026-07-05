# Instrument Designer — Project Roadmap

## 1. Desktop App (PySide6 GUI) — current

| Component | Status | Description |
|---|---|---|
| **Library** | Done | Browse 40+ instruments by family/type/tag, detail view with specs, image loading, generate button routes to Design tab |
| **Resources** | Done | Design tips, links to community projects, STL repositories, AI tools, tutorials, community forums |
| **Projects** | Done | Create/save/open projects, workspace management, project metadata (type, preset, transpose, models) |
| **Design** | Done | Family/subcategory/preset combo boxes with friendly display names, transpose spin, progress log, cancel support, preset routing from Library |
| **Simulate** | Stub | OpenWInD simulation tab (empty placeholder) |
| **3D Export** | Stub | FreeCAD export tab (empty placeholder) |
| **Style** | Done | Dark theme with gold/brown accents across all widgets |

## 2. Design Engine

| Component | Status | Description |
|---|---|---|
| **Demakein Wrapper** | Done | `DemakeinDesigner` class wrapping all 10 built-in presets, category lookup, stdout progress capture with `\r`/`\n` handling, PyInstaller-safe `_ProgressStream` |
| **Preset Display Names** | Done | `PRESET_DISPLAY_NAMES` map decouples internal keys (e.g. `folk_whistle`) from friendly names ("Penny Whistle (Tin Whistle)") |
| **Stdout Fix (exe)** | Done | `_ProgressStream` falls back to `io.StringIO()` when `sys.stdout` is None inside PyInstaller exe |
| **Remote Client** | Done | `RemoteDesigner` class with same interface, polls server for progress, downloads STL zip |

## 3. Remote Compute Server — planned infrastructure

| Component | Status | Description |
|---|---|---|
| **FastAPI Server** | Built | `design_server.py` — endpoints: `POST /design`, `GET /design/{id}/status`, `GET /design/{id}/download`, `GET /health`, `GET /presets` |
| **Server Requirements** | Listed | `requirements-server.txt` — fastapi, uvicorn, requests |
| **Deployment** | Not started | Need a Linux/VPS with Python, then `uvicorn woodwind_designer.engine.design_server:app --host 0.0.0.0 --port 8000` |
| **Concurrency** | Not started | Currently uses daemon threads — needs subprocess isolation for multi-user |
| **Persistence** | Not started | Jobs stored in-memory dict — needs database for production |
| **Auth** | Not started | No authentication — needs API keys or basic auth before public deployment |

## 4. Web App — future vision

| Component | Status | Description |
|---|---|---|
| **Web GUI** | Not started | Could build a React/Vue frontend that calls the same FastAPI server |
| **Shared Presets** | Not started | Community-contributed preset tunings |
| **STL Hosting** | Not started | Serve generated STLs directly from the server |
| **User Accounts** | Not started | Save designs, share with community |

## 5. Packaging & Distribution

| Component | Status | Description |
|---|---|---|
| **PyInstaller Exe** | Fixed | `InstrumentDesigner.exe` — uses `run.py` entry point (absolute import), `_ProgressStream` stdout fix |
| **run.bat** | Done | Double-click launcher: `python -m woodwind_designer` |
| **save-session.bat** | Done | Saves timestamped session log to Desktop |
| **backup.ps1** | Done | Full project backup script |
| **GitHub** | Done | Repo at `kooshikooo-lab/instrument-designer` |
| **instrument-designer.zip** | Done | Full project archive (excludes git/pycache/designs/build/dist) |

## 6. Instrument Library

| Entry | Category | Source | Status |
|---|---|---|---|
| Penny Whistle, Folk Flute, Recorder, Dorian Whistle, Three-Hole Whistle, Pan Flute | Flute > Fipple/Pan | Demakein built-in | Done |
| Whistle Pan Flute, Slide Whistle | Flute > Slide/Pan | Printables | Done |
| Transverse Flute (C), Axianov Irish Flute, Side-Blown Flute in A Major, Traditional Bansuri B Natural | Flute > Transverse | Printables/Cults3D | Done |
| 12-Hole Ocarina, Small 5-Hole Ocarina | Flute > Vessel | Printables | Done |
| Reedpipe, Modern Chalumeau, C Clarinet Remix, Membrane Clarinet, Reed Drone | Woodwind > Single Reed | Demakein/Printables | Done |
| Folk Shawm, Shawm | Woodwind > Double Reed | Demakein built-in | Done |
| Glissotar, Glissotar Bass | Woodwind > Slit Reed | Custom design | Done |
| Kazoo, Double Native American Flute | Woodwind > Free Reed/Fipple | Printables | Done |
| Trumpet, Kudu Horn | Brass | Printables | Done |
| Didgeridoo, D5 Drone Flute | Drone & Others | Printables/MakerWorld | Done |
| Mouthpieces, Barrels, Reeds, Ligatures, Tools | Parts & Accessories | Printables | Done |

## 7. Known Issues & Next Steps

- [ ] **Deploy FastAPI server** to a VPS (DigitalOcean, Hetzner, or home server)
- [ ] **Subprocess isolation** for server — each design runs in its own process for clean stdout
- [ ] **Simulate tab** — integrate OpenWInD acoustic simulation
- [ ] **3D Export tab** — integrate FreeCAD STL generation
- [ ] **Quick Draft mode** — add checkbox to skip heavy demakein optimization for faster results
- [ ] **Web frontend** — build a lightweight browser interface
