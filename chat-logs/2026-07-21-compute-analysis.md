# Compute Needs Analysis — Instrument Designer
## Last updated: 2026-07-21

---

## Architecture

Both Web App and Tauri Desktop use the **same compute backend**:

```
[Frontend] → HTTP → [FastAPI Server (Python)] → [Optimizer] → [OpenWInD]
```

- **Web App:** Browser → HTTP → Python server (must be running separately)
- **Tauri Desktop:** Tauri window → Tauri HTTP bridge → Python server (spawned as child process)
- **Offline Tauri:** Same as above, but no internet required. Server runs locally.

The Tauri binary (`commands.rs`) spawns the Python server on launch:
```rust
Command::new("python").args(["-c", "...uvicorn.run(app, host='127.0.0.1', port=8000)"])
```

---

## Measured Compute Costs

### OpenWInD Impedance Evaluation (the bottleneck)
| Scenario | Time | Notes |
|----------|------|-------|
| Cold start (first eval) | **1.7s** | Python import + OpenWInD init + computation |
| Uncached eval | **1.1-1.4s** | Computation only (varies with n_freqs) |
| Cached eval | **0.005s** | SQLite lookup (same bore profile) |
| n_freqs=5000 (default) | ~1.2s | Our current setting |
| n_freqs=1000 (coarse) | ~0.3s | For early exploration |

### Gradient Cost (L-BFGS-B with centered finite differences)
| Control Points | Evals per Iteration | Time per Iteration |
|----------------|--------------------|--------------------|
| 6 CP | 13 | ~16s |
| 8 CP | 17 | ~20s |
| 12 CP | 25 | ~30s |

### Optimizer Total Cost (measured)
| Optimizer | CP | Evals | Time | RMS (cents) |
|-----------|-----|-------|------|-------------|
| L-BFGS-B (30 iter) | 6 | 315 | **120s** | **1.27** |
| L-BFGS-B (50 iter) | 6 | ~500 | ~200s | ~1.0 (estimated) |
| L-BFGS-B (30 iter) | 12 | ~600 | ~360s | ~1.5 (estimated) |
| NSGA-II (pop=15, gen=10) | 12 | 150 | **250s** | **3.11** |
| NSGA-II (pop=40, gen=50) | 12 | 2000 | **~600s** | **38.78** (broken) |

---

## Per-Instrument Design Cost

### Quick Design (6 CP, L-BFGS-B, <2 cents)
- **Evals:** ~300-500
- **Serial time:** 2-4 min
- **Parallel (6 workers):** 1-2 min
- **Both machines:** ~1 min

### Full Design (12 CP, L-BFGS-B two-phase, <1.5 cents)
- **Evals:** ~600-800
- **Serial time:** 6-10 min
- **Parallel (6 workers):** 3-5 min
- **Both machines:** 2-3 min

### High-Accuracy Design (12 CP, CMA-ES with restarts)
- **Evals:** ~2000-5000
- **Serial time:** 20-50 min
- **Parallel (6 workers):** 11-28 min
- **Both machines:** 6-14 min

---

## System Requirements for Tauri Offline

### What "offline" means
- Tauri app launches Python server as child process (no internet needed)
- OpenWInD + scipy + numpy must be installed locally
- All computation happens on the user's machine

### Minimum Requirements
| Component | Requirement | Why |
|-----------|-------------|-----|
| Python | 3.10+ | OpenWInD compatibility |
| RAM | 4 GB | OpenWInD frequency arrays + Python overhead |
| CPU | 2+ cores | L-BFGS-B (serial) works fine on 2 cores |
| Disk | 500 MB | Python + OpenWInD + pymoo + scipy |
| GPU | Not needed | Pure CPU computation |

### Recommended Requirements
| Component | Requirement | Why |
|-----------|-------------|-----|
| Python | 3.12+ | Better performance, f-strings |
| RAM | 8 GB | Comfortable for parallel workers |
| CPU | 4-6 cores | Parallel optimization (1.8x speedup measured) |
| Disk | 1 GB | With cache storage |
| GPU | Not needed | No GPU-accelerated path currently |

