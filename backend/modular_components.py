"""
Modular instrument components: bells, necks, extensions, joints.

Each component is a standalone design object that can be combined
with others to build complete instruments. Designed for:
- 3D printing (each piece fits on print bed)
- PVC pipe compatibility (standard dimensions)
- Modular assembly (tenon/cork connections)
- Cross-instrument compatibility (same bell fits multiple bodies)

Components:
- BoreSection: cylindrical/conical bore segment
- Bell: flared end piece
- Neck/Crook: curved mouthpiece connector
- Extension: additional bore length (bass extension, etc.)
- Joint: keyed section (upper/lower joint)
- Mouthpiece: reed/windway interface
- TenonConnection: standardized joint connector

Usage:
    from backend.modular_components import (
        BoreSection, Bell, Neck, Extension, Joint,
        TenonConnection, PVC_PIPES, InstrumentAssembly
    )
"""

import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum


# ============================================================================
# PVC Pipe Standards (Schedule 40)
# ============================================================================

PVC_PIPES = {
    "1/2": {"nominal": "1/2\"", "od_mm": 21.3, "id_mm": 15.8, "wall_mm": 2.77},
    "3/4": {"nominal": "3/4\"", "od_mm": 26.7, "id_mm": 20.9, "wall_mm": 2.87},
    "1":   {"nominal": "1\"",    "od_mm": 33.4, "id_mm": 26.6, "wall_mm": 3.38},
    "1_1/4": {"nominal": "1-1/4\"", "od_mm": 42.2, "id_mm": 35.1, "wall_mm": 3.56},
    "1_1/2": {"nominal": "1-1/2\"", "od_mm": 48.3, "id_mm": 40.9, "wall_mm": 3.68},
    "2":   {"nominal": "2\"",    "od_mm": 60.3, "id_mm": 52.5, "wall_mm": 3.91},
}


# ============================================================================
# Connection types
# ============================================================================

class ConnectionType(Enum):
    TENON_CORK = "tenon_cork"        # Traditional: cork-wrapped male into female socket
    METAL_FRICTION = "metal_friction" # Sax-style: metal-to-metal precision fit
    THREADED = "threaded"             # Screw connection with wax seal
    SLIP_CLAMP = "slip_clamp"         # PVC-style: sleeve with thumb screw
    PRESS_FIT = "press_fit"           # 3D print: snap/friction fit
    ADHESIVE = "adhesive"             # Glued permanent joint


# ============================================================================
# Tenon Connection
# ============================================================================

@dataclass
class TenonConnection:
    """
    Standardized connector between instrument joints.

    For 3D printing: the tenon is printed as part of one joint,
    the socket as part of the next. Cork/felt provides seal.
    """
    connection_type: ConnectionType
    tenon_od_mm: float           # Outer diameter of male end
    socket_id_mm: float          # Inner diameter of female end
    tenon_length_mm: float       # How far the tenon inserts
    cork_thickness_mm: float = 1.5  # Seal thickness
    tolerance_mm: float = 0.2   # Print tolerance gap

    @property
    def fit_clearance(self) -> float:
        """Gap between tenon OD and socket ID (before cork)."""
        return self.socket_id_mm - self.tenon_od_mm

    @property
    def effective_seal_diameter(self) -> float:
        """Diameter when cork is compressed."""
        return self.tenon_od_mm + 2 * self.cork_thickness_mm

    def is_compatible(self, other: "TenonConnection") -> bool:
        """Check if two connections can mate."""
        if self.connection_type != other.connection_type:
            return False
        return abs(self.effective_seal_diameter - other.socket_id_mm) < 1.0

    def stl_clearance(self) -> dict:
        """Dimensions for STL generation with print tolerance."""
        return {
            "tenon_od": self.tenon_od_mm - self.tolerance_mm,
            "socket_id": self.socket_id_mm + self.tolerance_mm,
            "length": self.tenon_length_mm,
        }


