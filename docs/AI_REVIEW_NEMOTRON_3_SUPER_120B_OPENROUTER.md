We are given a specific task to review the instrument-designer repository at `C:\Users\Admin\Desktop\instrument-designer` (branch `opencode/main/desktop`).

We are to focus on:
1. Correctness bugs in acoustic/optimization code.
2. Architectural inconsistencies.
3. Parameter plumbing bugs.
4. Fingering/register convention bugs.
5. Hardcoded constants.
6. Missing error handling.
7. Import/reference rot.
8. Test quality.
9. Anything the audit missed.

We are to output a structured report with sections: Critical Bugs, Medium Issues, Low-Priority/Cleanup, False Positives/Intended Behavior, Recommended Validation Additions.

We are to prioritize specific files and be specific with file paths, line numbers, and code snippets.

Given the extensive audit already provided, we note that the audit highlights several issues. However, we are to perform our own review and note any issues we find, especially those that might have been missed.

We are to be cautious: do not hallucinate, and if unsure, mark as "needs verification".

Given the time, we will focus on the most critical issues that are likely to affect correctness.

Let's start by looking at the provided code snippets and the audit.

From the audit, we know:

1. There are deleted-module references (imports from non-existing modules).
2. Bare except clauses.
3. Hardcoded physical/geometric constants (e.g., outer_diameter < 2*bore_radius).
4. Fingering/hole mismatches (e.g., bass_chalumeau_Bb has 8 fingerings but no tone holes in the modular builder).
5. File placement violations.
6. Duplicate/dead code.

We are to look for more, especially in the acoustic/optimization code.

We are given specific files to prioritize. Let's examine them one by one for the issues we are to report.

However, note that we are not to modify the files, only report.

We'll break down by the sections of the report.

### 1. Critical Bugs (must fix before merging to main)

We'll look for bugs that would produce wrong instrument dimensions or wrong predicted pitches.

#### Example from audit: impossible outer diameters

In `backend/benchmark_all.py`:

- `pvc_flute_D`: `bore_radius=10.2`, `outer_diameter=14` → impossible wall (OD < 2×radius).
- `diatonic_D_chalumeau`: `bore_radius=8.0`, `outer_diameter=14` → impossible wall (OD < 2×radius).

We should check if there are more.

Let's look at the provided snippet of `backend/benchmark_all.py`:

We see:
```python
    "pvc_flute_D": {
        "desc": "PVC flute in D (open-open)",
        "closed_top": False,
        "targets": [293.66, 329.63, 369.99, 415.30, 466.16, 523.25],
        "names": ["D4", "E4", "F4", "G4", "A4", "B4"],
        "bore_radius": 10.2, "outer_diameter": 14,
        "hole_diameter": 12.5, "hole_length": 3.0,
        "fingerings": [
            ["closed"] * 6,
            ["open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed"],
        ],
    },
    ...
    "diatonic_D_chalumeau": {
        "desc": "Diatonic chalumeau in D (closed-open)",
        "closed_top": True,
        "targets": [293.66, 329.63, 369.99, 415.30, 466.16, 523.25],
        "names": ["D4", "E4", "F4", "G4", "A4", "B4"],
        "bore_radius": 8.0, "outer_diameter": 14,
        "hole_diameter": 7.0, "hole_length": 3.75,
        "fingerings": [
            ["closed"] * 6,
            ["open", "closed", "closed", "closed", "closed", "closed"],
            ["open", "open", "closed", "closed", "closed", "closed"],
            ["open", "open", "open", "closed", "closed", "closed"],
            ["open", "open", "open", "open", "closed", "closed"],
            ["open", "open", "open", "open", "open", "closed"],
        ],
    },
```

Indeed, for `pvc_flute_D`: bore_radius=10.2 → diameter=20.4, but outer_diameter=14 -> which is less than 20.4 -> impossible.
Similarly for `diatonic_D_chalumeau`: bore_radius=8.0 -> diameter=16, outer_diameter=14 -> impossible.

This is a critical bug because it leads to negative wall thickness, which is unphysical and would break the acoustic model (or at least produce nonsensical results).

We should also check other instruments.

In the same file, we see:
- `chalumeau_C`: bore_radius=7.25, outer_diameter=22.0 -> 2*7.25=14.5 < 22.0 -> OK.
- `bass_chalumeau_Bb`: bore_radius=9.5, outer_diameter=28.0 -> 2*9.5=19.0 < 28.0 -> OK.
- `soprano_sax_Bb`: bore_radius=6.0, outer_diameter=20.0 -> 12 < 20 -> OK.
- `xaphoon_C`: bore_radius=7.0, outer_diameter=20.0 -> 14 < 20 -> OK.
- `alto_sax_Eb`: bore_radius=8.5, outer_diameter=26.0 -> 17 < 26 -> OK.

