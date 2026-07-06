"""
scipy_optimizer.py — Scipy-based optimizer for demakein instrument designs.
============================================================================

Part of the Instrument Designer project. This is a PROTOTYPE alternative
optimizer that replaces demakein's custom legion-based multiprocessing
optimizer with scipy's single-process optimization algorithms.

Purpose
-------
demakein's built-in optimizer (demakein.optimize.improve) uses a custom
evolution strategy with a multiprocessing worker pool via demakein.legion.
This legion framework has proven fragile when frozen with PyInstaller
(worker processes crash due to None stdout/stderr, coordinator shutdown
races, etc.).

This module provides a drop-in alternative that avoids legion entirely,
using scipy's differential_evolution and basinhopping instead.

Tradeoffs
---------
+ No multiprocessing crashes (single-process)
+ More standard/well-tested optimization algorithms
+ Easier to debug and extend

- Significantly worse results (score ~245 vs demakein's ~13-35 for folk flute)
- Two-phase approach (constraint minimization + score minimization) is fragile
- Much slower for full optimization
- demakein's custom ES is genuinely better-tuned for this problem space

Verdict: demakein.optimize.improve IS the better optimizer. The crashes we
fixed were in demakein.legion (multiprocessing layer), not the optimizer
itself. Use DemakeinDesigner (demakein_wrapper.py) for production.

How this optimizer works (two-phase)
-------------------------------------
Phase 1 — Find ANY valid geometry:
    demakein's initial_state_vec violates constraints (score ~C85 for folk
    flute). We use differential_evolution with tight bounds around this
    vector and a penalty function that returns 1e6 for invalid geometries.
    This finds a constraint-satisfying (valid) instrument.

Phase 2 — Minimize the acoustic score:
    Starting from the valid geometry found in Phase 1, we use scipy's
    basinhopping (global optimization via random perturbations + local
    Nelder-Mead minimization) to minimize the acoustic score.

Why the two-phase approach?
    demakein's constrainer + scorer are split: constrainer returns 0 for
    valid, >0 for invalid; scorer returns the acoustic quality score.
    Combining them into a single objective (e.g., 2000 + constraint for
    invalid, score for valid) creates a discontinuous landscape that
    general-purpose optimizers handle poorly.

Why results are worse
    demakein's optimizer uses a weighted-combination mutation strategy
    tuned for this specific parameter space. It maintains a pool of the
    best candidates and generates new ones by taking weighted combinations,
    which efficiently explores the narrow valid region. General-purpose
    optimizers (DE, basinhopping, Nelder-Mead) use generic mutation
    strategies not specialized for this problem.

Usage
-----
    from woodwind_designer.engine.scipy_optimizer import ScipyDesigner

    designer = ScipyDesigner(output_base="designs_scipy")
    result = designer.design("folk_flute", transpose=0, quick=True,
                             on_progress=lambda msg: print(msg))
    print(result.success, result.log)

Requirements
------------
- demakein (pip install demakein)
- scipy >= 1.7.0 (pip install scipy)
- numpy
- PyYAML (for config export)
"""

import os
import sys
import time
import io
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# demakein imports — all design classes live here
# ---------------------------------------------------------------------------
try:
    from demakein import (
        Design_reedpipe, Design_folk_flute, Design_folk_shawm,
        Design_folk_whistle, Design_recorder, Design_dorian_whistle,
        Design_pflute, Design_reed_drone, Design_shawm,
        Design_three_hole_whistle,
    )
    HAVE_DEMAKEIN = True
except ImportError:
    HAVE_DEMAKEIN = False

# ---------------------------------------------------------------------------
# scipy imports — we use differential_evolution (Phase 1) and basinhopping
# (Phase 2). Falls back gracefully if scipy is missing.
# ---------------------------------------------------------------------------
try:
    from scipy.optimize import differential_evolution, basinhopping
    HAVE_SCIPY = True
except ImportError:
    HAVE_SCIPY = False


@dataclass
class DesignResult:
    """Result of a design optimization run.

    Attributes:
        output_dir: Absolute path to the directory containing output files.
        ident: Unique identifier string for this design instance
               (e.g. "design-folk-flute--<path>").
        stl_files: List of paths to generated .stl files (empty for
                   quick draft since STLs come from FreeCAD processing).
        config_yaml: Path to the generated YAML configuration file, or
                     "" if generation failed.
        log: Human-readable log message describing the outcome.
        success: True if optimization completed without fatal errors.
    """
    output_dir: str
    ident: str
    stl_files: list = field(default_factory=list)
    config_yaml: str = ""
    log: str = ""
    success: bool = False


