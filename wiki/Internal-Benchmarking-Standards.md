# Internal Benchmarking Standards

> Mandatory benchmarking standards for all instrument optimization and validation.
> Derived from research in [[Internal-Computational-Benchmark-Research]] and [[Internal-Research]].
> Enforced in code via ROADMAP.md and backend/optimization/selector.py.

---

## 1. Primary Metric: Absolute RMS (Pitch Accuracy)

**This is the ONLY primary metric. No median correction ever.**

```python
cents = [1200 * log2(actual / target) for each note]
absolute_rms = sqrt(mean(cents²))
```

Measures how far notes are from equal temperament targets at A=440 Hz.

**Why absolute RMS, not median-corrected?**
- Median correction measures **scale evenness**, NOT **pitch accuracy**
- An instrument can be perfectly even but 15¢ sharp (median: 0¢, absolute: 15¢)
- An instrument can be accurate but uneven (median: 5¢, absolute: 2¢)
- Professional makers explicitly trade intonation for timbre (Buffet R-13 vs RC)
- Ernoult et al. (2020) proved intonation and timbre are inherently at odds

---

## 2. Required Metric Suite (Report ALL)

| Metric | Formula | Measures | Status |
|--------|---------|----------|--------|
| **Absolute RMS** | `sqrt(mean(cent_dev²))` | **Accuracy (PRIMARY)** | Mandatory |
| **MAD** | `mean(|cent_dev|)` | Robust accuracy | Mandatory |
| **SD** | `std(cent_dev)` | Evenness | Mandatory |
| **Max Deviation** | `max(|cent_dev|)` | Worst note | Mandatory |

**Never** use median-corrected RMS as the primary metric.

---

## 3. Forbidden Practices

- ❌ Median correction as primary metric (hides systematic tuning errors)
- ❌ Reporting "0.01¢" without specifying absolute vs median-corrected
- ❌ Using Printables/Cults3D/Thingiverse STLs as validation targets (no acoustic data)
- ❌ Comparing absolute RMS from one pipeline to median-corrected from another

---

## 4. Required Documentation Per Benchmark Run

1. **Solver configuration**: TMM parameters, loss model, speed of sound value
2. **Geometry source**: Peer-reviewed paper, museum CT data, or validated reference
3. **Measurement scaling**: Confirm ρc/S scaling for measured impedance files
4. **Per-note table**: Full cent deviation profile for debugging
5. **Environment**: Temperature, humidity if physical measurement

---

## 5. Tiered Benchmark Strategy

| Tier | Target | Purpose | Acceptance |
|------|--------|---------|------------|
| **V1 Verification** | Inria 2026 pipe benchmark (Zenodo 20024938) | Solver-vs-solver + solver-vs-measurement on simple geometry | Match simulated ref; report discrepancy vs measured per end condition |
| **V2 Cross-software** | chalumier/demakein examples, WIDesigner XML | Same design, different implementation | <1¢ on reference bore profiles |
| **V3 Measured instrument** | UNSW flute Z(f) (Boehm/classical); Bowen bass clarinet | Real instrument, real measurements | Peak agreement at Bowen-level accuracy (¢-scale) |
| **V4 Printed replica** | Fagottino (open datasets + CT prints) / Hotteterre traverso / RCM prints | Full physical validation | Perceptually indistinguishable replicas; <5¢ print-induced shift (P3) |

---

## 6. Approved Benchmark Sources (Research-Grade Only)

| Category | Source | Access |
|----------|--------|--------|
| **V1** | Inria 2026 Pipe Benchmark (Ernoult et al. 2026) | Zenodo 20024938 + GitLab Inria |
| **V2** | chalumier `examples/`, demakein `examples/`, WIDesigner XML | GitHub (upstream) |
| **V3** | UNSW Flute Z(f) (Boehm B/C, Classical) | phys.unsw.edu.au/music/flute/ |
| **V3** | Bowen 1910 Heckel Bass Clarinet in A | oro.open.ac.uk/58268 (open access) |
| **V4** | Fagottino (SCB/FHNW) — 130+ small bassoons | historical-bassoon.ch, Zenodo, DaSCH |
| **V4** | Hotteterre Traverso (Fritz et al.) | HAL: hal-05393759v1 |
| **V4** | Digital Revival (Haka 1680, Warder 1540s) | arXiv:2606.24216 |
| **V4** | RCM 3D Printed Instruments (7 instruments) | Collaboration required (not open) |

### Explicitly Forbidden Sources
- Printables / Cults3D / Thingiverse / MakerWorld / GrabCAD / Sketchfab — hobbyist STLs, no acoustic validation, no impedance data
- Any source without published impedance measurements or CT-derived bore profiles

---

## 7. Implementation in Code

### Primary Metric Enforcement
- `backend/tmm_acoustics.py:phase_cost_with_offset()` → **deprecated**, returns absolute RMS
- `backend/two_phase_optimizer.py:phase_cost_with_offset()` → **deprecated**, returns absolute RMS
- `backend/benchmark_all.py:eval_all()` → uses absolute RMS (primary)

### Optimizer Selection Framework
- `backend/optimization/selector.py` — automatic best-method selection
- Strategies: FAST, ACCURATE (Noreland two-phase — DEFAULT), REFINED (JAX), PARETO, BENCHMARK
- Auto-selection based on instrument type, accuracy target, time budget

### Metric Suite Output
```python
OptimizationResult(
    rms_cents=rms_cents_abs,           # absolute RMS — PRIMARY
    rms_cents_median=rms_cents_median, # median-corrected — SECONDARY (evenness)
    peak_cents=peak_cents,
    ...
)
```

---

## 8. Key References

| Reference | Finding |
|-----------|---------|
| Ernoult et al. (2020) JASA | Intonation + timbre tradeoff proven: https://doi.org/10.1121/10.0002449 |
| Noreland et al. (2013) | "The Logical Clarinet" — two-phase optimization essential |
| Petiot et al. (2025) JASA | NSGA-II bi-objective Pareto front (intonation vs timbre) |
| Bowen et al. (2019) Applied Acoustics | Geometry-only impedance prediction validated |
| Szwarcberg et al. (2025) | 0.1mm radius → 3.4¢; chimney +1mm → 4¢ |
| Inria 2026 benchmark | Canonical V&V suite: https://doi.org/10.1051/aacus/2026048 |

---

## 9. Related Pages

- [[Internal-Computational-Benchmark-Research]] — full deep-dive report
- [[Internal-Research]] — topic-indexed reference tables
- [[Internal-Optimization]] — optimizer details
- ROADMAP.md → "Benchmarking Standards" section
- `backend/optimization/selector.py` — implementation

---

*Last updated: 2026-07-31*