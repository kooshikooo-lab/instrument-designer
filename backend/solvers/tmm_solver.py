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
    from backend.tmm_acoustics import (
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

    def from_network(
        self, network: AcousticNetwork, outer_diameter_mm: float | None = None,
    ) -> TMMInstrument:
        """Convert AcousticNetwork to TMMInstrument.

        This bridges the abstract network model to the chalumier TMM.

        Parameters
        ----------
        network : AcousticNetwork
            The abstract acoustic network to convert.
        outer_diameter_mm : float or None, optional
            Body outer diameter (mm).  The network carries no wall-thickness
            information, so when omitted a rough estimate (2.5x the max bore
            radius) is used.  Callers that know the real OD should pass it:
            the end-flange correction is sensitive to it.
        """
        positions, radii = network.to_bore_profile()
        hole_pos, hole_rad, hole_len = network.to_hole_data()

        if outer_diameter_mm is None:
            outer_diameter_mm = max(radii) * 2.5  # rough estimate fallback

        loss_model = None if isinstance(self.losses, NoLoss) else self.losses

        return tmm_instrument_from_radii(
            radii, network.total_length,
            hole_pos.tolist(), hole_rad.tolist(), hole_len.tolist(),
            outer_diameter_mm=outer_diameter_mm,
            closed_top=(network.boundary_reed.type.value == "reed"),
            cone_step=0.5,
            loss_model=loss_model,
        )

    def _with_register_state(
        self,
        network: AcousticNetwork,
        fingering_sets: List[List[str]],
        n_register: int,
    ) -> List[List[str]]:
        """Insert register-vent states at the correct port indices.

        The register vent is not guaranteed to be the first port, and the TMM
        consumes fingering states by port index, so the vent state must be
        inserted at the index of the register-vent port(s) rather than blindly
        prepended.  ``fingering_sets`` is expected to contain TONEHOLE-only
        states (one entry per non-vent port, in port order); if a set already
        has one entry per port it is passed through with the vent states
        overridden for the requested register.
        """
        vent_indices = [i for i, p in enumerate(network.ports) if p.is_register_vent]
        if not vent_indices:
            return [list(fs) for fs in fingering_sets]
        reg_state = "open" if n_register >= 2 else "closed"
        n_ports = len(network.ports)
        vent_set = set(vent_indices)
        adjusted = []
        for fs in fingering_sets:
            fs = list(fs)
            if len(fs) == n_ports:
                for vi in vent_indices:
                    fs[vi] = reg_state
            elif len(fs) == n_ports - len(vent_indices):
                full = [None] * n_ports
                k = 0
                for i in range(n_ports):
                    if i in vent_set:
                        full[i] = reg_state
                    else:
                        full[i] = fs[k]
                        k += 1
                fs = full
            else:
                raise ValueError(
                    f"fingering length {len(fs)} does not match {n_ports} ports "
                    f"minus {len(vent_indices)} register vent(s)"
                )
            adjusted.append(fs)
        return adjusted

    def compute_frequencies(
        self,
        network: AcousticNetwork,
        target_wavelengths: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
        outer_diameter_mm: float | None = None,
    ) -> np.ndarray:
        """Compute resonant frequencies for a set of fingerings.

        Args:
            network: acoustic network definition
            target_wavelengths: target wavelengths to search near (mm)
            fingering_sets: list of fingering states for TONEHOLES only
                (["open","closed",...], one entry per tonehole)
            n_register: register number (1 = fundamental/chalumeau, 2 = clarion)
            outer_diameter_mm: body outer diameter (mm); see ``from_network``.

        The register vent state is inserted automatically at the register-vent
        port position:
        - n_register=1 (chalumeau): register vent CLOSED
        - n_register=2 (clarion): register vent OPEN

        Returns:
            Array of actual frequencies in Hz
        """
        inst = self.from_network(network, outer_diameter_mm=outer_diameter_mm)
        adjusted_fingerings = self._with_register_state(
            network, fingering_sets, n_register
        )

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
        adjusted = self._with_register_state(network, [fingering], n_register)[0]
        return inst.resonance_phase(wavelength, adjusted)

    def find_resonance(
        self, network: AcousticNetwork, wavelength_near: float,
        fingering: List[str], n_register: int = 1,
    ) -> float:
        """Find resonant wavelength near target."""
        inst = self.from_network(network)
        adjusted = self._with_register_state(network, [fingering], n_register)[0]
        return inst.find_resonance(wavelength_near, adjusted, n_register)

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