class ScipyDesigner:
    """Design wind instruments using scipy-based optimization.

    Mirrors the public API of DemakeinDesigner (demakein_wrapper.py)
    but replaces demakein.optimize.improve with scipy algorithms.

    The optimizer uses a two-phase approach:
        1. Find any constraint-satisfying instrument geometry
        2. Minimize the acoustic score from that valid starting point

    See module docstring for detailed tradeoffs vs DemakeinDesigner.
    """

    # Nested dict: family -> subcategory -> preset_key -> Design class
    CATEGORIES = {
        "Wind": {
            "Woodwind": {
                "reedpipe": Design_reedpipe if HAVE_DEMAKEIN else None,
                "folk_shawm": Design_folk_shawm if HAVE_DEMAKEIN else None,
                "shawm": Design_shawm if HAVE_DEMAKEIN else None,
                "reed_drone": Design_reed_drone if HAVE_DEMAKEIN else None,
            },
            "Flute": {
                "folk_flute": Design_folk_flute if HAVE_DEMAKEIN else None,
                "folk_whistle": Design_folk_whistle if HAVE_DEMAKEIN else None,
                "recorder": Design_recorder if HAVE_DEMAKEIN else None,
                "dorian_whistle": Design_dorian_whistle if HAVE_DEMAKEIN else None,
                "pflute": Design_pflute if HAVE_DEMAKEIN else None,
                "three_hole_whistle": Design_three_hole_whistle if HAVE_DEMAKEIN else None,
            },
        },
    }

    PRESET_DISPLAY_NAMES = {
        "reedpipe": "Reedpipe",
        "folk_shawm": "Folk Shawm",
        "shawm": "Shawm",
        "reed_drone": "Reed Drone",
        "folk_flute": "Folk Flute",
        "folk_whistle": "Penny Whistle (Tin Whistle)",
        "recorder": "Soprano Recorder",
        "dorian_whistle": "Dorian Whistle",
        "pflute": "Pan Flute",
        "three_hole_whistle": "Three-Hole Whistle (Tabor Pipe)",
    }

    PRESET_DESCRIPTIONS = {
        "reedpipe": "Simple single-reed pipe (like a clarinet practice chanter)",
        "folk_shawm": "Compact double-reed folk shawm",
        "shawm": "Full double-reed shawm",
        "reed_drone": "Continuous-sounding reed drone pipe",
        "folk_flute": "Pennywhistle-style folk flute, 6 holes",
        "folk_whistle": "Tin whistle with pennywhistle fingering",
        "recorder": "Recorder with full fingering system",
        "dorian_whistle": "Whistle tuned to the Dorian mode",
        "pflute": "Pan flute with multiple pipes",
        "three_hole_whistle": "Medieval three-hole tabor pipe",
    }

    def __init__(self, output_base: str = "designs"):
        """Initialize the designer.

        Args:
            output_base: Directory under which design outputs are created.
                         Each design gets its own subdirectory.
        """
        self.output_base = Path(output_base)
        self.output_base.mkdir(parents=True, exist_ok=True)

    # ---- preset listing helpers (same API as DemakeinDesigner) ------------

    def list_families(self):
        return list(self.CATEGORIES.keys())

    def list_subcategories(self, family: str):
        return list(self.CATEGORIES.get(family, {}).keys())

    def list_presets(self, family: str, subcategory: str):
        subs = self.CATEGORIES.get(family, {})
        presets = subs.get(subcategory, {})
        return [k for k, v in presets.items() if v is not None]

    def get_description(self, preset: str):
        return self.PRESET_DESCRIPTIONS.get(preset, "")

    def _find_class(self, preset: str):
        for subs in self.CATEGORIES.values():
            for presets in subs.values():
                if preset in presets:
                    return presets[preset]
        return None

    # ---- main entry point ------------------------------------------------

    def design(self, preset: str, transpose: int = 0,
               output_dir: Optional[str] = None,
               on_progress=None, quick: bool = False) -> DesignResult:
        """Run a design optimization for the given preset.

        Args:
            preset: Instrument type key (e.g. "folk_flute", "recorder").
            transpose: Transposition in semitones (0 = concert pitch).
            output_dir: Custom output directory. If None, auto-generated
                        under output_base.
            on_progress: Callable receiving str status updates. Called
                         during optimization so the UI can show progress.
            quick: If True, use faster/coarser optimization (Quick Draft).
                   If False, run full high-quality optimization.

        Returns:
            DesignResult with success/failure, output paths, and log.
        """
        if not HAVE_DEMAKEIN:
            return DesignResult(output_dir="", ident="", success=False,
                                log="demakein not installed")
        if not HAVE_SCIPY:
            return DesignResult(output_dir="", ident="", success=False,
                                log="scipy not installed (pip install scipy)")

        cls = self._find_class(preset)
        if cls is None:
            return DesignResult(output_dir="", ident="", success=False,
                                log=f"Unknown preset '{preset}'")

        design_dir = output_dir or str(self.output_base / f"{preset}_design")
        os.makedirs(design_dir, exist_ok=True)

        # ---- create the demakein designer --------------------------------
        # We use demakein's design class for parameterization, constraints,
        # scoring, and I/O — only the optimizer algorithm is replaced.
        designer = cls(output_dir=design_dir, transpose=transpose)

        import numpy as np
        init_vec = designer.initial_state_vec
        n_params = len(init_vec)

        # ---- hyperparameters ---------------------------------------------
        # quick mode: fewer iterations, looser tolerances, larger steps
        if quick:
            maxiter = 500
            pop_scale = 5
            tol = 0.05
        else:
            maxiter = 2000
            pop_scale = 15
            tol = 1e-4

        # Tight bounds around the initial vector — ±0.5 for quick,
        # ±0.3 for full. The initial vector violates constraints, so we
        # need enough room for the optimizer to escape the invalid region.
        tight = 0.5 if quick else 0.3
        bounds = [(init_vec[i] - tight, init_vec[i] + tight)
                  for i in range(n_params)]

        # Seed the initial population near init_vec.
        np.random.seed(42)
        pop_size = max(10, int(n_params * pop_scale))
        init_pop = np.array([
            init_vec + np.random.uniform(-tight * 0.3, tight * 0.3, n_params)
            for _ in range(pop_size * 2)
        ])

        # ---- helper: validate a vector -----------------------------------
        def _check(vec):
            """Check if a state vector produces a valid, playable instrument.

            Returns (True, score) if valid, (False, constraint_value) if not.
            This wraps demakein's constrainer + scorer but also runs
            prepare()/prepare_phase() which have additional assertions
            not covered by the constrainer.
            """
            c = designer._constrainer(vec)
            if c:
                return False, c
            try:
                inst = designer.unpack(vec)
                patched = designer.patch_instrument(inst)
                patched.prepare()
                patched.prepare_phase()
            except Exception:
                return False, None
            return True, designer._scorer(vec)

        # ---- stdout wrapper for progress capture -------------------------
        class _ProgressStream:
            """A file-like object that wraps sys.stdout for the duration
            of optimization. Writes through to the real stdout but also
            discards ANSI codes. In frozen builds (console=False), the
            underlying stream is a StringIO to avoid None crashes.
            """
            def __init__(self, stream, callback):
                self.stream = stream or io.StringIO()
            def isatty(self):
                return False
            def fileno(self):
                raise OSError()
            def write(self, text):
                self.stream.write(text)
            def flush(self):
                try:
                    self.stream.flush()
                except (OSError, AttributeError):
                    pass

        stdout_orig = sys.stdout
        sys.stdout = _ProgressStream(sys.stdout, on_progress)

        def _status(msg):
            """Print a status message AND send it to the progress callback."""
            print(msg)
            if on_progress:
                on_progress(msg)

        try:
            # ---- Phase 1: find ANY valid geometry ------------------------
            # The initial vector violates constraints (C85+). We use
            # differential_evolution to minimize a penalty function that
            # returns 1e6 + constraint for invalid vectors, 0 for valid.
            # This guides the optimizer toward the valid region.
            print("Phase 1: seeking valid geometry...")
            _status("Seeking valid geometry...")

            def penalty_fn(vec):
                c = designer._constrainer(vec)
                if c:
                    return 1e6 + c
                try:
                    inst = designer.unpack(vec)
                    patched = designer.patch_instrument(inst)
                    patched.prepare()
                    patched.prepare_phase()
                except Exception:
                    return 1e6
                return 0.0

            res1 = differential_evolution(
                penalty_fn, bounds, seed=42,
                maxiter=200, init=init_pop,
                tol=1e-6, mutation=(0.5, 1.0),
                recombination=0.7, polish=False, workers=1,
            )

            # Extract the best valid vector from the result.
            valid_vec = res1.x
            ok, val = _check(valid_vec)
            if not ok:
                for v in res1.population:
                    ok2, val2 = _check(v)
                    if ok2:
                        valid_vec, val = v, val2
                        ok = True
                        break
            if not ok:
                raise RuntimeError(
                    f"No valid geometry found (best constraint={res1.fun:.4f})"
                )
            print(f"Valid. Score={val:.4f}")
            _status(f"Valid (score={val:.4f}) — optimizing...")

            # ---- Phase 2: minimize the acoustic score --------------------
            # From the valid geometry, use basinhopping (global random
            # jumps + local Nelder-Mead refinement) to minimize the score.
            best_known = [valid_vec.copy()]
            best_score_known = [val]
            last_report = [0.0]

            def obj_score(vec):
                ok, s = _check(vec)
                if not ok:
                    return 1e9
                if s < best_score_known[0]:
                    best_score_known[0] = s
                    best_known[0] = vec.copy()
                    t = time.time()
                    if t - last_report[0] >= 3.0:
                        last_report[0] = t
                        msg = f"Optimizing {preset} best={s:.5f}"
                        print(msg)
                        _status(msg)
                return s

            niter = 100 if quick else 500
            stepsize = 0.3 if quick else 0.15
            minimizer_kwargs = dict(
                method="Nelder-Mead",
                options=dict(maxiter=2000, xatol=1e-3, fatol=1e-3),
            )
            res2 = basinhopping(
                obj_score, valid_vec, niter=niter, stepsize=stepsize,
                minimizer_kwargs=minimizer_kwargs, seed=44, interval=10,
            )

            best_vec = res2.x
            ok, final_score = _check(best_vec)
            if not ok:
                best_vec = best_known[0]
                final_score = best_score_known[0]

            # ---- save final design & generate outputs --------------------
            designer._save(best_vec)
            print(f"Optimized {preset} best={final_score:.5f}")

            stl_files = sorted(Path(design_dir).rglob("*.stl"))

            config_yaml = ""
            try:
                sv = getattr(designer, 'state_vec', None)
                if sv is not None:
                    inst = designer.unpack(sv)
                    import yaml as _yaml
                    _n = 60
                    _positions = [
                        inst.length * i / (_n - 1) for i in range(_n)
                    ]
                    bore_profile = [
                        [round(p, 4), round(inst.inner(p) / 2.0, 4)]
                        for p in _positions
                    ]
                    tone_holes = [
                        {
                            "position": round(p, 4),
                            "radius": round(d / 2.0, 4),
                            "chimney_height": round(h, 4),
                        }
                        for p, d, h in zip(
                            inst.hole_positions, inst.hole_diameters,
                            inst.hole_lengths,
                        )
                    ]
                    yaml_cfg = {
                        "bore_length": round(inst.length / 1000.0, 4),
                        "bore_profile": bore_profile,
                        "tone_holes": tone_holes,
                    }
                    yaml_path = os.path.join(
                        design_dir, f"{preset}_config.yaml"
                    )
                    with open(yaml_path, "w") as _yh:
                        _yaml.dump(yaml_cfg, _yh, default_flow_style=None)
                    config_yaml = yaml_path
            except Exception:
                pass

            return DesignResult(
                output_dir=design_dir,
                ident=designer.ident(),
                stl_files=[str(f) for f in stl_files],
                config_yaml=config_yaml,
                success=True,
                log=(
                    f"Design '{designer.ident()}' completed. "
                    f"Best={final_score:.5f}. {len(stl_files)} STL files."
                ),
            )
        except Exception as e:
            import traceback
            return DesignResult(
                output_dir=design_dir,
                ident="",
                success=False,
                log=f"SciPy design failed: {e}\n{traceback.format_exc()}",
            )
        finally:
            sys.stdout = stdout_orig
