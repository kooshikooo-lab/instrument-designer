"""TMM solver implementing the physics plugin interface.

Wraps the existing chalumier-ported TMM engine and presents it
through the standardized physics plugin interfaces.
"""
from typing import List, Tuple, Optional
import numpy as np

from ..core.network import AcousticNetwork, Fingering, Segment, Port
from ..core.coordinates import CoordinateTransform
from ..physics.propagation import LosslessPropagation
from ..physics.junction import LosslessJunction
from ..physics.tonehole import SimpleTonehole
from ..physics.radiation import BesselRadiation
from ..physics.losses import NoLoss
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
        losses: NoLoss = None,
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
            fingering_sets: list of fingering states (["open","closed",...])
            n_register: register number (1 = fundamental, 2 = first overtone)

        Returns:
            Array of actual frequencies in Hz
        """
        inst = self.from_network(network)
        return inst.compute_fingered_frequencies(
            target_wavelengths, fingering_sets, n_register
        )

    def resonance_phase(
        self, network: AcousticNetwork, wavelength: float, fingering: List[str]
    ) -> float:
        """Compute resonance phase for a single wavelength and fingering."""
        inst = self.from_network(network)
        return inst.resonance_phase(wavelength, fingering)

    def find_resonance(
        self, network: AcousticNetwork, wavelength_near: float,
        fingering: List[str], n_register: int = 1,
    ) -> float:
        """Find resonant wavelength near target."""
        inst = self.from_network(network)
        return inst.find_resonance(wavelength_near, fingering, n_register)
