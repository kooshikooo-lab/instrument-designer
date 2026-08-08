"""
Graded / broadband metamaterial HR-array benchmark (bass clarinet).

Compares uniform vs graded (rainbow-trapping) HR arrays near the closed end:

  Section 1 — baseline: plain bore registers.
  Section 2 — uniform array (the tuned design, f0=572 Hz) registers + f1.
  Section 3 — graded arrays (linear / geometric f0 sweep) at the same N:
              f1 (low-register extension), resonance-band span, and estimated
              stopband coverage (union of per-cell gamma^2 stopband bounds).
  Section 4 — rainbow knob: sweep f0_stop at fixed f0_start -> coverage growth.

Note: graded designs are Level 1 (explicit array) only; the homogenized Level 2
segment holds a single f0. Per-cell stopband bounds use the L2 formula as a
design estimate for each cell's resonance band.

Run: python scripts/benchmark_metamaterial_graded_arrays.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.metamaterial_low_clarinets import (
    all_closed_fingers,
    array_resonance_band,
    explicit_hr_array,
    fundamental,
    graded_hr_array,
    registers,
    resonator_f0,
    stopband_bounds,
)

W = 84
KEY = "bass"
SPACING = 30.0
START_FRAC = 0.9
TUNED_F0 = 572.0  # the L1-refined bass design from the family benchmark
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "test_output", "metamaterial_graded_array_results.json")


def cell_stopband(f0):
    """[f0, f_hi] stopband bounds for a single-resonator cell (L2 estimate)."""
    return stopband_bounds(KEY, f0, SPACING)


def coverage_width(f0s):
    """Union width (Hz) of per-cell stopband intervals."""
    intervals = sorted([b for b in (cell_stopband(f) for f in f0s) if b[0]])
    if not intervals:
        return 0.0
    merged = [list(intervals[0])]
    for lo, hi in intervals[1:]:
        if lo <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], hi)
        else:
            merged.append([lo, hi])
    return sum(hi - lo for lo, hi in merged)


def sections():
    fingers = all_closed_fingers(KEY)
    out = {}

    print(f"{'':=<{W}}")
    print("Section 1 — plain bore baseline")
    plain = explicit_hr_array(KEY, 2000.0, SPACING)  # no effective array
    f1_plain = fundamental(plain, fingers)
    r_plain = registers(plain, fingers, 3)
    print(f"  f1={f1_plain:7.2f} Hz  registers 1..3 = "
          f"{[f'{x:.1f}' for x in r_plain]}")

    print(f"{'':=<{W}}")
    print(f"Section 2 — uniform array (tuned design f0={TUNED_F0:.0f} Hz)")
    uni = explicit_hr_array(KEY, TUNED_F0, SPACING)
    f1_uni = fundamental(uni, fingers)
    r_uni = registers(uni, fingers, 3)
    uf0s = [resonator_f0(s) for s in uni.meta_slots]
    print(f"  N={len(uf0s)}  f1={f1_uni:7.2f} Hz "
          f"(target 58.27)  regs={[f'{x:.1f}' for x in r_uni]}")
    print(f"  uniform band: {min(uf0s):.0f}..{max(uf0s):.0f} Hz, "
          f"coverage={coverage_width(uf0s):.0f} Hz")
    out["uniform"] = {"f1": f1_uni, "registers": r_uni,
                      "band": [min(uf0s), max(uf0s)],
                      "coverage_hz": coverage_width(uf0s)}

    print(f"{'':=<{W}}")
    print("Section 3 — graded arrays at the same N (rainbow trapping)")
    out["graded"] = {}
    for profile in ("linear", "geometric"):
        for f0_lo, f0_hi in ((350.0, 900.0), (300.0, 1200.0)):
            inst = graded_hr_array(KEY, f0_lo, f0_hi, SPACING,
                                   profile=profile)
            f1 = fundamental(inst, fingers)
            r = registers(inst, fingers, 3)
            g0s = [resonator_f0(s) for s in inst.meta_slots]
            lo, hi = array_resonance_band(inst.meta_slots)
            cov = coverage_width(g0s)
            print(f"  {profile:<9} sweep {f0_lo:5.0f}->{f0_hi:5.0f} Hz  "
                  f"N={len(g0s)}  f1={f1:7.2f}  "
                  f"band={lo:.0f}..{hi:.0f} Hz  coverage={cov:5.0f} Hz  "
                  f"cents={1200*math.log2(f1/58.27):+6.1f}")
            out["graded"][f"{profile}_{int(f0_lo)}_{int(f0_hi)}"] = {
                "f1": f1, "registers": r, "band": [lo, hi], "N": len(g0s),
                "coverage_hz": cov}

    print(f"{'':=<{W}}")
    print("Section 4 — rainbow knob: f0_stop sweep at fixed f0_start=400 Hz")
    out["rainbow"] = []
    for f0_hi in (600.0, 900.0, 1200.0, 1600.0):
        inst = graded_hr_array(KEY, 400.0, f0_hi, SPACING, profile="linear")
        g0s = [resonator_f0(s) for s in inst.meta_slots]
        lo, hi = array_resonance_band(inst.meta_slots)
        cov = coverage_width(g0s)
        f1 = fundamental(inst, fingers)
        print(f"  f0_hi={f0_hi:5.0f} Hz  band={lo:.0f}..{hi:.0f} Hz  "
              f"coverage={cov:5.0f} Hz  f1={f1:6.2f} Hz")
        out["rainbow"].append({"f0_hi": f0_hi, "band": [lo, hi],
                               "coverage_hz": cov, "f1": f1})

    print(f"{'':=<{W}}")
    print("Section 5 — graded tuned to the target (f1 = 58.27 Hz)")
    target = 58.27

    def graded_f1(scale):
        inst = graded_hr_array(KEY, 350.0 * scale, 900.0 * scale, SPACING,
                               profile="linear")
        return inst, fundamental(inst, fingers)

    lo_s, hi_s = 0.5, 3.0
    if graded_f1(lo_s)[1] > target:
        print("  cannot reach target at scale 0.5")
    else:
        for _ in range(60):
            mid = 0.5 * (lo_s + hi_s)
            f = graded_f1(mid)[1]
            if abs(f - target) < 0.02:
                break
            if f > target:
                hi_s = mid
            else:
                lo_s = mid
        inst, f1 = graded_f1(mid)
        g0s = [resonator_f0(s) for s in inst.meta_slots]
        lo, hi = array_resonance_band(inst.meta_slots)
        cov = coverage_width(g0s)
        print(f"  scale={mid:.3f}  sweep {350*mid:.0f}->{900*mid:.0f} Hz  "
              f"f1={f1:6.2f} Hz  coverage={cov:5.0f} Hz  "
              f"(uniform tuned: 466 Hz)")
        out["graded_tuned"] = {"scale": mid, "f1": f1,
                               "band": [lo, hi], "coverage_hz": cov}

    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n  results -> {OUT}")


if __name__ == "__main__":
    sections()
