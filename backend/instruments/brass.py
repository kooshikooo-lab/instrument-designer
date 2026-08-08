"""Brass instrument builder.

Builds an AcousticNetwork for brass instruments (trumpet, trombone, etc).
"""
from typing import List, Optional
import numpy as np

from ..core.network import (
    AcousticNetwork, Segment, Port, Boundary, Fingering,
    NodeType, BoundaryType, ExcitationType,
)


class BrassBuilder:
    """Build an AcousticNetwork for a brass instrument.

    Brass instruments have:
    - Mouthpiece (closed end with lip excitation)
    - Cylindrical/conical bore
    - Valves (which add/remove tube length)
    - Bell (open end with radiation)

    Usage:
        builder = BrassBuilder()
        builder.set_bore(length=1400, radius_in=5.5, radius_out=10.0)
        builder.add_valves(positions=[...], lengths=[...])
        builder.set_bell(radius=60.0, flare=220.0)
        network = builder.build()
    """

    def __init__(self):
        self._segments = []
        self._valves = []
        self._bell_radius = None
        self._bell_flare = None
        self._speed_of_sound = 346100.0

    def set_bore(self, length: float, radius_in: float, radius_out: float):
        """Set bore geometry.

        Args:
            length: total bore length in mm
            radius_in: radius at mouthpiece end in mm
            radius_out: radius at bell end in mm
        """
        self._segments = [
            Segment(length=length, radius_in=radius_in, radius_out=radius_out)
        ]
        self._bell_radius = radius_out
        return self

    def add_valves(self, positions: List[float], lengths: List[float], radii: List[float]):
        """Add valve ports (for adding tube length when engaged).

        Args:
            positions: valve positions along bore
            lengths: additional tube length per valve
            radii: bore radius at each valve
        """
        for pos, ln, rad in zip(positions, lengths, radii):
            self._valves.append(Port(
                position=pos,
                radius=rad,
                length=ln,
                is_open=False,
                node_type=NodeType.TONEHOLE,  # valves are modeled similarly
            ))
        return self

    def set_bell(self, radius: float, flare: float = 0.0):
        """Set bell geometry.

        Args:
            radius: bell exit radius in mm
            flare: flare length in mm (0 = no flare model)
        """
        self._bell_radius = radius
        self._bell_flare = flare
        return self

    def set_speed_of_sound(self, c: float):
        self._speed_of_sound = c
        return self

    def build(self) -> AcousticNetwork:
        """Build the AcousticNetwork."""
        boundary_mouthpiece = Boundary(
            type=BoundaryType.REED,  # closed end
            excitation=ExcitationType.LIP,
            position=self._segments[0].length if self._segments else 0.0,
        )
        boundary_bell = Boundary(
            type=BoundaryType.BELL,
            excitation=ExcitationType.NONE,
            position=0.0,
        )

        return AcousticNetwork(
            segments=self._segments,
            ports=self._valves,
            boundary_reed=boundary_mouthpiece,
            boundary_bell=boundary_bell,
            speed_of_sound=self._speed_of_sound,
        )
