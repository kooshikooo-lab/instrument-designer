"""Register-2 squeak suppression demo (bass clarinet).

An HR array whose stopband covers the all-closed register-2 (the 12th) removes
the resonance AT the squeak frequency: the phase at the squeak drops below the
resonance condition (2.0) and the note can no longer ring there. The same
compliance loading that opens the stopband retunes the register below it (the
documented low-register-extension coupling), so the demo also quantifies the
squeak-suppression vs low-register-shift trade-off across array designs.

Runs a phase-only model (no amplitude insertion loss): results are the
phase-resonance displacement picture, complementary to the extension / 12th-
intonation work. JSON -> test_output/metamaterial_register_suppression_results.json
(regenerable, uncommitted).
"""

import json
import math
import os

from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    all_closed_fingers,
    explicit_hr_array,
    make_hr_segment,
    make_low_clarinet,
    phase_at,
    registers,
    stopband_bounds,
)

KEY = "bass"
SQUEAK_BAND_TARGET = 2.0  # phase condition for the register-2 (12th) resonance

OUT = os.path.join("test_output", "metamaterial_register_suppression_results.json")


def first_crossing(inst, fingers, target_phase, fmin=25.0, fmax=1200.0, n=6000):
    """Lowest frequency where resonance_phase >= target_phase (scan + interp)."""
    lo_f = None
    lo_p = None
    for i in range(n):
        f = fmin + (fmax - fmin) * i / (n - 1)
        p = phase_at(inst, fingers, f)
        if p >= target_phase:
            if lo_f is None:
                return f
            return lo_f + (f - lo_f) * (target_phase - lo_p) / (p - lo_p)
        lo_f, lo_p = f, p
    return None


def cents(a, b):
    return 1200.0 * math.log2(a / b) if a and b else None


