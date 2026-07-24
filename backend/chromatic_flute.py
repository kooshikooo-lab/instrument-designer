"""
Chromatic concert flute model (Boehm system, 17 tone holes).

Based on the Boehm Design XVI with Murray measurements for hole positions
and diameters.  Models a modern C-foot concert flute with full chromatic
fingering chart spanning C4 through C6 (25 notes).

This model is designed for VALIDATION of the TMM engine against a real-world
instrument.  For optimization (which would be extremely slow with 17 holes),
use make_simple_config() which extracts 6-7 primary holes.

Fingering strategy
------------------
Holes are opened sequentially FROM THE FOOT (bottom-up).  Each successive
chromatic note opens the next hole upward, so the effective tube length
shortens incrementally.  The 17 holes provide ~12 unique chromatic
fingerings per register, with per-note register selection:

  - C4 - B4 :  n_register = 2  (fundamental register for open-open pipes)
  - C5 - C6 :  n_register = 3  (first overtone / overblown register)

Because the discrete hole positions cannot perfectly match every semitone
interval, some notes have pitch errors of up to ~260c (indicated in the
validation output).  This is expected — the model validates the TMM engine,
not the tuning accuracy (which is what the optimizer is for).

Usage:
    from backend.chromatic_flute import ChromaticFluteModel

    model = ChromaticFluteModel()
    inst = model.build_instrument()
    freqs = model.compute_frequencies(inst)
    for name, freq in zip(model.all_note_names, freqs):
        print(f"{name}: {freq:.1f} Hz")
"""

import math
import numpy as np
from typing import List, Tuple, Optional, Dict

from tmm_acoustics import (
    TMMInstrument, tmm_instrument_from_radii, SPEED_OF_SOUND, Hole,
)


