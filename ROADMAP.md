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

## 7. Acoustic Simulation & Measurement — planned

| Component | Status | Description |
|---|---|---|
| **Impedance Plot** | Done | Pre-computed Z(f) for 6 presets, canvas-based visualization |
| **Peak Detection** | Done (Python) | `_find_peaks()` finds resonance frequencies from impedance data |
| **Frequency-to-Note** | Done (Python) | `_freq_to_note()` converts Hz → note name + cents deviation |
| **Sound Synthesizer** | Done (Python) | `synthesize_from_peaks()` generates audio from impedance peaks |
| **Microphone Capture** | Not started | Web Audio API `getUserMedia` + `AnalyserNode` for browser mic input |
| **Real-time FFT Display** | Not started | Canvas-based frequency spectrum visualization |
| **Pitch Detection (HPS)** | Not started | Harmonic Product Spectrum algorithm in browser |
| **Predicted vs Measured** | Not started | Overlay impedance peaks with measured frequency, show cents deviation |
| **Audio Recording** | Not started | MediaRecorder API → save played notes as WAV |
| **Backend Audio Analysis** | Not started | `POST /analyze/audio` — librosa-based spectral analysis |
| **Sound Simulation** | Not started | `POST /simulate/sound` — OpenWInD time-domain waveform generation |
| **Impedance Import** | Not started | CSV upload of measured Z(f) for direct comparison with predicted |
| **Spectrogram Overlay** | Not started | Compare predicted vs measured time-frequency representations |
| **DIY Impedance Probe Guide** | Not started | Documentation for building 2-microphone measurement setup |

## 8. Known Issues & Next Steps

- [ ] **Microphone capture** — add Web Audio API getUserMedia to browser for live frequency analysis
- [ ] **Real-time FFT spectrum** — Canvas-based frequency display alongside impedance plot
- [ ] **Pitch detection (HPS)** — Harmonic Product Spectrum algorithm for note identification
- [ ] **Predicted vs measured comparison** — overlay impedance peaks with microphone frequency data
- [ ] **Audio recording** — MediaRecorder API to save played notes as WAV files
- [ ] **Backend audio analysis** — POST /analyze/audio endpoint using librosa
- [ ] **OpenWInD sound simulation** — POST /simulate/sound to generate predicted waveform
- [ ] **Impedance measurement import** — CSV upload for measured Z(f) comparison
- [ ] **Deploy FastAPI server** to a VPS (DigitalOcean, Hetzner, or home server)
- [ ] **Subprocess isolation** for server — each design runs in its own process for clean stdout
- [ ] **Web frontend** — build a lightweight browser interface (done: option-b-web-app branch)
