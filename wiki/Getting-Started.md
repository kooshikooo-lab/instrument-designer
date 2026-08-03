# Getting Started

## Prerequisites

- **Python 3.12+** with pip
- **Node.js 18+** (for web/Tauri frontend)
- **Rust + MSVC Build Tools** (for Tauri desktop app only)
- **JDK 17+** (for chalumier integration, optional)

## Installation

### Option A: Tauri Desktop App (Recommended)

```bash
# Clone the repo
git clone https://github.com/kooshikooo-lab/instrument-designer.git
cd instrument-designer

# Install Python dependencies
pip install -r requirements-server.txt

# Install frontend dependencies
cd web
npm install

# Run in dev mode
npx tauri dev
```

### Option B: Web App (Browser Only)

```bash
# Start the backend
python -m uvicorn woodwind_designer.engine.design_server:app --host 127.0.0.1 --port 8000

# In another terminal, start the frontend
cd web
npm install
npm run dev
# Open http://localhost:5173
```

### Option C: Original Python GUI

```bash
pip install -e .
python -m woodwind_designer
```

## First Design

1. Open the Design tab
2. Select an instrument from the preset dropdown (e.g., "Chalumeau C")
3. Click "Run Optimizer"
4. View results: bore profile, impedance plot, intonation chart
5. Export STL for 3D printing

## Branches

| Branch | Use Case |
|--------|----------|
| `laptop` | Active development — all features, optimizer, 91 instruments |
| `main` | Stable shared branch |
| `option-a-tauri` | Tauri UI, optimization UI, AI assistant |
| `refactor/architecture-redesign` | Solver-agnostic architecture |

See [[Internal-Branches]] for detailed branch documentation.