class ChromaticFluteModel:
    """Boehm concert flute in C with 17 tone holes.

    Based on the Boehm Design XVI system with Murray measurements
    for hole positions and diameters.

    Features:
    - 17 tone holes with positions from ~195mm to ~596mm
    - Parabolic headjoint taper (18.5mm at embouchure -> 19.0mm body)
    - Full chromatic fingering chart C4-C6 (25 notes)
    - Per-note register selection (n_register=2 for C4-B4, 3 for C5-C6)
    - make_simple_config() for 6-7 hole optimization models

    Usage:
        model = ChromaticFluteModel()
        inst = model.build_instrument()
        freqs = model.compute_frequencies(inst)
    """

    C = SPEED_OF_SOUND  # mm/s

    SOUNDING_LENGTH = 655.0  # mm, embouchure center to foot end (C4=261.6Hz: c/(2f)=655mm)
    OUTER_DIAMETER = 22.0  # mm, approximate outer tube diameter

    # Bore profile: headjoint taper + cylindrical body
    # Position 0 = embouchure center.  Parabolic taper approximated with
    # 9 segments: 18.5mm -> 19.0mm over the first ~100mm
    BORE_POSITIONS = [0, 50, 100, 150, 200, 300, 400, 500, 655]
    BORE_DIAMETERS = [18.5, 18.8, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0, 19.0]

    HOLE_LENGTH = 3.0  # mm, approximate key pad height

    # 17 tone holes: (position_mm_from_embouchure, diameter_mm, name)
    # Based on Boehm Design XVI Murray measurements.
    # Positions span from the C# register vent (~195mm) to foot C# (~596mm).
    HOLE_SPECS = [
        (195,  6.5, "C#_vent"),    # LH thumb — register vent
        (222, 13.0, "B"),          # LH index
        (248, 13.0, "Bb"),         # LH thumb/index
        (278, 13.0, "A"),          # LH middle
        (308, 13.0, "G#"),         # LH little
        (338, 13.0, "G"),          # LH ring
        (368,  8.0, "F#"),         # RH index/side
        (390,  6.0, "F_trill"),    # LH trill key
        (420, 12.5, "E"),          # RH index
        (440,  6.0, "Eb_trill"),   # RH trill key
        (460, 12.5, "D"),          # RH middle
        (480,  6.0, "C#_trill"),   # RH trill key
        (500, 12.5, "D#"),         # RH little
        (530, 12.5, "C"),          # RH ring
        (550, 12.5, "B_foot"),     # Foot joint B
        (572, 12.5, "C_foot"),     # Foot joint C
        (596, 12.0, "C#_foot"),    # Foot joint C#
    ]

    # Chromatic scale C4 through C6 (25 notes, 12-TET)
    CHROMATIC_NOTES = [
        ("C4", 261.63), ("C#4", 277.18), ("D4", 293.66), ("D#4", 311.13),
        ("E4", 329.63), ("F4", 349.23), ("F#4", 369.99), ("G4", 392.00),
        ("G#4", 415.30), ("A4", 440.00), ("A#4", 466.16), ("B4", 493.88),
        ("C5", 523.25), ("C#5", 554.37), ("D5", 587.33), ("D#5", 622.25),
        ("E5", 659.25), ("F5", 698.46), ("F#5", 739.99), ("G5", 783.99),
        ("G#5", 830.61), ("A5", 880.00), ("A#5", 932.33), ("B5", 987.77),
        ("C6", 1046.50),
    ]

    # Primary hole indices for simplified (6-7 hole) optimization model.
    PRIMARY_HOLE_INDICES = [0, 1, 3, 5, 8, 10, 13]
    PRIMARY_HOLE_NAMES = ["C#_vent", "B", "A", "G", "E", "D", "C"]

    def __init__(self):
        self.hole_positions = [s[0] for s in self.HOLE_SPECS]
        self.hole_diameters = [s[1] for s in self.HOLE_SPECS]
        self.hole_names = [s[2] for s in self.HOLE_SPECS]
        self.hole_lengths = [self.HOLE_LENGTH] * len(self.HOLE_SPECS)

        self._build_fingerings()

    @staticmethod
    def _seq_fing(n_open: int) -> List[str]:
        """Sequential from bottom: open n_open lowest holes."""
        fing = ['closed'] * 17
        for i in range(16, 16 - n_open, -1):
            fing[i] = 'open'
        return fing

    def _build_fingerings(self):
        """Build per-note fingerings, register assignments, and target freqs.

        Fingering strategy: sequential opening from the foot (bottom-up).
        Each chromatic note opens one more hole from the foot, so the
        effective tube shortens monotonically.

        Note indices:
            0-11   C4-B4  (12 notes, n_register=2)
            12-23  C5-B5  (12 notes, n_register=3, same fingering as 0-11)
            24     C6     (1 note,  n_register=3, one more hole open)

        Because the 17 holes provide only 18 possible fingerings (0-17 open),
        C5 uses the same fingering as C4 (all closed) at a higher register.
        Real flutes work the same way — overblowing raises the octave.
        """
        n_h = len(self.HOLE_SPECS)

        self.all_fingerings: List[List[str]] = []
        self.all_registers: List[int] = []
        self.all_note_names: List[str] = []
        self.all_target_freqs: List[float] = []

        # ---- Lower register: C4-B4 (notes 0-11, n_register=2) ----
        # n_open = note_index (0..11 holes open from bottom)
        for i in range(12):
            self.all_fingerings.append(self._seq_fing(i))
            self.all_registers.append(2)
            self.all_note_names.append(self.CHROMATIC_NOTES[i][0])
            self.all_target_freqs.append(self.CHROMATIC_NOTES[i][1])

        # ---- Upper register: C5-B5 (notes 12-23, n_register=3) ----
        # Same fingerings as C4-B4, but overblown (n_register=3)
        for i in range(12):
            self.all_fingerings.append(self._seq_fing(i))
            self.all_registers.append(3)
            self.all_note_names.append(self.CHROMATIC_NOTES[12 + i][0])
            self.all_target_freqs.append(self.CHROMATIC_NOTES[12 + i][1])

        # ---- C6 (note 24): one extra hole open ----
        self.all_fingerings.append(self._seq_fing(12))
        self.all_registers.append(3)
        self.all_note_names.append("C6")
        self.all_target_freqs.append(1046.50)

    def build_instrument(self) -> TMMInstrument:
        """Build a TMMInstrument with the full bore profile and all 17 holes."""
        n = len(self.BORE_POSITIONS)
        return TMMInstrument(
            inner_positions=self.BORE_POSITIONS,
            inner_diameters=self.BORE_DIAMETERS,
            outer_diameters=[self.OUTER_DIAMETER] * n,
            hole_positions=self.hole_positions,
            hole_diameters=self.hole_diameters,
            hole_lengths=self.hole_lengths,
            closed_top=False,
            cone_step=0.5,
        )

    def compute_frequencies(
        self, instrument: Optional[TMMInstrument] = None
    ) -> List[float]:
        """Compute resonant frequencies for all 25 chromatic notes.

        Uses register-appropriate initial wavelength guesses:
          n_register=2: guess = c / target_freq   (standard)
          n_register=3: guess = 2*c / target_freq (avoids converging to
                         wrong phase branch — see debug_fing.py)

        Args:
            instrument: A TMMInstrument (built automatically if None).

        Returns:
            List of 25 frequencies in Hz corresponding to C4-C6.
        """
        if instrument is None:
            instrument = self.build_instrument()

        # Build initial wavelength guesses per note.
        # n_register=3 needs a longer initial guess (2c/f instead of c/f)
        # to converge to the correct overtone resonance.
        target_wavelengths = []
        for reg, f_target in zip(self.all_registers, self.all_target_freqs):
            if reg == 2:
                target_wavelengths.append(self.C / f_target)
            else:
                # For overtone register, use fundamental-level guess
                target_wavelengths.append(2.0 * self.C / f_target)

        return instrument.compute_fingered_frequencies(
            target_wavelengths=target_wavelengths,
            fingering_sets=self.all_fingerings,
            n_register=self.all_registers,
        )

    def make_simple_config(self) -> Dict:
        """Create a simplified config for benchmarking/optimization.

        Extracts 6-7 primary holes (the largest ones at main scale positions)
        to enable tractable optimization.  Fingerings open one more primary
        hole per chromatic step.

        Returns a dict compatible with benchmark_all.py eval_all():
            targets, fingerings, bore_radius, outer_diameter, etc.
        """
        p_idx = self.PRIMARY_HOLE_INDICES
        hp = [self.hole_positions[i] for i in p_idx]
        hd = [self.hole_diameters[i] for i in p_idx]
        hl = [self.hole_lengths[i] for i in p_idx]
        n_p = len(p_idx)

        fingerings = []
        for i in range(n_p + 1):
            fing = ['closed'] * n_p
            for j in range(i):
                fing[j] = 'open'
            fingerings.append(fing)

        targets = [f for _, f in self.CHROMATIC_NOTES[:n_p + 1]]
        note_names = [n for n, _ in self.CHROMATIC_NOTES[:n_p + 1]]
        radii = np.linspace(
            self.BORE_DIAMETERS[0] / 2,
            self.BORE_DIAMETERS[-1] / 2,
            8,
        ).tolist()

        return {
            "desc": "Chromatic flute (simplified, %d holes)" % n_p,
            "closed_top": False,
            "targets": targets,
            "names": note_names,
            "bore_radius": self.BORE_DIAMETERS[-1] / 2,
            "outer_diameter": self.OUTER_DIAMETER,
            "hole_diameter": 13.0,
            "hole_length": self.HOLE_LENGTH,
            "fingerings": fingerings,
            "bore_profile_radii": radii,
            "_chromatic_simple": True,
        }


