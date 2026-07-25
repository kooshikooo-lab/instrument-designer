# Optimization

## Cost Functions

### Absolute RMS (Accuracy) — PRIMARY

```python
errors = [1200 * log2(actual / target) for each note]
rms = sqrt(mean(errors²))
```

Measures how far each note is from its equal temperament target at A=440 Hz.

### MAD (Robust Accuracy)

```python
mad = mean(|cent_deviations|)
```

Less sensitive to outliers than RMS.

### Standard Deviation (Evenness)

```python
sd = std(cent_deviations)
```

Measures consistency of pitch spacing. High SD = uneven scale.

### Max Deviation (Worst Note)

```python
max_dev = max(|cent_deviations|)
```

The worst note in the scale.

### Phase Cost (Ernoult 2020)

```python
phase_cost = sin²(π · (phase - n_register))
```

Smooth, differentiable cost that works even when peaks merge. Used in the two-phase optimizer.

### Peak Cost (Noreland)

```python
peak_cost = ∑(actual_peak_freq - target_freq)² / target_freq²
```

Direct frequency matching. Used in the two-phase optimizer's refinement phase.

## Metric Standardization (2026-07-25)

### The Problem

Desktop's `optimizer_global.py` and `phase_cost_with_offset` use **median-corrected RMS**:
```python
median_dev = median(cent_deviations)
corrected = [d - median_dev for d in cent_deviations]
rms = sqrt(mean(corrected²))
```
This measures **scale evenness**, not **accuracy**.

Laptop's `benchmark_all.py` uses **absolute RMS**:
```python
rms = sqrt(mean(cent_deviations²))
```
This measures **accuracy**.

### Why It Matters

An instrument can be:
- **Accurate AND even:** All notes within 2c of ET (ideal)
- **Accurate BUT uneven:** Notes hit targets but some +5c, some -5c
- **Even BUT inaccurate:** All notes exactly 15c sharp (median-corrected: 0c, absolute: 15c)
- **Neither:** Random deviations

### The Physics Connection

Impedance peak positions (intonation) and peak heights (timbre) are determined by the same physical parameters. The metric choice affects what the optimizer optimizes for:

- **Median-corrected (evenness):** Pushes toward harmonic alignment → brighter, more consistent timbre
- **Absolute RMS (accuracy):** Pushes toward exact frequencies → potentially uneven timbre

### Recommendation

Report ALL metrics separately:
| Metric | Formula | Measures |
|--------|---------|----------|
| Absolute RMS | `sqrt(mean(e²))` | Accuracy |
| MAD | `mean(|e|)` | Robust accuracy |
| SD | `std(e)` | Evenness |
| Max deviation | `max(|e|)` | Worst note |

## Optimizer Pipeline

### Sequential Optimizer (`tmm_optimizer_sequential.py`)

| Phase | Method | Variables | Purpose |
|-------|--------|-----------|---------|
| 1 | L-BFGS-B | 1 (bore length) | Fundamental pitch |
| 2 | L-BFGS-B | 1 per hole | Sequential hole placement |
| 2b | DE | 2×n_h (positions + diameters) | Global re-optimization |
| 3 S1 | L-BFGS-B | 1 | Bore length refinement |
| 3 S2 | L-BFGS-B | n_cp | Bore radii refinement |
| 3 S3 | L-BFGS-B | 2×n_h | Hole positions + diameters |
| 3 S4 | L-BFGS-B | All | Simultaneous fine-tune |

### Two-Phase Optimizer (`two_phase_optimizer.py`)

Noreland approach:
1. **Phase 1 (DE):** Fast global search using phase_cost (~1.4ms/call)
2. **Phase 2 (L-BFGS-B):** Precise refinement using peak_cost (~140ms/call)

Register detection essential for peak-cost phase.

### Staged Optimizer (`staged_optimizer.py`)

3-stage progressive refinement with KeefeLoss:
1. DE global search
2. L-BFGS-B bore refinement
3. L-BFGS-B hole refinement

## Timbre Optimization (Planned)

### Impedance Peak Amplitude Ratios

The ratio a₂/a₁ (second peak amplitude to first) determines:
- **Register stability:** Higher a₂/a₁ = more stable second register
- **Brightness:** Higher a₂/a₁ = brighter tone color

Target: varies linearly from ~2 (low register) to ~1 (high register).

### Bi-Objective Optimization

Planned: optimize intonation + timbre simultaneously using NSGA-II or similar.

Reference: Petiot et al. (2025) — found Pareto front between intonation and ease of emission on trumpet.

## Professional Tolerances

| Level | Tolerance | Source |
|-------|-----------|--------|
| Elite handmade | ±5 cents | Forum consensus |
| Good professional | ±10 cents | Academic consensus |
| Acceptable professional | ±15 cents | Bertsch 1998 |
| Needs correction | >20 cents | Forum consensus |
