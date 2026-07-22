# Desktop Session: Coordination & Code Audit (2026-07-22)

**Machine:** Desktop (Windows)
**Branch:** `experiment/tmm-improvements`
**Goal:** Audit codebase state, identify blockers, set up cross-machine communication

---

## Codebase Audit Findings

### CRITICAL: Missing `tmm_acoustics.py`
The file `backend/tmm_acoustics.py` does **not exist** on any branch (`main`, `experiment/tmm-improvements`, `experiment/flute-pvc`). It was never committed.

**Impact:** The following files all import from it and will fail:
- `backend/tmm_optimizer_v2.py` — imports `tmm_instrument_from_radii`, `SPEED_OF_SOUND`
- `backend/benchmark_diatonic.py` — imports `tmm_instrument_from_radii`, `SPEED_OF_SOUND`
- `backend/benchmark_chalumeau.py` — imports `tmm_instrument_from_radii`, `SPEED_OF_SOUND`
- `test_tmm_v2.py` — imports `TMMInstrument`, `SPEED_OF_SOUND`, `end_flange_length_correction`
- `test_optimizer.py` — imports `TMMInstrument`, `SPEED_OF_SOUND`, `end_flange_length_correction`
- `test_diagnose.py` — imports `TMMInstrument`, `SPEED_OF_SOUND`, `end_flange_length_correction`

**What `tmm_acoustics.py` must contain:**
- `SPEED_OF_SOUND` constant (346100.0)
- `end_flange_length_correction()` function
- `hole_length_correction()` function
- `TMMInstrument` class with:
  - `find_resonance(initial_wl, fingerings, n_register)` — root-finding resonance search
  - `frequency_from_wavelength(wl)` — wavelength → frequency conversion
  - Constructor: inner_positions, inner_diameters, outer_diameters, hole_positions, hole_diameters, hole_lengths, closed_top
- `tmm_instrument_from_radii()` factory function — creates TMMInstrument from bore radii array

**Note:** `tmm_acoustics_jax.py` exists with the JAX-vectorized version, but has a different API (`build_action_chain_v2`, `make_rms_cost`, `lax.scan`). It does NOT have `TMMInstrument` or `tmm_instrument_from_radii`.

### Dependencies Installed (but missing from pyproject.toml)
| Package | Version | In pyproject.toml? |
|---------|---------|-------------------|
| scipy | 1.18.0 | NO |
| pymoo | 0.6.2 | NO |
| pydantic | 2.13.4 | NO |
| fastapi | 0.139.2 | NO |
| uvicorn | 0.51.0 | NO |
| PySide6 | 6.11.1 | YES |
| jax | NOT INSTALLED | NO |

### Branch Status
- Current branch: `experiment/tmm-improvements`
- Clean working tree (only `test_phase_cost.py` and `tmp_issue.md` untracked)
- `bore_optimizer_lbfgs.py` was DELETED in this branch (absorbed into `tmm_optimizer_v2.py`)

### Files That DO Exist and Work
- `backend/tmm_acoustics_jax.py` — JAX TMM (358 lines, different API from what's needed)
- `backend/tmm_optimizer_v2.py` — Powell+L-BFGS-B two-phase optimizer (261 lines)
- `backend/tmm_optimizer_multi.py` — Multi-start wrapper (146 lines)
- `backend/bore_optimizer.py` — Original NSGA-II (741 lines, depends on pymoo)
- `backend/modular_components.py` — Modular instrument parts (864 lines)
- `backend/printability.py` — FDM printability validator (240 lines)
- `backend/flute_calculator.py` — Flutomat/Benade flute calculator
- `backend/mouthpiece_models.py` — Mouthpiece models
- `backend/tone_hole_corrections.py` — Tone hole corrections
- `backend/target_frequencies.py` — Harmonic series by instrument type

---

## Environment Differences

### Desktop (this machine)
- **OS:** Windows 10 Home, Build 19045
- **Python:** 3.14.6
- **Java:** 1.8.0_333 (needs JDK 17 for chalumier)
- **Packages:** scipy 1.18.0, pymoo 0.6.2, pydantic 2.13.4, fastapi 0.139.2, uvicorn 0.51.0, PySide6 6.11.1
- **NOT installed:** jax
- **WSL2:** BLOCKED (BIOS virtualization disabled)
- **Path:** `C:\Users\Admin\Desktop\Woodwind design automation\woodwind-designer`

### Laptop (confirmed from chat logs)
- **OS:** Windows 11
- **Python:** ?
- **Java:** JDK 17 Temurin 17.0.19 (installed via winget, on PATH)
- **Packages:** ? (likely has jax)
- **WSL2:** Cannot run (BIOS virtualization disabled)
- **Known:** Has `tmm_acoustics.py` locally (never pushed)

### Windows Version Impact
- Both machines use `spawn` multiprocessing (same behavior on Win 10/11)
- Python 3.14 on desktop may have different package compatibility than laptop
- Path differences: Desktop user is `Admin`, laptop user is different
- ProcessPoolExecutor: 1.67x on Windows spawn, 3-5x on Linux fork (WSL2 blocked on both)

---

## Communication Protocol Established

### Chat Log System
1. **Session logs:** `chat-logs/YYYY-MM-DD-<topic>.md` — per-session work log
2. **LIVE-CHAT-LOG.md:** Running coordination file — append-only, both machines update
3. **GitHub Issues:** Formal task tracking, assignments, blockers
4. **Branches:** `experiment/*` for features, `main` for stable

### Protocol
1. Start session: `git pull` + read LIVE-CHAT-LOG.md + `gh issue list`
2. Work: commit to feature branches, push early and often
3. End session: update LIVE-CHAT-LOG.md, update relevant GitHub issues
4. Check for conflicts before starting work on shared files

---

## Task Assignments (via GitHub Issues)

See Issue #9 for full coordination details.

### Laptop Tasks
- **P0:** Create `backend/tmm_acoustics.py` with TMMInstrument class (or confirm it exists locally)
- **P1:** Run diatonic benchmarks on known working code
- **P2:** Continue UI work (card/magazine/wiki design branches)

### Desktop Tasks
- **P0:** Fix `pyproject.toml` (Issue #5)
- **P1:** Set up WSL2 for Linux parallelization
- **P2:** Review and integrate TMM optimizer v2 into design_server.py

---

*Session ended: 2026-07-22*
