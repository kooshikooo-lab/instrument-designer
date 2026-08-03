"""
Benchmark batch: acoustic-metamaterial low-register extension for the
low-clarinet family (bass, contra-alto, contra-bass, octocontras).

Reports, per family member:
  1. Plain-tube register structure (f1, f2=f1*3, f3=f1*5, c/(4L)).
  2. Design-knob sweep (HR f0 ratio, spacing) -> achieved fundamental,
     effective-length gain, stopband placement, L1-vs-L2 parity error.
  3. Tuned low-register designs that hit each instrument's extension target,
     with the explicit-L1-array guarantee (the homogenized model under-estimates
     extension, so the printed array overshoots the target, never falls short).
  4. Promising models: designs that reach the target, keep the 12th (f0 between
     register-2 and register-3), and have a finite stopband.

Run: python scripts/benchmark_metamaterial_low_clarinets.py
"""
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.metamaterial_low_clarinets import (
    LOW_CLARINETS,
    all_closed_fingers,
    analytic_f1,
    cavity_volume_for_f0,
    fundamental,
    make_hr_segment,
    make_low_clarinet,
    registers,
    stopband_bounds,
    tune_f0_to_fundamental_l1,
)

W = 96  # table width


def _fmt_cents(f, target):
    return f"{1200.0 * math.log2(f / target):+.1f}"


def baseline_table():
    print("=" * W)
    print("1. LOW-CLARINET FAMILY BASELINE (plain closed-open tubes)")
    print("=" * W)
    print(f"{'key':<16} {'name':<24} {'L(mm)':>8} {'D(mm)':>6} "
          f"{'c/4L':>7} {'f1':>7} {'f2(12th)':>9} {'f3':>7}")
    print("-" * W)
    for key, spec in LOW_CLARINETS.items():
        inst = make_low_clarinet(key)
        f = all_closed_fingers(key)
        r = registers(inst, f, 3)
        print(f"{key:<16} {spec['name']:<24} {spec['bore_length_mm']:>8.1f} "
              f"{spec['bore_diameter_mm']:>6.1f} {analytic_f1(key):>7.1f} "
              f"{r[0]:>7.2f} {r[1]:>9.2f} {r[2]:>7.2f}")


def bass_knob_sweep():
    print()
    print("=" * W)
    print("2. BASS CLARINET: DESIGN-KNOB SWEEP (L2 homogenized model)")
    print("=" * W)
    key = "bass"
    target = LOW_CLARINETS[key]["extension_target_hz"]  # Bb1 58.27 Hz
    fingers = all_closed_fingers(key)
    print(f"target all-closed note: Bb1 = {target:.2f} Hz  (D2 -> Bb1, "
          f"{_fmt_cents(analytic_f1(key), target)} c)")
    print(f"\n{'f0/base':>8} {'spacing':>8} {'f1':>7} {'cents vs tgt':>13} "
          f"{'L_eff(mm)':>10} {'L_eff/L':>8} {'f0(Hz)':>7} "
          f"{'stopband':>13} {'reg2':>7} {'reg3':>7}")
    print("-" * W)
    rows = []
    base = analytic_f1(key)
    for ratio in (2.5, 3.0, 4.0, 6.0):
        for spacing in (20.0, 30.0, 40.0, 60.0):
            f0 = ratio * base
            seg, _ = make_hr_segment(key, f0, spacing)
            inst = make_low_clarinet(key, metamaterial_segments=[seg])
            f1 = fundamental(inst, fingers)
            r = registers(inst, fingers, 3)
            leff = 346100.0 / (4.0 * f1)
            lo, hi = stopband_bounds(key, f0, spacing)
            sb = f"({lo:6.0f},{hi:6.0f})" if lo else "none"
            row = {"ratio": ratio, "spacing": spacing, "f1": f1,
                   "cents": 1200.0 * math.log2(f1 / target), "leff": leff,
                   "f0": f0, "sb_lo": lo, "sb_hi": hi, "reg2": r[1], "reg3": r[2]}
            rows.append(row)
            print(f"{ratio:>8.1f} {spacing:>8.0f} {f1:>7.2f} "
                  f"{row['cents']:>+13.1f} {leff:>10.0f} {leff / 1211.3:>8.2f} "
                  f"{f0:>7.0f} {sb:>13} {r[1]:>7.1f} {r[2]:>7.1f}")
    return rows


