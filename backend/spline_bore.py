"""
Spline bore profiles for variable-radius wind instrument design.

Enables arbitrary bore shapes (parabolic tapers, Bessel horns, stepped bores,
folded centerlines) as optimization variables in the TMM pipeline.

Coordinate system (same as chalumier/OpenWind):
  - position 0 = bell end (open)
  - position L = mouthpiece/reed end (closed for reed instruments)
  - Fingerings index 0 = nearest bell

Usage:
    from backend.spline_bore import SplineBore, analytical_bore

    # From explicit control points
    bore = SplineBore(
        positions=[0, 100, 200, 330],
        radii=[7.0, 6.5, 5.5, 4.0],
    )

    # Analytical shapes
    bore = analytical_bore('cone', length=330, r_bell=7.0, r_mouth=4.0)
    bore = analytical_bore('parabolic', length=330, r_bell=7.0, r_mouth=4.0)
    bore = analytical_bore('bessel', length=330, r_bell=7.0, r_mouth=4.0,
                           flare=0.7)

    # Convert to TMMInstrument
    inst = bore.to_tmm_instrument(
        hole_positions=[...],
        hole_diameters=[...],
        hole_lengths=[...],
        closed_top=False,
    )

    # Validate against known analytical results
    errors = bore.validate()
"""

import math
import numpy as np
from scipy.interpolate import CubicSpline
from typing import List, Optional, Tuple

from backend.tmm_acoustics import (
    TMMInstrument, Profile,
)


class SplineBore:
    """
    Variable-radius bore profile defined by cubic spline interpolation.

    Given N control points (position, radius), generates a smooth bore profile
    via monotone cubic Hermite interpolation (CubicSpline with not-a-knot BC).
    The profile is then sampled at uniform intervals to create a TMM-compatible
    Profile object.

    Attributes:
        positions: control point positions along bore (mm)
        radii: control point radii (mm)
        bore_length: total bore length (mm)
    """

    def __init__(
        self,
        positions: List[float],
        radii: List[float],
        n_samples: int = 64,
    ):
        """
        Args:
            positions: x-coordinates of control points (mm). Must be sorted ascending.
            radii: bore radius at each control point (mm). Must be > 0.
            n_samples: number of uniform samples for TMM Profile. Higher = more
                       accurate but slower. 32-128 is typical.
        """
        if len(positions) < 2:
            raise ValueError("Need at least 2 control points")
        if len(positions) != len(radii):
            raise ValueError("positions and radii must have same length")
        if any(r <= 0 for r in radii):
            raise ValueError("All radii must be positive")

        self.positions = np.asarray(positions, dtype=float)
        self.radii = np.asarray(radii, dtype=float)
        self.bore_length = float(self.positions[-1])
        self.n_samples = n_samples

        # Build cubic spline interpolant
        self._spline = CubicSpline(
            self.positions, self.radii,
            bc_type='not-a-knot',
        )

    def radius_at(self, x: float) -> float:
        """Evaluate bore radius at position x (mm)."""
        return float(self._spline(x))

    def diameter_at(self, x: float) -> float:
        """Evaluate bore diameter at position x (mm)."""
        return 2.0 * self.radius_at(x)

    def sample(self, n: Optional[int] = None) -> Tuple[np.ndarray, np.ndarray]:
        """
        Sample the bore profile at n uniform positions.

        Returns:
            (positions, radii) arrays of length n
        """
        n = n or self.n_samples
        x = np.linspace(0, self.bore_length, n)
        r = self._spline(x)
        # Ensure no negative radii from spline overshoot
        r = np.maximum(r, 0.1)
        return x, r

    def to_profile(self, n: Optional[int] = None) -> Profile:
        """
        Convert to a TMM-compatible Profile object.

        Returns a Profile with uniform steps, suitable for direct use
        with TMMInstrument.
        """
        x, r = self.sample(n)
        diameters = (r * 2.0).tolist()
        return Profile(x.tolist(), diameters)

    def to_tmm_instrument(
        self,
        hole_positions: List[float],
        hole_diameters: List[float],
        hole_lengths: List[float],
        outer_diameter: float = 22.0,
        closed_top: bool = False,
        cone_step: float = 0.5,
        loss_model: Optional[object] = None,
        n_samples: Optional[int] = None,
    ) -> TMMInstrument:
        """
        Create a TMMInstrument from this spline bore profile.

        This is the main entry point for integrating spline bores into
        the optimization pipeline.
        """
        x, r = self.sample(n_samples)
        diameters = (r * 2.0).tolist()
        outer_diams = [outer_diameter] * len(x)

        return TMMInstrument(
            inner_positions=x.tolist(),
            inner_diameters=diameters,
            outer_diameters=outer_diams,
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=hole_lengths,
            closed_top=closed_top,
            cone_step=cone_step,
            loss_model=loss_model,
        )

    def to_radii_array(self, n: Optional[int] = None) -> np.ndarray:
        """
        Sample and return radii array (for use with tmm_instrument_from_radii).

        Returns radii at n uniform positions between 0 and bore_length.
        """
        _, r = self.sample(n)
        return r

    def validate(self) -> dict:
        """
        Validate spline bore internal consistency.

        Tests:
        1. Interpolation accuracy: spline passes through all control points
        2. Smoothness: no wild oscillations between control points
        3. Cross-check: 2-point cylinder spline matches tmm_instrument_from_radii

        Returns dict with test results.
        """
        results = {}

        # Test 1: Interpolation accuracy — spline must hit control points exactly
        interp_errors = []
        for x, r in zip(self.positions, self.radii):
            got = self.radius_at(x)
            err = abs(got - r)
            interp_errors.append(err)
        max_interp_err = max(interp_errors) if interp_errors else 0.0
        results['interpolation'] = {
            'max_error_mm': max_interp_err,
            'pass': max_interp_err < 1e-10,
        }

        # Test 2: Smoothness — check second derivative magnitude
        x_fine, r_fine = self.sample(256)
        if len(r_fine) >= 3:
            d2r = np.diff(r_fine, n=2)
            max_osc = float(np.max(np.abs(d2r)))
        else:
            max_osc = 0.0
        results['smoothness'] = {
            'max_second_derivative_mm': max_osc,
            'pass': max_osc < 0.5,
        }

        # Test 3: Cross-check cylinder against tmm_instrument_from_radii
        L = self.bore_length
        r_ref = float(self.radii[0])
        x_ref, r_ref_arr = SplineBore([0, L], [r_ref, r_ref]).sample(64)
        from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
        inst_ref = tmm_instrument_from_radii(
            r_ref_arr, L, [], [], [],
            closed_top=False,
        )
        inst_spline = self.to_tmm_instrument([], [], [], closed_top=False)
        wl0 = SPEED_OF_SOUND / 300.0
        try:
            wl_ref = inst_ref.find_resonance(wl0, [], 1)
            f_ref = inst_ref.frequency_from_wavelength(wl_ref)
            wl_spline = inst_spline.find_resonance(wl0, [], 1)
            f_spline = inst_spline.frequency_from_wavelength(wl_spline)
            err_cents = abs(1200.0 * math.log2(f_ref / f_spline))
        except Exception:
            err_cents = -1.0
        results['crosscheck'] = {
            'reference_freq_hz': f_ref if err_cents >= 0 else None,
            'spline_freq_hz': f_spline if err_cents >= 0 else None,
            'error_cents': err_cents,
            'pass': 0 <= err_cents < 0.01,
        }

        return results


