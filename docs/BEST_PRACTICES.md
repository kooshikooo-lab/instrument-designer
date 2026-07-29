# Best Practices

## Documentation

### What to Document
- **Docstrings**: Every public function must have a docstring describing its purpose, parameters, return values, and coordinate system convention used.
- **Coordinate systems**: Document which tool's convention is in effect at every function boundary. See `ARCHITECTURE.md` for the three coordinate systems (chalumier, OpenWind, TMM).
- **Physics references**: Cite the source (Nederveen, Fletcher & Rossing, chalumier source) for any non-trivial acoustic formula.
- **Data-flow comments**: When converting between units (mm, m, Hz, cents) or coordinate systems, annotate the conversion with a comment.
- **Architecture decisions**: Record decisions in `/docs/` with rationale, alternatives considered, and date. See `ARCHITECTURE.md`, `PHYSICS_PRINCIPLES.md`, `CODING_STANDARDS.md`.

### What NOT to Document
- Obvious code: `i += 1  # increment i`
- Implementation details that are clear from the code itself
- Outdated information: keep docs in sync with code or delete them

### Documentation Structure
```
docs/
  ARCHITECTURE.md        - Code structure, directory layout, coordinate systems
  PHYSICS_PRINCIPLES.md  - Acoustic first principles, never overridden by code
  CODING_STANDARDS.md    - Code style, naming, imports, conventions
  BEST_PRACTICES.md      - This file: process, verification, debugging, testing
  ROADMAP.md             - Project phases, completed milestones
  STATUS.md              - Current status, known issues
  session-logs/          - Daily development session logs
  prompts/               - AI prompt templates
```

## Architecture Adherence

### Before Adding New Code
1. **Check directory**: `backend/` is for core source modules only. Test code goes in `tests/`, utilities in `scripts/`.
2. **Check existing module**: Has someone already solved this? Look in `backend/optimization/`, `backend/solvers/`, `backend/core/`, `backend/physics/` before creating a new top-level file.
3. **Match coordinate system**: Always verify which tool's convention the target module uses.
4. **Keep fingering charts separate from bore geometry** (ARCHITECTURE.md §Fingering Charts).

### After Adding New Code
1. **Update ARCHITECTURE.md** if directory structure changes.
2. **Verify imports work**: `python -c "from backend.your_module import YourClass"` from repo root.
3. **Add a test** in `tests/`.

## Debugging: A Systematic Framework

When a result is wrong, follow this sequence. Do not skip steps.

### Step 1: Reproduce
Before changing anything, get a reliable reproduction:
- Record the **exact input**, **expected output**, and **actual output**
- Make the reproduction as simple as possible (hardcode the minimal inputs)
- Verify the bug is deterministic (run twice)
- **Rule**: If you can't reproduce it reliably, you can't fix it. Add instrumentation and run again.

### Step 2: Isolate
Narrow the fault to the smallest possible scope:
- **Binary search**: Comment out half the code, see if the bug persists. Repeat.
- **Substitute components**: Replace a complex module with a simple stub. If the bug disappears, the problem is in the substituted component.
- **Simplify inputs**: Reduce to a single data point, minimal configuration, trivial case.
- **Goal**: Identify the *first* function or line where the output diverges from expectation.

### Step 3: Observe
Gather evidence before forming a hypothesis:
- **Print intermediate values**: At each step in the suspected chain, print input and output
- **Compare with a known-good reference**: Run the same inputs through an independent implementation (chalumier, analytical formula, hand calculation)
- **Check invariants**: Does the state at this point satisfy the preconditions of the next step?
- **Visualize**: Plot the data (waveform, bore profile, error landscape) — visual inspection catches what numbers hide
- **Rule**: Don't guess. Collect data from the *actual* execution, not what you think should happen.

