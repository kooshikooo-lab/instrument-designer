"""Acoustic network data model.

An instrument is represented as a graph of acoustic elements:
- Nodes: junctions, bends, or connection points
- Segments: cylindrical or conical bore sections connecting nodes
- Ports: toneholes, register vents, or other side branches
- Boundaries: reed, bell, or other termination conditions
- Excitation: the source model (reed, lip, air jet)

The solver traverses this graph and computes acoustic response.
It does NOT know whether it's solving a clarinet or a trumpet.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple
import numpy as np
from backend.tmm_acoustics import SPEED_OF_SOUND


class NodeType(Enum):
    """Types of acoustic nodes."""
    JUNCTION = "junction"        # Simple connection between segments
    BORE_STEP = "bore_step"     # Diameter change
    TONEHOLE = "tonehole"       # Side branch (open or closed)
    REGISTER_VENT = "register_vent"  # Register hole


class BoundaryType(Enum):
    """Types of boundary conditions."""
    REED = "reed"               # Closed end with reed excitation
    BELL = "bell"               # Open end with radiation
    CLOSED = "closed"           # Rigid termination
    OPEN = "open"               # Open end (no radiation model)


class ExcitationType(Enum):
    """Types of excitation."""
    REED = "reed"               # Single reed (clarinet, saxophone)
    DOUBLE_REED = "double_reed" # Double reed (oboe, bassoon)
    LIP = "lip"                 # Lip reed (brass)
    AIR_JET = "air_jet"         # Air jet (flute, recorder)
    NONE = "none"               # Passive (for impedance calculation)


@dataclass
class Segment:
    """A bore section connecting two nodes.

    Attributes:
        length: segment length in mm
        radius_in: radius at input end (bell / open end, position 0)
        radius_out: radius at output end (reed / closed end, position L)
        n_points: number of discretization points for FEM
    """
    length: float
    radius_in: float
    radius_out: float
    n_points: int = 10

    @property
    def is_conical(self) -> bool:
        return abs(self.radius_in - self.radius_out) > 1e-6

    @property
    def is_cylindrical(self) -> bool:
        return not self.is_conical


@dataclass
class Port:
    """A side branch (tonehole, register vent, etc).

    Attributes:
        position: position along the bore (in internal coordinates: 0=bell, L=reed)
        radius: hole radius in mm
        length: chimney height in mm
        is_open: whether the hole is currently open
        node_type: type of node (tonehole, register vent, etc.)
    """
    position: float
    radius: float
    length: float
    is_open: bool = True
    node_type: NodeType = NodeType.TONEHOLE

    @property
    def is_tonehole(self) -> bool:
        """Whether this port is a tonehole (not a register vent)."""
        return self.node_type == NodeType.TONEHOLE

    @property
    def is_register_vent(self) -> bool:
        """Whether this port is a register (octave) vent."""
        return self.node_type == NodeType.REGISTER_VENT


@dataclass
class Boundary:
    """A boundary condition at one end of the instrument.

    Attributes:
        type: boundary type (reed, bell, closed, open)
        excitation: type of excitation
        position: position in internal coordinates
    """
    type: BoundaryType
    excitation: ExcitationType = ExcitationType.NONE
    position: float = 0.0


@dataclass
class Fingering:
    """A fingering state for the instrument.

    Attributes:
        name: note name (e.g., "C4", "D#3")
        port_states: dict mapping port index to open/closed state
    """
    name: str
    port_states: dict  # port_index -> bool (True = open)


@dataclass
class AcousticNetwork:
    """The complete acoustic network of an instrument.

    This is an abstract representation that the solver processes.
    The solver does NOT know what instrument this represents.

    Attributes:
        segments: bore sections, ordered from bell (position 0) to reed (position L)
        ports: side branches (toneholes, register vents)
        boundary_reed: boundary condition at reed end
        boundary_bell: boundary condition at bell end
        fingerings: available fingering states
        speed_of_sound: speed of sound in mm/s
    """
    segments: List[Segment] = field(default_factory=list)
    ports: List[Port] = field(default_factory=list)
    boundary_reed: Boundary = field(default_factory=lambda: Boundary(
        type=BoundaryType.REED, excitation=ExcitationType.REED, position=0.0
    ))
    boundary_bell: Boundary = field(default_factory=lambda: Boundary(
        type=BoundaryType.BELL, excitation=ExcitationType.NONE, position=0.0
    ))
    fingerings: List[Fingering] = field(default_factory=list)
    speed_of_sound: float = SPEED_OF_SOUND  # mm/s (chalumier value, ~346.1 m/s at 20°C)

    @property
    def total_length(self) -> float:
        """Total bore length in mm."""
        return sum(seg.length for seg in self.segments)

    @property
    def n_ports(self) -> int:
        return len(self.ports)

    @property
    def n_segments(self) -> int:
        return len(self.segments)

    def get_port_positions(self) -> np.ndarray:
        """Get all port positions as array."""
        return np.array([p.position for p in self.ports])

    def get_port_radii(self) -> np.ndarray:
        """Get all port radii as array."""
        return np.array([p.radius for p in self.ports])

    def get_port_lengths(self) -> np.ndarray:
        """Get all port chimney heights as array."""
        return np.array([p.length for p in self.ports])

    def get_port_states(self, fingering: Fingering) -> List[bool]:
        """Get open/closed state for each port given a fingering."""
        return [fingering.port_states.get(i, False) for i in range(len(self.ports))]

    def to_bore_profile(self) -> Tuple[np.ndarray, np.ndarray]:
        """Convert segments to position/radius arrays for TMM.

        Returns:
            positions: array of bore positions (internal coordinates)
            radii: array of bore radii at those positions
        """
        positions = []
        radii = []
        pos = 0.0
        for seg in self.segments:
            positions.append(pos)
            radii.append(seg.radius_in)
            pos += seg.length
            positions.append(pos)
            radii.append(seg.radius_out)
        return np.array(positions), np.array(radii)

    def to_hole_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Convert ports to hole position/radius/length arrays for TMM.

        Returns:
            positions: array of hole positions
            radii: array of hole radii
            lengths: array of chimney heights
        """
        return (
            self.get_port_positions(),
            self.get_port_radii(),
            self.get_port_lengths(),
        )