def family_tuned_table():
    print()
    print("=" * W)
    print("3. FAMILY TUNED LOW-REGISTER DESIGNS (L1 explicit array refinement)")
    print("   fast L2 coarse search -> explicit L1 array tuned to the target")
    print("=" * W)
    print(f"{'key':<16} {'target(Hz)':>10} {'f0':>7} {'sp':>5} {'N':>3} "
          f"{'f1(L1)':>8} {'cents':>8} {'L2 pred':>8} {'L_eff/L':>8} "
          f"{'12th':>8} {'12th dev':>8} {'stopband':>13} {'reg2':>7} {'reg3':>7}")
    print("-" * W)
    results = {}
    for key, spec in LOW_CLARINETS.items():
        target = spec["extension_target_hz"]
        spacing = 30.0 if key == "bass" else 40.0
        f0, n, achieved, inst = tune_f0_to_fundamental_l1(key, target,
                                                          spacing_mm=spacing)
        fingers = all_closed_fingers(key)
        r = registers(inst, fingers, 3)
        twelfth = r[1] / r[0]
        twelfth_cents = 1200.0 * math.log2(twelfth / 3.0)
        lo, hi = stopband_bounds(key, f0, spacing)
        # fast-model cross-check: what would the homogenized L2 predict?
        seg, _ = make_hr_segment(key, f0, spacing)
        inst_l2 = make_low_clarinet(key, metamaterial_segments=[seg])
        f_l2 = fundamental(inst_l2, fingers)
        leff = 346100.0 / (4.0 * achieved)
        sb = f"({lo:6.0f},{hi:6.0f})" if lo else "none"
        row = {"key": key, "target": target, "f0": f0, "spacing": spacing, "n": n,
               "f1_l1": achieved, "cents": 1200.0 * math.log2(achieved / target),
               "f1_l2": f_l2, "leff_ratio": leff / spec["bore_length_mm"],
               "twelfth_ratio": twelfth, "twelfth_cents": twelfth_cents,
               "sb_lo": lo, "sb_hi": hi, "reg2": r[1], "reg3": r[2],
               "cavity_v_mm3": cavity_volume_for_f0(f0)}
        results[key] = row
        print(f"{key:<16} {target:>10.2f} {f0:>7.1f} {spacing:>5.0f} {n:>3} "
              f"{achieved:>8.2f} {row['cents']:>+8.1f} {f_l2:>8.2f} "
              f"{row['leff_ratio']:>8.2f} {twelfth:>8.2f} "
              f"{twelfth_cents:>+8.1f} {sb:>13} {r[1]:>7.1f} {r[2]:>7.1f}")
    return results


def promising_models(tuned):
    print()
    print("=" * W)
    print("4. PROMISING MODELS (L1-tuned to the target, 12th kept, finite")
    print("   stopband; cavity volume is the print/practical knob)")
    print("=" * W)
    print(f"{'key':<16} {'f0':>7} {'sp':>5} {'N':>3} {'cavity V(mm3)':>13} "
          f"{'f1':>8} {'target':>8} {'12th dev(c)':>12} {'f0>reg2?':>9}")
    print("-" * W)
    promising = []
    for key, row in tuned.items():
        f0, spacing, n = row["f0"], row["spacing"], row["n"]
        target = row["target"]
        reg2 = row["reg2"]
        ok_twelfth = f0 > reg2               # 12th (overblowing) survives
        ok_sb = row["sb_lo"] is not None and row["sb_hi"] > row["sb_lo"]
        ok = ok_twelfth and ok_sb and abs(row["cents"]) < 5.0
        print(f"{key:<16} {f0:>7.1f} {spacing:>5.0f} {n:>3} "
              f"{row['cavity_v_mm3']:>13.0f} {row['f1_l1']:>8.2f} "
              f"{target:>8.2f} {row['twelfth_cents']:>+12.1f} {ok_twelfth!s:>9}")
        if ok:
            promising.append(row)
    print()
    print(f"  promising designs: {len(promising)}")
    for p in promising:
        print(f"    {p['key']:<16} f0={p['f0']:.1f} Hz spacing={p['spacing']:.0f} mm "
              f"N={p['n']} cavity={p['cavity_v_mm3']:.0f} mm^3 "
              f"-> f1={p['f1_l1']:.2f} Hz (target {p['target']:.2f}), "
              f"12th +{p['twelfth_cents']:.0f} c")
    return promising


def main():
    baseline_table()
    bass_knob_sweep()
    tuned = family_tuned_table()
    promising = promising_models(tuned)

    out = {
        "baseline": {k: {"name": v["name"], "bore_length_mm": v["bore_length_mm"],
                         "bore_diameter_mm": v["bore_diameter_mm"],
                         "analytic_f1_hz": analytic_f1(k),
                         "extension_target_hz": v["extension_target_hz"]}
                     for k, v in LOW_CLARINETS.items()},
        "tuned": tuned,
        "promising_keys": [p["key"] for p in promising],
    }
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "test_output")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.join(out_dir, "metamaterial_low_clarinet_benchmark_results.json")
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2)
    print(f"\n  JSON -> {out_path}")


if __name__ == "__main__":
    main()