def main():
    fingers = all_closed_fingers(KEY)
    plain = make_low_clarinet(KEY)
    regs = registers(plain, fingers, 4)
    f1, squeak = regs[0], regs[1]
    L = LOW_CLARINETS[KEY]["bore_length_mm"]

    lines = []
    def out(s=""):
        print(s)
        lines.append(s)

    out(f"Bass clarinet (unfolded {L:.0f} mm x {LOW_CLARINETS[KEY]['bore_diameter_mm']:.0f} mm, closed top)")
    out(f"All-closed registers: f1={f1:.1f} Hz, 12th(squeak)={squeak:.1f} Hz, "
        f"reg3={regs[2]:.1f} Hz, reg4={regs[3]:.1f} Hz")
    out()

    # ---------------------------------------------------------------- Section 1
    out("Section 1 -- single design: stopband over the register-2 squeak")
    out("-" * 72)
    f0 = 0.8 * squeak
    spacing = 30.0
    bounds = stopband_bounds(KEY, f0, spacing)
    seg, _ = make_hr_segment(KEY, f0, spacing, start_frac=0.9)
    inst2 = make_low_clarinet(KEY, metamaterial_segments=[seg])
    inst1 = explicit_hr_array(KEY, f0, spacing, start_frac=0.9)
    out(f"Design: HR f0={f0:.1f} Hz (0.80x the squeak), spacing {spacing:.0f} mm, "
        f"closed-end segment; stopband [{bounds[0]:.1f}, {bounds[1]:.1f}] Hz"
        + (" (squeak INSIDE)" if bounds[0] <= squeak <= bounds[1] else " (squeak OUTSIDE!)"))
    for label, inst in [("plain", plain), ("L2 homogenized", inst2), ("L1 explicit", inst1)]:
        p12 = phase_at(inst, fingers, squeak)
        p1 = phase_at(inst, fingers, f1)
        f1x = first_crossing(inst, fingers, 1.0)
        out(f"  {label:14s} phase@12th={p12:.3f} (delta {SQUEAK_BAND_TARGET - p12:+.3f})  "
            f"phase@f1={p1:.3f}  f1'={f1x:.1f} Hz ({cents(f1x, f1):+.0f}c)")

    sweep = [40.0, 60.0, 90.0, 130.0, 180.0, 212.0, 250.0, 300.0, 360.0, 450.0]
    out(f"  phase vs frequency sweep ({' '.join(str(int(x)) for x in sweep)} Hz):")
    for label, inst in [("plain", plain), ("L2", inst2), ("L1", inst1)]:
        out(f"    {label:4s} " + " ".join(f"{phase_at(inst, fingers, f):.2f}" for f in sweep))
    out()

    # ---------------------------------------------------------------- Section 2
    out("Section 2 -- design sweep (f0 ratio vs spacing)")
    out("-" * 72)
    out(f"  {'ratio':>5s} {'spacing':>8s} {'band lo':>8s} {'band hi':>8s} "
        f"{'in band':>7s} {'L1 d(12th)':>10s} {'L2 d(12th)':>10s} {'L1 d(f1)c':>9s} {'L2 d(f1)c':>9s}")
    sweep_rows = []
    for ratio in (0.7, 0.8, 0.9, 1.0):
        for sp in (30.0, 60.0, 100.0):
            f0 = ratio * squeak
            b = stopband_bounds(KEY, f0, sp)
            inb = b[0] is not None and b[0] <= squeak <= b[1]
            d1 = SQUEAK_BAND_TARGET - phase_at(explicit_hr_array(KEY, f0, sp, start_frac=0.9), fingers, squeak)
            seg, _ = make_hr_segment(KEY, f0, sp, start_frac=0.9)
            d2 = SQUEAK_BAND_TARGET - phase_at(make_low_clarinet(KEY, metamaterial_segments=[seg]), fingers, squeak)
            f1_L1 = first_crossing(explicit_hr_array(KEY, f0, sp, start_frac=0.9), fingers, 1.0)
            f1_L2 = first_crossing(make_low_clarinet(KEY, metamaterial_segments=[seg]), fingers, 1.0)
            row = {
                "f0_ratio": ratio, "spacing_mm": sp, "band": None if b[0] is None else [round(b[0], 1), round(b[1], 1)],
                "squeak_in_band": inb,
                "L1_suppression_delta": round(d1, 4), "L2_suppression_delta": round(d2, 4),
                "L1_f1_cents": round(cents(f1_L1, f1), 1) if f1_L1 else None,
                "L2_f1_cents": round(cents(f1_L2, f1), 1) if f1_L2 else None,
            }
            sweep_rows.append(row)
            out(f"  {ratio:5.2f} {sp:8.0f} {('-' if b[0] is None else round(b[0],1)):>8} "
                f"{('-' if b[1] is None else round(b[1],1)):>8} {str(inb):>7} "
                f"{d1:10.3f} {d2:10.3f} {cents(f1_L1, f1):9.0f} {cents(f1_L2, f1):9.0f}")
    out()

    # ---------------------------------------------------------------- Section 3
    out("Section 3 -- L1 trade-off curve (squeak suppression vs low-register shift)")
    out("-" * 72)
    out(f"  {'ratio':>5s} {'L1 d(12th)':>10s} {'L1 f1 cents':>12s} {'squeak in band':>15s}")
    curve = []
    for ratio in (0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00, 1.10):
        f0 = ratio * squeak
        sp = 30.0
        b = stopband_bounds(KEY, f0, sp)
        inst1 = explicit_hr_array(KEY, f0, sp, start_frac=0.9)
        d = SQUEAK_BAND_TARGET - phase_at(inst1, fingers, squeak)
        f1x = first_crossing(inst1, fingers, 1.0)
        c = cents(f1x, f1)
        inb = b[0] is not None and b[0] <= squeak <= b[1]
        curve.append({"ratio": ratio, "L1_suppression_delta": round(d, 4), "f1_cents": round(c, 1), "in_band": inb})
        out(f"  {ratio:5.2f} {d:10.3f} {c:12.0f} {str(inb):>15}")
    out()

    # ---------------------------------------------------------------- Finding
    out("Finding")
    out("-" * 72)
    out("- A stopband covering the register-2 squeak kills the resonance AT the squeak: "
        "the phase drops from 2.000 (plain) to <2.0 (arrayed), so the squeak no longer rings.")
    out("- L2 (homogenized) suppresses by a fixed margin (~0.15, closed-end segment) at any "
        "array depth; L1 (explicit) reaches stronger margins (~0.3-0.5) when f0 is tuned "
        "0.7-0.9x the squeak, i.e. with the squeak comfortably inside the band.")
    out("- Warning: tuning f0 EXACTLY at the squeak is a blind spot for L1 (phase returns to "
        "2.000) - the squeak sits at the band's lower edge, not inside it.")
    out("- Cost: the compliance tail below f0 retunes the low register - f1 drops by "
        "-300..-600c (L2) or -1000..-1700c (L1) at the strongest suppression. The deeper the "
        "squeak suppression, the bigger the low-register shift (same coupling as the "
        "extension / 12th-intonation work, seen from the register-filter side).")
    out()

    results = {
        "key": KEY,
        "plain_registers_hz": [round(r, 2) for r in regs],
        "squeak_hz": round(squeak, 2),
        "section1_design": {"f0_ratio": 0.8, "spacing_mm": 30.0, "stopband_hz": bounds},
        "section2_sweep": sweep_rows,
        "section3_l1_curve": curve,
        "finding": lines,
    }
    os.makedirs("test_output", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    out(f"wrote {OUT}")


if __name__ == "__main__":
    main()
