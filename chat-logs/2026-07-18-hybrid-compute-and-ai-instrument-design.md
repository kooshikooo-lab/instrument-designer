# Hybrid Compute & AI for Instrument Designer

Date: 2026-07-18
Stack: Tauri v2 + Rust + React (Vite) + Python (FastAPI + OpenWInD + Demakein)

---

## 1. Hybrid Offline/Remote Compute Architecture

### 1.1 Core Pattern: Tauri Sidecar + PyInstaller

The industry-standard approach for bundling Python with Tauri is the **Sidecar pattern**:

- **PyInstaller** compiles Python code + interpreter + all dependencies into a single platform-specific executable (`--onefile`).
- The `.exe` is placed in `src-tauri/binaries/` with a target-triple suffix (e.g. `main-x86_64-pc-windows-msvc.exe`).
- **`tauri.conf.json`** declares it under `bundle.externalBin`.
- **`tauri-plugin-shell`** spawns it from Rust or JS. The sidecar runs as a FastAPI server on `localhost:PORT`.
- The React frontend talks to it via HTTP (fetch or `@tauri-apps/plugin-http`).

**Key production reference:** [benitomartin/tauri-app-bundle](https://github.com/benitomartin/tauri-app-bundle) — bundles llama.cpp + FastAPI with PyInstaller spec file that collects dynamic libs. Also [dieharders/example-tauri-v2-python-server-sidecar](https://github.com/dieharders/example-tauri-v2-python-server-sidecar) — the canonical template.

### 1.2 Recommended Architecture for Instrument Designer

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tauri Desktop App                            │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  React Frontend (Vite)                                  │    │
│  │  - Design canvas, impedance plots, 3D preview           │    │
│  │  - BackendHealthBanner (online/offline/local/remote)    │    │
│  └──────────┬──────────────────────────────────────────────┘    │
│             │ IPC (invoke)            │ HTTP (localhost)         │
│  ┌──────────▼──────────────┐  ┌───────▼───────────────────┐     │
│  │  Rust (Tauri Core)      │  │  Local Python Sidecar     │     │
│  │  - Sidecar lifecycle    │  │  (PyInstaller bundle)     │     │
│  │  - Health check polling │  │  - Demakein design        │     │
│  │  - Offline/remote       │  │  - Build123d STEP export  │     │
│  │    routing logic        │  │  - OpenSCAD generation    │     │
│  │  - File I/O, settings   │  │  - FreeCAD STEP export    │     │
│  └─────────────────────────┘  │  - PrusaSlicer CLI wrap   │     │
│                                └──────────────────────────┘     │
│                                 Optional:                       │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  Remote FastAPI Server (cloud/self-hosted)              │    │
│  │  - OpenWInD FEM impedance simulation (heavy)            │    │
│  │  - Time-domain sound simulation                         │    │
│  │  - Audio analysis                                       │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘
```

### 1.3 Sidecar Lifecycle Management

**Startup (Rust, `main.rs` / `lib.rs`):**
```rust
// In setup closure:
let sidecar = app.shell().sidecar("instrument-engine")?
    .env("PYTHONUTF8", "1")
    .env("INSTRUMENT_DATA_DIR", app_data_dir);
let (mut rx, child) = sidecar.spawn()?;
// Store child handle for clean shutdown
// Spawn async task to read stdout/stderr and emit events
```

**Health Monitoring (TypeScript, React):**
- Poll `http://localhost:{PORT}/api/health` every ~12s with exponential backoff.
- Listen for Tauri event `backend-exit` for immediate crash detection.
- Show non-blocking status banner: `healthy | degraded | offline | exited`.
- On unhealthy: auto-restart up to 3 times with 2s grace period (pattern from [Stirling-PDF TauriBackendService](https://github.com/Stirling-Tools/Stirling-PDF/blob/dd44de34/frontend/src/desktop/services/tauriBackendService.ts)).

**Shutdown:**
- Tauri `on_exit` handler sends graceful shutdown signal to sidecar (SIGTERM or via HTTP `/shutdown`), then force-kills after timeout.
- Bonus: a [proposed `tauri-plugin-sidecar-lifecycle`](https://github.com/tauri-apps/plugins-workspace/issues/3062) would standardize this.

### 1.4 Offline-First Strategy

All local operations work without any network:
- **Demakein** (bore design, hole placement optimization)
- **Build123d** (STEP export with tone holes)
- **OpenSCAD** (3D model generation)
- **FreeCAD** (STEP export)
- **PrusaSlicer** (G-code generation)

These are all bundled as a single PyInstaller binary or as separate sidecars. They communicate via localhost HTTP.

**Remote server detection:**
- On startup, Rust spawns the local sidecar AND attempts a health check to the configured remote URL.
- Result is stored in React state as `computeMode: 'local' | 'remote' | 'hybrid'`.
- UI shows which operations are local vs. remote. Heavy operations (FEM, sound sim) show a toggle or auto-route to remote if available.
- Full offline: no degradation of core design workflow.

**Graceful fallback (from [silvermine/tauri-plugin-connectivity](https://github.com/silvermine/tauri-plugin-connectivity)):**
- Detect network connectivity via `@silvermine/tauri-plugin-connectivity`.
- If remote server is configured but unreachable, fall back to lower-quality local approximation or show a clear "Remote server unavailable — using local solver" message.

### 1.5 Build Pipeline

```
# 1. Bundle Python
cd src-python
uv run pyinstaller instrument-engine.spec  # custom spec for Demakein + Build123d + OpenSCAD deps
cp dist/instrument-engine.exe ../src-tauri/binaries/instrument-engine-x86_64-pc-windows-msvc.exe

# 2. Build Tauri app (bundles frontend + sidecar)
cd ..
npm run tauri build
```

**Dev mode:** Pass `--dev-sidecar` flag to use system Python directly (hot-reload), skipping PyInstaller.

**PyInstaller spec file considerations:**
- Use `--collect-all` or a custom `.spec` file for libraries like `demakein`, `build123d`, `openwind` that have data files or dynamic imports.
- For PrusaSlicer CLI: bundle the slicer binary separately as a second sidecar.

### 1.6 Existing Templates

| Template | Stack | Notes |
|----------|-------|-------|
| [dieharders/example-tauri-v2-python-server-sidecar](https://github.com/dieharders/example-tauri-v2-python-server-sidecar) | Tauri v2 + Next.js + FastAPI | Canonical reference |
| [fudanglp/tauri-fastapi-full-stack-template](https://github.com/fudanglp/tauri-fastapi-full-stack-template) | Tauri v2 + React + FastAPI + SQLite | Closest to your stack |
| [AlanSynn/vue-tauri-fastapi-sidecar-template](https://github.com/AlanSynn/vue-tauri-fastapi-sidecar-template) | Tauri v2 + Vue + FastAPI | Uses `uv` for Python build |
| [benitomartin/tauri-app-bundle](https://github.com/benitomartin/tauri-app-bundle) | Tauri v2 + FastAPI + llama.cpp | Production-ready with PyInstaller spec |
| [Guybrush.ink "box" bundler](https://guybrush.ink/writings/2025-05-18-bundling-python) | PyApp-based bundling | Alternative to PyInstaller, caches env on first run |
| [kination "smoodit"](https://dev.to/kination/story-of-smoodit-1-electron-to-tauri-3n7e) | Tauri v2 + FastAPI + Ollama sidecar | Real app, covers macOS quarantine, pipe buffer fixes |

---

## 2. AI/ML Landscape for Instrument Design

### 2.1 Existing Open-Source Woodwind Design Tools

| Tool | Language | Capabilities |
|------|----------|-------------|
| **Demakein** (Python) | Python 3 | Numerical optimization of bore shape, hole placement/size/depth for target fingerings. Generates STL for 3D printing. Command-line + library. |
| **OpenWInD** (Python, INRIA) | Python 3 | 1D spectral FEM for impedance computation, Full Waveform Inversion for bore reconstruction, time-domain sound simulation. Has a web GUI at demo-openwind.inria.fr. |
| **WWIDesigner** (Java) | Java | Parametric optimizer for woodwind geometry (bore, tone holes). Constraint-driven. NAF (Native American flute) and clarinet support. |
| **Chalumier** (Java/Kotlin) | JVM | Demakein port with evolutionary algorithm for instrument design. Produces SVG diagrams + parameter JSON. |

### 2.2 Research: Inverse Design & Optimization

**Full Waveform Inversion (FWI) for Woodwinds** (Ernoult et al., Acta Acustica 2021):
- Gradient-based optimization recovers bore geometry + hole locations from impedance measurements.
- Cost function gradient computed by solving the same linear system as the forward problem — negligible extra cost vs. finite differences.
- 14 design variables reconstructed in ~1 minute on a laptop.
- **Key insight:** You can invert this: instead of measuring impedance and recovering geometry, **specify target impedance and optimize geometry**. Already the foundation of OpenWInD's optimization module.

**Woodwind Design Optimization** (Ernoult et al., hal-02479433):
- Phase-based resonance formulation enables smooth gradient-based optimization of bore + tone holes.
- 38 variables optimized simultaneously (bore profile, hole radii, chimney heights, positions).
- Demonstrated on a pentatonic clarinet with two-register tuning.
- **Relevance:** This is the math behind gradient-based instrument design that an AI assistant could drive.

### 2.3 Research: Machine Learning for Topology Optimization

**MLGen** (Kallioras & Lagaros, 2021):
- LSTM + SIMP topology optimization framework.
- Generates multiple diverse optimized shapes from same boundary conditions.
- Output is 3D-printable. Combines image filtering for shape diversity.

**TopologyGAN / cGAN+TO** (Nie et al. 2021, Wang et al. 2023):
- Conditional GAN trained on topology optimization results.
- Near-instant generation of optimized structures given load/boundary conditions.
- **Relevance:** A GAN trained on OpenWInD impedance-optimized geometries could generate bore profiles in milliseconds.

**Differentiable Acoustics** (multiple, 2024-2026):
- **JAX-BEM** (2025): Differentiable Boundary Element Method for acoustic shape optimization. Gradient-based optimization of loudspeaker horn directivity using automatic differentiation.
- **DiffSound** (2024): Differentiable modal sound rendering. Infers geometry, material, and impact position from sound alone.
- **Differentiable Geometric Acoustic Path Tracing** (Finnendahl et al., 2025): Differentiable ray tracing for acoustic optimization.
- **Differentiable FEM** (Borrel-Jensen & Bjorgaard, 2025): JAX-FEM for acoustic inverse problems (shape optimization, admittance estimation). 48.1% energy reduction at target frequencies.
- **Acoustic hologram design** (j-Wave, 2023): Differentiable wave simulation for 3D-printed acoustic lenses.

**Key takeaway:** The tools now exist to build a fully differentiable pipeline from geometry -> acoustic simulation -> optimization. This is what enables ML-based inverse design.

### 2.4 LLM Integration for Instrument Design

**Existing music/audio LLM projects** (all local-first with Ollama):

| Project | What it does |
|---------|-------------|
| [jarvisonix](https://github.com/laygofiona/jarvisonix) | Voice -> MIDI -> DAW automation, uses Ollama for context-aware prompts |
| [swarmdj](https://github.com/harishkotra/swarmdj) | Multi-agent LLM system controlling live music synthesis |
| [meltfm](https://github.com/IFAKA/meltfm) | LLM translates natural language reactions into music parameters for ACE-Step |
| [the-muser](https://github.com/noah-chelednik/the-muser) | 46-tool LLM agent orchestrating multiple music generation models (NotaGen, ACE-Step, DiffSinger) |
| [impulse-instruct](https://github.com/Tok/impulse-instruct) | Multi-agent LLM synthesizer in Rust, uses llama-server pool |
| [somancer-studio](https://github.com/bbbbbb12331314141414141/somancer-studio) | Multi-agent songwriting studio with Ollama |
| [SOOG](https://github.com/zzigo/soog) | Instrument classification + organogram visualization with GPT-4/BERT |

**These demonstrate:** LLMs can meaningfully drive parametric design tools via structured JSON output. The pattern is:
1. User gives natural language prompt.
2. LLM outputs structured parameters (JSON schema).
3. Parameters are applied to the design/synthesis engine.
4. Result is evaluated and fed back.

### 2.5 LLM for Bore Profile & Tone Hole Design

**What an LLM assistant could do for Instrument Designer:**

| Capability | How |
|-----------|-----|
| Suggest bore profiles | LLM outputs bore profile parameters (cone angles, spline control points) that map to Demakein/OpenWInD geometry. Could condition on instrument type (clarinet, flute, shawm). |
| Suggest tone hole layout | LLM outputs hole positions, diameters, chimney heights. Feeds into Demakein optimization as initial guess or constraints. |
| "Make it sound warmer/brighter" | LLM maps qualitative descriptors to impedance targets (peak ratios, cutoff frequencies). Feeds into OpenWInD's inverse design. |
| Suggest fingerings | LLM outputs fingering charts for target scales. |
| Explain acoustic tradeoffs | RAG over OpenWInD docs + acoustics literature. |

**Recommended approach:**
- **Local inference** via Ollama (tiny models like `qwen2.5:3b` or `llama3.2:3b` are sufficient for parametric output).
- **Remote inference** optional via OpenAI/Anthropic API for more complex reasoning.
- **Structured output:** Use Ollama's JSON mode or OpenAI's `response_format: { type: "json_object" }` to get machine-parseable parameter suggestions.
- **No hallucinations in geometry:** LLM suggestions are treated as *starting points* or *constraint suggestions*. The actual optimization (Demakein, OpenWInD FWI) runs numerical methods that guarantee physical feasibility.

---

## 3. Implementation Recommendations

### 3.1 Hybrid Compute — Phased Rollout

**Phase 1 (immediate):**
- Bundle local Python as a single PyInstaller sidecar containing Demakein + Build123d + OpenSCAD wrapping.
- Simple FastAPI server with endpoints for each operation.
- Rust handles sidecar lifecycle (spawn, health check, kill).

**Phase 2 (near-term):**
- Add remote server support: configure remote URL in settings.
- Rust routes heavy requests (FEM, sound sim) to remote if available, else local.
- Frontend shows compute mode indicator.
- Health check polling with graceful degradation.
- Network connectivity detection plugin.

**Phase 3 (future):**
- Self-updating sidecar binary (fetch new version, SHA256 verify, atomic swap — pattern from [chenxxpro's Tauri sidecar blog](https://dev.to/chenxxpro/bundling-a-cli-binary-as-a-tauri-v2-sidecar-lessons-from-building-a-desktop-app-5po)).
- Multiple sidecars (separate `instrument-engine` and `slicer-engine`).
- Proposed `tauri-plugin-sidecar-lifecycle` if/when it ships.

### 3.2 AI Integration — Phased Rollout

**Phase 1 (immediate):**
- Offline LLM via Ollama (optional dependency, not bundled).
- "AI Assistant" panel in React UI.
- User types design intent ("design a G major pentatonic flute").
- LLM outputs structured JSON → pre-fills Demakein geometry fields.
- User reviews and runs design optimization.

**Phase 2 (near-term):**
- Integrate with OpenWInD: LLM suggests geometry changes to hit target impedance curves.
- Fine-tune a small model (LoRA on Qwen2.5 3B) on Demakein/OpenWInD design examples to improve suggestion quality.
- RAG pipeline over acoustics papers + OpenWInD docs.

**Phase 3 (future):**
- Train a GAN/diffusion model on OpenWInD-optimized geometries for instant bore profile generation.
- Differentiable pipeline: geometry -> acoustic sim -> gradient-based optimization, all in JAX.
- "Describe the sound you want" -> inverse design to geometry.

### 3.3 Key Files / Architecture

```text
instrument-designer/
├── src-python/                    # Python backend
│   ├── instrument_engine/         # FastAPI app
│   │   ├── main.py                # Routes: /design, /export, /impedance, /health
│   │   ├── routers/
│   │   │   ├── demakein.py        # Demakein design & make
│   │   │   ├── build123d.py       # STEP export with tone holes
│   │   │   ├── openscad.py        # OpenSCAD generation
│   │   │   ├── slicer.py          # PrusaSlicer CLI wrapper
│   │   │   └── ai_assistant.py    # LLM integration (Ollama/API)
│   │   └── models/                # Pydantic schemas
│   ├── instrument-engine.spec     # PyInstaller spec
│   └── pyproject.toml
├── src-tauri/
│   ├── binaries/                  # Bundled PyInstaller executables
│   ├── src/
│   │   ├── lib.rs                 # Tauri app setup, sidecar lifecycle
│   │   └── commands.rs            # Rust IPC commands
│   ├── tauri.conf.json            # externalBin config
│   └── capabilities/default.json  # shell:allow-spawn permissions
├── src/                           # React frontend
│   ├── hooks/
│   │   ├── useBackendHealth.ts    # Health check polling + event listener
│   │   └── useComputeMode.ts      # local/remote/hybrid routing
│   ├── components/
│   │   ├── BackendHealthBanner.tsx
│   │   ├── ComputeModeIndicator.tsx
│   │   └── AiAssistant.tsx        # LLM chat panel
│   └── stores/
│       └── backend-health.ts      # Zustand store
└── package.json                   # Build scripts (pyinstaller + tauri)
```

### 3.4 Resources

- [Tauri v2 Sidecar docs](https://v2.tauri.app/develop/sidecar/)
- [tauri-plugin-shell docs](https://v2.tauri.app/plugin/shell/)
- [PyInstaller manual](https://pyinstaller.org/en/stable/)
- [OpenWInD](https://openwind.inria.fr/) — Python library for wind instrument simulation
- [Demakein](https://github.com/pfh/demakein) — Woodwind design & 3D printing
- [Ollama API docs](https://github.com/ollama/ollama/blob/main/docs/api.md) — Local LLM inference
- [silvermine/tauri-plugin-connectivity](https://github.com/silvermine/tauri-plugin-connectivity) — Network detection

---

## 4. Physics-Based Generative AI & Evolutionary Algorithms

### 4.1 Physics-Based Generative Models

These are NOT LLMs. They learn the physics of sound propagation and generate geometry that produces desired acoustic output.

#### Neural Operators for Acoustic Simulation

| Model | What it does | Speed vs FEM | Relevance |
|-------|-------------|-------------|-----------|
| **Fourier Neural Operator (FNO)** | Learns mapping between geometry and pressure field in Fourier space | 1000x faster | Could replace OpenWInD FEM for real-time bore exploration |
| **DeepONet** | Operator network: maps function inputs (bore profile) to function outputs (impedance curve) | 500x faster | Instant impedance prediction from bore geometry |
| **Physics-Informed Neural Operator (PINO)** | Combines data + PDE constraints | 100x faster | Learns wave equation physics without full FEM |
| **Graph Neural Operator** | Mesh-based geometry → acoustic field | 200x faster | Handles complex 3D bore shapes with tone holes |

**Key paper:** Lu et al. (2021) "Learning nonlinear operators via DeepONet" — proves neural operators can learn solution operators of PDEs. Applied to acoustics by multiple groups since.

**Implementation path:**
1. Train FNO on OpenWInD simulation data (bore profile → impedance curve)
2. Embed in React frontend for instant impedance preview
3. Use as differentiable surrogate for gradient-based design

#### Differentiable Acoustics Pipeline

```
Target Impedance Curve
    ↓ (gradient descent)
Neural Operator Surrogate (fast forward)
    ↓ (gradient)
Bore Geometry Parameters
    ↓ (forward)
OpenWInD FEM (verification, occasional)
    ↓
Physical Geometry (STL/STEP)
```

**Key insight:** The neural operator is a *surrogate* — it approximates OpenWInD's FEM at 1000x speed. You can:
1. Run neural operator for rapid exploration (1000 bore profiles in seconds)
2. Verify final design with full FEM (10 seconds)
3. Use neural operator gradients for optimization (not possible with black-box FEM)

#### Variational Autoencoders for Instrument Geometry

| Approach | Input | Output | Training Data |
|----------|-------|--------|--------------|
| **VAE on bore profiles** | Bore radius at N points | Latent space → new bore profiles | OpenWInD simulation library |
| **VAE on 3D meshes** | Triangulated bore surface | Latent space → new geometries | STL library of instruments |
| **Conditional VEA** | Desired impedance + instrument type | Bore geometry | Paired (geometry, impedance) data |

**Usage:** User slides latent dimensions → bore shape morphs in real-time → impedance updates live. The latent space captures the "design manifold" of acoustically valid instruments.

#### Gaussian Process / Bayesian Optimization

For expensive-to-evaluate design spaces:
```
1. Evaluate 10 bore profiles with OpenWInD FEM (expensive)
2. Fit GP surrogate to (geometry → impedance) mapping
3. Use acquisition function (Expected Improvement) to suggest next best profile
4. Evaluate, update GP, repeat
5. Converge on optimal design in ~50 evaluations vs 1000s with grid search
```

**Python:** `scikit-optimize`, `GPyTorch`, `BoTorch`
**Key advantage:** Works with very few evaluations — ideal when OpenWInD is slow.

### 4.2 Evolutionary & Metaheuristic Algorithms

#### Genetic Algorithms (GA) for Bore Optimization

```
Population: 100 bore profiles (random initialization)
Fitness: Impedance peak height at target frequencies
Selection: Tournament selection (top 20% survive)
Crossover: Blend bore profiles (average two parent profiles)
Mutation: Random perturbation of bore radii (±0.5mm)
Elitism: Keep best 5 individuals unchanged
Generations: 50-200
```

**Python implementation:**
```python
import numpy as np
from openwind import imp_edo

def fitness(bore_radii: np.ndarray, target_freqs: list[float]) -> float:
    """Evaluate how well a bore profile plays at target frequencies."""
    # Compute impedance
    impedance = compute_impedance(bore_radii)
    # Score = sum of peak heights at target frequencies
    score = sum(impedance_at(f, impedance) for f in target_freqs)
    return score

def evolve_bore(target_freqs, n_generations=100, pop_size=50):
    """Genetic algorithm for bore profile optimization."""
    # Initialize population
    population = [np.random.uniform(8, 25, n_segments) for _ in range(pop_size)]
    
    for gen in range(n_generations):
        # Evaluate fitness
        scores = [fitness(ind, target_freqs) for ind in population]
        # Select parents (tournament)
        parents = tournament_select(population, scores, pop_size // 2)
        # Crossover + mutation
        offspring = [crossover(p1, p2) for p1, p2 in zip(parents[::2], parents[1::2])]
        offspring = [mutate(child) for child in offspring]
        # Elitism + replacement
        best = sorted(zip(scores, population), reverse=True)[:5]
        population = [ind for _, ind in best] + offspring[:pop_size - 5]
    
    return best_individual(population, scores)
```

**Libraries:**
- `DEAP` — Full GA/GP/ES framework for Python
- `pymoo` — Multi-objective optimization (NSGA-II, NSGA-III)
- `pygad` — Simple GA for neural network weight optimization

#### NSGA-II / Multi-Objective Optimization

Instruments have CONFLICTING objectives:
- Maximize tone hole coverage (more notes) vs minimize bore disruption (cleaner tone)
- Maximize projection (loudness) vs minimize playing resistance
- Maximize intonation accuracy vs minimize instrument length

**NSGA-II** finds the Pareto front — the set of optimal tradeoffs:

```
Objective 1: Impedance peak height (loudness) — MAXIMIZE
Objective 2: Peak frequency accuracy (intonation) — MINIMIZE error
Objective 3: Playing resistance — MINIMIZE

→ Pareto front shows: "you can have 90% intonation accuracy at 70% loudness,
   OR 95% accuracy at 55% loudness, OR 85% accuracy at 80% loudness"
```

**User picks their preferred tradeoff from the Pareto front.**

#### Particle Swarm Optimization (PSO)

Simpler than GA, good for continuous parameter spaces:
```
30 particles (bore profiles) fly through design space
Each particle has position (current bore) and velocity (direction of change)
Personal best: best bore this particle has found
Global best: best bore any particle has found
Update: velocity = inertia + cognitive (toward personal best) + social (toward global best)
```

**Advantages over GA:** No crossover/mutation to design. Faster convergence for smooth landscapes. Naturally handles continuous parameters (bore radii).

#### CMA-ES (Covariance Matrix Adaptation Evolution Strategy)

State-of-the-art for continuous black-box optimization:
- Adapts mutation strength AND direction automatically
- Handles ill-conditioned, non-separable problems
- The "gold standard" for instrument bore optimization

**Library:** `cma` (pure Python, maintained by Nikolaus Hansen)
```python
import cma

def optimize_bore(target_impedance):
    def objective(bore_params):
        computed = compute_impedance(bore_params)
        return np.sum((computed - target_impedance) ** 2)
    
    es = cma.CMAEvolutionStrategy(np.zeros(20), 1.0)  # 20 bore segments
    es.optimize(objective)
    return es.result.xbest
```

#### Simulated Annealing (SA)

Good for discrete decisions (hole positions, key mechanisms):
```
Start: random hole layout
Temperature: starts high (accept worse solutions), cools to 0
Move: randomly shift one hole position
Accept: if better, always accept. If worse, accept with probability e^(-delta/T)
Cooling: T = T * 0.995 each step
```

### 4.3 Hybrid Approaches (Best of Both)

#### GA + Neural Operator (Two-Phase)

```
Phase 1 (fast exploration):
  - GA with 1000 individuals, 50 generations
  - Fitness evaluated by neural operator surrogate (instant)
  - Result: top 10 candidate bore profiles

Phase 2 (precise refinement):
  - CMA-ES on top 3 candidates
  - Fitness evaluated by OpenWInD FEM (accurate, slower)
  - Result: final optimized bore profile
```

#### LLM + Evolutionary (Creative + Optimal)

```
Phase 1 (creative exploration):
  - LLM generates 20 wildly different bore concepts
  - "Make it sound like a didgeridoo but with saxophone range"
  - "Combine shakuhachi timbre with clarinet agility"

Phase 2 (evolutionary refinement):
  - NSGA-II optimizes each concept
  - Multi-objective: tone quality, range, playability, printability

Phase 3 (selection):
  - User compares Pareto fronts from each concept
  - Picks preferred design
```

#### Differentiable + Bayesian (Smart + Precise)

```
1. Bayesian optimization suggests 10 bore profiles to evaluate
2. OpenWInD FEM evaluates each (10 seconds each = 2 minutes)
3. Fit GP to results
4. GP gradients suggest next 5 profiles (gradient-guided search)
5. OpenWInD evaluates those (50 seconds)
6. Fit improved GP
7. Repeat until converged
```

### 4.4 Recommended Implementation for Instrument Designer

#### Phase 1: Evolutionary Optimization (Weekend Project)

Add to the Rust/Python backend:
```python
# backend/evolutionary_optimizer.py

from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.core.problem import Problem

class BoreOptimization(Problem):
    def __init__(self, target_notes, n_segments=20):
        super().__init__(n_var=n_segments, n_obj=2, n_constr=0,
                         xl=5.0, xu=30.0)  # bore radii 5-30mm
        self.target_notes = target_notes
    
    def _evaluate(self, X, out, *args, **kwargs):
        for i, x in enumerate(X):
            impedance = compute_impedance(x)
            # Objective 1: intonation error (minimize)
            out["F"][i, 0] = intonation_error(impedance, self.target_notes)
            # Objective 2: playing ease (minimize = easier)
            out["F"][i, 1] = -peak_prominence(impedance, self.target_notes)

algorithm = NSGA2(pop_size=50)
result = minimize(BoreOptimization(["C4", "D4", "E4", "F4", "G4"]),
                  algorithm, ('n_gen', 100), seed=42)
# result.X = Pareto-optimal bore profiles
# result.F = corresponding objective values
```

Frontend: show Pareto front plot, let user click preferred tradeoff.

#### Phase 2: Neural Operator Surrogate (Month Project)

1. Generate 10,000 bore profiles with random parameters
2. Run OpenWInD on each (batch job, ~10 hours)
3. Train DeepONet on (bore → impedance) pairs
4. Embed trained model in frontend via ONNX Runtime (WebAssembly)
5. Real-time impedance preview as user adjusts bore parameters

#### Phase 3: Full AI-Assisted Design (Quarter Project)

1. LLM chat panel for creative direction
2. Evolutionary optimization for exploration
3. Neural operator for instant feedback
4. Bayesian optimization for final refinement
5. OpenWInD FEM for verification

### 4.5 Open-Source Tools Reference

| Tool | Type | Language | Install |
|------|------|----------|---------|
| `pymoo` | Multi-objective optimization (NSGA-II/III) | Python | `pip install pymoo` |
| `DEAP` | Genetic algorithms, genetic programming | Python | `pip install deap` |
| `cma` | CMA-ES evolution strategy | Python | `pip install cma` |
| `scikit-optimize` | Bayesian optimization | Python | `pip install scikit-optimize` |
| `BoTorch` | Bayesian optimization (PyTorch) | Python | `pip install botorch` |
| `PyTorch` | Neural operators (FNO, DeepONet) | Python | `pip install torch` |
| `JAX` | Differentiable physics | Python | `pip install jax` |
| `deepxde` | Physics-informed neural networks | Python | `pip install deepxde` |
| `神经算子` | Fourier Neural Operator | Python | github.com/neuraloperator/neuraloperator |
| `Ollama` | Local LLM inference | Binary | ollama.com |
| `OpenWInD` | Acoustic FEM simulation | Python | `pip install openwind` |
| `Demakein` | Woodwind bore design | Python | `pip install demakein` |