But note: the audit also mentions `concert_flute_C` and `alto_flute_G` without giving the numbers. We don't see them in the provided snippet, but they might be defined elsewhere in the file.

We should also check for the fingering/hole mismatch.

The audit says:
- `benchmark_all.py::INSTRUMENTS["bass_chalumeau_Bb"]` has 8 target notes and 8-column fingerings, but `modular_components.build_bass_chalumeau_Bb()` does not add any tone holes to the assembly.

Let's look at `backend/modular_components.py` for the function `build_bass_chalumeau_Bb`.

We don't have the full file, but we can see from the audit that it doesn't add any tone holes.

This is a critical bug because the instrument would have no tone holes, so it could only play the fundamental (and overblown notes) but not the intended scale.

We should also look for parameter plumbing bugs.

For example, in `backend/jax_optimizer.py`, we see in the `sequential_placement` function:

```python
    def bore_obj(L):
        try:
            inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
                cfg["outer_diameter"], closed_top, 0.5)
            ...
```

Here, `cfg["outer_diameter"]` is used. But note: in the `benchmark_all.py` definitions, we have `outer_diameter` as a key. However, in the `tmm_instrument_from_radii` function (from `tmm_acoustics`), we see that it expects `outer_diameter_mm` as an argument.

But wait: in the call above, we are passing `cfg["outer_diameter"]` as the fifth argument? Let's see the function signature of `tmm_instrument_from_radii` from `tmm_acoustics` (not provided, but we can infer from usage).

In `backend/jax_optimizer.py` we also have:

```python
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
    )
```

So the function expects `outer_diameter_mm` as a keyword argument.

In the `sequential_placement` function, we are passing `cfg["outer_diameter"]` as the fifth positional argument. Let's check the order of arguments in `tmm_instrument_from_radii`.

We don't have the exact signature, but from the call in `jax_optimizer.py` we see:

```python
tmm_instrument_from_radii(radii, bore_length, hp, hd, hl, outer_diameter_mm=..., closed_top=..., cone_step=...)
```

So the first five are: radii, bore_length, hp, hd, hl.

Then comes `outer_diameter_mm` as a keyword.

In the `sequential_placement` function, the call is:

```python
inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
    cfg["outer_diameter"], closed_top, 0.5)
```

This is passing 6 positional arguments: bore_radii, L, [], [], [], cfg["outer_diameter"] and then two more: closed_top and 0.5.

But the function expects at least 5 positional arguments (radii, bore_length, hp, hd, hl) and then keyword arguments.

So the sixth positional argument is being interpreted as `outer_diameter_mm`? But wait, the function might have more parameters.

Alternatively, the function might be defined as:

```python
def tmm_instrument_from_radii(radii, bore_length, hole_positions, hole_diameters, hole_lengths, outer_diameter_mm, closed_top, cone_step):
```

But that doesn't match the keyword usage in `jax_optimizer.py` where we see `outer_diameter_mm=` and `closed_top=` and `cone_step=`.

Actually, in the `jax_optimizer.py` call, we are using keyword arguments for `outer_diameter_mm`, `closed_top`, and `cone_step`. So the function must have these as keyword-only or at least accept them as keywords.

But in the `sequential_placement` call, we are passing `cfg["outer_diameter"]` as the sixth positional argument. If the function's sixth parameter is `outer_diameter_mm`, then it would be correct. However, we cannot be sure without seeing the function.

But note: in the `jax_optimizer.py` call, we are using `outer_diameter_mm=22.0` as a keyword. This suggests that the function has a parameter named `outer_diameter_mm` that can be passed by keyword.

In the `sequential_placement` call, we are passing it as the sixth positional argument. If the function's signature is:

```python
def tmm_instrument_from_radii(radii, bore_length, hole_positions, hole_diameters, hole_lengths, outer_diameter_mm, closed_top, cone_step):
```

Then the call in `sequential_placement` would be:

- radii: bore_radii
- bore_length: L
- hole_positions: [] (first empty list)
- hole_diameters: [] (second empty list)
- hole_lengths: [] (third empty list)
- outer_diameter_mm: cfg["outer_diameter"]
- closed_top: closed_top
- cone_step: 0.5

This would be correct if the function expects exactly 8 parameters (6 positional and 2 keyword? Actually, no: if all are positional, then 8 positional).