# Standard clarinet tenon dimensions
CLARINET_TENONS = {
    "upper_top": TenonConnection(
        connection_type=ConnectionType.TENON_CORK,
        tenon_od_mm=23.6, socket_id_mm=24.6, tenon_length_mm=20.0,
    ),
    "upper_bottom": TenonConnection(
        connection_type=ConnectionType.TENON_CORK,
        tenon_od_mm=26.8, socket_id_mm=27.8, tenon_length_mm=20.0,
    ),
    "lower_bottom": TenonConnection(
        connection_type=ConnectionType.TENON_CORK,
        tenon_od_mm=25.9, socket_id_mm=26.9, tenon_length_mm=20.0,
    ),
    "bass_clarinet_neck": TenonConnection(
        connection_type=ConnectionType.TENON_CORK,
        tenon_od_mm=25.7, socket_id_mm=26.7, tenon_length_mm=21.0,
    ),
    "bass_clarinet_bell": TenonConnection(
        connection_type=ConnectionType.TENON_CORK,
        tenon_od_mm=26.0, socket_id_mm=27.0, tenon_length_mm=22.0,
    ),
}

SAX_TENONS = {
    "body_bell": TenonConnection(
        connection_type=ConnectionType.METAL_FRICTION,
        tenon_od_mm=50.0, socket_id_mm=50.5, tenon_length_mm=15.0,
        cork_thickness_mm=0.0,
    ),
    "neck_body": TenonConnection(
        connection_type=ConnectionType.METAL_FRICTION,
        tenon_od_mm=24.0, socket_id_mm=24.5, tenon_length_mm=12.0,
        cork_thickness_mm=0.0,
    ),
}

PVC_CONNECTIONS = {
    "slip_3_4": TenonConnection(
        connection_type=ConnectionType.SLIP_CLAMP,
        tenon_od_mm=20.9, socket_id_mm=20.9, tenon_length_mm=30.0,
        cork_thickness_mm=0.0, tolerance_mm=0.0,
    ),
    "slip_1": TenonConnection(
        connection_type=ConnectionType.SLIP_CLAMP,
        tenon_od_mm=26.6, socket_id_mm=26.6, tenon_length_mm=30.0,
        cork_thickness_mm=0.0, tolerance_mm=0.0,
    ),
}


# ============================================================================
# Bore Section
# ============================================================================

@dataclass
class BoreSection:
    """
    A cylindrical or conical bore segment.

    Can be a standalone piece (straight tube) or part of a larger assembly.
    """
    name: str
    length_mm: float
    bore_start_radius_mm: float
    bore_end_radius_mm: float          # Same as start for cylindrical
    outer_radius_mm: float = 15.0     # Wall thickness = outer - bore
    wall_thickness_mm: float = 3.0    # For 3D printing
    n_control_points: int = 20        # For TMM optimization

    @property
    def is_cylindrical(self) -> bool:
        return abs(self.bore_start_radius_mm - self.bore_end_radius_mm) < 0.01

    @property
    def is_conical(self) -> bool:
        return not self.is_cylindrical

    @property
    def taper_ratio(self) -> float:
        """Ratio of end to start bore radius."""
        if self.bore_start_radius_mm == 0:
            return 1.0
        return self.bore_end_radius_mm / self.bore_start_radius_mm

    def bore_at(self, position_mm: float) -> float:
        """Bore radius at a given position along the section."""
        if self.length_mm == 0:
            return self.bore_start_radius_mm
        t = max(0.0, min(1.0, position_mm / self.length_mm))
        return self.bore_start_radius_mm + t * (self.bore_end_radius_mm - self.bore_start_radius_mm)

    def to_stepped(self, step_mm: float = 2.0) -> List[Tuple[float, float]]:
        """Convert to stepped profile for TMM analysis."""
        n_steps = max(2, int(self.length_mm / step_mm) + 1)
        positions = [i * self.length_mm / (n_steps - 1) for i in range(n_steps)]
        radii = [self.bore_at(p) for p in positions]
        return list(zip(positions, radii))

    def optimal_print_orientation(self) -> str:
        """Suggest print orientation for 3D printing."""
        if self.is_cylindrical and self.length_mm < 200:
            return "vertical (standing up)"
        elif self.is_conical:
            return "horizontal (taper up) with supports"
        else:
            return "horizontal with supports"


