# Instrument Designer - Chat Log Summary

## Date: 2026-07-11
## Status: In Progress

---

## What We Built So Far

### Repository
- **Project**: `instrument-designer`
- **Repo**: `https://github.com/kooshikooo-lab/instrument-designer.git`
- **Location**: `C:\instrument-designer`
- **Git User**: kooshikooo (`kooshikooo@users.noreply.github.com`)

### Tech Stack Evolution
- **Original**: Python + PySide6 + Demakein + OpenWInD + FreeCAD + FastAPI
- **Problems**: Big exe (~100MB), no sharing, no 3D preview
- **Solution**: Two alternative branches

### Branch: `option-b-web-app` (Pure Web)
- React + Vite + TypeScript + Tailwind CSS
- Three.js for 3D preview (@react-three/fiber + @react-three/drei)
- JSCAD for in-browser parametric STL generation
- Same FastAPI backend
- **Location**: `C:\instrument-designer\web`

### Files Created
| File | Purpose |
|------|---------|
| `web/src/data/instruments.ts` | 42 instruments ported from Python (Demakein presets, metadata, tags) |
| `web/src/utils/api.ts` | FastAPI client (health check, design jobs, download) |
| `web/src/utils/filters.ts` | Search, subcategory, type, difficulty, tag filtering |
| `web/src/App.tsx` | Main layout: sidebar + 3 tabs (Library, Design, Resources) |
| `web/src/components/Sidebar.tsx` | Navigation with SVG icons |
| `web/src/components/InstrumentBrowser.tsx` | Search + 4 filter dropdowns + instrument list |
| `web/src/components/InstrumentDetail.tsx` | Full detail: specs, tags, download/listen/generate buttons |
| `web/src/components/DesignTab.tsx` | Preset selector, transpose, server connect, job polling, download |
| `web/src/components/ResourcesTab.tsx` | Tips, open-source projects, STL repos, AI tools, community |
| `web/src/components/STLViewer.tsx` | Three.js 3D STL file viewer with orbit controls |
| `web/src/components/ParametricGenerator.tsx` | JSCAD parametric bore generator (recorder, ocarina, didgeridoo, flute) |
| `web/src/main.tsx` | React entry point |
| `web/src/index.css` | Tailwind + brand gold theme (#bc6915) |
| `web/vite.config.ts` | Vite + React + Tailwind plugin |
| `web/index.html` | Entry HTML |
| `public/favicon.svg` | Brand icon |

### Key Decisions
1. **Demakein + OpenWInD** = best tools, no better alternatives exist
2. **Web app** solves all 3 major problems (size, sharing, 3D preview)
3. **Three.js** for real-time 3D model viewing in browser
4. **JSCAD** for parametric STL generation without Python backend
5. **Tailwind CSS** for dark theme UI with brand gold accents

### Build Status
- ✅ TypeScript compiles clean
- ✅ Vite build succeeds (233KB JS, 17KB CSS gzipped)
- ⏳ STLViewer + ParametricGenerator written, needs integration
- ⏳ Design tab needs update to use new components

### Pending Tasks
1. Integrate STLViewer into InstrumentDetail for 3D preview
2. Integrate ParametricGenerator into DesignTab
3. Commit and push `option-b-web-app` to GitHub
4. Create `option-a-tauri` branch (Tauri wrapper around web UI)
5. Initialize Rust toolchain
6. Scaffold Tauri project
7. Push `option-a-tauri` to GitHub

### Tools Installed
- Node.js v24.18.0 + npm
- Rust (via Rustlang.Rustup) - not yet initialized
- Vite, Three.js, JSCAD, React Three Fiber

### Environment Notes
- Git must use full path: `"C:\Program Files\Git\cmd\git.exe"`
- npm must use: `& "C:\Program Files\nodejs\npm.cmd"` or refresh PATH
- PowerShell blocks `npm.ps1` - must use `npm.cmd`
- Node installed via `winget install OpenJS.NodeJS.LTS`

---

## Next Session Commands
```powershell
# Refresh PATH
$env:PATH = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Run dev server
cd C:\instrument-designer\web
& "C:\Program Files\nodejs\npm.cmd" run dev

# Build
& "C:\Program Files\nodejs\npm.cmd" run build

# Git operations
& "C:\Program Files\Git\cmd\git.exe" status
& "C:\Program Files\Git\cmd\git.exe" add .
& "C:\Program Files\Git\cmd\git.exe" commit -m "message"
& "C:\Program Files\Git\cmd\git.exe" push origin option-b-web-app
```
