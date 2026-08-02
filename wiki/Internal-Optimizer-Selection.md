# Optimizer Selection Framework

> Automatic best-method selection for wind instrument optimization based on instrument type, accuracy target, and time budget.
> Implemented in `backend/optimization/selector.py`.

---

## Problem Solved

Previously, multiple optimizer implementations existed with **no selection mechanism**:
- Users manually chose which optimizer to call
- Inconsistent results across instruments
- No benchmark-driven validation of choices
- Tribal knowledge instead of documented decisions

---

## Architecture

```
OptimizerConfig (declarative)
    ↓
OptimizerFactory (selection logic)
    ↓
OptimizerProtocol (interface)
    ↓
Concrete Optimizer (FAST/ACCURATE/REFINED/PARETO/BENCHMARK)
```

---

## Strategies

| Strategy | Method | Best For | Time | Accuracy |
|----------|--------|----------|------|----------|
| `FAST` | DE only | Quick drafts, exploration | ~5-10s | ~10-20¢ |
| `ACCURATE` | **Two-phase (Noreland)** — **DEFAULT** | General woodwind | ~30-60s | **<3¢** |
| `REFINED` | JAX 4-stage + sequential init | Closed-open refinement | ~30-60s | <3¢ |
| `PARETO` | NSGA-II bi-objective | Intonation vs timbre tradeoff | ~60-120s | Pareto front |
| `BENCHMARK` | Sequential + DE + 4-stage L-BFGS-B | Maximum accuracy validation | ~60-120s | **<1¢** |

---

## Auto-Selection Logic

```python
def _select_strategy(config, network) -> OptimizerStrategy:
    # Explicit user choice takes priority
    if config.strategy != OptimizerStrategy.ACCURATE:
        return config.strategy
    
    # Brass instruments → need FEM (bell flare not handled by TMM)
    if config.instrument_type == InstrumentType.BRASS:
        return OptimizerStrategy.REFINED  # Will route to OpenWInD
    
    # Timbre-aware optimization requested
    if config.enable_timbre:
        return OptimizerStrategy.PARETO
    
    # High accuracy target → use benchmark-proven method
    if config.target_accuracy_cents < 2.0:
        return OptimizerStrategy.BENCHMARK
    
    # Fast draft mode
    if config.max_time_seconds < 10.0:
        return OptimizerStrategy.FAST
    
    # Default: Noreland two-phase (best general accuracy/speed)
    return OptimizerStrategy.ACCURATE
```

---

## Instrument Type Mapping

| InstrumentType | Acoustic Type | Default Strategy |
|----------------|---------------|------------------|
| CLARINET | closed-open | ACCURATE (Noreland) |
| SAXOPHONE | open-open (conical) | ACCURATE |
| FLUTE | open-open | ACCURATE |
| BRASS | open-open (strong flare) | REFINED (OpenWInD FEM) |
| CHALUMEAU | closed-open | ACCURATE |
| RECORDER | open-open | ACCURATE |
| OCARINA | open-open | ACCURATE |
| WHISTLE | open-open | ACCURATE |
| DRONE | open-open | ACCURATE |
| MEMBRANE | closed-open | ACCURATE |
| EXPERIMENTAL | varies | ACCURATE |

---

## Configuration

```python
config = OptimizerConfig(
    strategy=OptimizerStrategy.ACCURATE,      # or FAST, REFINED, PARETO, BENCHMARK
    instrument_type=InstrumentType.CLARINET,  # affects auto-selection
    acoustic_type="closed-open",              # "closed-open" or "open-open"
    enable_timbre=False,                      # → PARETO strategy
    max_time_seconds=60.0,                    # <10s → FAST
    target_accuracy_cents=3.0,                # <2.0¢ → BENCHMARK
)
```

---

## Usage

```python
from backend.optimization.selector import get_optimizer, OptimizerConfig, InstrumentType
from backend.core.network import AcousticNetwork

# Build your acoustic network
network = AcousticNetwork(...)

# Configure optimizer
config = OptimizerConfig(
    instrument_type=InstrumentType.CLARINET,
    target_accuracy_cents=2.0,  # will auto-select BENCHMARK
)

# Get best optimizer
optimizer = get_optimizer(config, network, targets, fingerings, n_register)

# Run
result = optimizer.optimize(verbose=True)
print(f"RMS: {result.rms_cents:.2f}¢, Time: {result.wall_time:.1f}s")
```

---

## Comparison Runner

```python
from backend.optimization.selector import run_optimizer_comparison

results = run_optimizer_comparison(
    instrument_cfg={"instrument_type": "clarinet", ...},
    network=network,
    targets=targets,
    fingerings=fingerings,
    n_register=1,
)

# Returns:
# {
#   "fast":       {"rms_cents": 12.3, "wall_time": 4.2, ...},
#   "accurate":   {"rms_cents": 1.8,  "wall_time": 42.1, ...},
#   "refined":    {"rms_cents": 1.5,  "wall_time": 55.3, ...},
#   "benchmark":  {"rms_cents": 0.7,  "wall_time": 98.2, ...},
# }
```

---

## Methodology References

| Method | Reference | Key Insight |
|--------|-----------|-------------|
| Noreland two-phase | Noreland et al. (2013) "The Logical Clarinet" | "Little success omitting Phase 1" |
| Phase-based tracking | Ernoult et al. (2020) JASA | Unwrapped phase = smooth, differentiable |
| Pareto front | Petiot et al. (2025) JASA | NSGA-II bi-objective (intonation vs timbre) |
| ML surrogate | Petiot et al. (2025) | Random Forest + NSGA-II |
| WIDesigner | Patkau (2017) | DIRECT-C + BOBYQA derivative-free |
| Sequential benchmark | Our research | Sequential + DE + 4-stage L-BFGS-B = proven best |

---

## Integration Points

| Component | File | Role |
|-----------|------|------|
| Factory | `backend/optimization/selector.py` | Strategy selection + instantiation |
| Config | `backend/optimization/selector.py` | `OptimizerConfig`, `OptimizerStrategy`, `InstrumentType` |
| Protocol | `backend/optimization/selector.py` | `OptimizerProtocol` (interface) |
| Base Result | `backend/optimization/base.py` | `OptimizationResult` (absolute RMS primary) |
| UI | `web/src/components/DesignTab.tsx` | Strategy dropdown, timbre checkbox, time/accuracy inputs |
| API | `web/src/utils/api.ts` | `startDesign` accepts `optimizer` settings |
| Server | `woodwind_designer/engine/design_server.py` | Passes optimizer kwargs to designer |

---

## Related Pages

- [[Internal-Benchmarking-Standards]] — metric definitions, tiered strategy
- [[Internal-Optimization]] — optimizer details
- [[Internal-Computational-Benchmark-Research]] — V&V methodology
- ROADMAP.md → §1j "Optimizer Selection Framework"

---

*Last updated: 2026-07-31*