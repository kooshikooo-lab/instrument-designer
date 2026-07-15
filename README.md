# Instrument Designer

A web-based parametric wind instrument design tool with integrated acoustic simulation. Design, simulate, and export playable wind instruments for 3D printing.

## Features

### Instrument Library
- 58 pre-configured instruments across 10+ families: flutes, whistles, recorders, shawms, reedpipes, didgeridoos, PVC instruments, hybrid instruments, overtone flutes, and more
- Searchable and filterable by family, difficulty, range, and tags
- Each instrument includes descriptions, fingering charts, and source attribution

### Acoustic Impedance Simulation
- Real-time input impedance computation powered by [OpenWInD](https://openwind.inria.fr/)
- Pre-computed impedance data for 6 instrument presets (recorder, folk whistle, flute, reedpipe, shawm, didgeridoo)
- Interactive impedance plot visualization with resonance peak identification
- **Resonance peaks** correspond to playable notes — peak height indicates ease of playing
- Impedance peaks for **flutes** = minima (low pressure, high flow); **reed instruments** = maxima

### Predicted vs Measured Sound Comparison
- **Microphone capture** via Web Audio API — record played sound directly in browser
- **Real-time FFT spectrum analysis** — visualize frequency content of played notes
- **Pitch detection** using Harmonic Product Spectrum (HPS) algorithm
- **Side-by-side comparison** — predicted impedance peaks vs measured fundamental frequency
- **Cents deviation display** — "Predicted: 523 Hz (C5) | Measured: 520 Hz | -10 cents"
- **Audio recording** — save played notes as WAV for offline analysis
- **Backend analysis** — upload recordings for Python-based spectral analysis (librosa)
- **OpenWInD sound simulation** — generate predicted waveform from bore geometry
- **Impedance measurement import** — compare measured Z(f) from DIY probes against predicted

See [chat-logs/2026-07-12-acoustic-simulation-research.md](chat-logs/2026-07-12-acoustic-simulation-research.md) for full research.

### 3D Design and Export
- **Bore Profile Modeling**: Parametric bore profiles with linear and Bessel interpolation
- **Tone Hole Generation**: Automatically placed tone holes based on instrument preset, subtracted via CSG (Constructive Solid Geometry)
- **STL Export**: Binary STL export with proper normals and geometry
- **STEP Export**: CAD-compatible STEP files via [Build123d](https://build123d.readthedocs.io/) for further editing in FreeCAD, SolidWorks, or Fusion 360
- **3D Preview**: Interactive Three.js viewer with orbit controls for inspecting generated models

### Parametric Generator
- JSCAD-based parametric bore generator with customizable dimensions
- Real-time 3D preview of generated geometry
- Adjustable bore length, inner diameter, wall thickness, and number of segments

### Tone Playback
- Web Audio API tone generation for each note in the instrument's range
- Per-note playback buttons and full scale playback
- Transposition support

## Architecture

```
instrument-designer/
├── backend/                  # Python FastAPI server
│   ├── server.py            # API endpoints (health, design, impedance, STEP export)
│   ├── bore_profiles/       # CSV bore profiles (6 instruments)
│   └── impedance_data/      # Pre-computed JSON impedance data
├── web/                     # React + TypeScript + Vite frontend
│   ├── src/
│   │   ├── components/      # UI components (DesignTab, ImpedancePlot, STLViewer, etc.)
│   │   ├── data/            # Instrument database and impedance data
│   │   └── utils/           # API client
│   └── package.json
├── tools/                   # Build utilities
│   └── bundle_impedance_data.py
└── chat-logs/               # Development notes and research
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19, TypeScript, Vite, Tailwind CSS |
| 3D Viewer | Three.js with OrbitControls |
| Parametric CAD | JSCAD (browser-based) |
| Backend | Python 3.12, FastAPI, Uvicorn |
| Acoustic Simulation | [OpenWInD](https://openwind.inria.fr/) (input impedance via spectral FEM) |
| CAD Export | [Build123d](https://build123d.readthedocs.io/) (STEP files), native STL writer |
| Desktop (optional) | [Tauri v2](https://tauri.app/) + Rust |

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- pip packages: `build123d`, `openwind`, `fastapi`, `uvicorn`, `numpy`

### Backend

```bash
# Install dependencies
pip install -r requirements-server.txt

# Start the backend
python -m uvicorn backend.server:app --port 8000
```

Or use the included scripts:
```bash
# Windows
start-backend.bat
# or
start-backend.ps1
```

### Frontend

```bash
cd web
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000` and the backend at `http://localhost:8000`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Health check |
| GET | `/presets` | List available presets |
| POST | `/design` | Start a design job |
| GET | `/design/{job_id}/status` | Poll design job status |
| GET | `/design/{job_id}/download` | Download generated STL with tone holes |
| POST | `/export/step` | Export bore as STEP file |
| POST | `/impedance/compute` | Compute impedance using OpenWInD (live) |
| GET | `/impedance/precomputed/{preset}` | Get pre-computed impedance data |
| POST | `/analyze/audio` | Upload audio file for spectral analysis (librosa) |
| POST | `/simulate/sound` | Generate predicted sound waveform from bore profile |

## Preset Instruments

Each preset includes a bore profile and tone hole configuration:

| Preset | Bore Length | Bore Diameter | Tone Holes | Hole Type |
|--------|-------------|---------------|------------|-----------|
| Recorder | 325mm | 12mm | 8 (7 finger + 1 thumb) | Round, 5.6mm |
| Folk Whistle | 305mm | 12mm | 6 finger | Round, 5mm |
| Flute | 620mm | 20mm | 6 finger | Round, 8mm |
| Reedpipe | 260mm | 10mm | 4 finger | Round, 4mm |
| Shawm | 380mm | 8-24mm (conical) | 6 finger | Round, 5mm |
| Didgeridoo | 1300mm | 28-32mm | 1 breath | Round, 12mm |

## Similar Projects

| Project | Description |
|---------|-------------|
| [Demakein](https://github.com/pfh/demakein) | Python library for designing and 3D printing woodwind instruments (the acoustic engine behind many tools) |
| [Chalumier](https://github.com/MarkChuCarroll/chalumier) | Kotlin rewrite of Demakein with 10x performance improvement |
| [OpenWInD](https://openwind.inria.fr/) | Python library for wind instrument impedance computation and sound simulation |
| [Flutomat NG](https://unityrobot.github.io/Flutomat/) | Web-based flute hole position calculator (Benade acoustic model) |
| [JDWoodwinds](https://jdwoodwind.com) | Fully 3D-printable piccolo clarinet with key mechanisms |
| [Ruby Whistles](https://git.woozle.org/neale/whistles/) | Parametric low whistle bodies with Axianov toneholes (OpenSCAD) |

## Key Mechanism References

For instruments requiring key mechanisms (clarinets, saxophones, keyed flutes):

- **Hollow tube keys**: Most common type. Hollow cylindrical tube on steel hinge rod. Multiple keys on one rod. ~0.001" tolerance.
- **Solid pivot keys**: Supported by pivot screws on each end. Used on smaller mechanisms.
- **Compliant mechanisms**: 3D-printed flexure springs that replace metal springs. Fully printable, no hardware needed.
- **Spring types**: Needle springs (blued steel coil), leaf springs (flat), or printed compliant springs.
- **Pads**: Neoprene foam (1/16"), leather, or gut. Cut with hole punch, glued with contact cement.

Key components: posts/pillars (mounted on body), hinge rods (2mm stainless steel), pivot screws, springs, and pads.

## Research Sources

- [Jeff Dening's Woodwindfixer](https://woodwindfixer.substack.com/) — Detailed woodwind mechanism engineering
- [OHMI Trust](https://www.ohmi.org.uk/woodwind.html) — One-handed instrument designs with 3D-printed keywork
- [Lefebvre & Scavone (2013)](https://arxiv.org/abs/1207.5490) — External tonehole interactions in woodwind instruments
- [Champ & Scavone (2025)](https://www.frontiersin.org/journals/signal-processing/articles/10.3389/frsip.2025.1519450/full) — Port-Hamiltonian system model of woodwind instruments
- [Larry Wang, MIT (2019)](https://dspace.mit.edu/handle/1721.1/123116) — Algorithmic design of wind instrument shape via 3D FDTD and deep learning

## Future Expansion

Non-wind instrument research is cataloged for future development: `chat-logs/2026-07-15-non-wind-instruments-catalog.md`
- Mbira/Kalimba, Circle Guitar, Hydraulophone, Theremin, Sea Organ, and more
- See `ROADMAP.md` Section 11 for priority order and architecture readiness

## Frequency Analysis & Acoustic Measurement

### Browser-Based Tools (Frontend)
| Tool | Purpose | Implementation |
|------|---------|----------------|
| Web Audio API `AnalyserNode` | Real-time FFT | Built into browser, configurable fftSize (512-16384) |
| Harmonic Product Spectrum (HPS) | Pitch detection | Downsample-multiply algorithm, robust for harmonic instruments |
| Canvas 2D | Spectrum/spectrogram display | Custom rendering, matches existing ImpedancePlot style |
| MediaRecorder API | Audio capture | Save played notes as WAV/OGG for offline analysis |

### Python Libraries (Backend)
| Library | Purpose | Use Case |
|---------|---------|----------|
| [librosa](https://librosa.org/) | Audio analysis | STFT, MFCC, harmonic separation, pitch tracking |
| [scipy.signal](https://docs.scipy.org/doc/scipy/reference/signal.html) | DSP primitives | FFT, filtering, windowing, spectral estimation |
| [OpenWInD](https://openwind.inria.fr/) | Sound simulation | Time-domain waveform from bore + oscillator coupling |

### Desktop Measurement Software
| Software | Price | Best For |
|----------|-------|----------|
| [REW (Room EQ Wizard)](https://www.roomeqwizard.com/) | Free | Impedance measurement, frequency response, CSV export |
| [ARTA](https://artalabs.com) | Free | Sweep recording, impulse response, impedance |
| [Smaart v9](https://trueaudio.com) | $895 | Professional dual-channel FFT, real-time alignment |

### Impedance Measurement Methods
- **Two-Microphone Transfer Function (TMTF)**: Standard method (Gibiat & Laloë, 1990). Cylindrical cavity + 2 mics + speaker + chirp excitation → Z(f).
- **Four-Microphone Four-Calibration (FMFC)**: For narrow-bore instruments (oboes, bassoons).
- **DIY Approach**: Single microphone captures played sound → FFT → compare with predicted peaks. Sufficient for relative comparison without absolute impedance calibration.

### Academic References
- Gibiat & Laloë (1990) — "Acoustical impedance measurements by the TMTC method" — JASA 88(6):2533-2545
- Wolfe (2018) — "The Acoustics of Woodwind Musical Instruments" — Acoustics Today
- Chabassier & Ernoult (2020) — "The Virtual Workshop OpenWinD" — HAL hal-02984478
- Eveno et al. (2012) — Impedance measurement of 45 historical serpents
- Bowen et al. — Validated bore geometry → predicted pitch, intonation, and timbre
- NEMUS Project — Digital revival of historical instruments via acoustic simulation

## License

This project is under active development. See individual dependency licenses for Build123d (Apache 2.0), OpenWInD (GPL 3.0), and Demakein (MIT).