# ============================================================================
# Bell
# ============================================================================

@dataclass
class Bell:
    """
    Flared end piece for the instrument.

    Bell flare affects the harmonic spectrum and projection.
    Standard flare profiles: exponential, parabolic, Bessel.
    """
    name: str
    bore_radius_start_mm: float    # Matches the joint it attaches to
    bore_radius_end_mm: float      # Bell opening
    length_mm: float
    flare_type: str = "exponential"  # exponential, parabolic, bessel, linear
    wall_thickness_mm: float = 2.0
    outer_radius_start_mm: float = 15.0
    outer_radius_end_mm: float = 40.0
    connection: Optional[TenonConnection] = None

    @property
    def flare_ratio(self) -> float:
        """Ratio of bell opening to bore."""
        if self.bore_radius_start_mm == 0:
            return 1.0
        return self.bore_radius_end_mm / self.bore_radius_start_mm

    def bore_at(self, position_mm: float) -> float:
        """Bore radius at a given position along the bell."""
        t = max(0.0, min(1.0, position_mm / self.length_mm))
        if self.flare_type == "exponential":
            return self.bore_radius_start_mm * math.exp(
                t * math.log(self.flare_ratio)
            )
        elif self.flare_type == "parabolic":
            return self.bore_radius_start_mm + (
                self.bore_radius_end_mm - self.bore_radius_start_mm
            ) * (t ** 2)
        elif self.flare_type == "linear":
            return self.bore_radius_start_mm + t * (
                self.bore_radius_end_mm - self.bore_radius_start_mm
            )
        else:  # Bessel
            return self.bore_radius_start_mm * (
                1 + t * (self.flare_ratio - 1)
            ) ** 2

    def to_stepped(self, step_mm: float = 2.0) -> List[Tuple[float, float]]:
        n_steps = max(3, int(self.length_mm / step_mm) + 1)
        positions = [i * self.length_mm / (n_steps - 1) for i in range(n_steps)]
        radii = [self.bore_at(p) for p in positions]
        return list(zip(positions, radii))


# ============================================================================
# Neck / Crook
# ============================================================================

@dataclass
class Neck:
    """
    Curved tube connecting mouthpiece to upper joint.

    For bass clarinet: the neck has a characteristic S-curve or U-bend.
    For soprano clarinet: straight or slightly curved crook.
    """
    name: str
    bore_radius_mm: float
    length_mm: float               # Total arc length
    straight_length_mm: float = 0  # Straight portion before curve
    bend_angle_deg: float = 0      # Total bend angle
    bend_radius_mm: float = 50     # Radius of curvature
    connection_top: Optional[TenonConnection] = None  # Mouthpiece end
    connection_bottom: Optional[TenonConnection] = None  # Joint end

    @property
    def effective_length(self) -> float:
        """Acoustic length accounting for bends."""
        # Bends add ~0.3 * bend_radius per radian of bend
        bend_length = (self.bend_angle_deg * math.pi / 180) * self.bend_radius_mm * 0.3
        return self.straight_length_mm + bend_length

    @property
    def is_curved(self) -> bool:
        return self.bend_angle_deg > 0

    def bore_at(self, position_mm: float) -> float:
        """Bore radius is constant through the neck."""
        return self.bore_radius_mm


# ============================================================================
# Extension
# ============================================================================

@dataclass
class Extension:
    """
    Additional bore length for extended range instruments.

    Examples:
    - Low C extension for Bb clarinet (adds a minor third below)
    - Bass extension for chalumeau
    - Sub-contrabass extension for bass clarinet
    """
    name: str
    bore_radius_mm: float
    length_mm: float
    extension_type: str = "straight"  # straight, U-bend, coiled
    n_holes: int = 0               # Additional tone holes in extension
    hole_positions: List[float] = field(default_factory=list)
    hole_diameters: List[float] = field(default_factory=list)
    connection_top: Optional[TenonConnection] = None
    connection_bottom: Optional[TenonConnection] = None

    @property
    def frequency_drop(self) -> float:
        """Approximate frequency drop from adding this extension (Hz)."""
        # For closed-open pipe: f = c / (4 * L)
        c = 343000  # mm/s
        return c / (4 * self.length_mm)

    def recommended_for(self) -> str:
        if self.length_mm < 100:
            return "Quarter-tone extension"
        elif self.length_mm < 200:
            return "Low C extension (Bb clarinet)"
        elif self.length_mm < 400:
            return "Bass extension (chalumeau/bass clarinet lower joint)"
        else:
            return "Sub-contrabass extension"


