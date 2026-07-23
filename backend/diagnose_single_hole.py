"""Single-hole frequency sweep: does the TMM model correctly predict
how a single open hole shifts the resonant frequency?

For open-open tubes: opening a hole at position p should shorten the
effective tube and raise the frequency. The expected position for a
target frequency f is roughly p = L - c/(2*f).
"""
import sys, os, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND

c = SPEED_OF_SOUND

INSTRUMENTS = [
    ("Soprano sax", 6.0, 20.0, 6.5, 3.0, 371, 466.2, 880.0, False),
    ("Xaphoon", 7.0, 20.0, 6.5, 3.0, 662, 261.6, 493.9, False),
    ("Alto sax", 8.5, 26.0, 7.5, 3.5, 556, 311.1, 587.3, False),
]

for name, br, od, hd, hl, L, f_low, f_high, closed_top in INSTRUMENTS:
    print(f"\n{'='*60}")
    print(f"{name}: bore_r={br}mm, L={L}mm")
    print(f"{'='*60}")

    bore_radii = np.full(8, br)

    # All-closed resonance
    inst = tmm_instrument_from_radii(bore_radii, L, [], [], [], od, closed_top, 0.5)
    wl_closed = inst.find_resonance(c / f_low, [], 2)
    f_closed = inst.frequency_from_wavelength(wl_closed)
    print(f"  All-closed: {f_closed:.1f} Hz (target: {f_low:.1f})")

    # Sweep single hole position for highest target
    # Expected: p = L - c/(2*f_high)
    p_expected = L - c / (2.0 * f_high)
    print(f"\n  Sweeping single hole for {f_high:.1f} Hz:")
    print(f"  Expected position: {p_expected:.0f}mm (from L - c/(2f))")

    positions = np.linspace(50, L - 50, 30)
    results = []
    for pos in positions:
        try:
            inst = tmm_instrument_from_radii(
                bore_radii, L, [pos], [hd], [hl], od, closed_top, 0.5
            )
            wl = inst.find_resonance(c / f_high, ["open"], 2)
            f = inst.frequency_from_wavelength(wl)
            err = 1200.0 * math.log2(f / f_high)
            results.append((pos, f, err))
            marker = " <--" if abs(err) < 10 else ""
            print(f"    pos={pos:6.0f}mm  f={f:7.1f}Hz  err={err:+7.1f}c{marker}")
        except:
            print(f"    pos={pos:6.0f}mm  FAILED")

    # Find closest to target
    if results:
        best = min(results, key=lambda r: abs(r[2]))
        print(f"\n  Best: pos={best[0]:.0f}mm, f={best[1]:.1f}Hz, err={best[2]:+.1f}c")

        # Now test: what happens when we add a SECOND hole at the expected position for
        # the second-highest target?
        f2 = f_high * 0.9  # roughly one semitone down
        p2_expected = L - c / (2.0 * f2)
        print(f"\n  Two-hole test: hole1={best[0]:.0f}mm (for {f_high:.0f}Hz), "
              f"hole2={p2_expected:.0f}mm (for {f2:.0f}Hz)")
        try:
            inst = tmm_instrument_from_radii(
                bore_radii, L,
                [best[0], p2_expected], [hd, hd], [hl, hl],
                od, closed_top, 0.5
            )
            # Test both fingerings
            for fing_label, fing in [
                ("only hole1 open", ["open", "closed"]),
                ("only hole2 open", ["closed", "open"]),
                ("both open", ["open", "open"]),
                ("all closed", ["closed", "closed"]),
            ]:
                wl = inst.find_resonance(c / f_high, fing, 2)
                f = inst.frequency_from_wavelength(wl)
                err = 1200.0 * math.log2(f / f_high)
                print(f"    {fing_label:25s}: f={f:7.1f}Hz err={err:+7.1f}c")
        except Exception as e:
            print(f"    FAILED: {e}")