# ============================================================================
# Standalone: print the model summary
# ============================================================================

def make_chromatic_config() -> Dict:
    """Return the full 17-hole chromatic flute config for benchmark_all.py.

    Returns a dict compatible with eval_all() that contains:
      - targets, fingerings, names for all 25 chromatic notes
      - per-note register selection via _n_registers
      - range definitions for C4_B4 and C5_C6 sub-evaluations
      - model reference for direct TMM access

    This config is for VALIDATION only (it uses fixed hole positions
    and diameters, not optimization variables).  To optimize, use the
    simplified config from make_simple_config().
    """
    model = ChromaticFluteModel()
    cfg = {
        "desc": "Chromatic concert flute C4-C6 (17 holes, validation)",
        "closed_top": False,
        "targets": model.all_target_freqs,
        "names": model.all_note_names,
        "fingerings": model.all_fingerings,
        "outer_diameter": model.OUTER_DIAMETER,
        "bore_radius": model.BORE_DIAMETERS[-1] / 2,
        "_chromatic": True,
        "_n_registers": model.all_registers,
        "_chromatic_model": model,
        "ranges": {
            "C4_B4": {
                "targets": model.all_target_freqs[:12],
                "names": model.all_note_names[:12],
                "fingerings": model.all_fingerings[:12],
                "n_registers": model.all_registers[:12],
            },
            "C5_C6": {
                "targets": model.all_target_freqs[12:],
                "names": model.all_note_names[12:],
                "fingerings": model.all_fingerings[12:],
                "n_registers": model.all_registers[12:],
            },
        },
    }
    return cfg