# ============================================================================
# Joint (Keyed Section)
# ============================================================================

@dataclass
class KeyHole:
    """Single tone hole with its key mechanism."""
    position_mm: float             # Distance from top of joint
    hole_diameter_mm: float
    hole_length_mm: float          # Wall thickness at hole
    pad_diameter_mm: float         # Key pad覆盖 area
    key_type: str = "ring"         # ring, plateau, spatula
    key_lever_length_mm: float = 0 # For spatula/lever keys
    needs_spring: bool = True
    key_height_mm: float = 10.0    # Height above body surface

    @property
    def bore_position(self) -> float:
        """Position along the bore (same as position_mm for now)."""
        return self.position_mm


@dataclass
class Joint:
    """
    Keyed body section of the instrument.

    Contains tone holes and key mechanisms.
    For 3D printing: can be split into sub-sections for print bed.
    """
    name: str
    bore_radius_mm: float
    length_mm: float
    outer_radius_mm: float = 15.0
    wall_thickness_mm: float = 3.0
    keys: List[KeyHole] = field(default_factory=list)
    connection_top: Optional[TenonConnection] = None
    connection_bottom: Optional[TenonConnection] = None
    max_print_length_mm: float = 200.0  # Max length for single print

    @property
    def n_keys(self) -> int:
        return len(self.keys)

    @property
    def needs_splitting(self) -> bool:
        """Whether this joint needs to be split for 3D printing."""
        return self.length_mm > self.max_print_length_mm

    def split_for_print(self) -> List["Joint"]:
        """Split joint into printable sub-sections."""
        if not self.needs_splitting:
            return [self]

        n_pieces = math.ceil(self.length_mm / self.max_print_length_mm)
        piece_length = self.length_mm / n_pieces
        pieces = []

        for i in range(n_pieces):
            start = i * piece_length
            end = (i + 1) * piece_length
            keys_in_piece = [
                k for k in self.keys
                if start <= k.position_mm < end
            ]
            # Adjust key positions relative to piece start
            adjusted_keys = []
            for k in keys_in_piece:
                adjusted_keys.append(KeyHole(
                    position_mm=k.position_mm - start,
                    hole_diameter_mm=k.hole_diameter_mm,
                    hole_length_mm=k.hole_length_mm,
                    pad_diameter_mm=k.pad_diameter_mm,
                    key_type=k.key_type,
                    key_lever_length_mm=k.key_lever_length_mm,
                    needs_spring=k.needs_spring,
                    key_height_mm=k.key_height_mm,
                ))

            pieces.append(Joint(
                name=f"{self.name} part {i+1}",
                bore_radius_mm=self.bore_radius_mm,
                length_mm=piece_length,
                outer_radius_mm=self.outer_radius_mm,
                wall_thickness_mm=self.wall_thickness_mm,
                keys=adjusted_keys,
                connection_top=CLARINET_TENONS["upper_top"] if i == 0 else None,
                connection_bottom=CLARINET_TENONS["upper_bottom"] if i == n_pieces - 1 else None,
            ))

        return pieces


# ============================================================================
# Mouthpiece
# ============================================================================

@dataclass
class Mouthpiece:
    """
    Reed or fipple mouthpiece interface.
    """
    name: str
    mouthpiece_type: str          # reed, fipple, embouchure
    bore_radius_mm: float         # Bore match to instrument
    tip_opening_mm: float = 1.0   # For reed mouthpieces
    facing_length_mm: float = 20  # Reed facing curve length
    baffle_type: str = "standard" # standard, flat, high, undercut
    chamber_type: str = "cylindrical"  # cylindrical, conical, parabolic
    connection: Optional[TenonConnection] = None

    @property
    def effective_bore(self) -> float:
        """Bore radius accounting for tip opening."""
        return self.bore_radius_mm + self.tip_opening_mm * 0.1


