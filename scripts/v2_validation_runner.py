"""V2 Cross-Software Validation Runner.

Compares our TMM optimizer against chalumier's optimizer on reference
instruments, using the fixtures in :mod:`backend.fixtures`, and generates a
detailed comparison report.

Run from the repo root:

    python -m scripts.v2_validation_runner --mode=all
    python -m scripts.v2_validation_runner --list
    python -m scripts.v2_validation_runner --mode=tmm --output validation_results
"""

import argparse
import json
import math
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np

from backend.fixtures import FIXTURE_REGISTRY, FixtureInstrument, load_all_fixtures
from backend.tmm_acoustics import SPEED_OF_SOUND, tmm_instrument_from_radii
from scripts.compare_chalumier import (
    build_inst_from_chalumier,
    evaluate_inst,
    parse_chal_fingerings,
    parse_json5,
)


class V2ValidationRunner:
    """Runs our TMM solver against reference instruments and chalumier output."""

    def __init__(self, output_dir: str = "validation_results") -> None:
        """Initialize the runner.

        Args:
            output_dir: directory in which validation reports are written.
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.results: List[Dict[str, Any]] = []
        self.start_time = time.time()

    def run_chalumier_comparison(
        self, chalumier_spec: str, chalumier_output: str
    ) -> Dict[str, Any]:
        """Evaluate a chalumier design with our TMM and compare intonation.

        Args:
            chalumier_spec: path to the ``.chal`` instrument spec (fingerings).
            chalumier_output: path to chalumier's JSON/JSON5 output file.

        Returns:
            Dict with mean/median/evenness/max cents statistics over the notes,
            or ``{"success": False, "error": ...}``.
        """
        if not Path(chalumier_spec).exists():
            return {"instrument": "unknown", "success": False,
                    "error": f"Spec not found: {chalumier_spec}"}
        if not Path(chalumier_output).exists():
            return {"instrument": "unknown", "success": False,
                    "error": f"Chalumier output not found: {chalumier_output}"}

        try:
            params = parse_json5(chalumier_output)
            fingerings, meta = parse_chal_fingerings(chalumier_spec)
            transpose = meta.get("transpose", 0)

            inst, *_ = build_inst_from_chalumier(params)
            results = evaluate_inst(inst, fingerings, transpose)

            cents = np.array(
                [r["cents"] for r in results if abs(r.get("cents", 1e10)) < 1e5]
            )
            if cents.size == 0:
                return {"success": False, "error": "No valid resonances found"}

            median = float(np.median(cents))
            return {
                "success": True,
                "mean_abs_cents": float(np.mean(np.abs(cents))),
                "median_cents": median,
                "evenness_cents": float(np.sqrt(np.mean((cents - median) ** 2))),
                "offset_cents": median,
                "max_abs_cents": float(np.max(np.abs(cents))),
                "n_notes": int(cents.size),
                "n_total": len(fingerings),
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_our_tmm(self, fixture: FixtureInstrument) -> Dict[str, Any]:
        """Run our TMM optimizer against a fixture's targets.

        Args:
            fixture: reference instrument fixture.

        Returns:
            Dict with mean/median/evenness/max cents statistics over the
            fixture's target frequencies.
        """
        try:
            inst = tmm_instrument_from_radii(
                radii_mm=[r for _, r in fixture.bore_profile],
                bore_length_mm=(
                    fixture.bore_profile[-1][0] if fixture.bore_profile else 300
                ),
                hole_positions_mm=[h["position"] for h in fixture.holes],
                hole_diameters_mm=[h["diameter"] for h in fixture.holes],
                hole_lengths_mm=[h["length"] for h in fixture.holes],
                outer_diameter_mm=22.0,
                closed_top=fixture.closed_top,
                cone_step=0.5,
            )
            if not fixture.targets:
                return {"success": False, "error": "No target frequencies"}

            n_register = 1 if fixture.closed_top else 2
            t0 = time.time()
            errors: List[float] = []
            for target in fixture.targets:
                wl_guess = SPEED_OF_SOUND / target
                try:
                    wl = inst.find_resonance(wl_guess, [], n_register=n_register)
                    freq = inst.frequency_from_wavelength(wl)
                    if freq > 0:
                        errors.append(abs(1200 * math.log2(freq / target)))
                except Exception:
                    continue

            if not errors:
                return {"success": False, "error": "No resonances computed"}

            errors_arr = np.array(errors)
            return {
                "success": True,
                "mean_abs_cents": float(np.mean(errors_arr)),
                "median_cents": float(np.median(errors_arr)),
                "evenness_cents": float(np.std(errors_arr)),
                "max_abs_cents": float(np.max(errors_arr)),
                "runtime_seconds": time.time() - t0,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_all(self) -> List[Dict[str, Any]]:
        """Run the TMM validation on every registered fixture.

        Returns:
            List of per-fixture result dicts (also stored in ``self.results``).
        """
        load_all_fixtures()
        results: List[Dict[str, Any]] = []
        for name, fixture in FIXTURE_REGISTRY.fixtures.items():
            print(f"\nTesting: {fixture.name} ({fixture.family}/{fixture.subcategory})")
            result = self.run_our_tmm(fixture)
            result.update({
                "instrument": fixture.name,
                "mode": "our_tmm",
                "fixture_family": fixture.family,
                "fixture_subcategory": fixture.subcategory,
                "fixture_source": fixture.source,
            })
            self.results.append(result)
            ok = "OK" if result["success"] else "FAIL"
            err = result.get("mean_abs_cents", 0)
            print(f"  TMM: {ok} mean_error={err:.2f}c")
        return results

    def generate_report(self) -> str:
        """Render a human-readable report from collected results."""
        successful = [r for r in self.results if r.get("success")]
        lines = [
            "=" * 80,
            "V2 CROSS-SOFTWARE VALIDATION REPORT",
            "=" * 80,
            f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Duration: {time.time() - self.start_time:.1f}s",
            f"Instruments tested: {len(self.results)}",
            f"Successful: {len(successful)}",
            f"Failed: {len(self.results) - len(successful)}",
            "",
            "DETAILED RESULTS:",
        ]
        for r in self.results:
            if r.get("success"):
                err = f"{r.get('mean_abs_cents', 0):.2f}c"
                lines.append(f"  OK   {r['instrument']} ({r.get('mode', 'N/A')}): {err}")
            else:
                lines.append(
                    f"  FAIL {r['instrument']} ({r.get('mode', 'N/A')}): "
                    f"{r.get('error', 'Unknown')}"
                )
        return "\n".join(lines)

    def save_results(self, filepath: Optional[str] = None) -> None:
        """Write collected results to a JSON report.

        Args:
            filepath: output path; defaults to a timestamped file in
                ``self.output_dir``.
        """
        if filepath is None:
            filepath = str(self.output_dir / f"validation_report_{int(time.time())}.json")
        with open(filepath, "w") as f:
            json.dump({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "duration_seconds": time.time() - self.start_time,
                "results": self.results,
            }, f, indent=2)
        print(f"\nResults saved to: {filepath}")


def main() -> None:
    """Parse arguments and run the requested validation mode."""
    parser = argparse.ArgumentParser(description="V2 Cross-Software Validation Runner")
    parser.add_argument(
        "--mode", choices=["all", "tmm"], default="all",
        help="Validation mode (chalumier comparison is available via the "
             "V2ValidationRunner API, not a CLI mode yet)",
    )
    parser.add_argument("--list", action="store_true", help="List available fixtures")
    parser.add_argument("--output", help="Output directory for results")
    args = parser.parse_args()

    runner = V2ValidationRunner(args.output or "validation_results")

    if args.list:
        load_all_fixtures()
        print("Available fixtures:")
        for name in FIXTURE_REGISTRY.list_all():
            f = FIXTURE_REGISTRY.get(name)
            print(f"  {name} ({f.family}/{f.subcategory}) - {f.source}")
        return

    runner.run_all()
    print(runner.generate_report())
    runner.save_results()


if __name__ == "__main__":
    main()
