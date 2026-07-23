"""
Trumpet model using OpenWind (1D FEM with visco-thermal losses).

This module provides a trumpet model using OpenWind's accurate FEM-based
acoustic simulation, which handles:
- Visco-thermal losses in arbitrary bore shapes
- Proper bell radiation conditions
- Valve (piston) modeling with deviation pipes
- Resonance peak detection

The OpenWind approach is more accurate than our custom TMM for brass instruments
because:
1. TMM uses approximate "equivalent radius" for conical sections with losses
2. FEM directly solves the wave equation with proper boundary conditions
3. OpenWind includes radiation impedance models for bells

Usage:
    from backend.trumpet_openwind import TrumpetOpenWind

    trumpet = TrumpetOpenWind()
    freqs = trumpet.played_frequencies(register=1)
    trumpet.plot_impedance()
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

try:
    import openwind
    from openwind import ImpedanceComputation, InstrumentGeometry
    HAS_OPENWIND = True
except ImportError:
    HAS_OPENWIND = False
    print("Warning: OpenWind not installed. Install with: pip install openwind")


# ============================================================================
# Trumpet geometry constants
# ============================================================================

# Standard Bb trumpet dimensions (meters)
SPEED_OF_SOUND = 343.0  # m/s at 20°C

# Note names and MIDI numbers
NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def midi_to_freq(midi_note: int) -> float:
    """Convert MIDI note number to frequency in Hz."""
    return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))

def note_to_midi(note: str, octave: int) -> int:
    """Convert note name and octave to MIDI number."""
    idx = NOTE_NAMES.index(note)
    return 12 * (octave + 1) + idx

def freq_to_note(freq: float) -> Tuple[str, int, float]:
    """Convert frequency to (note_name, octave, cents_sharp)."""
    midi = 69 + 12 * math.log2(freq / 440.0)
    nearest = round(midi)
    cents = 1200.0 * (midi - nearest)
    octave = (nearest // 12) - 1
    note_idx = nearest % 12
    return NOTE_NAMES[note_idx], octave, cents


# ============================================================================
# Trumpet bore geometry
# ============================================================================

@dataclass
class TrumpetBore:
    """
    Trumpet bore geometry defined as segments.
    
    Each segment: [start_x, end_x, start_radius, end_radius, shape]
    Shapes: 'linear' (cylinder/cone), 'bessel' (Bessel horn), 'exponential'
    """
    segments: List[List]
    valves: List[List]
    fingering_chart: List[List]
    
    @classmethod
    def default_bb(cls) -> 'TrumpetBore':
        """
        Create a default Bb trumpet bore geometry.
        
        Based on Bach 180-37 ML measurements:
        - ML bore: 0.459" = 11.66mm dia = 5.83mm radius
        - Bell: 122.24mm dia = 61.12mm radius  
        - Leadpipe venturi: 0.345" = 8.76mm dia = 4.38mm radius
        - Total tube length: ~1335mm (matches Bb3 = 233 Hz)
        
        The bore profile is: leadpipe taper -> cylinder -> bell flare (Bessel).
        From pulse reflectometry: "After initial widening, the profile is 
        approximately cylindrical. The radius remains fairly constant through 
        the valve section. At the bell, the radius increases rapidly."
        """
        # Main bore geometry (meters)
        # Format: [start_x, end_x, start_radius, end_radius, shape, ...]
        segments = [
            # Mouthpiece receiver (conical taper)
            [0, 0.05, 0.003, 0.00438, 'linear'],
            
            # Leadpipe (expanding taper from venturi to ML bore)
            [0.05, 0.25, 0.00438, 0.00583, 'linear'],
            
            # Central bore (cylindrical, includes valve section)
            [0.25, 0.75, 0.00583, 0.00583, 'linear'],
            
            # Bell flare (Bessel horn - critical for harmonic compression)
            [0.75, 1.335, 0.00583, 0.06112, 'bessel', 0.7],
        ]
        
        # Valve definitions (pistons)
        # Format: ['variety', 'label', 'position', 'reconnection', 'radius', 'length']
        # position = where valve diverts air from main bore
        # reconnection = where valve tube reconnects to main bore  
        # length = total length of deviation pipe
        #
        # CRITICAL: Each valve's entry MUST be AFTER the previous valve's 
        # reconnection, otherwise pressing both valves gives same result as 
        # pressing only the first one (wave bypasses second valve's entry).
        #
        # Standard Bb trumpet valve slides:
        #   V1 (whole tone): +160mm tubing
        #   V2 (semitone):   +70mm tubing  
        #   V3 (minor third): +270mm tubing
        valves = [
            ['variety', 'label', 'position', 'reconnection', 'radius', 'length'],
            ['valve', 'piston1', 0.30, 0.46, 0.005, 0.16],
            ['valve', 'piston2', 0.47, 0.54, 0.005, 0.07],
            ['valve', 'piston3', 0.55, 0.82, 0.005, 0.27],
        ]
        
        # Fingering chart for 8 valve combinations
        # Format: [['label', 'note0', 'note1', ...], ['piston1', 'o', 'x', ...], ...]
        # 'o' = valve open (not pressed), 'x' = valve pressed
        fingering_chart = [
            ['label', 'open', '2', '1', '1+2', '3', '2+3', '1+3', '1+2+3'],
            ['piston1', 'o', 'o', 'x', 'x', 'o', 'o', 'x', 'x'],
            ['piston2', 'o', 'x', 'o', 'x', 'o', 'x', 'o', 'x'],
            ['piston3', 'o', 'o', 'o', 'o', 'x', 'x', 'x', 'x'],
        ]
        
        return cls(segments=segments, valves=valves, fingering_chart=fingering_chart)
    
    @classmethod
    def from_leadpipe_profile(cls, leadpipe_diameters: List[float], 
                              leadpipe_length: float = 0.25) -> 'TrumpetBore':
        """
        Create trumpet bore from leadpipe diameter profile.
        
        This allows optimization of the leadpipe shape (Petiot's approach).
        
        Args:
            leadpipe_diameters: List of 5 diameters (mm) along the leadpipe
            leadpipe_length: Length of leadpipe section (m)
        """
        # Convert mm to meters
        diams = [d / 1000.0 for d in leadpipe_diameters]
        
        # Build leadpipe segments (truncated cones)
        segments = []
        n = len(diams)
        seg_length = leadpipe_length / n
        
        for i in range(n):
            start_x = i * seg_length
            end_x = (i + 1) * seg_length
            segments.append([start_x, end_x, diams[i] / 2, diams[i + 1] / 2 if i + 1 < n else diams[-1] / 2, 'linear'])
        
        # Central bore (cylindrical)
        central_start = leadpipe_length
        central_end = central_start + 0.40
        segments.append([central_start, central_end, 0.006, 0.006, 'linear'])
        
        # Bell tail
        bell_tail_start = central_end
        bell_tail_end = bell_tail_start + 0.10
        segments.append([bell_tail_start, bell_tail_end, 0.006, 0.006, 'linear'])
        
        # Bell flare
        segments.append([bell_tail_end, bell_tail_end + 0.37, 0.006, 0.0635, 'bessel', 0.7])
        
        # Use default valves and fingering chart
        default = cls.default_bb()
        
        return cls(segments=segments, valves=default.valves, fingering_chart=default.fingering_chart)


# ============================================================================
# Trumpet OpenWind model
# ============================================================================

class TrumpetOpenWind:
    """
    Trumpet model using OpenWind's FEM-based acoustic simulation.
    
    This model provides:
    - Accurate impedance computation with visco-thermal losses
    - Valve combinations with proper deviation pipes
    - Resonance peak detection
    - Optimization interface for leadpipe design
    """
    
    def __init__(self, bore: TrumpetBore, temperature: float = 25.0):
        """
        Initialize trumpet model.
        
        Args:
            bore: TrumpetBore geometry definition
            temperature: Air temperature in Celsius (affects speed of sound)
        """
        if not HAS_OPENWIND:
            raise ImportError("OpenWind not installed. Install with: pip install openwind")
        
        self.bore = bore
        self.temperature = temperature
        
        # Build OpenWind geometry
        self._build_geometry()
        
        # Pre-compute impedance for all fingerings
        self._compute_impedances()
    
    def _build_geometry(self):
        """Build OpenWind InstrumentGeometry from bore definition."""
        self.geometry = InstrumentGeometry(
            self.bore.segments,
            self.bore.valves,
            self.bore.fingering_chart,
            unit='m'
        )
    
    def _compute_impedances(self, freq_range: Tuple[float, float] = (50, 2000), 
                           freq_step: float = 1.0):
        """
        Compute impedance for all fingering combinations.
        
        Args:
            freq_range: (min_freq, max_freq) in Hz
            freq_step: Frequency step in Hz
        """
        frequencies = np.arange(freq_range[0], freq_range[1], freq_step)
        
        self.impedances = {}
        self.fingering_names = self.bore.fingering_chart[0][1:]  # Skip 'label'
        
        for name in self.fingering_names:
            try:
                result = ImpedanceComputation(
                    frequencies, 
                    self.bore.segments,
                    self.bore.valves,
                    self.bore.fingering_chart,
                    note=name,  # OpenWind uses 'note' parameter
                    temperature=self.temperature
                )
                self.impedances[name] = {
                    'frequencies': frequencies,
                    'Z': result.impedance,
                    'magnitude': np.abs(result.impedance),
                }
            except Exception as e:
                print(f"Warning: Failed to compute impedance for {name}: {e}")
                self.impedances[name] = None
    
    def find_resonances(self, fingering_name: str, n_peaks: int = 8) -> List[float]:
        """
        Find resonance frequencies for a given fingering.
        
        Args:
            fingering_name: Name of fingering ('open', '1', '2', etc.)
            n_peaks: Number of resonance peaks to find
        
        Returns:
            List of resonance frequencies in Hz
        """
        if fingering_name not in self.impedances or self.impedances[fingering_name] is None:
            return []
        
        data = self.impedances[fingering_name]
        freqs = data['frequencies']
        magnitude = data['magnitude']
        
        # Find peaks in impedance magnitude
        peaks = []
        for i in range(1, len(magnitude) - 1):
            if magnitude[i] > magnitude[i-1] and magnitude[i] > magnitude[i+1]:
                peaks.append((freqs[i], magnitude[i]))
        
        # Sort by magnitude (strongest resonances first)
        peaks.sort(key=lambda x: x[1], reverse=True)
        
        # Return top n_peaks frequencies, sorted by frequency
        result = sorted([p[0] for p in peaks[:n_peaks]])
        return result
    
    def played_frequencies(self, n_register: int = 1, n_peaks: int = 8) -> Dict[str, float]:
        """
        Get the fundamental frequency for each fingering combination.
        
        Args:
            n_register: Which register (1 = fundamental, 2 = octave, etc.)
            n_peaks: Number of peaks to search
        
        Returns:
            Dictionary mapping fingering name to frequency
        """
        frequencies = {}
        
        for name in self.fingering_names:
            resonances = self.find_resonances(name, n_peaks)
            if len(resonances) >= n_register:
                frequencies[name] = resonances[n_register - 1]
            elif resonances:
                frequencies[name] = resonances[-1]  # Use highest available
            else:
                frequencies[name] = 0.0
        
        return frequencies
    
    def cents_error(self, actual_freq: float, target_freq: float) -> float:
        """Compute pitch error in cents."""
        if actual_freq <= 0 or target_freq <= 0:
            return 1e10
        return 1200.0 * math.log2(actual_freq / target_freq)
    
    def evaluate_intonation(self, target_notes: Dict[str, Tuple[str, int]]) -> Dict:
        """
        Evaluate intonation against target notes.
        
        Args:
            target_notes: Dictionary mapping fingering name to (note_name, octave)
        
        Returns:
            Dictionary with evaluation results
        """
        played = self.played_frequencies()
        
        results = {}
        cents_errors = []
        
        for fingering, (note, octave) in target_notes.items():
            if fingering in played and played[fingering] > 0:
                target_freq = midi_to_freq(note_to_midi(note, octave))
                actual_freq = played[fingering]
                cents = self.cents_error(actual_freq, target_freq)
                cents_errors.append(cents)
                results[fingering] = {
                    'note': f"{note}{octave}",
                    'target_freq': target_freq,
                    'actual_freq': actual_freq,
                    'error_cents': cents,
                }
            else:
                results[fingering] = {'note': f"{note}{octave}", 'error_cents': 1e10}
        
        if cents_errors:
            rms = math.sqrt(sum(c**2 for c in cents_errors) / len(cents_errors))
            peak = max(abs(c) for c in cents_errors)
        else:
            rms = 1e10
            peak = 1e10
        
        return {
            'results': results,
            'rms_cents': rms,
            'peak_error_cents': peak,
        }
    
    def plot_impedance(self, fingering_name: str = 'open'):
        """Plot impedance for a given fingering."""
        import matplotlib.pyplot as plt
        
        if fingering_name not in self.impedances or self.impedances[fingering_name] is None:
            print(f"No impedance data for {fingering_name}")
            return
        
        data = self.impedances[fingering_name]
        plt.figure(figsize=(10, 6))
        plt.plot(data['frequencies'], 20 * np.log10(data['magnitude']))
        plt.xlabel('Frequency (Hz)')
        plt.ylabel('Impedance (dB)')
        plt.title(f'Trumpet Impedance - {fingering_name}')
        plt.grid(True)
        plt.show()
    
    def plot_all_impedances(self):
        """Plot impedance for all fingering combinations."""
        import matplotlib.pyplot as plt
        
        fig, axes = plt.subplots(2, 4, figsize=(16, 8))
        axes = axes.flatten()
        
        for i, name in enumerate(self.fingering_names):
            if i >= len(axes):
                break
            
            if self.impedances.get(name) is not None:
                data = self.impedances[name]
                axes[i].plot(data['frequencies'], 20 * np.log10(data['magnitude']))
                axes[i].set_title(f'{name}')
                axes[i].set_xlabel('Freq (Hz)')
                axes[i].set_ylabel('Impedance (dB)')
                axes[i].grid(True)
        
        plt.tight_layout()
        plt.show()


# ============================================================================
# Trumpet optimizer
# ============================================================================

class TrumpetOptimizer:
    """
    Optimize trumpet leadpipe for intonation using OpenWind.
    
    Based on Petiot's approach (2024-2025):
    - Optimize leadpipe shape (5 diameters + 1 length = 6 variables)
    - Minimize RMS intonation error across chromatic scale
    - Use L-BFGS-B or differential evolution
    """
    
    def __init__(self, target_notes: Dict[str, Tuple[str, int]], 
                 temperature: float = 25.0):
        """
        Initialize optimizer.
        
        Args:
            target_notes: Dictionary mapping fingering name to (note_name, octave)
            temperature: Air temperature in Celsius
        """
        self.target_notes = target_notes
        self.temperature = temperature
        
        # Convert targets to frequencies
        self.target_freqs = {}
        for fingering, (note, octave) in target_notes.items():
            self.target_freqs[fingering] = midi_to_freq(note_to_midi(note, octave))
    
    def objective(self, params: np.ndarray) -> float:
        """
        Objective function: RMS cents error.
        
        Args:
            params: [d1, d2, d3, d4, d5, L] - leadpipe diameters (mm) and length (m)
        
        Returns:
            RMS cents error (lower is better)
        """
        try:
            # Extract parameters
            diameters = params[:5]  # mm
            length = params[5]      # m
            
            # Create bore from leadpipe profile
            bore = TrumpetBore.from_leadpipe_profile(diameters, length)
            
            # Create trumpet model
            trumpet = TrumpetOpenWind(bore, self.temperature)
            
            # Evaluate intonation
            evaluation = trumpet.evaluate_intonation(self.target_notes)
            
            return evaluation['rms_cents']
            
        except Exception as e:
            return 1e10
    
    def optimize(self, method: str = 'L-BFGS-B', max_iter: int = 100, 
                 verbose: bool = True) -> Dict:
        """
        Run optimization.
        
        Args:
            method: Optimization method ('L-BFGS-B', 'Nelder-Mead', 'DE')
            max_iter: Maximum iterations
            verbose: Print progress
        
        Returns:
            Dictionary with optimization results
        """
        from scipy.optimize import minimize, differential_evolution
        
        # Initial guess (mm for diameters, m for length)
        x0 = np.array([6.0, 6.0, 6.0, 6.0, 6.0, 0.25])
        
        # Bounds
        bounds = [
            (4.0, 8.0),   # d1: mouthpiece end
            (5.0, 8.0),   # d2
            (5.5, 8.0),   # d3
            (5.8, 8.0),   # d4
            (6.0, 8.0),   # d5: central bore end
            (0.15, 0.35), # L: leadpipe length
        ]
        
        if verbose:
            print("Trumpet leadpipe optimization")
            print(f"Target notes: {self.target_notes}")
            print(f"Method: {method}")
        
        if method == 'DE':
            result = differential_evolution(
                self.objective, bounds,
                seed=42, maxiter=max_iter,
                popsize=10, tol=1e-6,
            )
        else:
            result = minimize(
                self.objective, x0,
                method=method,
                bounds=bounds,
                options={"maxiter": max_iter, "ftol": 1e-6},
            )
        
        if verbose:
            print(f"\nOptimization complete:")
            print(f"  RMS: {result.fun:.2f} cents")
            print(f"  Leadpipe diameters: {result.x[:5]} mm")
            print(f"  Leadpipe length: {result.x[5]:.3f} m")
        
        return {
            "success": result.success,
            "rms_cents": result.fun,
            "leadpipe_diameters": result.x[:5].tolist(),
            "leadpipe_length": result.x[5],
        }


# ============================================================================
# Convenience functions
# ============================================================================

def create_default_trumpet() -> TrumpetOpenWind:
    """Create a default Bb trumpet model."""
    bore = TrumpetBore.default_bb()
    return TrumpetOpenWind(bore)

def demo():
    """Demo trumpet analysis."""
    if not HAS_OPENWIND:
        print("OpenWind not installed. Install with: pip install openwind")
        return
    
    print("Trumpet OpenWind Demo")
    print("=" * 50)
    
    trumpet = create_default_trumpet()
    
    print("\nPlaying frequencies (1st register):")
    freqs = trumpet.played_frequencies(n_register=1)
    for name, freq in freqs.items():
        if freq > 0:
            note, octave, cents = freq_to_note(freq)
            print(f"  {name:8s}: {freq:8.1f} Hz  {note}{octave} ({cents:+.1f} cents)")
        else:
            print(f"  {name:8s}: no resonance")
    
    print("\nImpedance plot for open fingering:")
    trumpet.plot_impedance('open')


if __name__ == "__main__":
    demo()
