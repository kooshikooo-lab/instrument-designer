from __future__ import annotations

import dataclasses
from typing import Sequence

import numpy as np

from backend.core.network import AcousticNetwork


@dataclasses.dataclass(frozen=True)
class BoreProfile:
    """Bore radius as a function of axial position.

    Parameters
    ----------
    positions : np.ndarray
        Axial positions measured from bell (mm).
    radii : np.ndarray
        Bore radius at each position (mm).
    """
    positions: np.ndarray
    radii: np.ndarray

    def __post_init__(self) -> None:
        assert self.positions.ndim == 1 and self.radii.ndim == 1
        assert len(self.positions) == len(self.radii)

    def interpolate(self, z: float) -> float:
        """Return bore radius at an arbitrary axial position *z* (mm)."""
        return float(np.interp(z, self.positions, self.radii))


@dataclasses.dataclass(frozen=True)
class HoleLayout:
    """Tone hole geometry.

    Parameters
    ----------
    positions : np.ndarray
        Axial positions measured from bell (mm).
    diameters : np.ndarray
        Hole diameters (mm).
    chimney_heights : np.ndarray
        Chimney heights (mm).  Defaults to 8 mm per hole if omitted.
    """
    positions: np.ndarray
    diameters: np.ndarray
    chimney_heights: np.ndarray | None = None

    def __post_init__(self) -> None:
        assert self.positions.ndim == 1 and self.diameters.ndim == 1
        assert len(self.positions) == len(self.diameters)
        if self.chimney_heights is None:
            object.__setattr__(self, "chimney_heights",
                               np.full_like(self.diameters, 8.0))

    @property
    def n_holes(self) -> int:
        return len(self.positions)


@dataclasses.dataclass(frozen=True)
class InstrumentGeometry:
    """Complete instrument geometry — pure shape, no acoustics.

    Parameters
    ----------
    total_length : float
        Total bore length from bell to mouthpiece (mm).
    bore : BoreProfile
        Bore radius profile.
    holes : HoleLayout
        Tone hole layout.
    closed_top : bool
        True for closed-open instruments (clarinet, chalumeau).
    mouthpiece_diameter : float
        Mouthpiece / reed diameter (mm).  Defaults to bore radius at tip.
    """
    total_length: float
    bore: BoreProfile
    holes: HoleLayout
    closed_top: bool
    mouthpiece_diameter: float | None = None

    def __post_init__(self) -> None:
        if self.mouthpiece_diameter is None:
            r = self.bore.interpolate(self.total_length)
            object.__setattr__(self, "mouthpiece_diameter", 2.0 * r)

    def to_network(
        self,
        outer_diameter_mm: float = 22.0,
    ) -> AcousticNetwork:
        """Convert geometry to a solver-agnostic AcousticNetwork.

        Parameters
        ----------
        outer_diameter_mm : float, optional
            Outer diameter of the instrument body (mm).  Default 22.0.

        Returns
        -------
        AcousticNetwork
            Solver-agnostic representation.
        """
        bore_points = [
            (float(z), float(r), outer_diameter_mm / 2.0)
            for z, r in zip(self.bore.positions, self.bore.radii)
        ]
        holes = [
            (float(p), float(d) / 2.0, float(h))
            for p, d, h in zip(self.holes.positions,
                               self.holes.diameters,
                               self.holes.chimney_heights)
        ]
        return AcousticNetwork(
            bore_points=bore_points,
            holes=holes,
            closed_top=self.closed_top,
            total_length=self.total_length,
        )

    def to_tmm(self) -> tuple[np.ndarray, np.ndarray, list[dict]]:
        """Convert geometry to TMM arrays.

        Returns
        -------
        radii : np.ndarray
            Bore radii at each segment (mm).
        lengths : np.ndarray
            Segment lengths (mm).
        hole_specs : list[dict]
            Each dict has keys ``pos``, ``d``, ``l`` for position, diameter,
            chimney height (all mm).
        """
        radii = self.bore.radii
        z = self.bore.positions
        lengths = np.diff(z, prepend=0.0)
        hole_specs = [
            {"pos": float(p), "d": float(d), "l": float(h)}
            for p, d, h in zip(self.holes.positions,
                               self.holes.diameters,
                               self.holes.chimney_heights)
        ]
        return radii, lengths, hole_specs
