# Rebuild Plan: Instrument Designer v2
## Based on deep research findings (2026-07-21)

---

## Guiding Principle

> **Integrate proven tools. Don't reinvent the wheel.**
> Original work only where it genuinely improves on existing methods.

The academic literature and existing open-source tools already solve most of our problems. Our job is to **integrate them into a usable platform**.

---

## What We Keep

| Component | Status | Why Keep |
|-----------|--------|----------|
| Tauri frontend | Good UX | Native features + web tech |
| OpenWInD | Proven simulation | 1D spectral FEM, FWI gradients, actively maintained |
| FastAPI backend | Working | Good Python ecosystem integration |
| SQLite cache | Working | Shared evaluation cache |
| AI advisor | Useful | Rule-based analysis + LLM suggestions |
| SVG export | Useful | Bore profile visualization |
| BoreProfileView | Useful | SVG cross-section renderer |

## What We Replace

| Current | Problem | Replacement |
|---------|---------|-------------|
| Custom NSGA-II optimizer | Wrong algorithm, np.inf bug, poor convergence | scipy.optimize (L-BFGS-B or trust-constr) |
| Peak-based frequency matching | Discontinuous cost function | Phase-based resonance detection (Ernoult) |
| Random initialization | No good starting point | Known-good bore profiles (Buffet R13) |
| Single-phase optimization | Gets stuck in local minima | Two-phase (Noreland) |

## What We Add

| Feature | Source | Benefit |
|---------|--------|---------|
| Two-phase optimization | Noreland 2013 | Phase 1 (simple) -> Phase 2 (full) |
| Gradient computation | OpenWInD FWI | 10-100x faster convergence |
| Phase-based resonance | Ernoult 2020 | Smooth cost function |
| CMA-ES global search | Research | Better than NSGA-II for continuous problems |
| Known-good initialization | Buffet R13 dimensions | Start from good basin |

---

## Architecture v2

```
┌─────────────────────────────────────────────────────┐
│                   Tauri Frontend                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │
│  │ Designer │  │ Optimizer│  │ Results Viewer   │  │
│  │ (editor) │  │ (wizard) │  │ (impedance/bore) │  │
│  └────┬─────┘  └────┬─────┘  └────────┬─────────┘  │
│       │              │                  │             │
│       └──────────────┼──────────────────┘             │
│                      │                                │
└──────────────────────┼────────────────────────────────┘
                       │ HTTP API
┌──────────────────────┼────────────────────────────────┐
│                FastAPI Backend                         │
│  ┌───────────────────┼──────────────────────────────┐  │
│  │              Design Server                        │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │  │
│  │  │ OpenWInD│ │ scipy   │ │ Phase Detection  │  │  │
│  │  │ FWI     │ │ optimize│ │ (Ernoult method) │  │  │
│  │  └─────────┘ └─────────┘ └──────────────────┘  │  │
│  │  ┌─────────┐ ┌─────────┐ ┌──────────────────┐  │  │
│  │  │chalumier│ │demakein │ │ AI Advisor       │  │  │
│  │  │wrapper  │ │wrapper  │ │ (rule+LLM)       │  │  │
│  │  └─────────┘ └─────────┘ └──────────────────┘  │  │
│  └────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────┘
```

---

## Branch Strategy

### `option-a-tauri` (main integration branch)
- Stable, tested code
- All experiments merge here after validation

### `experiment/v2-scipy-gradient`
- Replace NSGA-II with scipy.optimize
- Gradient-based optimization using finite differences
- Single-phase first, then add two-phase
- **Expected: <5 cents in <60 seconds**

### `experiment/v2-phase-detection`
- Implement Ernoult's phase-based resonance detection
- Unwrapped angle of reflection function
- Smooth cost function for gradient methods
- **Expected: eliminates peak-merging discontinuities**

### `experiment/v2-two-phase`
- Noreland-style two-phase optimization
- Phase 1: 1st register only (simple)
- Phase 2: full instrument (complex, seeded from Phase 1)
- **Expected: avoids local minima**

### `experiment/v2-cmaes`
- CMA-ES global search (better than NSGA-II for continuous)
- Weighted single-objective (frequency accuracy primary)
- **Expected: better convergence than evolutionary methods**

---

## Implementation Order

### Week 1: Core v2 Optimizer
1. Create `experiment/v2-scipy-gradient` branch
2. Implement scipy.optimize wrapper with OpenWInD
3. Add finite-difference gradient computation
4. Test on clarinet Bb with known-good initialization
5. Benchmark: accuracy vs speed vs current NSGA-II

### Week 2: Phase Detection
1. Create `experiment/v2-phase-detection` branch
2. Implement Ernoult's unwrapped phase method
3. Replace peak detection in impedance analysis
4. Verify smooth cost function landscape
5. Test gradient convergence with new cost function

### Week 3: Two-Phase Workflow
1. Create `experiment/v2-two-phase` branch
2. Implement Phase 1 (1st register only)
3. Implement Phase 2 (full, seeded from Phase 1)
4. Test on clarinet Bb and penny whistle
5. Compare with Noreland's results

### Week 4: Integration
1. Merge validated experiments into `option-a-tauri`
2. Update frontend for two-phase wizard
3. Update AI advisor with new metrics
4. Document accuracy benchmarks
5. Update ROADMAP.md

---

## Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Accuracy (clarinet Bb) | 3.11 cents (small pop) | <3 cents reliably |
| Speed (clarinet Bb) | 620s (batch, pop=40/gen=50) | <60s |
| Convergence | Unreliable at large pop | Reliable gradient convergence |
| Code complexity | Custom optimizer + pymoo | scipy.optimize (proven) |
| Dependencies | pymoo + custom code | scipy (standard) |

---

## What We're NOT Doing

1. **Reimplementing acoustic simulation** — OpenWInD already does this
2. **Reimplementing instrument design** — chalumier/demakein already do this
3. **Reimplementing bore representation** — existing tools have this
4. **Reimplementing tone hole modeling** — OpenWInD handles this
5. **Building a research tool** — we're building a PLATFORM

---

## Key References

1. Noreland et al. (2013) "The Logical Clarinet" — two-phase optimization
2. Ernoult et al. (2020) — phase-based resonance detection
3. Ernoult et al. (2021) — FWI gradient computation
4. OpenWInD — 1D spectral FEM + FWI
5. Chalumier — evolutionary instrument design
6. Demakein — practical instrument design + manufacturing
7. WWIDesigner — two-stage DIRECT + BOBYQA optimization

---

*Created: 2026-07-21 (Desktop Session 7)*
*Status: Plan — waiting for laptop coordination*
