"""OpenWInD FEM solver implementing the physics plugin interface.

Wraps OpenWInD's ImpedanceComputation and presents it through
the standardized solver interface, bridging from our AcousticNetwork
data model.

Key differences from TMM:
- Uses meters (we use mm)
- x=0 at mouthpiece/reed (same as our internal convention)
- Includes viscothermal losses, multiple radiation models
- Supports arbitrary bore shapes (spline, Bessel, exponential)
"""
from typing import List, Optional
import numpy as np

from ..core.network import AcousticNetwork, Fingering, Segment, Port, NodeType, BoundaryType

try:
    from openwind import ImpedanceComputation
except ImportError:
    ImpedanceComputation = None


class OpenWindSolver:
    """OpenWInD FEM solver.

    Wraps OpenWInD's ImpedanceComputation and presents it through
    the standardized solver interface.
    """

    def __init__(
        self,
        temperature: float = 25.0,
        losses: bool = True,
        radiation_category: str = "unflanged",
        compute_method: str = "FEM",
        nondim: bool = True,
    ):
        if ImpedanceComputation is None:
            raise ImportError(
                "OpenWInD is required. Install with: pip install openwind"
            )
        self.temperature = temperature
        self.losses = losses
        self.radiation_category = radiation_category
        self.compute_method = compute_method
        self.nondim = nondim

    def _network_to_openwind(self, network: AcousticNetwork):
        """Convert AcousticNetwork to OpenWInD inline list format.

        Converts mm -> m (OpenWInD default unit).
        Bore: our segments go reed(pos=0) -> bell(pos=L).
              OpenWInD also uses x=0 at entrance, so no flip needed.
        """
        # Main bore: list of [x1, x2, r1, r2, 'linear']
        bore_list = []
        pos = 0.0
        for seg in network.segments:
            x1 = pos / 1000.0
            x2 = (pos + seg.length) / 1000.0
            r1 = seg.radius_in / 1000.0
            r2 = seg.radius_out / 1000.0
            bore_list.append([x1, x2, r1, r2, 'linear'])
            pos += seg.length

        # Holes: list with header + [label, position, radius, length]
        hole_list = [['label', 'position', 'radius', 'length']]
        for i, port in enumerate(network.ports):
            hole_list.append([
                f'hole{i+1}',
                port.position / 1000.0,
                port.radius / 1000.0,
                port.length / 1000.0,
            ])

        return bore_list, hole_list

    def _build_fingering_chart(self, network: AcousticNetwork, fingering: List[str]):
        """Build OpenWInD fingering chart from our fingering state."""
        if not network.ports or not fingering:
            return []

        labels = [f'hole{i+1}' for i in range(len(network.ports))]
        chart = [['label', 'note']]
        for i, port in enumerate(network.ports):
            state = fingering[i] if i < len(fingering) else 'closed'
            chart.append([labels[i], 'o' if state == 'open' else 'x'])
        return chart

    def compute_impedance(
        self,
        network: AcousticNetwork,
        frequencies: np.ndarray,
        fingering: List[str] = None,
    ) -> np.ndarray:
        """Compute input impedance at given frequencies.

        Args:
            network: acoustic network definition
            frequencies: frequencies in Hz
            fingering: optional fingering state (["open","closed",...])

        Returns:
            Complex impedance array
        """
        bore_list, hole_list = self._network_to_openwind(network)

        fingering_chart = None
        if fingering and network.ports:
            fingering_chart = self._build_fingering_chart(network, fingering)

        result = ImpedanceComputation(
            frequencies,
            bore_list,
            holes_valves=hole_list if network.n_ports > 0 else [],
            fingering_chart=fingering_chart if fingering_chart else [],
            temperature=self.temperature,
            losses=self.losses,
            radiation_category=self.radiation_category,
            compute_method=self.compute_method,
            nondim=self.nondim,
            unit='m',
        )
        return result.impedance

    def compute_frequencies(
        self,
        network: AcousticNetwork,
        target_wavelengths: List[float],
        fingering_sets: List[List[str]],
        n_register: int = 1,
    ) -> np.ndarray:
        """Compute sounding frequencies for a set of fingerings.

        Mirrors ``TMMSolver.compute_frequencies``: each (target_wavelength,
        fingering) pair returns the register feature nearest the target. The
        feature type depends on the input boundary, which is the physically
        decisive difference between woodwind families:

        - REED/CLOSED input (clarinet-like): the sounding notes are the input
          impedance *resonances* (phase zero, decreasing).
        - OPEN input (flute-like): the sounding notes are the input impedance
          *antiresonances* (phase zero, increasing). A pipe open at both ends
          has impedance peaks only at its odd modes, so scanning peaks alone
          returns 3x/5x/9x... the fundamental and never the played notes.

        The register vent (first port, closest to the input) is OPEN for
        ``n_register >= 2``, matching ``TMMSolver.compute_frequencies``.

        Args:
            network: acoustic network definition
            target_wavelengths: target wavelengths (mm) near the register-n note
            fingering_sets: list of fingering states (toneholes only)
            n_register: register number, or a list with one value per note

        Returns:
            Array of sounding frequencies in Hz
        """
        from openwind.impedance_tools import (
            antiresonance_peaks_from_phase,
            resonance_peaks_from_phase,
        )

        c = network.speed_of_sound  # mm/s
        input_open = network.boundary_reed.type == BoundaryType.OPEN
        peaks_fn = antiresonance_peaks_from_phase if input_open else resonance_peaks_from_phase

        # Grid wide enough to bracket the lowest fundamental AND the highest
        # overblown register. The previous bounds broke both cases: f_min =
        # c/(2*max_wl) starts exactly on an open pipe's first antiresonance
        # (so the fundamental was silently skipped) and f_max = c/(min_wl*0.5)
        # truncates above the second peak, so register >= 2 returned NaN.
        f_min = max(10, c / (4.0 * max(target_wavelengths)))
        f_max = c / min(target_wavelengths) * 4.0
        frequencies = np.linspace(f_min, f_max, 4000)

        has_register = any(
            getattr(p, "is_register_vent", False) for p in network.ports
        )
        is_list = isinstance(n_register, list)
        registers = n_register if is_list else [n_register] * len(fingering_sets)

        results = []
        for target_wl, fingering, reg in zip(
            target_wavelengths, fingering_sets, registers
        ):
            if has_register:
                reg_state = "open" if reg >= 2 else "closed"
                fingering = [reg_state] + list(fingering)

            bore_list, hole_list = self._network_to_openwind(network)
            fingering_chart = self._build_fingering_chart(network, fingering)

            result = ImpedanceComputation(
                frequencies,
                bore_list,
                holes_valves=hole_list if network.n_ports > 0 else [],
                fingering_chart=fingering_chart if fingering_chart else [],
                temperature=self.temperature,
                losses=self.losses,
                radiation_category=self.radiation_category,
                compute_method=self.compute_method,
                nondim=self.nondim,
                unit='m',
            )

            features = peaks_fn(
                np.asarray(result.frequencies),
                np.asarray(result.impedance),
                k=100,
                display_warning=False,
            )[0]

            if len(features) == 0:
                # Degenerate case: no phase crossing inside the window. Use the
                # magnitude extremum (minimum for open pipes, maximum otherwise).
                mag = np.abs(result.impedance)
                idx = int(np.argmin(mag)) if input_open else int(np.argmax(mag))
                features = [float(result.frequencies[idx])]

            f_target = c / target_wl
            best = min(features, key=lambda f: abs(np.log2(f / f_target)))
            results.append(float(best))

        return np.array(results)

    def resonance_phase(
        self, network: AcousticNetwork, wavelength: float,
        fingering: List[str],
    ) -> float:
        """Compute resonance phase at a single wavelength."""
        c = network.speed_of_sound
        freq = c / wavelength
        imp = self.compute_impedance(network, np.array([freq]), fingering)
        return float(np.angle(imp[0]))
