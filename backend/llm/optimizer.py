"""Standalone candidate optimizer for Dask serialization."""
from __future__ import annotations

import math
import os
import sys
import time
import traceback

import numpy as np

from backend.tmm_acoustics import SPEED_OF_SOUND
from backend.optimization.pareto import pareto_sweep, run_pareto

_c = SPEED_OF_SOUND


def _generate_cylindrical_radii(length_mm: float, radius_mm: float,
                                 flare_radius_mm: float | None = None,
                                 n_cp: int = 6) -> np.ndarray:
    return np.full(n_cp, radius_mm)


def _generate_conical_radii(length_mm: float, radius_start_mm: float,
                             radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    return np.linspace(radius_start_mm, radius_end_mm, n_cp)


def _generate_parabolic_radii(length_mm: float, radius_min_mm: float,
                               radius_max_mm: float, n_cp: int = 6) -> np.ndarray:
    t = np.linspace(0, 1, n_cp)
    r = radius_min_mm + (radius_max_mm - radius_min_mm) * t ** 2
    return r


def _generate_bessel_radii(length_mm: float, radius_start_mm: float,
                            radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    x = np.linspace(0.1, 1.0, n_cp)
    r = radius_start_mm + (radius_end_mm - radius_start_mm) * (1.0 - 1.0 / x) / (1.0 - 1.0)
    return np.clip(r, 1.0, 50.0)


def _generate_exponential_radii(length_mm: float, radius_start_mm: float,
                                 radius_end_mm: float, n_cp: int = 6) -> np.ndarray:
    x = np.linspace(0, 1, n_cp)
    growth = math.log(radius_end_mm / max(radius_start_mm, 0.1))
    r = radius_start_mm * np.exp(growth * x)
    return r


BORE_SHAPE_GENERATORS = {
    "cylindrical": _generate_cylindrical_radii,
    "conical": _generate_conical_radii,
    "parabolic": _generate_parabolic_radii,
    "bessel": _generate_bessel_radii,
    "exponential": _generate_exponential_radii,
}


def _build_targets_from_spec(spec_dict: dict) -> list[float]:
    """Build multi-octave target frequencies from scale definition."""
    from backend.instrument_knowledge import SCALES
    scale = SCALES.get(spec_dict.get("scale", "12_tet"))
    if not scale:
        return []

    fundamental = spec_dict.get("lowest_note_hz", 261.63)
    targets = []
    interval_count = len(scale.intervals_cents)
    for octave in range(max(spec_dict.get("n_octaves", 1), 1)):
        for cents in scale.intervals_cents:
            f = fundamental * (2.0 ** ((octave * 1200 + cents) / 1200.0))
            targets.append(f)
    max_targets = max(spec_dict.get("hole_count", 6) + 3, 8)
    return targets[:max_targets]


def optimize_candidate(spec_dict: dict, verbose: bool = False) -> dict:
    """Optimize a single design candidate. Module-level for Dask serialization.

    Parameters
    ----------
    spec_dict : dict
        DesignSpec fields serialized as a plain dict.
    verbose : bool
        If True, print progress messages.

    Returns
    -------
    dict
        CandidateResult fields serialized as a plain dict, plus a copy of
        the input spec.
    """
    # Ensure repo is on path (Dask workers may not have it)
    _repo = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    if _repo not in sys.path:
        sys.path.insert(0, _repo)

    t0 = time.time()
    result: dict = {"success": False, "error": "", "opt_time_s": 0.0}

    targets = spec_dict.get("targets", [])
    if not targets or len(targets) < 2:
        try:
            targets = _build_targets_from_spec(spec_dict)
        except Exception:
            pass
        if not targets or len(targets) < 2:
            result["error"] = "Insufficient target frequencies"
            result["opt_time_s"] = time.time() - t0
            return result

    closed_top = spec_dict.get("closed_top", False)
    bore_r = spec_dict.get("bore_radius_mm", 7.25)
    outer_d = spec_dict.get("outer_diameter_mm", 22.0)
    hole_d = spec_dict.get("hole_diameter_mm", 7.0)
    hole_l = spec_dict.get("hole_length_mm", 3.75)
    bore_len = spec_dict.get("bore_length_mm", 500.0)
    hole_cnt = spec_dict.get("hole_count", 6)
    bore_type = spec_dict.get("bore_type", "cylindrical")
    name = spec_dict.get("name", "Unknown")

    n_holes = int(min(hole_cnt, len(targets) - 1))

    cfg = {
        "desc": name,
        "closed_top": closed_top,
        "targets": targets,
        "bore_radius": bore_r,
        "outer_diameter": outer_d,
        "hole_diameter": hole_d,
        "hole_length": hole_l,
    }

    generator = BORE_SHAPE_GENERATORS.get(bore_type, _generate_cylindrical_radii)
    bore_radii = generator(bore_len, bore_r, bore_r * 1.2)

    pareto_front = []
    try:
        sweep = pareto_sweep(cfg, n_weights=5, maxiter=60, verbose=False)
        pareto_front = [
            {"w_int": w, "intonation": intl, "timbre": timb}
            for w, intl, timb, L in sweep
        ]
    except Exception as e:
        if verbose:
            print(f"    Pareto sweep failed: {e}")

    front, designs, elapsed = [], [], 0.0
    try:
        front, designs, elapsed = run_pareto(
            cfg, pop_size=20, n_gen=25, verbose=False,
        )
    except Exception:
        if verbose:
            print("  NSGA-II failed:")
            traceback.print_exc()
        result["error"] = "NSGA-II optimization failed"
        result["opt_time_s"] = time.time() - t0
        return result

    if front:
        pareto_front = [
            {"intonation": intl, "timbre": timb}
            for intl, timb in front
        ]
        best_idx = min(range(len(front)), key=lambda i: front[i][0])
        best_design = designs[best_idx]

        n_cp = 6
        result["bore_radii"] = best_design[:n_cp].tolist()
        hp = sorted(best_design[n_cp:n_cp + n_holes].tolist())
        result["hole_positions_mm"] = hp
        result["hole_diameters_mm"] = best_design[n_cp + n_holes:].tolist()
        result["intonation_rms"] = float(front[best_idx][0])
        result["timbre_cost"] = float(front[best_idx][1])
        result["bore_length_opt_mm"] = bore_len
        result["success"] = True
    else:
        result["error"] = "NSGA-II returned empty front"

    result["pareto_front"] = pareto_front
    result["opt_time_s"] = time.time() - t0
    return result