### "Acceptable" Wait Times (subjective, needs testing)
| Duration | UX Perception | Strategy |
|----------|---------------|----------|
| **<30s** | Instant, feels like a tool | Quick design (6 CP) or cached |
| **30s-2min** | Acceptable, show progress bar | Standard design (12 CP) |
| **2-5min** | Tolerable with progress + stages | Full design with two-phase |
| **5-15min** | "Go get coffee" — needs background task | High-accuracy CMA-ES |
| **>15min** | Frustrating — needs async + save/resume | Batch production runs |

---

## Web App vs Tauri: Compute Comparison

| Aspect | Web App | Tauri Desktop |
|--------|---------|---------------|
| **Compute location** | Server (same machine or remote) | Same machine (spawned Python) |
| **Offline capable** | No (needs server running) | Yes |
| **Parallel workers** | Unlimited (server hardware) | Limited to user's CPU cores |
| **Startup time** | Server must be started manually | Auto-starts with app |
| **Process management** | Manual (uvicorn/systemd) | Automatic (Tauri manages) |
| **Compute cost to user** | Server admin burden | Free (runs locally) |
| **Multi-user** | Yes (server serves many clients) | No (single user) |

### Key Insight
Tauri offline compute is **identical** to web app compute — same Python, same OpenWInD, same optimizer. The only difference is process management. A 4-core laptop running Tauri offline has the same compute as a 4-core server running the web app.

---

## Development Compute Budget

### Phase 1: Optimizer Development (current)
| Task | Runs | Evals/run | Time/run | Total |
|------|------|-----------|----------|-------|
| Algorithm testing | 30 | 300 | 4 min | 2 hrs |
| Parameter tuning | 20 | 500 | 7 min | 2.3 hrs |
| Validation (3 instruments) | 10 | 500 | 7 min | 1.2 hrs |
| **Total Phase 1** | | | | **~5.5 hrs** |

### Phase 2: Print Validation (future)
| Task | Runs | Evals/run | Time/run | Total |
|------|------|-----------|----------|-------|
| Print + measure loop | 10 | 300 | 4 min | 0.7 hrs |
| Shrinkage calibration | 5 | 200 | 3 min | 0.25 hrs |
| **Total Phase 2** | | | | **~1 hr** |

### Phase 3: Production (per instrument)
| Task | Runs | Evals/run | Time/run | Total |
|------|------|-----------|----------|-------|
| Design (12 CP) | 1 | 500 | 7 min | 7 min |
| Refinement | 2 | 200 | 3 min | 6 min |
| Validation | 1 | 300 | 4 min | 4 min |
| **Per instrument** | | | | **~17 min** |

---

## Recommendations

### For Tauri Offline (User-Facing)
1. **Default to L-BFGS-B** (not NSGA-II) — 2-4 min, <2 cents
2. **Show progress** — "Phase 1: optimizing pitch accuracy... (2/30)"
3. **Save/resume** — checkpoint optimization state, resume if interrupted
4. **Cache aggressively** — SQLite cache persists across sessions
5. **Background processing** — optimize while user browses presets or edits bore

### For Development
1. **Use 6 CP for quick tests** — 2 min vs 7 min
2. **Use 12 CP for final validation** — more control points = better bore shape
3. **Share SQLite cache** between machines — reduces redundant OpenWInD calls
4. **Profile OpenWInD** — the 1.2s/eval is the hard floor; only a surrogate model can beat it

### For Future (Surrogate Model)
If we train a neural net on 1000+ OpenWInD evaluations:
- Training: ~20 min (one-time cost)
- Inference: ~0.001s per evaluation (1000x faster)
- Full optimization: ~3s instead of ~7 min
- **This is the path to truly instant offline optimization**
