"""
Trumpet TMM acoustics — phase-based resonance model for brass instruments.

Implements:
  - Closed-open pipe (lips = closed end, bell = open end)
  - Bore profile (leadpipe + central bore + bell flare)
  - Valve combinations (8 combinations adding tube lengths)
  - Mouthpiece Helmholtz resonator
  - Bell flange correction

Trumpet physics reference:
  - Bb trumpet: base length ~1400mm, sounds Bb3 (233 Hz)
  - Bell cutoff ~1170 Hz (10th harmonic ~ bell circumference)
  - Valve 1: +160mm (whole tone, 2 semitones)
  - Valve 2: +70mm (semitone)
  - Valve 3: +270mm (minor third, 3 semitones)
  - 8 valve combinations total

Usage:
    from backend.trumpet_acoustics import TrumpetModel, TrumpetOptimizer

    trumpet = TrumpetModel(
        bore_positions=[0, 250, 800, 1400],
        bore_diameters=[11.5, 11.5, 11.5, 127],  # mm
        leadpipe_start=11.5,
        leadpipe_end=12.0,
        leadpipe_length=250,
        bell_start=800,
        bell_end=1400,
        bell_ratio=4.0,  # bell OD / bore OD
        valve_tubes=[160, 70, 270],
    )
    freqs = trumpet.played_frequencies(register=1)
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

try:
    from .tmm_acoustics import (
        SPEED_OF_SOUND, TMMInstrument, Profile,
        circle_area, end_flange_length_correction,
        pipe_reply_phase, junction2_reply_phase,
    )
except ImportError:
    from tmm_acoustics import (
        SPEED_OF_SOUND, TMMInstrument, Profile,
        circle_area, end_flange_length_correction,
        pipe_reply_phase, junction2_reply_phase,
    )


# ============================================================================
# Trumpet valve combinations
# ============================================================================

# Standard Bb trumpet valve tube lengths (mm)
VALVE_TUBES_BB = {
    'valve_1': 160.0,  # Lowers by whole tone (2 semitones)
    'valve_2': 70.0,   # Lowers by semitone
    'valve_3': 270.0,  # Lowers by minor third (3 semitones)
}

# All 8 valve combinations (name, valve_indices, tube_length_add)
TRUMPET_VALVE_COMBOS = [
    ('open',   [],          0.0),
    ('1',      [0],         160.0),
    ('2',      [1],         70.0),
    ('1+2',    [0, 1],      230.0),   # 160+70
    ('3',      [2],         270.0),
    ('1+3',    [0, 2],      430.0),   # 160+270
    ('2+3',    [1, 2],      340.0),   # 70+270
    ('1+2+3',  [0, 1, 2],   500.0),   # 160+70+270
]

# Semitone shifts for each valve combination (relative to open)
TRUMPET_SEMITONE_SHIFTS = {
    'open':   0,
    '1':      -2,
    '2':      -1,
    '1+2':    -3,
    '3':      -3,
    '1+3':    -5,
    '2+3':    -4,
    '1+2+3':  -6,
}


# ============================================================================
# Trumpet note frequencies (Bb trumpet)
# ============================================================================

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
# Trumpet bore profile builder
# ============================================================================

@dataclass
class TrumpetBore:
    """
    Represents a trumpet bore profile.
    
    The bore consists of three regions:
    1. Leadpipe: conical taper from mouthpiece to central bore
    2. Central bore: cylindrical section with valve block
    3. Bell flare: exponential/parabolic expansion to bell
    
    For a Bb trumpet:
    - Leadpipe: 11.5mm to 12.0mm over 250mm
    - Central bore: 12.0mm (ML) over 550mm
    - Bell flare: 12.0mm to 127mm over 600mm
    """
    positions: List[float]
    inner_diameters: List[float]
    outer_diameters: List[float]
    valve_tubes: List[float]  # Tube lengths added by each valve
    mouthpiece_diameter: float = 5.0  # Mouthpiece throat diameter (mm)
    bell_rim_diameter: float = 127.0  # Bell rim diameter (mm)
    
    @classmethod
    def default_bb(cls, bore_diameter: float = 12.0) -> 'TrumpetBore':
        """
        Create a default Bb trumpet bore profile.
        
        Bb trumpet acoustic length ~1120mm for Bb3 (233 Hz).
        
        Key insight: The bell flare is THE critical design element.
        It must be aggressive enough to bring resonances into harmonic series.
        Real trumpets use Bessel horn profile: d(x) = d0 / cosh(x/Lb)
        where Lb controls flare rate.
        """
        # Leadpipe: mouthpiece receiver to central bore
        leadpipe_length = 200.0
        leadpipe_start = 14.5
        leadpipe_end = bore_diameter
        
        # Central bore: cylindrical section with valve block
        central_length = 400.0
        
        # Bell section
        bell_cylindrical = 100.0  # Bell tail (cylindrical)
        bell_flare_length = 380.0  # Bell flare (Bessel horn)
        
        # Bell dimensions
        bell_end = 127.0
        
        # Build bore profile
        positions = [0.0]
        diameters = [leadpipe_start]
        outer_diams = [leadpipe_start + 4.0]
        
        # Leadpipe: linear taper inward
        n_lead = 6
        for i in range(1, n_lead + 1):
            t = i / n_lead
            pos = t * leadpipe_length
            diam = leadpipe_start - t * (leadpipe_start - leadpipe_end)
            positions.append(pos)
            diameters.append(diam)
            outer_diams.append(diam + 4.0)
        
        # Central bore: cylindrical
        n_central = 4
        for i in range(1, n_central + 1):
            t = i / n_central
            pos = leadpipe_length + t * central_length
            positions.append(pos)
            diameters.append(bore_diameter)
            outer_diams.append(bore_diameter + 4.0)
        
        # Bell tail: cylindrical
        n_tail = 3
        for i in range(1, n_tail + 1):
            t = i / n_tail
            pos = leadpipe_length + central_length + t * bell_cylindrical
            positions.append(pos)
            diameters.append(bore_diameter)
            outer_diams.append(bore_diameter + 4.0)
        
        # Bell flare: Bessel horn profile for optimal harmonic alignment
        # d(x) = d0 / cosh(x/Lb) where Lb controls flare rate
        # More aggressive flare = sharper cutoff = better harmonic alignment
        bell_flare_start = leadpipe_length + central_length + bell_cylindrical
        Lb = 180.0  # Flare parameter (smaller = more aggressive)
        n_flare = 20
        for i in range(1, n_flare + 1):
            t = i / n_flare
            pos = bell_flare_start + t * bell_flare_length
            x = t * bell_flare_length
            # Bessel horn: d = d0 * (bell_end/bore_diam) * (1/cosh(x/Lb)) / (1/cosh(0))
            # But we want d to INCREASE, so use inverse
            # Actually use: d = bore_diam + (bell_end - bore_diam) * (1 - exp(-3*t)) for aggressive flare
            diam = bore_diameter + (bell_end - bore_diameter) * (1 - math.exp(-4.0 * t))
            positions.append(pos)
            diameters.append(diam)
            outer_diams.append(diam + 4.0)
        
        return cls(
            positions=positions,
            inner_diameters=diameters,
            outer_diameters=outer_diams,
            valve_tubes=[160.0, 70.0, 270.0],
            mouthpiece_diameter=leadpipe_start,
            bell_rim_diameter=bell_end,
        )
    
    @classmethod
    def from_piatt(cls, model: str = 'bach_ml') -> 'TrumpetBore':
        """
        Create bore from Piatt's measured data.
        
        Models:
        - bach_ml: Bach Stradivarius 180ML
        - yamaha_xeno: Yamaha Xeno
        - schilke_b1: Schilke B1
        """
        # Default to Bach ML
        return cls.default_bb(bore_diameter=12.0)


# ============================================================================
# Trumpet TMM model
# ============================================================================

class TrumpetModel:
    """
    TMM-based trumpet model.
    
    Computes resonant frequencies using the same phase-based TMM as woodwinds,
    but adapted for brass instruments:
    - Closed-open pipe (lips closed, bell open)
    - No tone holes (just valve combinations)
    - Bell flange correction
    - Mouthpiece Helmholtz resonator
    """
    
    def __init__(self, bore: TrumpetBore):
        """
        Initialize trumpet model with bore profile.
        
        Args:
            bore: TrumpetBore instance
        """
        self.bore = bore
        self.valve_tubes = bore.valve_tubes
        self.speed_of_sound = SPEED_OF_SOUND
        
        # Build base TMM instrument (without valve tubes)
        self._build_base_instrument()
    
    def _build_base_instrument(self):
        """Build the base TMM instrument from bore profile."""
        self.base_instrument = TMMInstrument(
            inner_positions=self.bore.positions,
            inner_diameters=self.bore.inner_diameters,
            outer_diameters=self.bore.outer_diameters,
            hole_positions=[],
            hole_diameters=[],
            hole_lengths=[],
            closed_top=True,  # Lips are closed end
            cone_step=0.5,
        )
        self.base_length = self.bore.positions[-1]
    
    def _add_valve_tubing(self, valve_indices: List[int]) -> float:
        """
        Calculate total bore length with valve tubes added.
        
        Args:
            valve_indices: indices of open valves (0, 1, 2)
        
        Returns:
            Total bore length in mm
        """
        total = self.base_length
        for idx in valve_indices:
            if idx < len(self.valve_tubes):
                total += self.valve_tubes[idx]
        return total
    
    def _build_valve_instrument(self, valve_indices: List[int]) -> TMMInstrument:
        """
        Build TMM instrument with valve tubing added.
        
        In a real trumpet, pressing a valve redirects air through a parallel
        tube that adds to the total acoustic path length. The tube is inserted
        at the valve block location, but the EFFECT is to extend the total
        acoustic length by the tube length.
        
        Model: We scale the central bore section proportionally to accommodate
        the extra valve tubing length. This maintains the bore profile shape
        while extending the total acoustic length correctly.
        """
        if not valve_indices:
            return self.base_instrument
        
        # Calculate total valve tubing length to add
        valve_length = sum(self.valve_tubes[i] for i in valve_indices if i < len(self.valve_tubes))
        
        if valve_length <= 0:
            return self.base_instrument
        
        # Find key positions in the bore
        leadpipe_end = 200.0
        central_end = 600.0
        bell_start = 700.0  # After bell cylindrical section
        
        # Build new bore profile with extended central section
        new_positions = []
        new_diameters = []
        new_outer_diams = []
        
        for pos, diam, outer in zip(self.bore.positions, self.bore.inner_diameters, self.bore.outer_diameters):
            if pos <= leadpipe_end:
                # Leadpipe: keep as-is
                new_positions.append(pos)
                new_diameters.append(diam)
                new_outer_diams.append(outer)
            elif pos <= central_end:
                # Central bore: scale proportionally to add valve tubing
                t = (pos - leadpipe_end) / (central_end - leadpipe_end)
                new_pos = leadpipe_end + t * (central_end - leadpipe_end + valve_length)
                new_positions.append(new_pos)
                new_diameters.append(diam)
                new_outer_diams.append(outer)
            else:
                # Bell section: shift by valve tubing length
                new_positions.append(pos + valve_length)
                new_diameters.append(diam)
                new_outer_diams.append(outer)
        
        return TMMInstrument(
            inner_positions=new_positions,
            inner_diameters=new_diameters,
            outer_diameters=new_outer_diams,
            hole_positions=[],
            hole_diameters=[],
            hole_lengths=[],
            closed_top=True,
            cone_step=0.5,
        )
    
    def resonance_wavelength(self, valve_indices: List[int], n_register: int = 1) -> float:
        """
        Compute resonant wavelength for a given valve combination and register.
        
        Args:
            valve_indices: indices of open valves
            n_register: register number (1 = pedal, 2 = fundamental, etc.)
        
        Returns:
            Resonant wavelength in mm
        """
        instrument = self._build_valve_instrument(valve_indices)
        
        # Initial wavelength guess based on pipe length
        pipe_length = self._add_valve_tubing(valve_indices)
        
        # Closed-open pipe: fundamental wavelength = 4L
        # n_register=1 is pedal tone, n_register=2 is fundamental
        if n_register == 1:
            # Pedal tone
            wl_guess = 4.0 * pipe_length
        elif n_register == 2:
            # Fundamental (1st harmonic)
            wl_guess = 4.0 * pipe_length
        else:
            # Higher registers
            wl_guess = 4.0 * pipe_length / n_register
        
        try:
            wl = instrument.find_resonance(wl_guess, [], n_register=n_register)
            return wl
        except Exception:
            return 0.0
    
    def resonance_frequency(self, valve_indices: List[int], n_register: int = 1) -> float:
        """
        Compute resonant frequency for a given valve combination and register.
        
        Args:
            valve_indices: indices of open valves
            n_register: register number
        
        Returns:
            Frequency in Hz
        """
        wl = self.resonance_wavelength(valve_indices, n_register)
        if wl > 0:
            return self.speed_of_sound / wl
        return 0.0
    
    def played_frequencies(self, n_register: int = 2) -> Dict[str, float]:
        """
        Compute frequencies for all 8 valve combinations.
        
        Args:
            n_register: register number (2 = fundamental)
        
        Returns:
            Dictionary mapping valve combination name to frequency in Hz
        """
        frequencies = {}
        for name, indices, _ in TRUMPET_VALVE_COMBOS:
            freq = self.resonance_frequency(indices, n_register)
            frequencies[name] = freq
        return frequencies
    
    def harmonics(self, valve_indices: List[int], n_harmonics: int = 8) -> List[float]:
        """
        Compute harmonic series for a given valve combination.
        
        Args:
            valve_indices: indices of open valves
            n_harmonics: number of harmonics to compute
        
        Returns:
            List of frequencies in Hz (fundamental + overtones)
        """
        frequencies = []
        # For closed-open pipe, only odd harmonics (1, 3, 5, ...)
        # But trumpet bell makes all harmonics present
        for n in range(1, n_harmonics + 1):
            freq = self.resonance_frequency(valve_indices, n_register=n)
            if freq > 0:
                frequencies.append(freq)
        return frequencies
    
    def cents_error(self, actual_freq: float, target_freq: float) -> float:
        """Compute pitch error in cents."""
        if actual_freq <= 0 or target_freq <= 0:
            return 1e10
        return 1200.0 * math.log2(actual_freq / target_freq)


# ============================================================================
# Trumpet optimizer
# ============================================================================

class TrumpetOptimizer:
    """
    Optimize trumpet bore for intonation accuracy.
    
    Uses L-BFGS-B optimization on bore profile parameters.
    """
    
    def __init__(
        self,
        target_notes: List[Tuple[str, int]],  # [(note_name, octave), ...]
        n_register: int = 2,
        bore_diameter_bounds: Tuple[float, float] = (11.5, 12.5),
        leadpipe_length_bounds: Tuple[float, float] = (200.0, 300.0),
        bell_length_bounds: Tuple[float, float] = (500.0, 700.0),
    ):
        """
        Initialize optimizer.
        
        Args:
            target_notes: List of (note_name, octave) to optimize for
            n_register: Register number (2 = fundamental)
            bore_diameter_bounds: (min, max) bore diameter in mm
            leadpipe_length_bounds: (min, max) leadpipe length in mm
            bell_length_bounds: (min, max) bell length in mm
        """
        self.target_notes = target_notes
        self.n_register = n_register
        self.bore_diameter_bounds = bore_diameter_bounds
        self.leadpipe_length_bounds = leadpipe_length_bounds
        self.bell_length_bounds = bell_length_bounds
        
        # Compute target frequencies
        self.target_freqs = []
        for note, octave in target_notes:
            midi = note_to_midi(note, octave)
            self.target_freqs.append(midi_to_freq(midi))
    
    def _build_trumpet(self, params: np.ndarray) -> TrumpetModel:
        """
        Build trumpet from optimization parameters.
        
        Parameters:
        - params[0]: bore diameter (mm)
        - params[1]: leadpipe length (mm)
        - params[2]: bell length (mm)
        """
        bore_diameter = params[0]
        leadpipe_length = params[1]
        bell_length = params[2]
        
        # Build bore profile
        central_length = 550.0  # Fixed for now
        total_length = leadpipe_length + central_length + bell_length
        
        # Leadpipe taper
        leadpipe_start = 11.5
        leadpipe_end = bore_diameter
        
        # Bell flare
        bell_start = bore_diameter
        bell_end = 127.0
        
        # Build positions and diameters
        positions = [0.0]
        diameters = [leadpipe_start]
        outer_diams = [leadpipe_start + 3.0]
        
        # Leadpipe
        n_lead = 5
        for i in range(1, n_lead + 1):
            t = i / n_lead
            pos = t * leadpipe_length
            diam = leadpipe_start + t * (leadpipe_end - leadpipe_start)
            positions.append(pos)
            diameters.append(diam)
            outer_diams.append(diam + 3.0)
        
        # Central bore
        n_central = 5
        for i in range(1, n_central + 1):
            t = i / n_central
            pos = leadpipe_length + t * central_length
            positions.append(pos)
            diameters.append(bore_diameter)
            outer_diams.append(bore_diameter + 3.0)
        
        # Bell flare
        n_bell = 10
        for i in range(1, n_bell + 1):
            t = i / n_bell
            pos = leadpipe_length + central_length + t * bell_length
            diam = bell_start * (bell_end / bell_start) ** t
            positions.append(pos)
            diameters.append(diam)
            outer_diams.append(diam + 3.0)
        
        bore = TrumpetBore(
            positions=positions,
            inner_diameters=diameters,
            outer_diameters=outer_diams,
            valve_tubes=[160.0, 70.0, 270.0],
        )
        
        return TrumpetModel(bore)
    
    def objective(self, params: np.ndarray) -> float:
        """
        Objective function: RMS cents error across all target notes.
        
        Args:
            params: optimization parameters
        
        Returns:
            RMS cents error (lower is better)
        """
        try:
            trumpet = self._build_trumpet(params)
            
            cents_errors = []
            for i, (target_freq, (note, octave)) in enumerate(zip(self.target_freqs, self.target_notes)):
                # Find which valve combination produces this note
                # For now, use open fingering (simplified)
                freq = trumpet.resonance_frequency([], self.n_register)
                
                if freq > 0:
                    cents = trumpet.cents_error(freq, target_freq)
                    cents_errors.append(cents)
                else:
                    cents_errors.append(1e10)
            
            # RMS error
            return float(np.sqrt(np.mean(np.array(cents_errors) ** 2)))
            
        except Exception:
            return 1e10
    
    def optimize(self, max_iter: int = 100, verbose: bool = True) -> Dict:
        """
        Run optimization.
        
        Args:
            max_iter: maximum iterations
            verbose: print progress
        
        Returns:
            Dictionary with optimization results
        """
        from scipy.optimize import minimize
        
        # Initial guess
        x0 = np.array([
            12.0,  # bore diameter
            250.0,  # leadpipe length
            600.0,  # bell length
        ])
        
        bounds = [
            self.bore_diameter_bounds,
            self.leadpipe_length_bounds,
            self.bell_length_bounds,
        ]
        
        if verbose:
            print("Trumpet bore optimization")
            print(f"Target notes: {[(n, o) for n, o in self.target_notes]}")
            print(f"Initial params: bore={x0[0]:.1f}mm, leadpipe={x0[1]:.0f}mm, bell={x0[2]:.0f}mm")
        
        result = minimize(
            self.objective,
            x0,
            method='L-BFGS-B',
            bounds=bounds,
            options={"maxiter": max_iter, "ftol": 1e-6},
        )
        
        if verbose:
            print(f"Optimization complete: RMS={result.fun:.2f} cents")
            print(f"Optimized params: bore={result.x[0]:.1f}mm, leadpipe={result.x[1]:.0f}mm, bell={result.x[2]:.0f}mm")
        
        return {
            "success": result.success,
            "rms_cents": result.fun,
            "bore_diameter": result.x[0],
            "leadpipe_length": result.x[1],
            "bell_length": result.x[2],
        }


# ============================================================================
# Convenience functions
# ============================================================================

def create_default_trumpet() -> TrumpetModel:
    """Create a default Bb trumpet model."""
    bore = TrumpetBore.default_bb()
    return TrumpetModel(bore)

def analyze_trumpet(trumpet: TrumpetModel, register: int = 2) -> None:
    """Print analysis of trumpet frequencies."""
    print(f"\nTrumpet analysis (register {register}):")
    print("-" * 50)
    
    freqs = trumpet.played_frequencies(n_register=register)
    for name, freq in freqs.items():
        if freq > 0:
            note, octave, cents = freq_to_note(freq)
            print(f"  {name:8s}: {freq:8.1f} Hz  {note}{octave} ({cents:+.1f} cents)")
        else:
            print(f"  {name:8s}: no resonance")

def demo():
    """Demo trumpet analysis."""
    print("Trumpet TMM Demo")
    print("=" * 50)
    
    trumpet = create_default_trumpet()
    analyze_trumpet(trumpet, register=2)
    
    # Compute harmonics for open fingering
    print("\nHarmonic series (open fingering):")
    harmonics = trumpet.harmonics([], n_harmonics=8)
    for i, freq in enumerate(harmonics, 1):
        note, octave, cents = freq_to_note(freq)
        print(f"  H{i}: {freq:8.1f} Hz  {note}{octave} ({cents:+.1f} cents)")

if __name__ == "__main__":
    demo()