# ============================================================================
# PVC Instrument Builder
# ============================================================================

@dataclass
class PVCInstrument:
    """
    Build an instrument from standard PVC pipe sections.

    PVC is cheap, available, and easy to work with.
    Good for prototyping before 3D printing.
    """
    name: str
    key: str
    bore_sections: List[dict] = field(default_factory=list)  # {"pipe_size": "3/4", "length_mm": 200}
    bell_pvc_size: str = "1_1/2"
    bell_length_mm: float = 200
    mouthpiece_pvc_size: str = "3/4"

    def total_bore_length(self) -> float:
        return sum(s.get("length_mm", 0) for s in self.bore_sections)

    def bore_profile(self) -> List[dict]:
        """Generate bore profile from PVC sections."""
        profile = []
        pos = 0
        for section in self.bore_sections:
            pipe = PVC_PIPES.get(section["pipe_size"], PVC_PIPES["3/4"])
            length = section.get("length_mm", 200)
            profile.append({
                "start_pos_mm": pos,
                "end_pos_mm": pos + length,
                "bore_diameter_mm": pipe["id_mm"],
                "pipe_size": section["pipe_size"],
            })
            pos += length
        return profile

    def to_tmm_config(self) -> dict:
        """Convert to TMM optimizer configuration."""
        profile = self.bore_profile()
        positions = []
        diameters = []
        for seg in profile:
            positions.append(seg["start_pos_mm"])
            diameters.append(seg["bore_diameter_mm"])
        positions.append(profile[-1]["end_pos_mm"])
        diameters.append(profile[-1]["bore_diameter_mm"])

        bell = PVC_PIPES.get(self.bell_pvc_size, PVC_PIPES["1_1/2"])
        return {
            "inner_positions": positions,
            "inner_diameters": diameters,
            "total_length_mm": profile[-1]["end_pos_mm"],
            "bell_diameter_mm": bell["id_mm"],
        }


# ============================================================================
# Bass Clarinet Assembly (Reference)
# ============================================================================

BASS_CLARINET_REF = {
    "name": "Bass Clarinet in Bb",
    "key": "Bb",
    "range": "Bb1 to G5",
    "bore_diameter_mm": 25.0,  # ~12.5mm radius
    "total_length_mm": 1800,   # Including U-bend
    "components": {
        "mouthpiece": {
            "type": "reed",
            "bore_mm": 12.5,
            "tip_opening_mm": 1.1,
        },
        "neck": {
            "type": "S-curve",
            "length_mm": 180,
            "bore_mm": 12.5,
            "bend_angle_deg": 180,
            "bend_radius_mm": 40,
        },
        "upper_joint": {
            "length_mm": 320,
            "bore_mm": 12.5,
            "n_keys": 10,
            "key_types": ["ring_x3", "plateau_x4", "spatula_x3"],
        },
        "lower_joint": {
            "length_mm": 350,
            "bore_mm": 12.5,
            "n_keys": 8,
            "key_types": ["ring_x3", "plateau_x2", "spatula_x3"],
        },
        "bell": {
            "type": "exponential_flare",
            "bore_start_mm": 12.5,
            "bore_end_mm": 55,
            "length_mm": 280,
            "keys": 4,  # Low D, Eb, C#, C
        },
    },
    "key_pad_sizes": {
        "upper_holes": (10.0, 13.0),   # mm range
        "lower_holes": (13.0, 17.0),   # mm range
        "bell_keys": (19.0, 26.0),     # mm range
        "register_key": (8.0, 10.0),   # mm
    },
    "tone_hole_sizes": {
        "upper_small": (8.0, 10.0),
        "upper_medium": (11.0, 13.0),
        "lower_medium": (13.0, 15.0),
        "lower_large": (14.0, 15.0),
        "bell": (19.0, 21.0),
    },
}


