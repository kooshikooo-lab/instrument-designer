"""Impedance-first solver design.

Per ChatGPT: Make impedance the primary solver output.
Resonance extraction becomes post-processing.

Matches Benade, Nederveen, Keefe, OpenWInD literature.
"""
from abc import ABC, abstractmethod
from typing import List, Tuple, Optional
import numpy as np
from dataclasses import dataclass


@dataclass
class ImpedanceSpectrum:
    """Input impedance spectrum Z(f) = p(f)/U(f)."""
    frequencies: np.ndarray  # Hz
    impedance: np.ndarray    # complex Z (Pa·s/m³)
    
    def magnitude(self) -> np.ndarray:
        return np.abs(self.impedance)
    
    def phase(self) -> np.ndarray:
        return np.angle(self.impedance)
    
    def peaks(self, n_peaks: int = 10) -> List[Tuple[float, float]]:
        """Find impedance peaks (magnitude) with parabolic interpolation.
        
        Returns: list of (frequency, magnitude) tuples
        """
        mag = self.magnitude()
        peaks = []
        for i in range(1, len(mag) - 1):
            if mag[i] > mag[i-1] and mag[i] > mag[i+1]:
                # Parabolic interpolation
                alpha = np.log(mag[i-1])
                beta = np.log(mag[i])
                gamma = np.log(mag[i+1])
                denom = alpha - 2*beta + gamma
                if abs(denom) > 1e-10:
                    shift = 0.5 * (alpha - gamma) / denom
                    shift = np.clip(shift, -0.5, 0.5)
                    df = self.frequencies[1] - self.frequencies[0]
                    f_peak = self.frequencies[i] + shift * df
                    mag_peak = np.exp(beta - 0.25 * (alpha - gamma) * shift)
                    peaks.append((f_peak, mag_peak))
        peaks.sort(key=lambda x: -x[1])
        return peaks[:n_peaks]


class ImpedanceSolver(ABC):
    """Base class: impedance is the primary output."""
    
    @abstractmethod
    def compute_impedance(
        self,
        network: 'AcousticNetwork',
        frequencies: np.ndarray,
        fingering: List[str],
    ) -> ImpedanceSpectrum:
        """Compute input impedance at given frequencies."""
        pass
    
    def find_resonances(
        self,
        network: 'AcousticNetwork',
        fingering: List[str],
        f_min: float = 20.0,
        f_max: float = 2000.0,
        n_points: int = 50000,
    ) -> List[float]:
        """Extract resonance frequencies from impedance peaks."""
        frequencies = np.linspace(f_min, f_max, n_points)
        Z = self.compute_impedance(network, frequencies, fingering)
        peaks = Z.peaks(n_peaks=20)
        return [f for f, _ in peaks]
    
    def playing_frequencies(
        self,
        network: 'AcousticNetwork',
        fingering: List[str],
        n_register: int = 1,
        reed_model: 'ReedModel' = None,
    ) -> List[float]:
        """Compute playing frequencies (including reed interaction).
        
        This is the musician-relevant output.
        Requires reed model for complete simulation.
        """
        # For now: return impedance peaks near register targets
        resonances = self.find_resonances(network, fingering)
        # Filter for register
        if n_register == 1:
            return [f for f in resonances if f < resonances[0] * 2.5]
        elif n_register == 2:
            return [f for f in resonances if f > resonances[0] * 2.0]
        return resonances


# --- TMMSolver adapts to ImpedanceSolver ---