### Step 4: Hypothesize
Form a specific, testable hypothesis:
- **Good**: "The coordinate conversion at line 142 reverses the hole order, so hole positions are wrong."
- **Bad**: "The optimizer has a bug somewhere."
- **Testability rule**: A hypothesis is only useful if you can write a test that proves or disproves it.

### Step 5: Test the Hypothesis
Write a minimal test that isolates the suspected root cause:
- If the hypothesis is correct, the test should fail with the same symptom
- If the hypothesis is wrong, the test should pass (and you move to the next hypothesis)
- Keep the test even after fixing — it becomes a regression guard

### Step 6: Fix
Apply the minimal change that addresses the root cause:
- Fix the *cause*, not the symptom
- One fix per root cause (don't bundle unrelated changes)
- Run the reproduction case before and after to confirm the fix works

### Step 7: Verify and Lock
- Run all existing tests to check for regressions
- Add a regression test that fails without the fix
- Document: what was wrong, how it was found, what the fix was

### Common Anti-Patterns
- **Shotgunning**: Changing random things hoping the bug goes away. Always diagnose first.
- **Confirmation bias**: Only looking for evidence that confirms your hypothesis. Test the opposite too.
- **Over-isolation**: Removing so much context that the bug no longer reproduces. Keep enough structure to trigger the fault.
- **Ignoring the data**: Trusting an assumption over measured output. The code is what it does, not what you think it does.

---

## Verification: A Systematic Framework

Verification is the process of building confidence that the code is correct. Do it at every level, not just at the end.

### Levels of Verification

| Level | What It Catches | When | Effort |
|-------|----------------|------|--------|
| **L0: Smoke** | Crash on import, missing dependencies, obvious errors | Every edit | Seconds |
| **L1: Invariants** | Violation of known constraints (physics, bounds, types) | Every commit | Minutes |
| **L2: Regression** | Previously fixed bugs reappearing, known outputs changing | Before merge | Minutes |
| **L3: Cross-validation** | Overfitting, hidden dependencies between train/test sets | Before release | Hours |

### How to Verify at Each Level

**L0 — Smoke**
```
Check: Does the module import without error?
Check: Does the constructor accept valid inputs?
Check: Does the main function run without crashing on minimal input?
```

**L1 — Invariants**
```
Identify: What must always be true about this code's output?
  - Bounds: Is the value in the expected range?
  - Monotonicity: Are sequences strictly increasing/decreasing?
  - Conservation: Does energy/mass/phase sum to the expected value?
  - Consistency: Do two independent paths produce the same result?
  - Sign: Is the sign of the result physically correct?

Test: Write an assertion for each invariant. Fail fast on violation.
```

**L2 — Regression**
```
Identify: What known-good outputs exist?
  - Previous correct results (saved in test output or session logs)
  - Reference implementations (chalumier, OpenWind)
  - Analytical solutions (uniform tube, cone, known bore profile)

Test: Compare current output against known-good. Flag any difference.
     Threshold matters: 1% difference may be noise, 10% is a regression.
```

**L3 — Cross-validation**
```
Goal: Does the model generalize, or did it memorize the training data?

Method:
  1. Split inputs into training set (80%) and hold-out set (20%)
  2. Optimize/train on training set only
  3. Evaluate on hold-out set
  4. If hold-out error is much larger than training error → overfitting

This catches: over-tuned parameters, hidden data leakage,
              optimizer finding brittle solutions that don't generalize.
```

### When to Write Tests

| Situation | Action |
|-----------|--------|
| Adding new code | Write L0 + L1 tests alongside the code |
| Fixing a bug | Write a test that reproduces the bug *before* fixing |
| Changing existing code | Run existing L2 tests. Add L1 invariants for new logic |
| Performance optimization | Add L0 smoke test; verify output unchanged with L2 regressions |
| Release | Run all L0–L3. Document any known deviations |

### Test Structure Rules

1. **Self-contained**: A test must be runnable independently. No shared global state.
2. **Deterministic**: Same inputs → same outputs every time. No random seeds (or fix the seed).
3. **Fast**: A test you don't run is useless. Keep smoke tests under 1s, full suite under 1min.
4. **Informative**: On failure, the test should report what was expected vs what was actually produced.
5. **Isolated**: Tests must not depend on network access, GPU availability, or other tests running first.

```
# Good test structure (any language):
test_<feature>_<scenario>():
    input = minimal_valid_input()
    expected = computed_independently()
    actual = function_under_test(input)
    assert close_enough(actual, expected), f"Expected {expected}, got {actual}"
```

### Verification Artifacts
- **Test scripts**: In `tests/`, runnable standalone
- **Session logs**: In `docs/session-logs/`, record what was tested and the result
- **Known-good outputs**: Save reference outputs (JSON, CSV, plot PNG) when a result is verified correct
- **Bug database**: GitHub issues document each bug with reproduction steps, root cause, and fix

## Performance

### Profiling
- Use `scripts/profile_single.py` for single-instrument profiling
- Use `scripts/dask_benchmark.py` for distributed benchmarks
- Use `scripts/profile_openwind.py` for OpenWind comparison
- Record benchmark results in session logs

### Optimization Rules
1. **Correctness first**: Get the physics right before optimizing speed
2. **Measure before optimizing**: Profile to find the bottleneck
3. **JAX for throughput**: Use `backend/tmm_acoustics_jax.py` for vmap/batched evaluations
4. **Lazy imports**: Heavy dependencies (JAX, OpenWind) imported inside functions, not at module level
5. **Cache repeated computations**: Use `impedance_cache.py` and `mp_cache.py` for expensive calculations

## Pipeline Verification

### Three-Tier Pipeline
| Tier | Task | Verification |
|------|------|-------------|
| 1: Analysis | Extract fundamental + harmonics from WAV | Confidence > 90% |
| 2: Design | Place holes, set bore length | Intonation error < 50c |
| 3: Tuning | Optimize bore radii + Pareto timbre | Cross-val degradation < 5c |

### Cross-Validation Guard
If Tier 3 tuning degrades intonation on hold-out notes > 5c, fall back to Tier 2 radii:
```python
if degradation_cents > 5:
    logger.warning("Tier 3 degraded intonation by %.1fc, using Tier 2 radii", degradation_cents)
    radii = tier2_radii  # fallback
```

## External Tool Validation

### Chalumier
- Use `scripts/compare_chalumier.py` to compare TMM results against chalumier
- Verify: same bore geometry produces same resonant frequencies (within 1c)
- If TMM diverges from chalumier, the TMM code is likely wrong

### OpenWind
- Use `scripts/debug_openwind_pipeline.py` to validate against OpenWind FEM
- OpenWind results are reference, not ground truth — OpenWind itself may have bugs
- Prefer chalumier agreement over OpenWind for pure TMM comparisons

## Change Management

### Before Making Changes
1. Understand the existing code's convention (coordinate system, units, naming)
2. Check if the module already exists or if there's a neighboring module that does this
3. Write a test that reproduces the bug or validates the feature (L0/L1)

### After Making Changes
1. Run `test_import.py` and `test_architecture.py` to check for regressions
2. Run any directly relevant tests
3. Verify physics invariants still hold
4. Record the change in the session log

### Bug Fix Checklist
1. Reproduce bug with a test
2. Identify root cause (check coordinate system, units, boundary conditions first)
3. Fix with minimal change
4. Verify test passes
5. Run existing tests to check for regressions
6. Document root cause and fix in session log

## Dependencies

### When Adding a Dependency
1. Is it really needed? Can you use numpy/scipy instead?
2. Is it available on Windows, macOS, Linux?
3. Add to `pyproject.toml` dependencies or optional-dependencies
4. Guard the import with `try/except ImportError` for optional deps
5. Document what it's used for in a comment near the import
