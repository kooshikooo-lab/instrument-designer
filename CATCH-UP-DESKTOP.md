# Desktop Catch-Up Document (2026-07-22)

## Current State
- **Branch:** experiment/tmm-improvements (latest: 7ca44fe)
- **Both machines synced** and on same commit
- **Tailscale active:** Laptop 100.100.66.117, Desktop 100.69.113.41
- **LAN chat:** `python backend/lan_chat.py send "message" 100.69.113.41` (one-shot mode)

---

## What's Been Done (Laptop Sessions 2026-07-22)

### 1. TMM Acoustics Port (tmm_acoustics.py) — CRITICAL, NOW COMMITTED
- Faithful Python port of chalumier's ResonanceMath.kt + Instrument.kt
- `TMMInstrument` class: constructor takes inner/outer positions+diameters, hole params, closed_top
- `find_resonance(initial_wl, fingerings, n_register)` — root-finding resonance search
- `tmm_instrument_from_radii()` — factory function from radii arrays
- `SPEED_OF_SOUND = 346100.0` mm/s
- Tests pass at 0% error vs chalumier Java output
- **Was untracked locally, NOW committed (f039f8f)**

### 2. Sequential Bore Optimizer (tmm_optimizer_sequential.py)
- Bordeaux method (Noreland 2013) for tone hole placement
- Phase 1: Bore length optimized as FREE variable via Nelder-Mead
- Phase 2: Holes placed bottom-to-top, one at a time (combined fingering for closed-open)
- Phase 3: 4-stage Nelder-Mead refinement (bore-length → radii → holes → simultaneous)
- **Benchmark results:**

| Instrument | Sequential | Seq+Refine | Time | Holes |
|---|---|---|---|---|
| Chalumeau C (closed-open) | 18.8c | **0.00c** | 13.9s | 5 |
| Bass Chalumeau Bb (closed-open) | 26.8c | **0.00c** | 50.7s | 7 |
| Soprano Sax Bb (open-open) | 52.2c | **0.00c** | 20.1s | 6 |
| Alto Sax Eb (open-open) | 386c | 126c | 19.3s | 5 (WIP) |

### 3. Key Discovery: Open-Open vs Closed-Open
- **Closed-open (clarinets):** holes near bell → lower freq, near reed → higher freq. Monotonic. Bordeaux works perfectly.
- **Open-open (sax/flute):** non-monotonic freq response. Independent placement needed.
- This means the Bordeaux method was designed for clarinets, NOT saxophones.

### 4. Bugs Fixed in Sequential Optimizer (6 total)
1. Fundamental getting a hole → skip fundamental
2. Fingering wrong → open ALL previous holes + new one
3. Powell hang on >10 vars → Nelder-Mead 4-stage refinement
4. Bore length FIXED → now free variable
5. Open-open needs independent placement → separate code path
6. Holes past bore end → bore extension + break

### 5. Modular Component System (modular_components.py)
- BoreSection, Bell, Neck, Extension, Joint, Mouthpiece
- TenonConnection (cork/friction/threaded/slip)
- KeyHole model (ring/plateau/spatula, pad sizes 7-26mm)
- PVC pipe cross-reference (3/4" = chalumeau, 1" = bass clarinet, 2" = bell)
- Pre-built assemblies: chalumeau C, bass chalumeau Bb, bass clarinet Bb, soprano sax Bb

### 6. UI Design Branches (3 options)
- ui/card-design: Card-based with AI art, sound player, spectrum analyzer, impedance viz
- ui/magazine-design: Editorial magazine layout
- ui/wiki-design: Minimal monospace wiki
- All pushed, all have AIInstrumentArt, InstrumentSoundPlayer, SpectrumAnalyzer, ImpedanceVisualization

### 7. LAN Chat (lan_chat.py)
- One-shot send mode added: `python lan_chat.py send "msg" 100.69.113.41`
- Server runs on port 9123 over Tailscale

---

## Key Files Reference

### Core Acoustics
- `backend/tmm_acoustics.py` — TMM phase resonance (THE critical file, now committed)
- `backend/tmm_acoustics_jax.py` — JAX vectorized TMM (different API, NOT drop-in)

### Optimizers
- `backend/tmm_optimizer.py` — Baseline L-BFGS-B
- `backend/tmm_optimizer_v2.py` — Powell + L-BFGS-B
- `backend/tmm_optimizer_multi.py` — Multi-start optimizer
- `backend/tmm_optimizer_sequential.py` — Sequential Bordeaux (THE main one now)

### Benchmarks
- `backend/benchmark_all.py` — Sequential + Nelder-Mead refinement (FIXED, 3/4 converge)
- `backend/benchmark_optimizers.py` — Comparison of all optimizers

### Tests
- `backend/test_v3_sequential.py` — Sequential with correct fingering + bore constraint
- `backend/test_fixed_sequential.py` — Fixed sequential test
- `backend/test_sequential.py` — Basic sequential test
- `backend/test_independent_vs_combined.py` — Open-open vs closed-open comparison
- `backend/test_open_vs_closed.py` — Single-hole frequency sweep

### Debug Scripts
- `backend/debug_fingering.py` — Fingering construction debugging
- `backend/debug_hole.py` — Single-hole position sweep
- `backend/debug_alto.py` — Alto sax debugging
- `backend/test_phase_cost.py` — Phase cost function test (desktop's file)

### Design System
- `backend/modular_components.py` — BoreSection, Bell, Neck, Extension, etc.
- `backend/printability.py` — 3D printability validator
- `backend/target_frequencies.py` — All instrument target frequencies
- `woodwind_designer/engine/design_server.py` — FastAPI server

### Communication
- `backend/lan_chat.py` — Tailscale LAN chat with one-shot send mode

---

## What's Pending

### High Priority
1. **Integrate sequential optimizer into design_server.py** — make tone hole optimization available via API
2. **Fix alto sax** — open-open non-monotonic issue, only 5 holes placed instead of 6
3. **Get desktop's phase-based resonance** — replace peak-finding with unwrapped phase (Ernoult)
4. **Verify tmm_acoustics.py works on desktop** — run `python -c "from tmm_acoustics import TMMInstrument; print('OK')"`

### Medium Priority
5. Run bass clarinet design using modular components + sequential optimizer
6. Test on real PVC pipe dimensions
7. Merge sequential optimizer into the web UI

### Low Priority
8. Continue UI design work (card/magazine/wiki branches)
9. Flute calculator enhancements

---

## Laptop Environment
| Item | Value |
|------|-------|
| OS | Windows 11 |
| Python | 3.12.10 |
| Java | JDK 17 Temurin 17.0.19 |
| PowerShell | 5.1.26100.8875 |
| Tailscale | 100.100.66.117 |
| jax | 0.11.0 |
| scipy | 1.18.0 |
| fastapi | 0.139.0 |

---

## How to Communicate
- **GitHub Issues** — async coordination (Issues #1, #9, #10, #11, #12)
- **LAN Chat** — `python backend/lan_chat.py send "msg" 100.69.113.41` (one-shot)
- **Tailscale** — direct ping/SCP between machines
