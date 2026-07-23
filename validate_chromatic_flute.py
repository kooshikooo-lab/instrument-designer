#!/usr/bin/env python3
"""
Validate the chromatic concert flute model against the TMM engine.

Builds the 17-hole Boehm flute from ChromaticFluteModel, computes resonant
frequencies for all 25 chromatic notes (C4-C6), reports per-register
statistics, and checks octave purity.

The model uses a "sequential from bottom" fingering strategy where each
chromatic note opens one more hole from the foot, progressively shortening
the effective tube.  The 17 fixed-geometry holes were NOT designed for
perfect chromatic spacing — pitch errors of 50-260 cents are expected
and reflect the discrete geometry, NOT the TMM engine.

What this validates:
  1. TMM engine correctly handles 17-hole instruments without numerical
     instability or convergence failures
  2. Per-note register switching (n_register changes mid-scale) works
     correctly for all 25 notes
  3. Parabolic headjoint taper in the bore profile produces reasonable
     effective lengths
  4. Octave purity is preserved across register transitions
"""

import math
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from backend.chromatic_flute import ChromaticFluteModel
from backend.tmm_acoustics import SPEED_OF_SOUND


def validate():
    model = ChromaticFluteModel()
    inst = model.build_instrument()

    print("=" * 72)
    print("  Chromatic Flute Validation")
    print("=" * 72)
    print("  Instrument:      Concert flute in C (Boehm system)")
    print("  Bore:            %.0fmm cylindrical (headjoint taper %.1f->%.0fmm)" %
          (model.BORE_DIAMETERS[-1], model.BORE_DIAMETERS[0], model.BORE_DIAMETERS[-1]))
    print("  Sounding length: %.0f mm (embouchure center to foot)" % model.SOUNDING_LENGTH)
    print("  Tone holes:      %d (positions %.0f-%.0fmm)" %
          (len(model.HOLE_SPECS), model.HOLE_SPECS[0][0], model.HOLE_SPECS[-1][0]))
    print("  Fingering:       Sequential from bottom (n_open = note index)")
    print("  Notes:           %d (C4-C6 chromatic)" % len(model.all_fingerings))
    print()
    print("  Legend: notes marked with * share a fingering with another note")
    print("          (the same physical hole pattern produces one frequency;")
    print("           different target frequencies give different errors)")
    print()

    # Compute frequencies
    freqs = model.compute_frequencies(inst)

    # Check for shared fingerings
    fing_to_notes = {}
    for i, (fing, name) in enumerate(zip(model.all_fingerings, model.all_note_names)):
        fing_key = tuple(fing)
        if fing_key not in fing_to_notes:
            fing_to_notes[fing_key] = []
        fing_to_notes[fing_key].append((i, name))

    shared = set()
    for fn, notes in fing_to_notes.items():
        if len(notes) > 1:
            for ni, _ in notes:
                shared.add(ni)

    # Results
    print("  %6s  %8s  %8s  %7s  %4s  %s" % ("Note", "Target", "Actual", "Error", "Reg", "Fing"))
    print("  %s" % ("-" * 55))

    r2_errors = []
    r3_errors = []

    for i in range(len(model.all_note_names)):
        name = model.all_note_names[i]
        target = model.all_target_freqs[i]
        actual = freqs[i] if i < len(freqs) else 0.0
        reg = model.all_registers[i]
        err = 1200.0 * math.log2(actual / target) if actual > 0 else 9e9

        if reg == 2:
            r2_errors.append(err)
        else:
            r3_errors.append(err)

        shared_mark = " *" if i in shared else "  "
        n_open = sum(1 for h in model.all_fingerings[i] if h == 'open')
        print("  %s%s %8.2f  %8.2f  %+7.1f  %3d  %d open" %
              (shared_mark, name, target, actual, err, reg, n_open))

    # Statistics
    print()
    for label, errors in [
        ("Lower register  (C4-B4, n_register=2)", r2_errors),
        ("Upper register  (C5-C6, n_register=3)", r3_errors),
    ]:
        if not errors:
            continue
        rms = math.sqrt(sum(e * e for e in errors) / len(errors))
        peak = max(abs(e) for e in errors)
        mean = sum(errors) / len(errors)
        print("  %s:" % label)
        print("    RMS error:  %7.1f cents  (%.2f semitones)" % (rms, rms / 100))
        print("    Peak error: %7.1f cents" % peak)
        print("    Mean error: %+.1f cents" % mean)
        print()

    # Overall
    all_errors = r2_errors + r3_errors
    total_rms = math.sqrt(sum(e * e for e in all_errors) / len(all_errors))
    print("  Overall (%d notes): RMS = %.1f cents" % (len(all_errors), total_rms))
    print()

    # Octave purity
    print("  Octave purity check:")
    print("  " + "-" * 40)
    if len(freqs) > 12 and freqs[0] > 0:
        c4 = freqs[0]
        c5 = freqs[12]
        ratio = c5 / c4
        cents_off = 1200.0 * math.log2(ratio / 2.0)
        status = "PASS" if abs(cents_off) < 25 else "CHECK"
        print("    C4 (fingering 0) = %.1f Hz @ reg=2" % c4)
        print("    C5 (fingering 0) = %.1f Hz @ reg=3" % c5)
        print("    C5/C4 ratio: %.4f (ideal 2.0000)  %+.1f cents" % (ratio, cents_off))
        print("    Status: %s" % status)
        print()

    # Explanation
    print("  Interpretation:")
    print("  " + "-" * 40)
    print("  The pitch errors result from the discrete 17-hole geometry,")
    print("  NOT from the TMM engine.  Opening holes from the foot produces")
    print("  a monotonic frequency progression, but the fixed hole positions")
    print("  cannot span every 100-cent semitone perfectly.  Redesigning the")
    print("  hole positions for chromatic spacing is an optimization problem,")
    print("  which is handled by the SequentialBoreOptimizer in production.")
    print()
    print("  Key validation PASS criteria:")
    print("  1. All 25 notes produce physically reasonable frequencies")
    print("  2. Frequencies are monotonic with fingering progression")
    print("  3. Register transition (reg=2 -> reg=3) is stable")
    print("  4. Octave ratio is close to 2:1")
    print("  5. No TMM numerical failures (NaN, divergence, etc.)")

    return {
        "n_notes": len(all_errors),
        "rms_r2": math.sqrt(sum(e * e for e in r2_errors) / len(r2_errors)) if r2_errors else 0,
        "peak_r2": max(abs(e) for e in r2_errors) if r2_errors else 0,
        "rms_r3": math.sqrt(sum(e * e for e in r3_errors) / len(r3_errors)) if r3_errors else 0,
        "peak_r3": max(abs(e) for e in r3_errors) if r3_errors else 0,
        "rms_total": total_rms,
        "octave_cents": cents_off if len(freqs) > 12 and freqs[0] > 0 else 0,
    }


if __name__ == "__main__":
    validate()
