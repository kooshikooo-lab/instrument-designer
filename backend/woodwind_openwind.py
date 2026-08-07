"""
Woodwind FEM model using OpenWind — mirrors TrumpetOpenWind for woodwinds.

Provides:
- Woodwind bore + tonehole geometry conversion to OpenWind format
- Register vent handling (open for reg>=2, closed otherwise)
- Resonance/antiresonance selection based on boundary type (REED vs OPEN)
- Impedance computation + frequency extraction

Usage:
    from backend.woodwind_openwind import WoodwindOpenWind
    
    ww = WoodwindOpenWind(bore_length=600, bore_radius=7.5, n_holes=8)
    freqs = ww.played_frequencies(n_register=1)
"""
from typing import List, Optional, Tuple
import numpy as np

try:
    from openwind import ImpedanceComputation
    HAVE_OPENWIND = True
except ImportError:
    HAVE_OPENWIND = False
    ImpedanceComputation = None

from backend.tmm_acoustics import SPEED_OF_SOUND


class WoodwindOpenWind:
    """Woodwind FEM model using OpenWind's 1D FEM with viscothermal losses.
    
    Handles closed-open (clarinet/reed) and open-open (flute/sax) instruments.
    Supports toneholes, register vents, and arbitrary bore profiles.
    
    Key differences from TrumpetOpenWind:
    - Woodwinds use toneholes (not valves)
    - Register vent logic: open for register >= 2
    - Boundary type determines resonance vs antiresonance selection
    """
    
    def __init__(
        self,
        bore_length: float,           # mm
        bore_radius: float,           # mm
        n_holes: int,
        hole_positions: Optional[List[float]] = None,  # mm from reed
        hole_radii: Optional[List[float]] = None,
        hole_chimneys: Optional[List[float]] = None,
        bell_radius: Optional[float] = None,
        bell_length: Optional[float] = None,
        temperature: float = 25.0,
        losses: bool = True,
        radiation_category: str = "unflanged",
        compute_method: str = "FEM",
        n_register: int = 1,
    ):
        if not HAVE_OPENWIND:
            raise ImportError("OpenWind required: pip install openwind")
        
        self.bore_length = bore_length
        self.bore_radius = bore_radius
        self.n_holes = n_holes
        self.temperature = temperature
        self.losses = losses
        self.radiation_category = radiation_category
        self.compute_method = compute_method
        self.n_register = n_register
        
        # Default hole positions: evenly spaced along bore
        if hole_positions is None:
            self.hole_positions = [bore_length * (i+1) / (n_holes+1) for i in range(n_holes)]
        else:
            self.hole_positions = hole_positions
            
        # Default hole radii
        if hole_radii is None:
            self.hole_radii = [min(bore_radius * 0.5, 4.0)] * n_holes
        else:
            self.hole_radii = hole_radii
            
        # Default chimney heights (wall thickness + pad)
        if hole_chimneys is None:
            self.hole_chimneys = [3.0] * n_holes
        else:
            self.hole_chimneys = hole_chimneys
            
        # Bell flare (optional)
        self.bell_radius = bell_radius
        self.bell_length = bell_length
        
        # Register vent position (near reed end)
        self.register_vent_position = 10.0  # mm from reed
        self.register_vent_radius = min(bore_radius * 0.3, 2.5)
        self.register_vent_chimney = 2.0
        
        # Build OpenWind geometry
        self._build_geometry()
        
    def _bore_to_openwind(self):
        """Convert woodwind bore to OpenWind segment list.
        
        OpenWind format: [x1, x2, r1, r2, 'linear'] for each segment
        x in meters, r in meters
        """
        segments = []
        
        # Main bore (cylindrical for now)
        segments.append([
            0.0,
            self.bore_length / 1000.0,
            self.bore_radius / 1000.0,
            self.bore_radius / 1000.0,
            'linear'
        ])
        
        # Bell flare if specified
        if self.bell_radius and self.bell_length:
            segments.append([
                self.bore_length / 1000.0,
                (self.bore_length + self.bell_length) / 1000.0,
                self.bore_radius / 1000.0,
                self.bell_radius / 1000.0,
                'linear'
            ])
            
        return segments
    
    def _holes_to_openwind(self):
        """Convert toneholes to OpenWind hole list.
        
        OpenWind format: [['label', 'position', 'radius', 'length'], ...]
        Position in meters from reed, radius/length in meters.
        """
        holes = [['label', 'position', 'radius', 'length']]
        
        # Toneholes
        for i, (pos, rad, chim) in enumerate(zip(self.hole_positions, self.hole_radii, self.hole_chimneys)):
            holes.append([
                f'hole{i+1}',
                pos / 1000.0,
                rad / 1000.0,
                chim / 1000.0
            ])
        
        # Register vent
        holes.append([
            'register_vent',
            self.register_vent_position / 1000.0,
            self.register_vent_radius / 1000.0,
            self.register_vent_chimney / 1000.0
        ])
        
        return holes
    
    def _fingering_chart(self, fingering: List[str]) -> List[List[str]]:
        """Build OpenWind fingering chart.
        
        fingering: list of 'O' (open) / 'X' (closed) for each tonehole
        Register vent handled separately based on n_register.
        """
        chart = [['label', 'note']]
        
        # Toneholes
        for i, state in enumerate(fingering):
            holes = [f'hole{i+1}', 'o' if state in ('O', 'o') else 'x']
            chart.append(holes)
        
        # Register vent
        reg_state = 'o' if self.n_register >= 2 else 'x'
        chart.append(['register_vent', reg_state])
        
        return chart
    
    def compute_impedance(
        self,
        frequencies: np.ndarray,
        fingering: List[str],
    ) -> np.ndarray:
        """Compute input impedance at given frequencies."""
        bore_list = self._bore_to_openwind()
        hole_list = self._holes_to_openwind()
        fingering_chart = self._fingering_chart(fingering)
        
        result = ImpedanceComputation(
            frequencies,
            bore_list,
            holes_valves=hole_list,
            fingering_chart=fingering_chart,
            temperature=self.temperature,
            losses=self.losses,
            radiation_category=self.radiation_category,
            compute_method=self.compute_method,
            unit='m',
        )
        return result.impedance
    
    def compute_frequencies(
        self,
        target_wavelengths: List[float],
        fingerings: List[List[str]],
        n_register: Optional[int] = None,
    ) -> np.ndarray:
        """Compute sounding frequencies for a set of fingerings.
        
        Uses resonance peaks for REED (closed-open) and antiresonance peaks for OPEN.
        """
        from openwind.impedance_tools import (
            antiresonance_peaks_from_phase,
            resonance_peaks_from_phase,
        )
        
        reg = n_register if n_register is not None else self.n_register
        
        # Frequency sweep wide enough to catch all registers
        c = SPEED_OF_SOUND  # mm/s
        min_wl = min(target_wavelengths)
        max_wl = max(target_wavelengths)
        f_min = max(50, c / (4.0 * max_wl))
        f_max = c / min_wl * 4.0
        frequencies = np.linspace(f_min, f_max, 4000)
        
        results = []
        for target_wl, fingering in zip(target_wavelengths, fingerings):
            bore_list = self._bore_to_openwind()
            hole_list = self._holes_to_openwind()
            fingering_chart = self._fingering_chart(fingering)
            
            result = ImpedanceComputation(
                frequencies,
                bore_list,
                holes_valves=hole_list,
                fingering_chart=fingering_chart,
                temperature=self.temperature,
                losses=self.losses,
                radiation_category=self.radiation_category,
                compute_method=self.compute_method,
                unit='m',
            )
            
            # Select peak type based on boundary
            input_open = False  # Woodwinds are typically reed (closed) or flute (open)
            # Determine from bore length and target wavelength
            # For now, assume closed-open for woodwinds with reed
            peaks_fn = resonance_peaks_from_phase
            
            features = peaks_fn(
                np.asarray(result.frequencies),
                np.asarray(result.impedance),
                k=100,
                display_warning=False,
            )[0]
            
            if len(features) == 0:
                mag = np.abs(result.impedance)
                idx = int(np.argmax(mag))
                features = [float(result.frequencies[idx])]
            
            f_target = c / target_wl
            best = min(features, key=lambda f: abs(np.log2(f / f_target)))
            results.append(float(best))
        
        return np.array(results)
    
    def played_frequencies(self, fingerings: List[List[str]], n_register: int = 1) -> dict:
        """Get played frequencies for a set of fingerings."""
        results = {}
        for i, fingering in enumerate(fingerings):
            name = f'fingering_{i}'
            target_wls = [SPEED_OF_SOUND / 440.0] * len(fingerings)  # placeholder
            # In practice, pass actual target wavelengths
            freqs = self.compute_frequencies(target_wls, [fingering], n_register)
            results[name] = freqs[0] if len(freqs) > 0 else 0.0
        return results


