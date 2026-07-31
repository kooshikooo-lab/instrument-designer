"""Bore shape generators for unconventional instrument geometries.

Supports cylindrical, conical, parabolic, exponential, Bessel, spline,
spiral, ridged, elliptical, and stepped bore profiles.
Each generator returns an array of radii (mm) along the bore length.
"""

import math
import numpy as np
from scipy import interpolate

from backend.tmm_acoustics import SPEED_OF_SOUND


def generate_cylindrical_radii(
    length_mm: float, radius_mm: float,
    n_cp: int = 6,
) -> np.ndarray:
    return np.full(int(n_cp), radius_mm)


def generate_conical_radii(
    length_mm: float, radius_start_mm: float,
    radius_end_mm: float, n_cp: int = 6,
) -> np.ndarray:
    return np.linspace(radius_start_mm, radius_end_mm, int(n_cp))


def generate_parabolic_radii(
    length_mm: float, radius_min_mm: float,
    radius_max_mm: float, n_cp: int = 6,
) -> np.ndarray:
    t = np.linspace(0, 1, int(n_cp))
    return radius_min_mm + (radius_max_mm - radius_min_mm) * t ** 2


def generate_exponential_radii(
    length_mm: float, radius_start_mm: float,
    radius_end_mm: float, n_cp: int = 6,
) -> np.ndarray:
    x = np.linspace(0, 1, int(n_cp))
    growth = math.log(radius_end_mm / max(radius_start_mm, 0.1))
    return radius_start_mm * np.exp(growth * x)


def generate_bessel_radii(
    length_mm: float, radius_start_mm: float,
    radius_end_mm: float, n_cp: int = 6,
) -> np.ndarray:
    x = np.linspace(0.1, 1.0, int(n_cp))
    eps = math.log(radius_start_mm / max(radius_end_mm, 0.1)) / math.log(10.0)
    r = radius_start_mm * (x / 0.1) ** (-eps)
    return np.clip(r, 1.0, 50.0)


def generate_spline_radii(
    length_mm: float,
    control_points: list[tuple[float, float]],
    n_samples: int = 50,
) -> np.ndarray:
    if len(control_points) < 2:
        return np.full(n_samples, control_points[0][1] if control_points else 7.0)
    pts = np.array(control_points)
    if len(pts) == 2:
        return np.linspace(pts[0, 1], pts[1, 1], n_samples)
    tck = interpolate.splrep(pts[:, 0], pts[:, 1], s=0)
    x_new = np.linspace(pts[0, 0], pts[-1, 0], n_samples)
    return interpolate.splev(x_new, tck)


def generate_spiral_radii(
    length_mm: float, base_radius_mm: float,
    amplitude_mm: float, cycles: float,
    n_cp: int = 50,
) -> np.ndarray:
    """Sinusoidal oscillation in radius (spiral-like internal profile)."""
    x = np.linspace(0, 1, int(n_cp))
    return base_radius_mm + amplitude_mm * np.sin(2 * math.pi * cycles * x)


def generate_ridged_radii(
    length_mm: float, base_radius_mm: float,
    ridge_depth_mm: float, n_ridges: int,
    n_cp: int = 50,
) -> np.ndarray:
    """Periodic grooves/ridges along the bore (like corrugated tube)."""
    x = np.linspace(0, 1, int(n_cp))
    ridge = ridge_depth_mm * (np.sin(2 * math.pi * n_ridges * x)) ** 2
    return base_radius_mm - ridge


def generate_elliptical_radii(
    length_mm: float, radius_base_mm: float,
    eccentricity: float, n_cp: int = 6,
) -> np.ndarray:
    """Elliptical cross-section approximated as equivalent circular radius.

    eccentricity 0 = circle, >0 flattens. Equivalent radius for TMM
    uses hydraulic radius approximation: r_eq = a * sqrt(1 - e^2/2)
    where a = radius_base_mm, e = eccentricity.
    """
    eq_factor = math.sqrt(max(1.0 - eccentricity ** 2 / 2.0, 0.25))
    return np.full(int(n_cp), radius_base_mm * eq_factor)