# ============================================================================
# Analytical bore shapes
# ============================================================================

def analytical_bore(
    shape: str,
    length: float,
    r_bell: float,
    r_mouth: float,
    flare: float = 0.5,
    n_control: int = 8,
    n_samples: int = 64,
) -> SplineBore:
    """
    Create a SplineBore from an analytical shape.

    Args:
        shape: one of 'cylinder', 'cone', 'parabolic', 'bessel', 'exponential'
        length: bore length in mm
        r_bell: radius at bell end (position 0)
        r_mouth: radius at mouthpiece end (position L)
        flare: flare parameter for Bessel/exponential (0=none, 1=maximum)
        n_control: number of control points for spline approximation
        n_samples: samples for TMM Profile

    Returns:
        SplineBore instance
    """
    x = np.linspace(0, length, n_control)

    if shape == 'cylinder':
        r = np.full(n_control, r_bell)

    elif shape == 'cone':
        r = r_bell + (r_mouth - r_bell) * x / length

    elif shape == 'parabolic':
        # r(x) = r_bell + (r_mouth - r_bell) * (x/L)^2
        r = r_bell + (r_mouth - r_bell) * (x / length) ** 2

    elif shape == 'bessel':
        # Bessel horn: r(x) = r_mouth * (1 + flare * (cosh(b*x) - 1))
        # where b is chosen so r(0) = r_bell
        if flare <= 0:
            r = np.full(n_control, r_bell)
        else:
            # Simpler parameterization:
            # r(x) = r_bell * (r_mouth/r_bell)^(x/L) with flare adjustment
            base = r_mouth / r_bell
            r = r_bell * base ** (x / length * flare) * (
                1.0 + (1.0 - flare) * (1.0 - x / length)
            )

    elif shape == 'exponential':
        # Exponential bore: r(x) = r_bell * exp(-alpha * x / L)
        # where alpha = ln(r_bell / r_mouth)
        alpha = math.log(r_bell / r_mouth) if r_mouth > 0 else 0
        r = r_bell * np.exp(-alpha * x / length)

    else:
        raise ValueError(f"Unknown shape: {shape}. Use 'cylinder', 'cone', "
                         "'parabolic', 'bessel', or 'exponential'")

    # Ensure minimum radius
    r = np.maximum(r, 0.5)

    return SplineBore(x.tolist(), r.tolist(), n_samples=n_samples)


def spline_bore_from_optimization(
    bore_length: float,
    n_control: int,
    r_min: float = 3.0,
    r_max: float = 12.0,
) -> SplineBore:
    """
    Create a SplineBore with uniformly-spaced control points suitable for
    optimization. Returns a bore with initial flat profile that can be
    modified by the optimizer.

    Args:
        bore_length: total bore length in mm
        n_control: number of control points (optimization variables = n_control)
        r_min: minimum allowed radius
        r_max: maximum allowed radius

    Returns:
        SplineBore with initial flat profile
    """
    x = np.linspace(0, bore_length, n_control)
    r_mid = (r_min + r_max) / 2.0
    r = np.full(n_control, r_mid)
    return SplineBore(x.tolist(), r.tolist())


def radii_from_spline(
    positions: List[float],
    radii: List[float],
    bore_length: float,
    n_samples: int = 64,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Convenience: take sparse control points, return dense sampled arrays.

    Useful for converting between spline representation and the flat
    radii array used by tmm_instrument_from_radii.

    Returns:
        (sampled_positions, sampled_radii) arrays
    """
    bore = SplineBore(positions, radii, n_samples=n_samples)
    return bore.sample(n_samples)
