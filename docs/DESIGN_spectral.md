# DESIGN — `backend/spectral` module (proposal for approval)

Status: **DRAFT — awaiting user approval** (per BOOT_STATE: "awaits user approval of design")
Date: 2026-08-02
Author: desktop (opencode)

## Problem

We can score an instrument's **intonation** (via `backend/metrics.py` on TMM/OpenWind
sounding frequencies) and a coarse **timbre proxy** (via `backend/timbre_objectives.py`
impedance-peak ratios). What's missing is a validation layer that compares the
**acoustic spectrum a design actually produces** against a **target timbre** — using
synthesized/simulated audio in the loop for now (no mic/recording integration yet).

## Scope (what this module is)

A deterministic, synthetic-only audio → timbre-metrics pipeline:

```
design (bore/geometry)
  └─ acoustic sim (TMM / OpenWind)        ─ frequencies + magnitudes
       └─ audio synth (harmonics)          ─ synthetic WAV in time domain
            └─ spectral analysis            ─ FFT / harmonic decomposition
                 └─ timbre metrics           ─ matched to target signature
```

It is **not** (out of scope for v1):
- Real audio recording / microphone capture
- Onset/transient modelling, noise, multiphonics, nonlinear effects
- Real-time DSP or GUI preview

## Key decisions (from BOOT_STATE)

1. **Synthetic-only tests** — no mic/recording integration. Tests use generated
   WAVs (reuse `backend/inverse_design.py` synthesis helpers where possible).
2. **Reuse canonical modules, never modify** — `backend/metrics.py` and
   `backend/target_frequencies.py` are the single source of truth for tuning and
   target-note logic. `backend/spectral` imports them, does not fork them.
3. **The 4 canonical metrics** (approved Phase 2G target contract) apply to
   spectral analysis too: `final_rms_cents`, `scale_rms_cents`,
   `median_offset_cents`, `peak_error_cents` (`metrics.compute_metrics`).

## Proposed layout

```
backend/spectral/
  __init__.py
  analysis.py        # FFT, harmonic decomposition, f0 estimate
  signature.py       # target timbre signature dataclass (harmonics, rolloff, centroid)
  metrics.py         # timbre-similarity metrics (spectral distance vs target)
  pipeline.py        # orchestration: geometry -> sim -> audio -> analysis -> metrics
```

### `analysis.py`
- `analyze_wav(path, fft_size=4096, hop=512)` → dict `{f0, harmonics: [(n, f, mag)], spectral_centroid, rolloff}`
- Thin wrapper over numpy FFT / `scipy.signal` (no hard librosa dependency in v1;
  librosa stays a documented optional extra for later perceptual features).

### `signature.py`
- `TimbreSignature(harmonics: list[tuple[int,float]], centroid, rolloff)` — the
  "target timbre" a design should reproduce. Built from either:
  - an existing instrument's measured/simulated spectrum, or
  - the WAV-to-harmonics extraction in `backend/inverse_design.py`.

### `metrics.py`
- `timbre_distance(actual: TimbreSignature, target: TimbreSignature, weights) -> dict`
  returning the **canonical 4 metric dict** plus a `timbre_rms` and `centroid_error`.
- Harmonic registration uses the same nearest-harmonic logic as
  `backend/timbre_objectives.py.compute_harmonic_signature` (reuse, don't fork).

### `pipeline.py`
- `score_design(bore, target, solver='tmm') -> dict` — end-to-end hook for the
  optimizer cost function / benchmark scripts, keeping the solver pluggable
  (TMM default, OpenWind validation reference).

## Testing (`tests/test_spectral.py` — to be whitelisted)

Synthetic-only, deterministic:
1. Sine WAV with known f0 → `analyze_wav` recovers f0 within ±10c (regression lock).
2. Harmonic-stack WAV (n·f0, given magnitudes) → harmonic decomposition recovers
   magnitudes within tolerance.
3. Identical signatures → `timbre_distance` == 0; perturbed → metric rises
   monotonically with perturbation.
4. `score_design` end-to-end on a reference bore produces the canonical 4-metric dict.
5. Reuses `metrics.compute_metrics` semantics (import-time equality, never forked).

## Acceptance

- All tests pass on `main`, no new undeclared imports (toolcheck guard stays green).
- The module is importable without audio hardware / network.

## Open questions for the user

1. Priority: ship `analysis + signature + metrics` first (no pipeline hook), or
   full `pipeline.py` in the first commit?
2. Should `backend/spectral/metrics.py` reuse `timbre_objectives.py` sharpness or
   keep pure spectral-distance metrics separate?
3. librosa optional-extra now, or wait until a perceptual feature is actually needed?

— desktop (opencode)
