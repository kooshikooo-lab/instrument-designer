# Session Log — 2026-07-25 (Laptop)

## Summary
Session focused on merging desktop branches, integrating KeefeLoss viscothermal losses into the full TMM pipeline, adding two-phase Noreland optimizer, expanding instrument library to 91 instruments, fixing Tauri sidecar integration, and cleaning up frontend. Tauri build verified successful. Desktop chat confirmed working on port 9123. LAN chat server on desktop timed out by end of session.

---

## Branch: `experiment/cadquery-test`

### Commits Made This Session
1. `d3c2873` — feat: Add professional low clarinets (contra-alto, contra-bass, octo-contra) + baritone saxes + mouthpieces
2. `ede73b4` — fix: naming consistency — contra-alto / contra-bass (hyphenated), octo-contra-bass
3. `8450dd1` — feat: KeefeLoss viscothermal losses integrated into TMM + staged optimizer
4. `dedbe0f` — feat: Two-phase optimizer (Noreland) + KeefeLoss viscothermal losses
5. `5485d23` — Merge remote-tracking branch 'origin/experiment/bore-profile-optimization'
6. `e83dfaa` — Merge remote-tracking branch 'origin/experiment-staged-optimization'
7. `17057e6` / `0f5a23d` — feat: Complete two-phase optimizer + KeefeLoss + Tauri sidecar integration

### Merged Desktop Branches
- `origin/exp/impedance-primary` — KeefeLoss losses, OpenWInD FEM solver
- `origin/experiment-staged-optimization` — Noreland staged optimizer
- `origin/experiment/bore-profile-optimization` — Two-phase optimizer, chromatic flute, cross-fingering charts

### Merged `refactor/architecture-redesign`
- `325a2ab` — Merge branch 'refactor/architecture-redesign' into experiment/cadquery-test

---

## KeefeLoss Viscothermal Integration

### What Was Done
- **Created** `backend/physics/losses.py` — KeefeLoss class implementing Keefe 1984 model
  - Sutherland's temperature correction for viscosity/thermal conductivity
  - Computes loss factor (complex R + iX) per frequency
  - Loss factor magnitude < 1 (damping), phase shift applied
- **Modified** `backend/tmm_acoustics.py`:
  - `TMMInstrument.loss_model` parameter (default None = lossless)
  - `pipe_reply_phase_with_loss()` — applies bore loss phase shift to pipe element
  - `resonance_phase()` — applies losses to resonance computation
  - `phase_cost_with_offset()` — includes losses in cost evaluation
  - `tmm_instrument_from_radii()` — accepts loss_model parameter
  - `phase` stores diameter for loss calculation
- **Modified** `backend/staged_optimizer.py` — passes KeefeLoss through to TMM
- **Modified** `backend/two_phase_optimizer.py` — KeefeLoss integrated throughout

### Verification
- Loss factor magnitude: 0.3864 (< 1, correct damping)
- Phase shift: -0.000405 rad (small, correct for 1200mm pipe)
- Loss factor decreases with frequency (correct physics)

---

## Two-Phase Optimizer (Noreland Approach)

### Architecture
**Phase 1: Global Search** — `scipy.optimize.differential_evolution`
- Cost: `phase_cost_with_offset` (fast, ~1.4ms/call)
- Finds global basin of attraction
- 200 generations, popsize=15

**Phase 2: Local Refinement** — `scipy.optimize.l-bfgs-b`
- Cost: `peak_cost_nearest` (correct, ~140ms/call)
- Refines within basin found by DE
- 500 iterations max

### Key Finding: Register Detection
- Peak-cost phase MUST use register detection
- `n_register = 1 if closed_top else 2` — auto-detect from bore topology
- Without this, optimizer targets wrong harmonic → -3000c error

### Pipeline
`seed sampling → DE (global, fast) → L-BFGS-B (local, correct)`

---

## Instrument Library Expansion (55 → 91)

### New Instruments Added
**Professional Low Clarinets:**
- Contra-Alto Clarinet (EEb) — verified, measurements from JD Woodwinds
- Contra-Bass Clarinet (BBb) — verified, measurements from JD Woodwinds
- Octo-Contra-Alto Clarinet (EEEb) — verified
- Octo-Contra-Bass Clarinet (BBBb) — verified

