# Branch: laptop

> Current active development branch. 77 commits ahead of main, 0 behind.

## Purpose

All active development happens here. This is the integration branch for the acoustic engine, optimizer, instrument library, Tauri sidecar, and research.

## What It Has

| Feature | Status |
|---------|--------|
| KeefeLoss viscothermal losses | ✅ Integrated |
| true_wavelength_near / true_nth_wavelength_near | ✅ Ported from chalumier |
| Per-note register support | ✅ `Union[int, List[int]]` |
| Two-phase optimizer (DE → L-BFGS-B) | ✅ Created |
| Staged optimizer (3-stage) | ✅ KeefeLoss integrated |
| 91 instruments, 10 families | ✅ |
| Hole diameter co-optimization | ✅ Added to benchmark |
| Absolute RMS metric | ✅ (correct) |
| Tauri sidecar integration | ✅ Build verified |
| Benchmark audit | ✅ 3 bugs found, 5 design issues |
| Acoustics research | ✅ 40+ references |
| Maker compromises research | ✅ 10 objectives |
| ChatGPT/Claude prompts | ✅ 6 ready-to-paste |

## What It Doesn't Have

| Feature | Branch | Status |
|---------|--------|--------|
| AI assistant | `option-a-tauri` | Desktop decides |
| Optimization UI | `option-a-tauri` | Desktop decides |
| Wiki tab | `option-a-tauri` | Desktop decides |
| Chalumier integration (SVG, build trigger) | `origin/experiment-chalumier-integration` | Needs merge |
| Trumpet model | `experiment/trumpet-openwind` | Side branch |

## Merge Plan

1. Merge `experiment/lbfgs-bore` (clean, useful optimizer)
2. Merge `ui/card-design` (clean, enriches UI)
3. Merge `origin/experiment-chalumier-integration` (conflicts, manual resolution needed)
4. Push to origin
5. Merge `laptop` → `main`
6. Desktop pulls `main`

## Key Files

| File | Purpose |
|------|---------|
| `backend/tmm_acoustics.py` | Core TMM engine |
| `backend/physics/losses.py` | KeefeLoss model |
| `backend/two_phase_optimizer.py` | DE → L-BFGS-B |
| `backend/staged_optimizer.py` | 3-stage refinement |
| `backend/tmm_optimizer_sequential.py` | Sequential + DE + L-BFGS-B |
| `backend/benchmark_all.py` | Full benchmark (14 instruments) |
| `backend/cadquery_export.py` | 91 instruments, STL export |
| `web/src-tauri/` | Tauri desktop integration |
