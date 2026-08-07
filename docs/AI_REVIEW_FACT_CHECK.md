# Fact-Check: AI Review from Nemotron 3 Super 120B (OpenRouter)

Generated: 2026-08-06
Model: `nvidia/nemotron-3-super-120b-a12b:free`
Source review: `docs/AI_REVIEW_NEMOTRON_3_SUPER_120B_OPENROUTER.md`

## Important Caveat

The review output was truncated at 318 lines / 14,442 characters because it hit
`max_tokens=4000`. It stops mid-sentence while analyzing `backend/chromatic_flute.py`.
Therefore the findings below are only from the first part of the review. A
follow-up run with a larger token budget or a narrower prompt is needed for a
complete review.

## Findings and Verdicts

### 1. Critical: Impossible outer diameters in `backend/benchmark_all.py`

**AI claim:** `pvc_flute_D` and `diatonic_D_chalumeau` have `outer_diameter < 2 * bore_radius`,
leading to negative wall thickness.

**Fact-check:** **CONFIRMED.**

- `pvc_flute_D`: `bore_radius=10.2`, `outer_diameter=14` → bore diameter 20.4 > OD 14.
- `diatonic_D_chalumeau`: `bore_radius=8.0`, `outer_diameter=14` → bore diameter 16 > OD 14.

**Impact:** Unphysical wall thickness; acoustic simulation uses invalid geometry.
**Action:** Add `assert outer_diameter > 2 * bore_radius` sanity check and fix
instrument definitions.

---

### 2. Critical: `bass_chalumeau_Bb` has no tone holes in modular builder

**AI claim:** `benchmark_all.py` defines 8 target notes and 8-column fingerings for
`bass_chalumeau_Bb`, but `modular_components.build_bass_chalumeau_Bb()` only adds
a bore and bell, no tone holes.

**Fact-check:** **CONFIRMED.**

- `backend/modular_components.py` lines 699-711 only add `BoreSection` and `Bell`.
- No `toneholes` or `keys` are added.

**Impact:** The modular builder cannot produce the instrument that the benchmark
expects to optimize.
**Action:** Add 7-8 tone holes to `build_bass_chalumeau_Bb()` matching the
benchmark's fingering chart, or remove the benchmark target until the builder is
ready.

---

### 3. Critical: `backend/jax_optimizer.py` hardcodes `outer_diameter_mm=22.0` in `eval_all`

**AI claim:** `eval_all` ignores the caller's outer diameter and uses `outer_diameter_mm=22.0`.

**Fact-check:** **CONFIRMED.**

- Line 34-36 of `backend/jax_optimizer.py`:
  ```python
  inst = tmm_instrument_from_radii(
      radii, bore_length, hp, hd, hl,
      outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
  )
  ```

**Impact:** All instruments evaluated by this function use the same wall thickness,
regardless of their actual config. This corrupts radiation impedance and end
correction calculations.
**Action:** Add an `outer_diameter` parameter to `eval_all` and pass it through.

---

### 4. Critical: `backend/two_phase_optimizer.py` hardcodes `outer_diameter_mm=22.0` and `closed_top=False`

**AI claim:** Multiple calls in `phase1_de_search`, `phase2_lbfgsb_refine`, etc.
use `outer_diameter_mm=22.0` and `closed_top=False`.

**Fact-check:** **CONFIRMED.**

- Lines 129-131, 187-189, 300-305, 327-329, 355-357 all hardcode 22.0 and `False`.

**Impact:** Same as above, plus `closed_top=False` is wrong for clarinet-family
(closed-top) instruments.
**Action:** Thread `outer_diameter` and `closed_top` from the caller through all
optimizer stages.

---

### 5. Correct: `backend/pareto_optimizer.py` threads `outer_diameter` correctly

**AI claim:** `evaluate_bi_objective` accepts `outer_diameter` and passes it as
`outer_diameter_mm=outer_diameter`.

**Fact-check:** **CONFIRMED.**

- Line 294-296:
  ```python
  inst = tmm_instrument_from_radii(
      radii, bore_length, hole_positions, hole_diameters, hole_lengths,
      outer_diameter_mm=outer_diameter, closed_top=closed_top, cone_step=0.5,
      loss_model=loss_model,
  )
  ```

**Action:** None needed; this is the correct pattern for the other optimizers.

---

### 6. False Alarm: Positional argument in `jax_optimizer.sequential_placement` is correct

**AI concern:** Passing `cfg["outer_diameter"]` as the 6th positional argument to
`tmm_instrument_from_radii` might be wrong because other calls use the keyword
`outer_diameter_mm=`.

**Fact-check:** **NOT A BUG.**

- `backend/tmm_acoustics.py` line 1020-1032 defines the signature as:
  ```python
  def tmm_instrument_from_radii(
      radii_mm, bore_length_mm, hole_positions_mm, hole_diameters_mm,
      hole_lengths_mm, outer_diameter_mm=22.0, closed_top=False, cone_step=0.5, ...
  )
  ```
- The 6th positional argument is exactly `outer_diameter_mm`. The call is correct.

**Action:** No change needed. Optionally convert to keyword for readability.

---

## Issues the AI Started But Did Not Finish

- `backend/chromatic_flute.py` register/fingering convention analysis was cut off
  mid-sentence. The AI was about to make a claim about the upper/lower register
  mapping but did not complete it.

## Recommendations for the Next AI Review

1. Run with `max_tokens` > 4000, or break the prompt into smaller chunks.
2. Add a request to the prompt: "Be concise; do not restate the audit; focus on
   new findings and mark confidence."
3. Include full files for the targeted optimizers (`jax_optimizer.py`,
   `two_phase_optimizer.py`) so the AI can trace the entire call chain.
4. Ask the AI to explicitly rate each finding as High/Medium/Low confidence.

## Human Decisions Needed

1. What is the correct outer diameter for `pvc_flute_D` and `diatonic_D_chalumeau`?
2. Should `build_bass_chalumeau_Bb()` be completed, or should the benchmark target
   be removed until the builder is ready?
3. Is `two_phase_optimizer.py` still used, or has it been superseded by
   `jax_optimizer.py` and `pareto_optimizer.py`? If it is dead code, deleting it is
   safer than fixing it.
