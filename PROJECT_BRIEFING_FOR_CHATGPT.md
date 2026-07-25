# Computational Wind Instrument Design Platform — Project Briefing for ChatGPT

## Executive Summary

We are building a **general computational wind instrument design platform** that combines:
- **TMM (Transfer Matrix Method)** for fast optimization (~1.7ms/note)
- **OpenWInD FEM** for high-fidelity validation (~10-50s/note)
- **Staged optimization** with physics-informed correction models

**Current milestone:** Architecture redesign complete, solver-agnostic core working, TMM/FEM agreement verified (71.0 vs 70.2 Hz on cylindrical bore). Bass clarinet is the first target instrument (<5 cents RMS chromatic).

---

## Goals

### Primary (Bass Clarinet)
- Chromatic intonation <5 cents RMS across 2+ octaves
- 12-14 toneholes, graduated diameters (14.5→20mm)
- Register vent at 80mm from reed, 3.5mm diameter
- Effective length ~1159mm (optimized from 1200mm)
- Bell: 220mm Bessel flare, 52mm ID (deferred — degrades 12ths)

### Platform (General)
- Instrument-agnostic solver layer (TMM, FEM, future BEM/CFD)
- AcousticNetwork as universal intermediate representation
- Physics plugin system for interchangeable models
- Correction model: learns TMM error vs FEM for future optimization
- CAD export (STL/STEP) for manufacturing
- Web UI for interactive design (React + Three.js + Tauri)

---

## Architecture (5-Layer, Solver-Agnostic)

```
┌─────────────────────────────────────────────────────────────┐
│ 1. USER INTERFACE (React + Three.js + Tauri)               │
│    DesignTab, parameter sliders, 3D viewer, STL export     │
├─────────────────────────────────────────────────────────────┤
│ 2. INSTRUMENT DEFINITION (builders)                        │
│    ClarinetBuilder, BassClarinetBuilder, BrassBuilder      │
│    → produces AcousticNetwork                               │
├─────────────────────────────────────────────────────────────┤
│ 3. ACOUSTIC MODEL (AcousticNetwork)                        │
│    Segments (cylindrical/conical bore sections)            │
│    Ports (Tonehole, RegisterVent, Valve) — PHYSICAL only   │
│    Boundaries (reed, bell, radiation)                      │
│    Fingerings (toneholes[] + register: bool) — MUSICAL     │
│    CoordinateTransform (chalumier/internal/openwind)       │
├─────────────────────────────────────────────────────────────┤
│ 4. PHYSICS SOLVERS (plugin interface)                      │
│    TMMSolver — wraps chalumier TMM (lossless, phase-based) │
│    OpenWindSolver — wraps OpenWInD FEM (viscothermal)      │
│    Common interface: compute_frequencies(), resonance_phase()│
├─────────────────────────────────────────────────────────────┤
│ 5. OPTIMIZATION FRAMEWORK                                  │
│    BoreOptimizer (DE + L-BFGS-B), FingeringOptimizer       │
│    Staged: Stage 1 (bore+toneholes) → Stage 2 (register) → │
│    Stage 3 (joint)                                          │
│    CorrectionModel: learns TMM↔FEM residual                 │
└─────────────────────────────────────────────────────────────┘
```

### Key Design Decisions

1. **Solver doesn't know instrument type** — receives AcousticNetwork graph
2. **Physics plugins are swappable** — propagation, junction, tonehole, radiation, losses, excitation
3. **CoordinateTransform is the ONLY place conversions happen** — no coordinate math outside
4. **Fingering model separates physical from musical** — Port has no `is_open`; Fingering has `toneholes[]` + `register`
5. **Vent hierarchy**: `Port` → `Tonehole` (length_control) / `RegisterVent` (mode_selection, preferred_harmonic=3)

---

## Current State (July 24, 2026)

