# Instrument Designer — Project Roadmap

## 1. Desktop App (PySide6 GUI) — current

| Component | Status | Description |
|---|---|---|
| **Library** | Done | Browse 58 instruments by family/type/tag, detail view with specs, image loading, generate button routes to Design tab |
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

## 9. Design Philosophy — Simplify, Don't Dilute

**Core principle:** Less customized, not less quality. The instrument output must be
acoustically sound and printable regardless of how the user interacts with the tool.

### Beginner Path (3 clicks to printable STL)
1. Pick instrument from library (visual, searchable, categorized)
2. Click "Generate This Instrument" (uses pre-validated preset)
3. Download STL → print

The quality is identical to what an expert would produce. The user never sees
bore profiles, tone hole coordinates, or impedance curves unless they want to.

### Expert Path (full parametric control)
- Custom bore geometry (CSV upload or manual entry)
- Tone hole placement, size, chimney height
- Impedance simulation with configurable frequency range
- Predicted vs measured comparison
- STEP export for CNC machining
- OpenWInD player type selection (FLUTE, CLARINET, LIPS, etc.)

### UI Simplification Roadmap
- [ ] **Guided mode toggle** — hide advanced controls behind "Show Expert Options"
- [ ] **Contextual help** — tooltips on every parameter explaining what it does in plain language
- [ ] **Error messages for humans** — "This preset needs the backend server running" not "Connection refused"
- [ ] **Server URL config that works** — wire the existing input to api.ts instead of hardcoded localhost
- [ ] **Progress feedback** — show a simple "Generating your recorder..." with a spinner, not raw log lines
- [ ] **One-click presets** — most-used instruments as large clickable cards, not buried in a dropdown
- [ ] **Print settings helper** — recommend slicer settings (layer height, infill, material) per instrument
- [ ] **Build checklist** — step-by-step assembly guide after download (glue type, tools needed, time estimate)

### Quality Safeguards
- Presets are validated by domain experts (Demakein/OpenWInD verified)
- Impedance data pre-computed so acoustic quality is guaranteed before user sees it
- Resource pages curated per instrument (tips, FAQs, video links)
- Tone hole positions computed by numerical optimization, not manual placement
- Bore profiles sourced from published acoustic research

### What "Less Customized" Means in Practice
- User picks "Recorder in D" instead of specifying bore taper, hole count, hole spacing
- User picks "Beginner/Intermediate/Advanced" instead of setting reed stiffness
- User gets recommended print settings instead of choosing every slicer parameter
- User sees "This instrument needs 2 hours of print time + 30 min assembly" not raw G-code estimates

### What "Not Less Quality" Means in Practice
- Same Build123d CSG engine regardless of UI mode
- Same OpenWInD impedance simulation
- Same acoustic validation (peak detection, cents deviation)
- Same STL output quality (watertight, printable, correct tolerances)
- Same resource depth (58 instruments with curated tips, build notes, FAQs)

## 10. Unusual Scales & Experimental Instruments — planned

### Non-Western Scale Instruments

| Instrument | Scale/Region | Notes | Status |
|-----------|-------------|-------|--------|
| Quarter-Tone Ney | 24-TET, Middle East | End-blown flute, 5-6 holes, quarter-tone fingering | Research done |
| Slendro Suling | 5-note equidistant, Indonesia | Bamboo flute, gamelan tuning | Research done |
| Pelog Suling | 7-note unequal, Indonesia | Bamboo flute, gamelan tuning | Research done |
| Bohlen-Pierce Recorder | 13-TET tritave, Western experimental | 13-tone scale replacing octave with 3:1 ratio | Research done |
| Xiao (Bei & Tang) | Pentatonic+chromatic, China | End-blown vertical flute, 8 holes | Research done |
| Dizi | Pentatonic, China | Transverse flute with buzzing membrane (dimo) | Research done |
| Daegeum | Pentatonic, Korea | Large transverse flute with buzzing membrane | Research done |
| Maqam Flute | Maqam system, Middle East | Quarter-tone intervals, modal | Research done |
| Quena | Andean pentatonic, South America | End-blown flute, notched lip plate | Research done |
| Harry Partch Cloud Chamber | 43-TET just intonation | Tuned resonant vessels | Research done |

### Experimental Instruments

