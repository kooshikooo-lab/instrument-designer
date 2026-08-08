"""Generic clarinet builder.

Builds an AcousticNetwork for any clarinet-family instrument.
"""
from typing import List, Optional
import numpy as np

from ..core.network import (
    AcousticNetwork, Segment, Port, Boundary, Fingering,
    NodeType, BoundaryType, ExcitationType,
)


class ClarinetBuilder:
    """Build an AcousticNetwork for a clarinet-family instrument.

    Usage:
        builder = ClarinetBuilder()
        builder.set_bore(length=1200, radius=12.5)
        builder.add_toneholes(positions=[...], radii=[...], lengths=[...])
        builder.set_register_vent(position=80, radius=1.25)
        network = builder.build()
    """

    def __init__(self):
        self._segments = []
        self._ports = []
        self._register_vent = None
        self._bell_radius = None
        self._speed_of_sound = 346100.0  # mm/s

    def set_bore(self, length: float, radius: float, taper: float = 0.0):
        """Set bore geometry.

        Args:
            length: total bore length in mm
            radius: bore radius in mm
            taper: radius increase from bell to reed (0 = cylindrical)
        """
        self._segments = [
            Segment(
                length=length,
                radius_in=radius,
                radius_out=radius + taper,
            )
        ]
        self._bell_radius = radius + taper
        return self

    def set_bore_profile(self, positions: np.ndarray, radii: np.ndarray):
        """Set bore geometry from a profile (for non-uniform bores).

        Args:
            positions: bore positions in internal coordinates (0=bell, L=reed)
            radii: bore radii at those positions
        """
        self._segments = []
        for i in range(len(positions) - 1):
            self._segments.append(Segment(
                length=positions[i+1] - positions[i],
                radius_in=radii[i],
                radius_out=radii[i+1],
            ))
        self._bell_radius = radii[-1]
        return self

    def add_toneholes(
        self,
        positions: List[float],
        radii: List[float],
        lengths: List[float],
    ):
        """Add toneholes.

        Args:
            positions: hole positions in internal coordinates (0=bell, L=reed)
            radii: hole radii in mm
            lengths: chimney heights in mm
        """
        for pos, rad, ln in zip(positions, radii, lengths):
            self._ports.append(Port(
                position=pos,
                radius=rad,
                length=ln,
                is_open=True,
                node_type=NodeType.TONEHOLE,
            ))
        return self

    def set_register_vent(self, position: float, radius: float, length: float = 3.0):
        """Set register vent ( octave hole).

        Args:
            position: position in internal coordinates (0=bell)
            radius: hole radius in mm
            length: chimney height in mm
        """
        self._register_vent = Port(
            position=position,
            radius=radius,
            length=length,
            is_open=False,
            node_type=NodeType.REGISTER_VENT,
        )
        return self

    def set_speed_of_sound(self, c: float):
        """Set speed of sound in mm/s."""
        self._speed_of_sound = c
        return self

    def build(self) -> AcousticNetwork:
        """Build the AcousticNetwork."""
        # Add register vent to ports if set
        ports = list(self._ports)
        if self._register_vent is not None:
            ports.append(self._register_vent)

        # Sort ports by position (bell to reed)
        ports.sort(key=lambda p: p.position)

        # Create boundaries
        boundary_reed = Boundary(
            type=BoundaryType.REED,
            excitation=ExcitationType.REED,
            position=self._segments[0].length if self._segments else 0.0,
        )
        boundary_bell = Boundary(
            type=BoundaryType.BELL,
            excitation=ExcitationType.NONE,
            position=0.0,
        )

        return AcousticNetwork(
            segments=self._segments,
            ports=ports,
            boundary_reed=boundary_reed,
            boundary_bell=boundary_bell,
            speed_of_sound=self._speed_of_sound,
        )