class TMMImpedanceSolver(ImpedanceSolver):
    """TMM solver with impedance as primary output."""
    
    def __init__(self, tmm_solver: 'TMMSolver'):
        self.tmm = tmm_solver
    
    def compute_impedance(
        self,
        network: 'AcousticNetwork',
        frequencies: np.ndarray,
        fingering: List[str],
    ) -> ImpedanceSpectrum:
        """Compute input impedance using TMM resonance phase.

        Uses the relationship between resonance phase and impedance:
            R = exp(i * pi * resonance_phase)     (reflection coefficient)
            Z = Z0 * (1 + R) / (1 - R)            (input impedance)

        where Z0 = rho * c / A is the characteristic impedance of the
        input bore cross-section.

        NOTE 2026-07-28: This implementation derives impedance from the
        reflection phase rather than cascading transfer matrices directly.
        The two approaches are mathematically equivalent for lossless
        systems. For lossy systems, the phase-only approach misses the
        magnitude reduction from losses in the reflection coefficient.
        This is acceptable for intonation-centric optimization but may
        need a full TMM cascade for accurate impedance magnitudes.
        """
        inst = self.tmm.from_network(network)
        has_register = any(p.is_register_vent for p in network.ports)
        if has_register:
            fingering = ["open"] + list(fingering)

        # Characteristic impedance at the input
        rho = 1.204  # kg/m^3 at 20C
        c = 343200.0  # mm/s
        input_radius = network.segments[0].radius_in if network.segments else 7.25
        A = np.pi * input_radius ** 2  # mm^2
        Z0 = rho * c / A  # Pa·s/mm^2 (characteristic impedance)

        Z_arr = np.zeros(len(frequencies), dtype=complex)
        for i, f in enumerate(frequencies):
            wl = c / f if f > 0 else 1e10
            try:
                phase = inst.resonance_phase(wl, fingering)
                R = np.exp(1j * np.pi * phase)
                Z_arr[i] = Z0 * (1.0 + R) / (1.0 - R)
            except Exception:
                Z_arr[i] = Z0  # matched load fallback

        return ImpedanceSpectrum(frequencies=frequencies, impedance=Z_arr)


# --- OpenWindSolver already computes impedance ---

class OpenWindImpedanceSolver(ImpedanceSolver):
    """OpenWInD FEM solver with impedance as primary output."""
    
    def __init__(self, openwind_solver: 'OpenWindSolver'):
        self.ow = openwind_solver
    
    def compute_impedance(
        self,
        network: 'AcousticNetwork',
        frequencies: np.ndarray,
        fingering: List[str],
    ) -> ImpedanceSpectrum:
        """Compute impedance using OpenWInD's ImpedanceComputation."""
        bore_list, hole_list = self.ow._network_to_openwind(network)
        chart, note_names = self.ow._build_fingering_chart(network, [fingering])
        
        from openwind import ImpedanceComputation
        result = ImpedanceComputation(
            frequencies=frequencies,
            main_bore=bore_list,
            holes_valves=hole_list,
            fingering_chart=chart,
            note=note_names[0],
            temperature=25.0,
            losses=True,
            radiation_category='unflanged',
            compute_method='FEM',
            nondim=True,
            unit='m',
        )
        
        return ImpedanceSpectrum(
            frequencies=frequencies,
            impedance=result.impedance,
        )


# --- Usage pattern ---

def solve_instrument(
    network: 'AcousticNetwork',
    fingering: List[str],
    solver: ImpedanceSolver,
    target_frequencies: List[float] = None,
) -> dict:
    """Solve instrument: impedance → resonances → playing frequencies.
    
    Returns dict with all outputs for analysis/optimization.
    """
    # 1. Impedance (primary)
    f_max = max(target_frequencies) * 3 if target_frequencies else 2000
    frequencies = np.linspace(20, f_max, 50000)
    Z = solver.compute_impedance(network, frequencies, fingering)
    
    # 2. Resonances
    resonances = Z.peaks(n_peaks=15)
    
    # 3. Playing frequencies (with reed model)
    playing = solver.playing_frequencies(network, fingering)
    
    # 4. Metrics
    metrics = {
        'impedance': Z,
        'resonances': [f for f, _ in resonances],
        'resonance_magnitudes': [m for _, m in resonances],
        'playing_frequencies': playing,
    }
    
    if target_frequencies:
        cents_errors = []
        for target, actual in zip(target_frequencies, playing):
            if actual > 0:
                cents_errors.append(1200 * np.log2(actual / target))
        metrics['cents_errors'] = cents_errors
        metrics['rms_cents'] = np.sqrt(np.mean(np.array(cents_errors)**2))
    
    return metrics