**Baritone Saxophones:**
- Printgear3D (3D-printed, documented)
- Selmer Mark VI (vintage, measurements)
- Yamaha YBS-62 (professional)
- Selmer Series III (professional)

**Professional Mouthpieces:**
- Bass clarinet mouthpiece (Chedeville, Runyon, Yamaha)
- Contra-bass clarinet mouthpiece
- Baritone sax mouthpiece (D'Addario, Otto Link, Berg Larsen)
- Bass sax mouthpiece
- Alto/Tenor sax mouthpieces
- Clarinet mouthpieces
- Trumpet mouthpieces (3C, 7C)
- Trombone mouthpiece

**Membrane Instruments:**
- Diplica (reed + membrane)
- Sipsi (horsehair reed)
- Zummara (double reed + membrane)
- Membrane clarinet

### Naming Convention (Locked)
contra-alto, contra-bass, octo-contra-bass — all hyphenated consistently

---

## Tauri Sidecar Integration

### Changes
- `web/src-tauri/tauri.conf.json` — shell plugin allowlist for python, CSP for 127.0.0.1
- `web/src-tauri/src/commands.rs` — uses `ShellExt`, `CommandChild` from tauri_plugin_shell, mutex drop before await
- `web/src-tauri/Cargo.toml` — `tauri-plugin-shell` dependency
- `web/src-tauri/src/tauri.ts` — `ensureBackendRunning()` checks if backend is alive before API calls
- `web/src/utils/api.ts` — unified fetch with async base URL

### Backend Launch Command
```
python -m uvicorn woodwind_designer.engine.design_server:app --host 127.0.0.1 --port 8000
```

### Build Status
- Tauri build: SUCCESS (~4 min)
- MSI + NSIS installers generated

---

## Frontend Cleanup

### Removed
- Broken advisor UI (getAdvisorStatus, analyzeDesign, storeDesignInMemory, AdvisorResult, AdvisorSuggestion)
- Non-existent API exports from api.ts

### Fixed
- `getDesignDownloadUrl()` → async (await fetch, get blob URL)
- Added `downloadUrl` state for anchor tag download
- Fixed unused `isTauri` import in DesignTab.tsx

---

## Merged Desktop Branches

### From `exp/impedance-primary`
- KeefeLoss viscothermal losses
- OpenWInD FEM solver plugin interface

### From `experiment-staged-optimization`
- 3-stage Noreland optimizer (DE → L-BFGS-B → Nelder-Mead)
- Progressive refinement with seed sampling

### From `experiment/bore-profile-optimization`
- Two-phase optimizer (Noreland approach)
- Chromatic flute module
- Cross-fingering charts
- Hole diameter optimization

---

## TMM vs OpenWInD FEM Verification
- Cylinder: 1200mm, radius 12.5mm
- TMM: 71.0 Hz
- OpenWInD FEM: 70.8 Hz
- Agreement: 0.3%

---

## Communication Status
- Desktop IP: 100.69.113.41 (Tailscale)
- Laptop IP: 100.100.66.117 (Tailscale)
- Ping: 4ms ✓
- LAN chat port 9123: Connection timed out (server not running by end of session)
- LAN chat port 9999: Connection timed out
- Desktop chat server was running earlier (2026-07-23 logs show port 9123)
- Desktop chat server confirmed working before timeout — sent test message, got ACK response

---

## Next Steps
1. **Desktop:** Pull `experiment/cadquery-test`, verify KeefeLoss + two-phase optimizer
2. **Merge** `experiment/cadquery-test` → `main` or update PR #16
3. **Profile** two-phase optimizer on real instruments (clarinet 12-hole sequential)
4. **Investigate** impedance-first solver (`exp/impedance-primary`) and GP correction model (`exp/gp-correction-model`)
5. **Architecture:** Remove `Port.is_open`, unify speed_of_sound, implement OpenWInD FEM plugin
6. **UI:** Define InstrumentModel as single source of truth, wire build123d CAD export

---

## Branches
- `experiment/cadquery-test` — current, all work, pushed
- `refactor/architecture-redesign` — synced
- PR #16 open: https://github.com/kooshikooo-lab/instrument-designer/pull/16
- Remote branches merged: exp/impedance-primary, exp/gp-correction-model, experiment-staged-optimization, experiment/bore-profile-optimization