But wait, the function might have default values for `closed_top` and `cone_step`. We don't know.

However, note that in the `jax_optimizer.py` call, we are explicitly passing `closed_top` and `cone_step` as keywords. This is safe regardless of order.

But in the `sequential_placement` call, we are relying on the order. If the function's signature changed, this could break.

But more importantly, we are passing `cfg["outer_diameter"]` for `outer_diameter_mm`. This is correct if the configuration key is named `outer_diameter` and the function expects `outer_diameter_mm`.

However, in the `benchmark_all.py` definitions, we see the key is `outer_diameter` (without `_mm`). So the configuration uses `outer_diameter` but the function expects `outer_diameter_mm`. This is a mismatch.

In the `jax_optimizer.py` call, we are passing `outer_diameter_mm=22.0` (a hardcoded value) instead of using the config. This is another bug: the config's `outer_diameter` is being ignored in favor of a hardcoded 22.0.

Let me check:

In `jax_optimizer.py` in the `eval_all` function:

```python
    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
    )
```

Here, `outer_diameter_mm` is hardcoded to 22.0, ignoring the config.

Similarly, in the `sequential_placement` function, we are using `cfg["outer_diameter"]` but note that the config key is `outer_diameter` (without `_mm`). However, the function call in `sequential_placement` is passing it as the sixth positional argument, which we assume is `outer_diameter_mm`. But if the function expects the parameter to be named `outer_diameter_mm` and we are passing it positionally, then it is correct only if the function's sixth parameter is `outer_diameter_mm`.

But the hardcoded 22.0 in `eval_all` is definitely wrong because it ignores the config.

This is a critical bug because the outer diameter is being ignored in the cost function, leading to incorrect acoustic simulations (since outer diameter affects the end correction and radiation impedance).

We should also check the `two_phase_optimizer.py` and `pareto_optimizer.py` for similar issues.

In `two_phase_optimizer.py`, in the `phase1_de_search` function:

```python
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lens,
                outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
                loss_model=loss_model,
            )
```

Again, hardcoded 22.0 and `closed_top=False` (which might be wrong for closed-top instruments).

In `phase2_lbfgsb_refine`:

```python
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lens,
                outer_diameter_mm=22.0, closed_top=False, cone_step=0.5,
                loss_model=loss_model,
            )
```

Same issue.

In `pareto_optimizer.py`, we see in the `evaluate_bi_objective` function (incomplete in the snippet, but we can see the call):

```python
    inst = tmm_instrument_from_radii(
        radii, bore_length, hole_positions, hole_diameters, hole_lengths,
        outer_diameter_mm=outer_diameter, closed_top=closed_top, cone_step=0.5,
        loss_model=loss_model,
    )
```

Here, `outer_diameter_mm=outer_diameter` is used, and `outer_diameter` is an argument to the function. So this one is correct if the argument `outer_diameter` is passed in.

But note: in the function signature of `evaluate_bi_objective` we see:

```python
def evaluate_bi_objective(
    radii: np.ndarray,
    bore_length: float,
    hole_positions: list[float],
    hole_diameters: list[float],
    hole_lengths: list[float],
    closed_top: bool,
    targets: Sequence[float],
    bore_radius: float,
    outer_diameter: float,
    n_register: int | None = None,
    loss_model: object | None
```

So `outer_diameter` is passed in and then used as `outer_diameter_mm=outer_diameter`. This is correct.

However, note that the `benchmark_all.py` definitions use the key `outer_diameter` (without `_mm`). So when the config is passed, the value of `outer_diameter` in the config is used. This is correct.

But in `jax_optimizer.py` and `two_phase_optimizer.py`, we are hardcoding 22.0 and ignoring the config.

This is a critical bug.

Let's also check for fingering/register convention bugs.

In `backend/chromatic_flute.py`, we see:

```python
    # ---- Lower register: C4-B4 (notes 0-11, n_register=2) ----
    # n_open = note_index (0..11 holes open from bottom)
    for i in range(12):
        self.all_fingerings.append(self._seq_fing(i))
        self.all_registers.append(2)
        self.all_note_names.append(self.CHROMATIC_NOTES[i][0])
        self.all_target_freqs.append(self.CHROMATIC_NOTES[i][1])

    # ---- Upper register: C5-B5 (notes 12-23, n_register=3) ----
    # Same fingerings as C4-B4, but overblown (n_register=3)
    for i in range(12):
        self.all_fingerings.append(self._seq_fing(i))
        self.all_register