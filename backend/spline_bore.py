"""SplineBore: variable-radius bore profile using cubic spline interpolation.

Provides a continuous bore profile from sparse control points, with
conversion to the TMM-compatible format for acoustic simulation.

Coordinate system: position 0 = mouthpiece/reed (closed end),
position L = bell (open end).
"""

import numpy as np
from scipy.interpolate import CubicSpline

from backend.tmm_acoustics import TMMInstrument, Profile, SPEED_OF_SOUND, tmm_instrument_from_radii


class SplineBore:
    def __init__(self, positions: list[float], radii: list[float], n_samples: int = 64) -> None:
        self._positions = np.array(positions, dtype=float)
        self._radii = np.array(radii, dtype=float)
        self._n_samples = n_samples
        self._length = float(self._positions[-1])
        self._spline = CubicSpline(self._positions, self._radii, bc_type='not-a-knot')

    def radius_at(self, x: float | np.ndarray) -> float | np.ndarray:
        return np.maximum(self._spline(x), 1e-6)

    def diameter_at(self, x: float | np.ndarray) -> float | np.ndarray:
        return 2.0 * self.radius_at(x)

    def sample(self, n: int | None = None) -> tuple[np.ndarray, np.ndarray]:
        if n is None:
            n = self._n_samples
        x = np.linspace(0.0, self._length, n)
        return x, self.radius_at(x)

    def to_profile(self, n: int | None = None) -> Profile:
        x, r = self.sample(n)
        return Profile(x.tolist(), (2.0 * r).tolist())

    def to_tmm_instrument(
        self,
        hole_positions: list[float],
        hole_diameters: list[float],
        hole_lengths: list[float],
        outer_diameter: float = 22.0,
        closed_top: bool = False,
        cone_step: float = 0.5,
        loss_model: object | None = None,
        n_samples: int | None = None,
    ) -> TMMInstrument:
        x, r = self.sample(n_samples)
        n = len(x)
        inner_diameters = (2.0 * r).tolist()
        outer_diameters = [outer_diameter] * n
        return TMMInstrument(
            inner_positions=x.tolist(),
            inner_diameters=inner_diameters,
            outer_diameters=outer_diameters,
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=hole_lengths,
            closed_top=closed_top,
            cone_step=cone_step,
            speed_of_sound=SPEED_OF_SOUND,
            reed_virtual_length=0.0,
            whistle_clip=0.0,
            whistle_windway_diameter=0.0,
            whistle_windway_length=0.0,
            loss_model=loss_model,
        )

    def to_radii_array(self, n: int | None = None) -> np.ndarray:
        _, r = self.sample(n)
        return r

    def to_radii(self, n: int | None = None) -> np.ndarray:
        return self.to_radii_array(n)

    def validate(self) -> dict:
        x = np.linspace(0.0, self._length, 1000)
        r = self._spline(x)
        results = {}
        results['min_radius'] = float(np.min(r))
        results['has_negative_radius'] = bool(np.any(r < 0.0))
        d2 = self._spline.derivative(2)(x)
        results['max_second_derivative'] = float(np.max(np.abs(d2)))
        mean_r = float(np.mean(r))
        results['cylinder_deviation'] = float(np.sqrt(np.mean((r - mean_r) ** 2)))
        return results


def analytical_bore(
    shape: str,
    length: float,
    r_bell: float,
    r_mouth: float,
    flare: float = 0.5,
    n_control: int = 8,
    n_samples: int = 64,
) -> SplineBore:
    positions = np.linspace(0.0, length, n_control)
    x = positions / length

    if shape == 'cylinder':
        radii = np.full(n_control, r_mouth)
    elif shape == 'cone':
        radii = r_mouth + (r_bell - r_mouth) * x
    elif shape == 'parabolic':
        radii = r_mouth + (r_bell - r_mouth) * x ** 2
    elif shape == 'bessel':
        radii = r_mouth + (r_bell - r_mouth) * x ** flare
    elif shape == 'exponential':
        if r_mouth <= 0.0 or r_bell <= 0.0:
            raise ValueError("Radii must be positive for exponential bore")
        radii = r_mouth * np.exp(x * np.log(r_bell / r_mouth))
    elif shape == 'sinusoidal':
        amplitude = 0.15 * (r_bell - r_mouth)
        n_cycles = 2.0
        taper = r_mouth + (r_bell - r_mouth) * x
        radii = taper + amplitude * np.sin(2.0 * np.pi * n_cycles * x)
    elif shape == 'stepped':
        radii = np.where(x < 1/3, r_mouth,
                        np.where(x < 2/3, 0.5 * (r_mouth + r_bell), r_bell))
    elif shape == 'inverse_taper':
        bell_narrow = min(r_mouth * 0.6, r_bell * 0.5)
        radii = r_mouth + (bell_narrow - r_mouth) * x
        # Clamp to prevent negative radii
        radii = np.maximum(radii, 1.0)
    elif shape == 'trumpet':
        radii = r_mouth + (r_bell - r_mouth) * x ** 3
    else:
        raise ValueError(f"Unknown bore shape: {shape}")

    return SplineBore(positions.tolist(), radii.tolist(), n_samples=n_samples)


def spline_bore_from_optimization(
    bore_length: float,
    n_control: int,
    r_min: float = 3.0,
    r_max: float = 12.0,
) -> SplineBore:
    positions = np.linspace(0.0, bore_length, n_control).tolist()
    radii = [0.5 * (r_min + r_max)] * n_control
    return SplineBore(positions, radii)


def radii_from_spline(
    positions: list[float],
    radii: list[float],
    bore_length: float,
    n_samples: int = 64,
) -> tuple[np.ndarray, np.ndarray]:
    bore = SplineBore(positions, radii)
    x = np.linspace(0.0, bore_length, n_samples)
    return x, bore.radius_at(x)