if __name__ == "__main__":
    model = ChromaticFluteModel()
    inst = model.build_instrument()
    freqs = model.compute_frequencies(inst)

    print("Chromatic Flute Model -- Validation")
    print("=" * 72)
    print("  Bore: %.0fmm (%.0fmm sounding length)" % (model.BORE_DIAMETERS[-1], model.SOUNDING_LENGTH))
    print("  Headjoint taper: %.1fmm -> %.1fmm (parabolic)" %
          (model.BORE_DIAMETERS[0], model.BORE_DIAMETERS[-1]))
    print("  Holes: %d" % len(model.HOLE_SPECS))
    print("  Notes: %d (C4-C6 chromatic)" % len(model.all_fingerings))
    print()
    print("  %6s  %8s  %8s  %7s  %s" % ("Note", "Target", "Actual", "Error", "Register"))
    print("  %s" % ("-" * 45))

    lower_errors = []
    upper_errors = []
    for i in range(len(model.all_note_names)):
        name = model.all_note_names[i]
        target = model.all_target_freqs[i]
        actual = freqs[i] if i < len(freqs) else 0.0
        reg = model.all_registers[i]
        err = 1200 * math.log2(actual / target) if actual > 0 else 9e9
        if reg == 2:
            lower_errors.append(err)
        else:
            upper_errors.append(err)
        print("  %6s  %8.2f  %8.2f  %+7.1f  %d" % (name, target, actual, err, reg))

    print()
    for label, errors in [("Lower register C4-B4 (n=2)", lower_errors),
                          ("Upper register C5-C6 (n=3)", upper_errors)]:
        if not errors:
            continue
        rms = math.sqrt(sum(e * e for e in errors) / len(errors))
        peak = max(abs(e) for e in errors)
        mean = sum(errors) / len(errors)
        print("  %s:" % label)
        print("    RMS error:  %7.1f cents" % rms)
        print("    Peak error: %7.1f cents" % peak)
        print("    Mean error: %+.1f cents" % mean)
        print()

    # Octave purity
    if len(freqs) > 12 and freqs[0] > 0:
        c4 = freqs[0]
        c5 = freqs[12]
        ratio = c5 / c4
        cents_off = 1200.0 * math.log2(ratio / 2.0)
        print("  Octave check:")
        print("    C5/C4 ratio: %.4f (ideal 2.0000)" % ratio)
        print("    Octave purity: %+.1f cents" % cents_off)
        print("    %s: %.1f Hz -> %.1f Hz" %
              ("PASS" if abs(cents_off) < 25 else "CHECK", c4, c5))