# ============================================================================
# Instrument Assembly
# ============================================================================

class InstrumentAssembly:
    """
    Combine modular components into a complete instrument.

    Validates connections, computes total bore profile,
    and generates TMM configuration.
    """

    def __init__(self, name: str, pipe_type: str = "closed-open"):
        self.name = name
        self.pipe_type = pipe_type
        self.components: List[Tuple[str, float, any]] = []  # (name, offset_mm, component)

    def add(self, name: str, component):
        """Add a component. Offset is auto-calculated from previous components."""
        offset = sum(getattr(c, 'length_mm', 0) for _, _, c in self.components)
        self.components.append((name, offset, component))
        return self

    def get_bore_profile(self) -> List[Tuple[float, float]]:
        """Generate the complete bore profile from all components."""
        profile = []

        for name, offset, comp in self.components:
            if isinstance(comp, BoreSection):
                for p, r in comp.to_stepped():
                    profile.append((offset + p, r))
            elif isinstance(comp, Bell):
                for p, r in comp.to_stepped():
                    profile.append((offset + p, r))
            elif isinstance(comp, Joint):
                profile.append((offset, comp.bore_radius_mm))
                profile.append((offset + comp.length_mm, comp.bore_radius_mm))
            elif isinstance(comp, Neck):
                profile.append((offset, comp.bore_radius_mm))
                profile.append((offset + comp.length_mm, comp.bore_radius_mm))
            elif isinstance(comp, Extension):
                profile.append((offset, comp.bore_radius_mm))
                profile.append((offset + comp.length_mm, comp.bore_radius_mm))

        return profile

    def to_tmm_config(self) -> dict:
        """Generate TMM optimizer configuration."""
        profile = self.get_bore_profile()
        if not profile:
            return {}

        positions = [p for p, r in profile]
        diameters = [r * 2 for p, r in profile]

        # Collect all keys/holes
        hole_positions = []
        hole_diameters = []
        hole_lengths = []
        wall_thickness = 3.0  # default

        for name, offset, comp in self.components:
            if isinstance(comp, Joint):
                for key in comp.keys:
                    hole_positions.append(offset + key.position_mm)
                    hole_diameters.append(key.hole_diameter_mm)
                    hole_lengths.append(key.hole_length_mm)
            elif isinstance(comp, Extension):
                for i, hp in enumerate(comp.hole_positions):
                    hole_positions.append(offset + hp)
                    hole_diameters.append(comp.hole_diameters[i])
                    hole_lengths.append(wall_thickness)

        return {
            "inner_positions": positions,
            "inner_diameters": diameters,
            "outer_diameters": [d + 6.0 for d in diameters],  # 3mm wall each side
            "hole_positions": hole_positions,
            "hole_diameters": hole_diameters,
            "hole_lengths": hole_lengths,
            "closed_top": self.pipe_type == "closed-open",
            "total_length_mm": positions[-1] if positions else 0,
        }

    def summary(self) -> str:
        """Print assembly summary."""
        lines = [f"Assembly: {self.name} ({self.pipe_type})"]
        for name, offset, comp in self.components:
            length = getattr(comp, 'length_mm', 0)
            bore = getattr(comp, 'bore_radius_mm', getattr(comp, 'bore_start_radius_mm', 0))
            lines.append(f"  [{name}] {type(comp).__name__}: "
                        f"{comp.name} | L={length:.0f}mm | r={bore:.1f}mm | offset={offset:.0f}mm")
        total = sum(getattr(c, 'length_mm', 0) for _, _, c in self.components)
        lines.append(f"  Total length: {total:.0f}mm")
        return "\n".join(lines)


# ============================================================================
# Pre-built instrument configurations
# ============================================================================

def build_chalumeau_C() -> InstrumentAssembly:
    """Build a diatonic chalumeau in C from modular components."""
    asm = InstrumentAssembly("Chalumeau in C", "closed-open")
    asm.add("body", BoreSection(
        name="Main body", length_mm=280,
        bore_start_radius_mm=7.25, bore_end_radius_mm=7.25,
        outer_radius_mm=11.0,
    ))
    asm.add("bell", Bell(
        name="Simple bell", bore_radius_start_mm=7.25, bore_radius_end_mm=15.0,
        length_mm=40, flare_type="exponential",
    ))
    return asm


