"""
Design instruments from unconventional bore profiles.

A thin orchestrator that converts SplineBore descriptions into
optimizable parameters and delegates search to ``nsga2_minimize``.

Usage:
    from backend.design_from_unconventional import (
        design_from_profile,
        optimize_conical_bore,
        spline_bore_to_geometry,
    )
"""
from __future__ import annotations

import numpy as np

from backend.geometry import BoreProfile, HoleLayout, InstrumentGeometry
from backend.tmm_acoustics import SPEED_OF_SOUND


def spline_bore_to_geometry(
    spline,
    total_length: float,
    hole_positions: list[float],
    hole_diameters: list[float],
    closed_top: bool = False,
) -> InstrumentGeometry:
    """Convert a SplineBore to an ``InstrumentGeometry``."""
    z = np.linspace(0, total_length, 200)
    radii = np.array([spline.radius_at(zi) for zi in z])
    bore = BoreProfile(positions=z, radii=radii)
    holes = HoleLayout(
        positions=np.array(hole_positions),
        diameters=np.array(hole_diameters),
    )
    return InstrumentGeometry(
        total_length=total_length,
        bore=bore,
        holes=holes,
        closed_top=closed_top,
    )


def optimize_conical_bore(
    fundamental_hz: float,
    cone_angle_deg: float = 1.0,
    n_generations: int = 20,
    population_size: int = 30,
) -> dict:
    """Optimize a conical bore profile for the given fundamental.

    Calls ``optimization.nsga2.nsga2_minimize`` — never re-implements
    pymoo setup.
    """
    from backend.optimization.nsga2 import nsga2_minimize

    bore_length = SPEED_OF_SOUND / (2.0 * fundamental_hz)
    cone_rad = np.radians(cone_angle_deg)
    tip_radius = 5.0
    bell_radius = tip_radius + bore_length * np.tan(cone_rad)

    def _cost_fn(params: np.ndarray) -> float:
        r_tip, r_bell = float(params[0]), float(params[1])
        if r_tip <= 0 or r_bell <= r_tip:
            return 1e10
        # Simple conical bore: linear taper
        z = np.linspace(0, bore_length, 100)
        r = np.linspace(r_tip, r_bell, 100)
        # Cost is smoothness (second derivative)
        dr = np.diff(r)
        smoothness = float(np.std(np.diff(dr))) if len(dr) > 1 else 0.0
        return smoothness

    xl = np.array([max(1.0, tip_radius * 0.5), bell_radius * 0.8])
    xu = np.array([tip_radius * 2.0, bell_radius * 1.5])

    result = nsga2_minimize(
        _cost_fn, n_var=2, xl=xl, xu=xu,
        pop_size=population_size, n_gen=n_generations,
    )

    if result is None:
        return {"success": False, "error": "NSGA-II unavailable"}

    return {
        "success": True,
        "bore_length_mm": bore_length,
        "tip_radius_mm": float(result["x"][0]),
        "bell_radius_mm": float(result["x"][1]),
        "cost": result["fun"],
    }


def design_from_profile(
    spline,
    total_length: float,
    hole_positions: list[float],
    hole_diameters: list[float],
    closed_top: bool = False,
) -> dict:
    """Design an instrument from a spline bore profile.

    Converts to ``InstrumentGeometry`` and returns a design dict
    suitable for downstream processing (TMM evaluation, CAD export).
    """
    geom = spline_bore_to_geometry(
        spline, total_length, hole_positions, hole_diameters, closed_top,
    )
    radii, lengths, hole_specs = geom.to_tmm()
    return {
        "geometry": geom,
        "n_segments": len(radii),
        "total_length_mm": total_length,
        "bore_radii_mm": radii.tolist(),
        "segment_lengths_mm": lengths.tolist(),
        "hole_specs": hole_specs,
        "n_holes": len(hole_specs),
    }