### ✅ Completed
- **Architecture**: All 5 layers implemented on `refactor/architecture-redesign`
- **TMM Core**: Ported from chalumier Kotlin, phase-based resonance, bell→reed walk
- **OpenWInD FEM**: Working through `OpenWindSolver`, mm→m conversion
- **Builders**: ClarinetBuilder, BassClarinetBuilder, BrassBuilder
- **Physics plugins**: Interfaces defined (LosslessPropagation, LosslessJunction, SimpleTonehole, BesselRadiation, NoLoss, ReedExcitation)
- **CoordinateTransform**: Chalumier (0=bell) ↔ Internal (0=reed) ↔ OpenWInD (0=mouthpiece)
- **Property tests**: 4/4 pass (coordinate inverses, analytical tube)
- **TMM vs FEM**: 71.0 Hz vs 70.2 Hz on 1200mm cylinder — **agreement confirmed**
- **Speed of sound**: Unified to 346100 mm/s (chalumier value)
- **Register vent**: Corrected to 1.75mm radius (3.5mm diameter) per Benade/Nederveen
- **Fingering convention**: CHALUMIER ORDER (index 0 = nearest bell) locked

### 🔴 Pending (Critical)
| Task | Description | Blocker |
|------|-------------|---------|
| TMM stash fixes | `true_wavelength_near`, `reed_virtual_length` (493mm), `whistle_clip` | Laptop has fixes in stash, need to merge |
| KeefeLoss plugin | Viscothermal losses for TMM | Interface exists, implementation needed |
| Saxophone n_register=2 | Open-open instruments use n=2 for fundamental | Architecture supports, needs builder update |
| Staged optimization | Stage 1→2→3 pipeline | FingeringOptimizer ready, needs orchestration |

### 🟡 High Priority
- **Correction model**: TMM error vs FEM (learned residual for optimization)
- **InstrumentModel schema**: Single source of truth for UI/CAD/solvers
- **CAD export**: STL/STEP via build123d (port from option-b-web-app commit 6cdc3df)
- **Bass clarinet validation**: Chromatic <5c RMS with corrected TMM

---

## Physics & Conventions (LOCKED)

### Coordinate Systems
| System | Position 0 | Position L | Walk Direction |
|--------|------------|------------|----------------|
| Chalumier | Bell (open) | Reed (closed) | Bell → Reed (ascending) |
| Internal | Reed (closed) | Bell (open) | Bell → Reed (descending) |
| OpenWInD | Mouthpiece | Bell | Mouthpiece (closed) | Bell (open) | Mouthpiece → Bell |

### Fingering Convention
- **Tonehole positions**: `hole_positions[0]` = nearest bell (CHALUMIER ORDER)
- **Fingering arrays**: `fingerings[i]` maps to `hole_positions[i]`
- **Standard clarinet chart**: H1 = nearest reed → REVERSED vs chalumier
- **Conversion**: `chart_to_chalumier()` in `fingering_reference.py`

### Register Vent Physics (Benade 1976, Nederveen 1998)
- Suppresses fundamental (1st mode) → 3rd harmonic (clarion) dominates
- Position: x/L ≈ 0.05-0.08 → 80mm on 1.2m bass clarinet ✓
- Diameter: 3-4mm typical → 3.5mm set ✓
- n_register=1 (chalumeau, closed) → n_register=2 (clarion, open)

---

## Tools & Dependencies

