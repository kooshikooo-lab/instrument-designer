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

from ..core.network import AcousticNetwork, Fingering, Segment, Port, NodeType

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
        """Compute resonant frequencies for a set of fingerings.

        Args:
            network: acoustic network definition
            target_wavelengths: target wavelengths in mm
            fingering_sets: list of fingering states
            n_register: register number (1=fundamental)

        Returns:
            Array of resonant frequencies in Hz
        """
        c = network.speed_of_sound  # mm/s
        f_min = max(10, c / (max(target_wavelengths) * 2))
        f_max = c / (min(target_wavelengths) * 0.5)
        frequencies = np.linspace(f_min, f_max, 5000)

        results = []
        for fingering in fingering_sets:
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

            freqs = result.resonance_frequencies(k=n_register + 2)
            if len(freqs) >= n_register:
                results.append(freqs[n_register - 1])
            else:
                results.append(np.nan)

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
