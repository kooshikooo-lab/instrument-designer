"""AcousticNetwork — solver-agnostic discretised instrument model.

Sits between geometry (:class:`~backend.geometry.InstrumentGeometry`)
and acoustic solvers (TMM, OpenWind, FEM).  Each solver provides its own
``from_network()`` converter function.

Usage::

    from backend.core.network import AcousticNetwork
    from backend.tmm_acoustics import tmm_instrument_from_network

    network = geometry.to_network()
    tmm_inst = tmm_instrument_from_network(network)
"""
from __future__ import annotations

import dataclasses


@dataclasses.dataclass(frozen=True)
class AcousticNetwork:
    """Solver-agnostic discretised acoustic network.

    A wind instrument represented as a sequence of bore profile points
    with tone holes, independent of any particular solver implementation.

    Parameters
    ----------
    bore_points : list of (float, float, float)
        ``(z_mm, inner_radius_mm, outer_radius_mm)`` for each bore profile
        point, ordered from bell (z=0) to mouthpiece.
    holes : list of (float, float, float)
        ``(z_mm, radius_mm, chimney_height_mm)`` for each tone hole.
    closed_top : bool
        True for closed-open instruments (clarinet family).
    total_length : float
        Total bore length from bell to mouthpiece tip (mm).
    """
    bore_points: list[tuple[float, float, float]]
    holes: list[tuple[float, float, float]]
    closed_top: bool
    total_length: float

    @property
    def n_segments(self) -> int:
        """Number of bore profile points."""
        return len(self.bore_points)

    @property
    def n_holes(self) -> int:
        """Number of tone holes."""
        return len(self.holes)