def generate_stepped_radii(
    length_mm: float, radius_start_mm: float,
    radius_end_mm: float, n_steps: int,
    n_cp: int = 6,
) -> np.ndarray:
    """Discrete stepped bore (like recorder/flageolet)."""
    n = int(n_cp)
    x = np.linspace(0, 1, n)
    step_pos = np.linspace(0, 1, int(n_steps) + 1)
    radii = np.linspace(radius_start_mm, radius_end_mm, int(n_steps) + 1)
    idx = np.clip(np.searchsorted(step_pos, x, side="right") - 1, 0, len(radii) - 1)
    return radii[idx]


BORE_SHAPE_GENERATORS: dict[str, callable] = {
    "cylindrical": generate_cylindrical_radii,
    "conical": generate_conical_radii,
    "parabolic": generate_parabolic_radii,
    "exponential": generate_exponential_radii,
    "bessel": generate_bessel_radii,
    "spline": generate_spline_radii,
    "spiral": generate_spiral_radii,
    "ridged": generate_ridged_radii,
    "elliptical": generate_elliptical_radii,
    "stepped": generate_stepped_radii,
}


BORE_TYPE_META: dict[str, dict] = {
    "cylindrical": {
        "label": "Cylindrical",
        "params": {"radius_mm": (3.0, 15.0, 7.25)},
        "description": "Constant-radius bore (clarinets, flutes)",
    },
    "conical": {
        "label": "Conical",
        "params": {"radius_start_mm": (3.0, 20.0, 5.0), "radius_end_mm": (5.0, 25.0, 9.0)},
        "description": "Linear taper from mouthpiece to bell (saxes, oboes)",
    },
    "parabolic": {
        "label": "Parabolic",
        "params": {"radius_min_mm": (3.0, 15.0, 5.0), "radius_max_mm": (5.0, 25.0, 9.0)},
        "description": "Quadratic flare, narrow mouthpiece widening to bell",
    },
    "exponential": {
        "label": "Exponential",
        "params": {"radius_start_mm": (3.0, 20.0, 5.0), "radius_end_mm": (5.0, 25.0, 9.0)},
        "description": "Exponential flare (brass instruments, didgeridoo)",
    },
    "bessel": {
        "label": "Bessel",
        "params": {"radius_start_mm": (3.0, 20.0, 5.0), "radius_end_mm": (5.0, 25.0, 9.0)},
        "description": "Power-law flare, Bessel horn profile",
    },
    "spline": {
        "label": "Spline (Free-form)",
        "params": {},
        "description": "User-defined control points, cubic spline interpolation",
    },
    "spiral": {
        "label": "Spiral",
        "params": {
            "base_radius_mm": (5.0, 15.0, 8.0),
            "amplitude_mm": (0.5, 5.0, 2.0),
            "cycles": (1.0, 8.0, 3.0),
        },
        "description": "Sinusoidal radius oscillation along bore (spiral-like)",
    },
    "ridged": {
        "label": "Ridged",
        "params": {
            "base_radius_mm": (5.0, 15.0, 8.0),
            "ridge_depth_mm": (0.5, 4.0, 1.5),
            "n_ridges": (2, 12, 5),
        },
        "description": "Periodic radial grooves along the bore (corrugated)",
    },
    "elliptical": {
        "label": "Elliptical",
        "params": {
            "radius_base_mm": (5.0, 15.0, 8.0),
            "eccentricity": (0.0, 0.95, 0.3),
        },
        "description": "Elliptical cross-section via equivalent circular radius",
    },
    "stepped": {
        "label": "Stepped",
        "params": {
            "radius_start_mm": (3.0, 12.0, 5.0),
            "radius_end_mm": (5.0, 20.0, 10.0),
            "n_steps": (2, 10, 4),
        },
        "description": "Discrete stepped bore profile (recorder-like)",
    },
}


def bore_profile_to_diameter(
    radii: np.ndarray, n_samples: int = 50,
) -> list[tuple[float, float]]:
    x = np.linspace(0, 1, len(radii))
    x_new = np.linspace(0, 1, n_samples)
    if len(radii) < 2:
        return [(pos, float(radii[0] * 2)) for pos in np.linspace(0, 1, n_samples)]
    tck = interpolate.splrep(x, radii, s=0)
    r_interp = interpolate.splev(x_new, tck)
    return [(float(x_new[i]), float(r_interp[i] * 2)) for i in range(n_samples)]