def build_bass_chalumeau_Bb() -> InstrumentAssembly:
    """Build a bass chalumeau prototype for Bb major scale."""
    asm = InstrumentAssembly("Bass Chalumeau in Bb", "closed-open")
    asm.add("body", BoreSection(
        name="Main body", length_mm=560,
        bore_start_radius_mm=9.5, bore_end_radius_mm=9.5,
        outer_radius_mm=14.0,
    ))
    asm.add("bell", Bell(
        name="Flared bell", bore_radius_start_mm=9.5, bore_radius_end_mm=30.0,
        length_mm=60, flare_type="exponential",
    ))
    return asm


def build_bass_clarinet_Bb() -> InstrumentAssembly:
    """Build a bass clarinet from modular components."""
    asm = InstrumentAssembly("Bass Clarinet in Bb", "closed-open")

    # Neck
    asm.add("neck", Neck(
        name="S-curve neck", bore_radius_mm=12.5, length_mm=180,
        bend_angle_deg=180, bend_radius_mm=40,
        connection_top=None,
        connection_bottom=CLARINET_TENONS["bass_clarinet_neck"],
    ))

    # Upper joint
    upper_keys = [
        KeyHole(position_mm=30, hole_diameter_mm=9.0, hole_length_mm=3.5,
                pad_diameter_mm=11.0, key_type="ring"),
        KeyHole(position_mm=65, hole_diameter_mm=10.0, hole_length_mm=3.5,
                pad_diameter_mm=12.0, key_type="ring"),
        KeyHole(position_mm=100, hole_diameter_mm=11.0, hole_length_mm=3.5,
                pad_diameter_mm=13.0, key_type="ring"),
        KeyHole(position_mm=150, hole_diameter_mm=12.0, hole_length_mm=3.5,
                pad_diameter_mm=14.0, key_type="plateau"),
        KeyHole(position_mm=200, hole_diameter_mm=12.5, hole_length_mm=3.5,
                pad_diameter_mm=15.0, key_type="plateau"),
        KeyHole(position_mm=250, hole_diameter_mm=13.0, hole_length_mm=3.5,
                pad_diameter_mm=16.0, key_type="plateau"),
    ]
    asm.add("upper_joint", Joint(
        name="Upper Joint", bore_radius_mm=12.5, length_mm=320,
        outer_radius_mm=16.0, keys=upper_keys,
        connection_top=CLARINET_TENONS["bass_clarinet_neck"],
        connection_bottom=CLARINET_TENONS["upper_bottom"],
    ))

    # Lower joint
    lower_keys = [
        KeyHole(position_mm=30, hole_diameter_mm=13.5, hole_length_mm=3.5,
                pad_diameter_mm=16.0, key_type="ring"),
        KeyHole(position_mm=70, hole_diameter_mm=14.0, hole_length_mm=3.5,
                pad_diameter_mm=17.0, key_type="ring"),
        KeyHole(position_mm=110, hole_diameter_mm=14.5, hole_length_mm=3.5,
                pad_diameter_mm=18.0, key_type="ring"),
        KeyHole(position_mm=180, hole_diameter_mm=15.0, hole_length_mm=3.5,
                pad_diameter_mm=19.0, key_type="plateau"),
        KeyHole(position_mm=250, hole_diameter_mm=15.0, hole_length_mm=3.5,
                pad_diameter_mm=19.0, key_type="plateau"),
    ]
    asm.add("lower_joint", Joint(
        name="Lower Joint", bore_radius_mm=12.5, length_mm=350,
        outer_radius_mm=17.0, keys=lower_keys,
        connection_top=CLARINET_TENONS["upper_bottom"],
        connection_bottom=CLARINET_TENONS["lower_bottom"],
    ))

    # Bell
    asm.add("bell", Bell(
        name="Bass Clarinet Bell", bore_radius_start_mm=12.5,
        bore_radius_end_mm=55.0, length_mm=280,
        flare_type="exponential",
        connection=CLARINET_TENONS["bass_clarinet_bell"],
    ))

    return asm


