"""
Low-register-extension vs 12th-intonation design-curve benchmark.

Quantifies the smooth trade-off that near-closed-end compliance arrays create:
extending the all-closed note (deeper = lower f1) stretches the register-2
(12th) ratio above 3:1. For every family member, reports the design curve at
several extension depths plus the 0.8x target design.

Finding from the tuning scan: the 12th distortion is monotonic in extension
depth and placement/spacing do not fix it; extra low-f0 resonators break
register 2. The curve is the design tool (pick your extension / 12th point).

Run: python scripts/benchmark_metamaterial_intonation.py
"""

import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    analytic_f1,
    all_closed_fingers,
    registers,
    tune_f0_to_fundamental_l1,
    twelfth_deviation,
)

W = 96
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                   "test_output", "metamaterial_intonation_results.json")
DEPTHS = (0.95, 0.90, 0.85, 0.80, 0.75)


def curve(key, spacing=40.0):
    fingers = all_closed_fingers(key)
    base = analytic_f1(key)
    rows = []
    for frac in DEPTHS:
        target = frac * base
        f0, n, f1, inst = tune_f0_to_fundamental_l1(
            key, target, spacing_mm=spacing)
        r = registers(inst, fingers, 3)
        dev = twelfth_deviation(inst, fingers)
        rows.append({"target_frac": frac, "target_hz": round(target, 2),
                     "f0_hz": round(f0, 1), "n": n, "f1_hz": round(f1, 2),
                     "f2_hz": round(r[1], 2), "f3_hz": round(r[2], 2),
                     "twelfth_cents": round(dev, 1)})
    return rows


def main():
    print(f"{'key':<16} {'depth':>6} {'f1':>7} {'f0':>7} {'N':>3} "
          f"{'f2':>7} {'ratio':>6} {'12th(c)':>8}")
    print("-" * W)
    out = {}
    for key in sorted(LOW_CLARINETS):
        rows = curve(key)
        out[key] = rows
        for row in rows:
            print(f"{key:<16} {row['target_frac']:>6.2f} "
                  f"{row['f1_hz']:>7.2f} {row['f0_hz']:>7.0f} {row['n']:>3} "
                  f"{row['f2_hz']:>7.2f} "
                  f"{3.0 * math.exp(row['twelfth_cents'] / 1200.0 * math.log(2)):>6.3f} "
                  f"{row['twelfth_cents']:>+8.1f}")
        print("-" * W)
    with open(OUT, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n  results -> {OUT}  (uncommitted, regenerable)")


if __name__ == "__main__":
    main()
