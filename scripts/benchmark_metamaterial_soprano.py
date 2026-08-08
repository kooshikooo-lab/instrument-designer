"""Soprano-clarinet metamaterial demo (standalone).

Applies the acoustic-metamaterial machinery (L1 explicit HR array / L2
homogenized segment) to a Bb soprano clarinet (600 mm x 15 mm bore) to
demonstrate family generality. Runs:
- Baseline plain-tube registers
- Register-2 squeak suppression (the all-closed 12th at ~429 Hz)
- L1 trade-off curve (suppression margin vs low-register shift)

Run: python scripts/benchmark_metamaterial_soprano.py
"""

import json
import math
import os

from backend.metamaterial_low_clarinets import (
    SPEED_OF_SOUND,
    cavity_volume_for_f0,
    phase_at,
    registers,
)
from backend.tmm_acoustics import (
    TMMInstrument,
    MetamaterialSegment,
    MetamaterialSideBranch,
)

OUT = os.path.join("test_output", "metamaterial_soprano_demo_results.json")


def main():
    # Soprano Bb clarinet spec (written low E3 = concert D3 ≈ 146.8 Hz)
    L = 600.0
    D = 15.0
    OD = 25.0
    fingers = []  # no holes for this demo

    plain = TMMInstrument(
        inner_positions=[0, L],
        inner_diameters=[D, D],
        outer_diameters=[OD, OD],
        hole_positions=[],
        hole_diameters=[],
        hole_lengths=[],
        closed_top=True,
        speed_of_sound=SPEED_OF_SOUND,
    )

    regs_plain = registers(plain, fingers, 4)
    f1, squeak, reg3 = regs_plain[0], regs_plain[1], regs_plain[2]
    print(f"Soprano Bb (unfolded {L:.0f} mm x {D:.0f} mm, closed top)")
    print(f"All-closed registers: f1={f1:.1f} Hz, 12th(squeak)={squeak:.1f} Hz, "
          f"reg3={reg3:.1f} Hz, reg4={regs_plain[3]:.1f} Hz")
    print()

    # ---- Section 1: register-2 squeak suppression (at the all-closed 12th) ----
    print("Section 1 -- register-2 squeak suppression (stopband over the 12th)")
    print("-" * 72)
    f0 = 0.85 * squeak
    spacing = 30.0
    start_frac = 0.9  # closed-end segment
    start = L * start_frac
    end = L
    v = cavity_volume_for_f0(f0)

    def _gamma2(freq_hz, bore_diameter_mm, v_mm3, neck_r_mm, neck_l_mm,
                spacing_mm, speed_of_sound, rho=1.2e-9):
        c = speed_of_sound
        omega = 2.0 * math.pi * freq_hz
        a = math.pi * (bore_diameter_mm / 2.0) ** 2
        s_n = math.pi * neck_r_mm ** 2
        l_n = neck_l_mm + 1.45 * neck_r_mm
        m_ac = rho * l_n / s_n
        c_ac = v_mm3 / (rho * c * c)
        denom = omega * m_ac - 1.0 / (omega * c_ac)
        if denom == 0.0:
            return float("inf")
        return -omega * omega / (c * c) + omega * rho / (a * spacing_mm * denom)

    def soprano_stopband_bounds(f0_hz, spacing_mm, neck_r=4.0, neck_l=8.0):
        def g(f):
            return _gamma2(f, D, v, neck_r, neck_l, spacing_mm, SPEED_OF_SOUND)
        lo, hi = f0_hz * (1.0 + 1e-6), max(f0_hz * 100.0, 1e6)
        if g(lo) <= 0.0:
            return (None, None)
        for _ in range(140):
            mid = 0.5 * (lo + hi)
            if g(mid) > 0.0:
                lo = mid
            else:
                hi = mid
        return (f0_hz, lo)

    sb = soprano_stopband_bounds(f0, spacing)

    # L2 homogenized segment
    mb = MetamaterialSideBranch(position_mm=start, neck_radius_mm=4.0,
                                neck_length_mm=8.0, cavity_volume_mm3=v)
    soprano_seg = MetamaterialSegment(start, end, mb, spacing)
    inst2 = TMMInstrument(
        inner_positions=[0, L], inner_diameters=[D, D], outer_diameters=[OD, OD],
        hole_positions=[], hole_diameters=[], hole_lengths=[],
        closed_top=True, speed_of_sound=SPEED_OF_SOUND,
        metamaterial_segments=[soprano_seg],
    )

    # L1 explicit array
    slots = []
    for i in range(int((end - start) // spacing)):
        pos = start + i * spacing + spacing / 2.0
        if pos > end:
            break
        slots.append(MetamaterialSideBranch(position_mm=pos, neck_radius_mm=4.0,
                                            neck_length_mm=8.0, cavity_volume_mm3=v))
    inst1 = TMMInstrument(
        inner_positions=[0, L], inner_diameters=[D, D], outer_diameters=[OD, OD],
        hole_positions=[], hole_diameters=[], hole_lengths=[],
        closed_top=True, speed_of_sound=SPEED_OF_SOUND,
        meta_slots=slots,
    )

    print(f"Design: HR f0={f0:.1f} Hz (0.85x the squeak), spacing {spacing:.0f} mm, "
          f"closed-end segment; stopband [{sb[0]:.1f}, {sb[1]:.1f}] Hz")
    for label, inst in [("plain", plain), ("L2 homogenized", inst2), ("L1 explicit", inst1)]:
        p12 = phase_at(inst, fingers, squeak)
        p1 = phase_at(inst, fingers, f1)
        f1x = inst.find_resonance(4.0 * inst.length, fingers, 1)
        f1x = inst.frequency_from_wavelength(f1x)
        print(f"  {label:14s} phase@12th={p12:.3f} (delta {2.0 - p12:+.3f})  "
              f"phase@f1={p1:.3f}  f1'={f1x:.1f} Hz ({1200*math.log2(f1x/f1):+.0f}c)")

    sweep = [50.0, 80.0, 120.0, 200.0, 300.0, 429.0, 500.0, 600.0, 720.0]
    print(f"  phase vs frequency sweep ({' '.join(str(int(x)) for x in sweep)} Hz):")
    for label, inst in [("plain", plain), ("L2", inst2), ("L1", inst1)]:
        out = [f"{phase_at(inst, fingers, f):.2f}" for f in sweep]
        print(f"    {label:4s} " + " ".join(out))
    print()

    # ---- Section 2: L1 trade-off curve (squeak suppression vs f1 shift) ----
    print("Section 2 -- L1 trade-off curve (squeak suppression vs low-register shift)")
    print("-" * 72)
    print(f"  {'ratio':>5s} {'L1 d(12th)':>10s} {'L1 f1 cents':>12s}")
    curve = []
    for ratio in (0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00):
        f0 = ratio * squeak
        v = cavity_volume_for_f0(f0)
        slots = []
        for i in range(int((end - start) // spacing)):
            pos = start + i * spacing + spacing / 2.0
            if pos > end:
                break
            slots.append(MetamaterialSideBranch(position_mm=pos, neck_radius_mm=4.0,
                                                neck_length_mm=8.0, cavity_volume_mm3=v))
        inst1 = TMMInstrument(
            inner_positions=[0, L], inner_diameters=[D, D], outer_diameters=[OD, OD],
            hole_positions=[], hole_diameters=[], hole_lengths=[],
            closed_top=True, speed_of_sound=SPEED_OF_SOUND, meta_slots=slots,
        )
        d = 2.0 - phase_at(inst1, fingers, squeak)
        f1x = inst1.find_resonance(4.0 * inst1.length, fingers, 1)
        f1x = inst1.frequency_from_wavelength(f1x)
        c = 1200 * math.log2(f1x / f1)
        curve.append({"ratio": ratio, "L1_d12th": round(d, 4), "f1_cents": round(c, 1)})
        print(f"  {ratio:5.2f} {d:10.3f} {c:12.0f}")
    print()

    # ---- Summary JSON ----
    results = {
        "instrument": "Soprano clarinet Bb",
        "bore_length_mm": L,
        "bore_diameter_mm": D,
        "plain_registers_hz": [round(r, 2) for r in regs_plain],
        "squeak_hz": round(squeak, 2),
        "section1": {"f0_ratio": 0.85, "spacing_mm": spacing, "stopband_hz": sb},
        "section2_l1_curve": curve,
    }
    os.makedirs("test_output", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2)
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()