| Category | Tools |
|----------|-------|
| **TMM** | `tmm_acoustics.py` (chalumier port), NumPy, SciPy |
| **FEM** | `openwind` (pip install openwind), FEM impedance computation |
| **Optimization** | SciPy DE, L-BFGS-B, Nelder-Mead |
| **CAD** | build123d (STL/STEP), trimesh |
| **UI** | React 18, TypeScript, Three.js (r158), Tauri 2.0 |
| **Testing** | unittest, property-based tests |
| **Coordination** | GitHub Issues (#1 project hub, #15 backup comms) |

---

## Repository Structure (Key Files)

```
instrument-designer/
├── backend/
│   ├── core/
│   │   ├── network.py          # AcousticNetwork, Segment, Port, Tonehole, RegisterVent, Fingering
│   │   └── coordinates.py      # CoordinateTransform
│   ├── physics/                # Plugin interfaces
│   │   ├── propagation.py
│   │   ├── junction.py
│   │   ├── tonehole.py
│   │   ├── radiation.py
│   │   ├── losses.py
│   │   └── excitation.py
│   ├── solvers/
│   │   ├── tmm_solver.py       # TMMSolver
│   │   └── openwind_solver.py  # OpenWindSolver
│   ├── instruments/
│   │   ├── clarinet.py         # ClarinetBuilder
│   │   ├── bass_clarinet.py    # BassClarinetBuilder
│   │   └── brass.py            # BrassBuilder
│   ├── optimization/
│   │   ├── bore_optimizer.py
│   │   └── fingering_optimizer.py
│   ├── tests/
│   │   ├── test_properties.py
│   │   └── test_tmm_vs_openwind.py
│   ├── tmm_acoustics.py        # Core TMM engine
│   └── fingering_reference.py  # Convention conversion
├── web/
│   ├── src/
│   │   ├── components/         # React components
│   │   ├── api.ts              # Backend API client (bugs being fixed)
│   │   └── tauri.ts            # Tauri transport
│   └── src-tauri/              # Rust backend
└── chat-logs/                  # Session documentation
```

---

## Known Issues & Research Gaps

### TMM Limitations (vs FEM)
| Aspect | TMM | OpenWInD FEM |
|--------|-----|--------------|
| Tonehole model | SimpleTonehole (shunt, tan(kL)) | Full bore-hole junction |
| Open-hole error | Underestimates by 137-225 cents | Reference |
| Losses | None (unless KeefeLoss added) | Viscothermal + radiation |
| Speed | ~1.7ms/note | ~10-50s/note |

### Correction Model Strategy
```
Geometry → TMM → f_TMM
       → FEM → f_FEM (sparse sampling)
       → NeuralNet: (geometry, f_TMM) → Δf
       → Corrected: f_TMM + Δf
```

### Bell Model
- 220mm Bessel flare degrades 12ths from 9.5c → 423c
- Deferred until chromatic baseline validated

---

## Questions for ChatGPT

1. **Correction Model Architecture**: Best approach for learning TMM→FEM residual? Gaussian Process vs small MLP? Training data strategy?

2. **Staged Optimization Convergence**: How to guarantee Stage 3 doesn't escape local minimum found in Stage 1? Trust region? Warm-start L-BFGS-B?

3. **Register Vent Joint Optimization**: Should vent position/size be continuous variables in Stage 3, or discrete choices?

4. **Saxophone Open-Open**: Bore profile deviations essential (Lefebvre 2011). How to parameterize deviations for optimizer? Control points on radius profile?

5. **InstrumentModel Schema**: What's the minimal JSON schema that captures: bore profile, toneholes (pos/radius/length), register vents, joints, metadata?

6. **Validation Targets**: Beyond intonation RMS, what acoustic metrics matter for playability? Input impedance magnitude/phase, playing frequency vs impedance peaks, spectral centroid?

---

## Next Session Priorities

1. Merge laptop's TMM stash fixes (`true_wavelength_near`, `reed_virtual_length`, `whistle_clip`)
2. Implement `KeefeLoss` plugin for viscothermal TMM
3. Run Stage 1 bore+tonehole optimization on bass clarinet (register vent closed)
4. Define `InstrumentModel` TypeScript interface + Python dataclass
5. Port build123d STEP export from option-b-web-app

---

## Communication Protocol

- **Primary**: GitHub Issue #1 (Project Hub) — all decisions, logs, questions
- **Backup**: GitHub Issue #15 — when Tailscale down
- **Branch**: `refactor/architecture-redesign` (main development)
- **Laptop branches**: `experiment/bore-profile-optimization`, `experiment/tmm-improvements`

---

*Generated 2026-07-24 for ChatGPT consultation. Architecture follows ChatGPT 2026-07-24 recommendations (see chat-logs/chatgpt-architecture-recommendations.txt).*