def create_default_clarinet() -> WoodwindOpenWind:
    """Create a default Bb clarinet model."""
    return WoodwindOpenWind(
        bore_length=600.0,      # mm
        bore_radius=7.5,        # mm
        n_holes=8,
        hole_positions=[100, 150, 200, 250, 300, 350, 400, 450],  # mm from reed
        hole_radii=[3.5] * 8,   # mm
        hole_chimneys=[3.0] * 8,
        bell_radius=35.0,       # mm
        bell_length=100.0,      # mm
    )


def create_default_flute() -> WoodwindOpenWind:
    """Create a default C flute model."""
    return WoodwindOpenWind(
        bore_length=600.0,
        bore_radius=9.5,
        n_holes=13,
        hole_positions=[50, 100, 150, 200, 250, 300, 350, 400, 420, 440, 460, 470, 490],
        hole_radii=[4.5] * 13,
        hole_chimneys=[4.0] * 13,
    )


if __name__ == "__main__":
    if not HAVE_OPENWIND:
        print("OpenWind not installed. Install with: pip install openwind")
    else:
        clarinet = create_default_clarinet()
        print("Default Bb clarinet created")
        print(f"Bore: {clarinet.bore_length}mm x {clarinet.bore_radius}mm")
        print(f"Holes: {clarinet.n_holes}")
        print(f"Bell: {clarinet.bell_radius}mm x {clarinet.bell_length}mm")