| Instrument | Category | Notes | Status |
|-----------|----------|-------|--------|
| Hydraulophone | Fluid-state | Water-jet instrument, needs pump system | Research done |
| Dinosaur Choir Resonator | Bio-acoustic | CT-scanned skull + physical modeling synthesis | Research done |
| Chromaplane | Electromagnetic | Isomorphic EM field instrument | Research done |
| Circle Guitar | Mechanical | Programmable strumming wheel | Research done |
| Sea Organ Module | Environmental | Wave-driven resonant tube section | Research done |
| Sharpsichord | Solar/mechanical | Solar-powered pin-barrel harp | Research done |

### Design Workflow for Microtonal Instruments

1. **Calculate frequencies** for your scale (quarter-tones, just intonation, etc.)
2. **Calculate tube lengths** using open/closed tube formulas with end corrections
3. **Calculate hole positions** for each note frequency
4. **Generate 3D model** using Build123d/OpenSCAD parametrically
5. **Print, measure, iterate** — target ±5 cents accuracy
6. **Add to instrument library** with curated resources

### Key References

- University of Wollongong: "3D Modelling and Printing of Microtonal Flutes" (NIME 2016)
- Bohlen-Pierce scale: xen.wiki/Bohlen–Pierce
- Harry Partch: 43-tone just intonation scale
- Guthman Competition 2024-2026: guthman.gatech.edu
- Steve Mann hydraulophone: mannlab.com/hydraulophone
- Royal College of Music: 3D Printed Musical Instruments project

---

## 11. Future Expansion — Non-Wind Instruments

**Status:** Research cataloged, deferred until wind instrument resources are fully working.
**Reference:** `chat-logs/2026-07-15-non-wind-instruments-catalog.md`

### Scope
Once the wind instrument library (58 instruments) and resource system are complete, the app architecture supports extending to other instrument families. All parametric CAD (Build123d), acoustic simulation (OpenWInD), and UI components are family-agnostic.

### Instrument Families Cataloged

#### Strings
| Instrument | 3D Print Feasibility | Notes |
|-----------|---------------------|-------|
| Mbira / Kalimba | HIGH | Board + tines fully printable, any scale, Thingiverse/MakerWorld models exist |
| Circle Guitar | Moderate | Resonance chamber printable, strings/wheel traditional |
| Adjustable Microtonal Guitar | Moderate | Fretboard printable, strings traditional |
| Harpejji | Low | High string tension requires sturdy body |
| Sharpsichord | Moderate | Barrel + frame printable, strings traditional |

#### Electronic
| Instrument | 3D Print Feasibility | Notes |
|-----------|---------------------|-------|
| Chromaplane | Low | EM sensors need traditional manufacturing |
| Theremin | Moderate | Housing/antenna printable, circuitry traditional |
| Ondes Martenot | Moderate | Ring + keyboard housing printable, electronics traditional |
| Eigenharp | Low | Complex electronic assembly |
| ModμMIDI | Moderate | Housing + buttons printable, electronics traditional |

#### Fluid-State
| Instrument | 3D Print Feasibility | Notes |
|-----------|---------------------|-------|
| Hydraulophone | HIGH | Jet plates, manifold, resonant chambers all printable (needs external pump) |
| Sea Organ | Moderate | Individual tube modules printable (architectural scale) |
| Glass Armonica | Low | Glass bowls cannot be 3D printed |

#### Percussion
| Instrument | 3D Print Feasibility | Notes |
|-----------|---------------------|-------|
| Babel Table | Moderate | Membrane housing printable, membranes need latex |

#### Vocal
| Instrument | 3D Print Feasibility | Notes |
|-----------|---------------------|-------|
| VocalCords | Low | Rubber cords are core component |

### Priority Order for Expansion
1. **Mbira/Kalimba** — highest feasibility, fully parametric, any tuning scale
2. **Hydraulophone body** — printable jet plates + manifold, sell pump as accessory
3. **Theremin/Ondes Martenot housing** — 3D-printable enclosures for electronic kits
4. **Circle Guitar chamber** — printable resonance body for experimental luthiers
5. **Sea Organ modules** — printable tube sections for architectural installations

### Architecture Readiness
- `Instrument` interface: family-agnostic, supports any instrument type
- `INSTRUMENT_RESOURCES`: extensible to any family
- `Build123d` backend: parametric CAD works for any 3D geometry
- `OpenWInD`: wind-specific but acoustic principles generalize
- UI components: `InstrumentBrowser`, `InstrumentDetail`, `ResourcePage` are family-agnostic
