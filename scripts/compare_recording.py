"""Compare a WAV recording against TMM synthesis of the same instrument design.

Cross-checks the physical model against audio:
  1. analyze_wav   -> measured fundamental + harmonic frequencies/amplitudes
  2. TMM instrument -> predicted fundamental frequency (find_resonance, all
     holes closed) and predicted harmonic envelope (estimate_harmonic_magnitudes)
  3. report pitch error in cents + harmonic-envelope RMSE/correlation

Usage:
    python scripts/compare_recording.py --wav out.wav --design design.json
    python scripts/compare_recording.py --design design.json --synthesize predicted.wav --plot cmp.png

Design JSON accepts either an explicit bore profile:
    {"inner_positions": [...], "inner_diameters": [...], "hole_positions": [...],
     "hole_diameters": [...], "hole_lengths": [...], "closed_top": false}
or bore parameters (passed to tmm_instrument_from_radii):
    {"bore_length_mm": 600, "bore_radii": [...], "outer_diameter_mm": 22,
     "hole_positions_mm": [...], "hole_diameters_mm": [...], "hole_lengths_mm": [...],
     "closed_top": false}
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.inverse_design import (  # noqa: E402
    analyze_wav,
    estimate_harmonic_magnitudes,
    save_synthetic_wav,
    synthesize_harmonic,
)
from backend.tmm_acoustics import (  # noqa: E402
    SPEED_OF_SOUND,
    TMMInstrument,
    tmm_instrument_from_radii,
)

try:
    from backend.physics.losses import KeefeLoss

    _KEEFE_LOSS = KeefeLoss()
except ImportError:
    _KEEFE_LOSS = None

DEFAULT_OUT_DIR = os.path.join(
    os.path.dirname(__file__), "..", "test_output", "recording_compare"
)


def build_instrument(design: dict) -> TMMInstrument:
    if design.get("inner_positions") and design.get("inner_diameters"):
        return TMMInstrument(
            inner_positions=[float(p) for p in design["inner_positions"]],
            inner_diameters=[float(d) for d in design["inner_diameters"]],
            outer_diameters=[float(design.get("outer_diameter_mm", 22.0))] * len(
                design["inner_positions"]
            ),
            hole_positions=[float(h) for h in design.get("hole_positions", [])],
            hole_diameters=[float(h) for h in design.get("hole_diameters", [])],
            hole_lengths=[float(h) for h in design.get("hole_lengths", [])],
            closed_top=bool(design.get("closed_top", False)),
            loss_model=_KEEFE_LOSS,
        )
    radii = [float(r) for r in design.get("bore_radii", [])]
    if not radii:
        raise ValueError("design JSON needs inner_positions/inner_diameters or bore_radii")
    return tmm_instrument_from_radii(
        radii_mm=np.asarray(radii),
        bore_length_mm=float(design.get("bore_length_mm", 600.0)),
        hole_positions_mm=[float(h) for h in design.get("hole_positions_mm", [])],
        hole_diameters_mm=[float(h) for h in design.get("hole_diameters_mm", [])],
        hole_lengths_mm=[float(h) for h in design.get("hole_lengths_mm", [])],
        outer_diameter_mm=float(design.get("outer_diameter_mm", 22.0)),
        closed_top=bool(design.get("closed_top", False)),
        loss_model=_KEEFE_LOSS,
    )


def fingering_for(n_holes: int, open_holes: list[int]) -> list[str]:
    opened = set(int(h) for h in open_holes)
    return ["open" if i in opened else "closed" for i in range(n_holes)]


def predict_pitch(inst: TMMInstrument, open_holes: list[int]) -> float:
    f0_guess = (
        SPEED_OF_SOUND / (4.0 * inst.length)
        if inst.closed_top
        else SPEED_OF_SOUND / (2.0 * inst.length)
    )
    n_register = 1 if inst.closed_top else 2  # open-open: f0 is 2nd resonance
    wl = inst.find_resonance(
        SPEED_OF_SOUND / f0_guess,
        fingering_for(inst.n_holes, open_holes),
        n_register=n_register,
    )
    return inst.frequency_from_wavelength(wl)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--wav", help="path to WAV recording (omit with --synthesize)")
    parser.add_argument("--design", required=True, help="design JSON (geometry)")
    parser.add_argument("--n-harmonics", type=int, default=8, help="harmonics to compare")
    parser.add_argument("--open-holes", default="", help="space-separated hole indices to open")
    parser.add_argument("--plot", help="optional matplotlib comparison plot path")
    parser.add_argument("--synthesize", help="optional predicted WAV output path")
    parser.add_argument("--out", help="report JSON path (default: under test_output/)")
    args = parser.parse_args(argv)

    if not args.wav and not args.synthesize:
        parser.error("need --wav and/or --synthesize")

    with open(args.design) as f:
        design = json.load(f)

    open_holes = [int(x) for x in args.open_holes.split() if x]
    inst = build_instrument(design)
    f0_pred = predict_pitch(inst, open_holes)
    est_mags = estimate_harmonic_magnitudes(inst, n_harmonics=args.n_harmonics)

    report: dict = {
        "design_file": os.path.abspath(args.design),
        "n_holes": inst.n_holes,
        "bore_length_mm": round(inst.length, 3),
        "closed_top": bool(inst.closed_top),
        "open_holes": open_holes,
        "predicted_f0_hz": round(f0_pred, 3),
        "predicted_harmonic_magnitudes": [round(float(m), 6) for m in est_mags],
    }

    if args.wav:
        analysis = analyze_wav(args.wav)
        f0_meas = analysis["fundamental_hz"]
        harm_freqs = analysis["harmonic_frequencies"]
        harm_amps = analysis["harmonic_amplitudes"]
        report["wav_file"] = os.path.abspath(args.wav)
        report["measured_f0_hz"] = round(f0_meas, 3) if f0_meas > 0 else None
        report["measured_harmonic_frequencies"] = [round(float(f), 2) for f in harm_freqs]
        if f0_meas > 0:
            cents = 1200.0 * math.log2(f0_meas / f0_pred)
            report["pitch_cents_error"] = round(cents, 2)
            n_cmp = min(len(harm_amps), len(est_mags), args.n_harmonics)
            if n_cmp > 0:
                meas = np.asarray(harm_amps[:n_cmp], dtype=float)
                est = np.asarray(est_mags[:n_cmp], dtype=float)
                if meas[0] > 0:
                    meas = meas / meas[0]
                if est[0] > 0:
                    est = est / est[0]
                rmse = float(np.sqrt(np.mean((meas - est) ** 2)))
                corr = float(np.corrcoef(meas, est)[0, 1]) if n_cmp > 2 else 0.0
                report["harmonic_envelope_rmse"] = round(rmse, 6)
                report["harmonic_envelope_corr"] = round(corr, 6)
                report["compared_harmonics"] = n_cmp
            print(
                f"[pitch] measured={f0_meas:.2f}Hz predicted={f0_pred:.2f}Hz "
                f"err={cents:+.2f}c"
            )
            print(f"[envelope] RMSE={report.get('harmonic_envelope_rmse'):.6f} "
                  f"corr={report.get('harmonic_envelope_corr'):.3f}")
        else:
            print("[pitch] measured f0 unavailable (silence or no autocorrelation peak)")

        if args.plot:
            try:
                import matplotlib

                matplotlib.use("Agg")
                import matplotlib.pyplot as plt
            except ImportError:
                print("[plot] matplotlib not available; skipping")
            else:
                fig, ax = plt.subplots(figsize=(8, 4.5))
                if len(harm_amps) > 0 and harm_amps[0] > 0:
                    meas_bar = harm_amps / harm_amps[0]
                else:
                    meas_bar = np.zeros(len(est_mags))
                ax.bar(np.arange(1, len(meas_bar) + 1), meas_bar, alpha=0.6, label="measured")
                ax.plot(
                    np.arange(1, len(est_mags) + 1),
                    est_mags, "o-", color="tab:red", label="TMM predicted",
                )
                ax.set_xlabel("harmonic #")
                ax.set_ylabel("normalized magnitude")
                ax.set_title(
                    f"f0 measured={f0_meas:.1f}Hz vs predicted={f0_pred:.1f}Hz "
                    f"({report.get('pitch_cents_error', 0):+.1f}c)"
                )
                ax.legend()
                fig.tight_layout()
                fig.savefig(args.plot, dpi=110)
                print(f"[plot] saved: {os.path.abspath(args.plot)}")

    if args.synthesize:
        sig = synthesize_harmonic(
            f0_pred, n_harmonics=args.n_harmonics, amplitudes=est_mags
        )
        save_synthetic_wav(args.synthesize, sig)
        print(f"[synthesize] predicted WAV saved: {os.path.abspath(args.synthesize)}")

    if args.out:
        out_path = args.out
    else:
        os.makedirs(DEFAULT_OUT_DIR, exist_ok=True)
        stem = os.path.splitext(os.path.basename(args.wav or args.synthesize))[0]
        out_path = os.path.join(DEFAULT_OUT_DIR, f"{stem}_report.json")
    with open(out_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"[report] saved: {os.path.abspath(out_path)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
