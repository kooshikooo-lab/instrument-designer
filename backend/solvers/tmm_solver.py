"""TMM solver implementing the physics plugin interface.

Wraps the existing chalumier-ported TMM engine and presents it through
the standardized physics plugin interfaces.
"""
from typing import List, Tuple, Optional
import numpy as np

from ..core.network import AcousticNetwork, Fingering, Segment, Port
from ..core.coordinates import CoordinateTransform
from ..physics.propagation import LosslessPropagation
from ..physics.junction import LosslessJunction
from ..physics.tonehole import SimpleTonehole
from ..physics.radiation import BesselRadiation
from ..physics.losses import NoLoss, LossModel
from ..physics.excitation import ReedExcitation

# Import the existing TMM engine
try:
    from ..tmm_acoustics import (
        TMMInstrument, tmm_instrument_from_radii,
        SPEED_OF_SOUND as CHALUMIER_SPEED_OF_SOUND,
    )
except ImportError:
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from tmm_acoustics import (
        TMMInstrument, tmm_instrument_from_radii,
        SPEED_OF_SOUND as CHALUMIER_SPEED_OF_SOUND,
    )


class TMMSolver:
    """Transfer Matrix Method solver.

    Wraps the chalumier-ported TMM engine and presents it through
    the standardized physics plugin interface.
    """

    def __init__(
        self,
        propagation: LosslessPropagation = None,
        junction: LosslessJunction = None,
        tonehole: SimpleTonehole = None,
        radiation: BesselRadiation = None,
        losses: LossModel = None,
        excitation: ReedExcitation = None,
    ):
        self.propagation = propagation or LosslessPropagation()
        self.junction = junction or LosslessJunction()
        self.tonehole = tonehole or SimpleTonehole()
        self.radiation = radiation or BesselRadiation()
        self.losses = losses or NoLoss()
        self.excitation = excitation or ReedExcitation()

    def from_network(self, network: AcousticNetwork) -> TMMInstrument:
        """Convert AcousticNetwork to TMMInstrument.

        This bridges the abstract network model to the chalumier TMM.
        """
        positions, radii = network.to_bore_profile()
        hole_pos, hole_rad, hole_len = network.to_hole_data()

        outer_diameter = max(radii) * 2.5  # rough outer diameter estimate

        return tmm_instrument_from_radii(
            radii, network.total_length,
            hole_pos.tolist(), hole_rad.tolist(), hole_len.tolist(),
            outer_diameter,
            closed_top=(network.boundary_reed.type.value == "reed"),
            cone_step=0.5,
        )

    def compute_frequencies(
        self,
        network: AcousticNetwork,
        target_wavelengths: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> np.ndarray:
        """Compute resonant frequencies for a set of fingerings.

        Args:
            network: acoustic network definition
            target_wavelengths: target wavelengths to search near (mm)
            fingering_sets: list of fingering states for TONEHOLES only
                (["open","closed",...], one entry per tonehole)
            n_register: register number (1 = fundamental/chalumeau, 2 = clarion)

        The register vent state is automatically prepended:
        - n_register=1 (chalumeau): register vent CLOSED
        - n_register=2 (clarion): register vent OPEN

        Returns:
            Array of actual frequencies in Hz
        """
        inst = self.from_network(network)

        # Prepend register vent state to each fingering set
        # TMM instrument expects entries for ALL holes (toneholes + register vent)
        # Register vent is at the first port position (closest to reed)
        has_register = any(p.is_register_vent for p in network.ports)
        if has_register:
            reg_state = "open" if n_register >= 2 else "closed"
            adjusted_fingerings = [[reg_state] + list(fs) for fs in fingering_sets]
        else:
            adjusted_fingerings = [list(fs) for fs in fingering_sets]

        return inst.compute_fingered_frequencies(
            target_wavelengths, adjusted_fingerings, n_register
        )

    def resonance_phase(
        self, network: AcousticNetwork, wavelength: float,
        fingering: List[str], n_register: int = 1,
    ) -> float:
        """Compute resonance phase for a single wavelength and fingering.

        Args:
            fingering: tonehole states only (["open","closed",...])
            n_register: register number (1=chalumeau, 2=clarion)
        """
        inst = self.from_network(network)
        has_register = any(p.is_register_vent for p in network.ports)
        if has_register:
            reg_state = "open" if n_register >= 2 else "closed"
            fingering = [reg_state] + list(fingering)
        return inst.resonance_phase(wavelength, fingering)

    def find_resonance(
        self, network: AcousticNetwork, wavelength_near: float,
        fingering: List[str], n_register: int = 1,
    ) -> float:
        """Find resonant wavelength near target."""
        inst = self.from_network(network)
        has_register = any(p.is_register_vent for p in network.ports)
        if has_register:
            reg_state = "open" if n_register >= 2 else "closed"
            fingering = [reg_state] + list(fingering)
        return inst.find_resonance(wavelength_near, fingering, n_register)

    # --- Loss model integration (for future TMM with losses) ---
    def _apply_bore_losses(self, network: AcousticNetwork, wavelengths: np.ndarray):
        """Apply viscothermal losses to bore segments.

        For each segment and wavelength, compute loss factor.
        This is a placeholder for future integration into TMMInstrument.
        """
        segment_losses = []
        for seg in network.segments:
            losses = []
            for wl in wavelengths:
                losses.append(self.losses.bore_loss(seg.length, seg.radius_in, wl))
            segment_losses.append(losses)
        return np.array(segment_losses)

    def _apply_hole_losses(self, network: AcousticNetwork, wavelengths: np.ndarray):
        """Apply viscothermal losses to tonehole chimneys."""
        hole_losses = []
        for port in network.ports:
            if port.is_tonehole or port.is_register_vent:
                losses = []
                for wl in wavelengths:
                    losses.append(self.losses.hole_loss(port.radius, port.length, wl))
                hole_losses.append(losses)
        return np.array(hole_losses) if hole_losses else np.array([])