def build_soprano_sax_Bb() -> InstrumentAssembly:
    """Build a soprano saxophone from modular components."""
    asm = InstrumentAssembly("Soprano Saxophone in Bb", "open-open")

    # Neck
    asm.add("neck", Neck(
        name="Straight neck", bore_radius_mm=6.0, length_mm=120,
        bend_angle_deg=0,
        connection_top=SAX_TENONS["neck_body"],
    ))

    # Body (single piece for soprano)
    body_keys = [
        KeyHole(position_mm=50, hole_diameter_mm=6.5, hole_length_mm=2.5,
                pad_diameter_mm=8.0, key_type="ring"),
        KeyHole(position_mm=110, hole_diameter_mm=7.0, hole_length_mm=2.5,
                pad_diameter_mm=9.0, key_type="ring"),
        KeyHole(position_mm=170, hole_diameter_mm=7.5, hole_length_mm=2.5,
                pad_diameter_mm=10.0, key_type="ring"),
        KeyHole(position_mm=230, hole_diameter_mm=8.0, hole_length_mm=2.5,
                pad_diameter_mm=10.5, key_type="ring"),
        KeyHole(position_mm=290, hole_diameter_mm=8.5, hole_length_mm=2.5,
                pad_diameter_mm=11.0, key_type="ring"),
        KeyHole(position_mm=350, hole_diameter_mm=9.0, hole_length_mm=2.5,
                pad_diameter_mm=12.0, key_type="ring"),
        KeyHole(position_mm=450, hole_diameter_mm=9.5, hole_length_mm=2.5,
                pad_diameter_mm=13.0, key_type="plateau"),
    ]
    asm.add("body", Joint(
        name="Body", bore_radius_mm=6.0, length_mm=520,
        outer_radius_mm=10.0, keys=body_keys,
        connection_top=SAX_TENONS["neck_body"],
    ))

    # Bell
    asm.add("bell", Bell(
        name="Saxophone Bell", bore_radius_start_mm=6.0,
        bore_radius_end_mm=35.0, length_mm=120,
        flare_type="exponential",
    ))

    return asm


# ============================================================================
# Demo
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("MODULAR INSTRUMENT COMPONENTS")
    print("=" * 60)

    # Show PVC compatibility
    print("\nPVC Pipe Cross-Reference:")
    print(f"  {'Nominal':<10} {'ID (mm)':>10} {'OD (mm)':>10}  Matches:")
    for key, pipe in PVC_PIPES.items():
        match = ""
        if 18 < pipe["id_mm"] < 22:
            match = "<-- chalumeau bore (7-10mm radius)"
        elif 24 < pipe["id_mm"] < 28:
            match = "<-- clarinet/bass clarinet bore"
        elif 34 < pipe["id_mm"] < 36:
            match = "<-- bass clarinet bell start"
        elif 50 < pipe["id_mm"] < 54:
            match = "<-- bass clarinet bell end"
        print(f"  {pipe['nominal']:<10} {pipe['id_mm']:>10.1f} {pipe['od_mm']:>10.1f}  {match}")

    # Build and display instruments
    for builder, label in [
        (build_chalumeau_C, "CHALUMEAU IN C"),
        (build_bass_chalumeau_Bb, "BASS CHALUMEAU IN Bb"),
        (build_bass_clarinet_Bb, "BASS CLARINET IN Bb"),
        (build_soprano_sax_Bb, "SOPRANO SAXOPHONE IN Bb"),
    ]:
        asm = builder()
        print(f"\n{'=' * 60}")
        print(label)
        print("=" * 60)
        print(asm.summary())

        config = asm.to_tmm_config()
        print(f"\n  TMM Config:")
        print(f"    Points: {len(config.get('inner_positions', []))}")
        print(f"    Holes: {len(config.get('hole_positions', []))}")
        print(f"    Length: {config.get('total_length_mm', 0):.0f}mm")
        print(f"    Closed top: {config.get('closed_top', False)}")
