"""V1 Benchmark: Inria 2026 Pipe Impedance Benchmark with Dask.

Runs our TMM solver on the canonical V&V benchmark geometries:
- 180mm cylinders: 14mm ID, 4 end conditions (flanged/unflanged x open/closed)
- 180mm cones: 10->22.6mm, 3 end conditions
Materials: brass, boxwood, 3D-printed ABS

Reference: Ernoult et al. 2026, Acta Acustica 10:51, DOI 10.1051/aacus/2026048
Data: Zenodo 20024938 (v2)

Creates STL files for each benchmarked geometry and lists the instruments that
would be added to the library (does not edit ``instruments.ts``).

Run from the repo root:

    python -m scripts.benchmark_v1_inria
"""

import json
import math
import os
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from distributed import Client, LocalCluster

from backend.cadquery_export import export_stl, generate_variable_bore_instrument
from backend.metrics import FIXTURE_TOLERANCE_CENTS
from backend.tmm_acoustics import SPEED_OF_SOUND, tmm_instrument_from_radii

# Benchmark geometries from the Inria 2026 paper.
BENCHMARK_GEOMETRIES: Dict[str, Dict[str, Any]] = {
    "cylinder_14mm_open_open": {
        "length_mm": 180.0, "radii_mm": [7.0] * 20, "closed_top": False,
        "end_condition": "open_open", "description": "Cylinder 14mm ID, open-open",
        "instrument_name": "Inria Benchmark Cylinder 14mm Open-Open",
        "instrument_type": "Flutes", "instrument_subtype": "End-Blown Flutes",
    },
    "cylinder_14mm_open_closed": {
        "length_mm": 180.0, "radii_mm": [7.0] * 20, "closed_top": True,
        "end_condition": "open_closed", "description": "Cylinder 14mm ID, open-closed",
        "instrument_name": "Inria Benchmark Cylinder 14mm Open-Closed",
        "instrument_type": "Woodwinds", "instrument_subtype": "Clarinets",
    },
    "cylinder_14mm_flanged_open": {
        "length_mm": 180.0, "radii_mm": [7.0] * 20, "closed_top": False,
        "end_condition": "flanged_open", "description": "Cylinder 14mm ID, flanged-open",
        "instrument_name": "Inria Benchmark Cylinder 14mm Flanged-Open",
        "instrument_type": "Flutes", "instrument_subtype": "End-Blown Flutes",
    },
    "cylinder_14mm_flanged_closed": {
        "length_mm": 180.0, "radii_mm": [7.0] * 20, "closed_top": True,
        "end_condition": "flanged_closed", "description": "Cylinder 14mm ID, flanged-closed",
        "instrument_name": "Inria Benchmark Cylinder 14mm Flanged-Closed",
        "instrument_type": "Woodwinds", "instrument_subtype": "Clarinets",
    },
    "cone_10_22.6mm_open_open": {
        "length_mm": 180.0, "radii_mm": np.linspace(5.0, 11.3, 20).tolist(),
        "closed_top": False, "end_condition": "open_open",
        "description": "Cone 10->22.6mm, open-open",
        "instrument_name": "Inria Benchmark Cone 10-22.6mm Open-Open",
        "instrument_type": "Flutes", "instrument_subtype": "Transverse Flutes",
    },
    "cone_10_22.6mm_open_closed": {
        "length_mm": 180.0, "radii_mm": np.linspace(5.0, 11.3, 20).tolist(),
        "closed_top": True, "end_condition": "open_closed",
        "description": "Cone 10->22.6mm, open-closed",
        "instrument_name": "Inria Benchmark Cone 10-22.6mm Open-Closed",
        "instrument_type": "Woodwinds", "instrument_subtype": "Oboes",
    },
    "cone_10_22.6mm_flanged_open": {
        "length_mm": 180.0, "radii_mm": np.linspace(5.0, 11.3, 20).tolist(),
        "closed_top": False, "end_condition": "flanged_open",
        "description": "Cone 10->22.6mm, flanged-open",
        "instrument_name": "Inria Benchmark Cone 10-22.6mm Flanged-Open",
        "instrument_type": "Flutes", "instrument_subtype": "Transverse Flutes",
    },
}


def theoretical_frequencies(
    geometry: Dict[str, Any], n_modes: int = 10
) -> np.ndarray:
    """Compute theoretical resonance frequencies for simple geometries.

    Uses the same unit convention as the TMM solver: ``SPEED_OF_SOUND`` is in
    mm/s and the bore length in mm, so frequencies come out in Hz.

    Args:
        geometry: benchmark geometry entry from :data:`BENCHMARK_GEOMETRIES`.
        n_modes: number of modes to return.

    Returns:
        Array of theoretical resonance frequencies in Hz.
    """
    length_mm = geometry["length_mm"]
    if geometry["closed_top"]:
        # Closed-open pipe: f_n = (2n-1) * c / (4L).
        return np.array(
            [(2 * n - 1) * SPEED_OF_SOUND / (4 * length_mm) for n in range(1, n_modes + 1)]
        )
    # Open-open pipe: f_n = n * c / (2L).
    return np.array(
        [n * SPEED_OF_SOUND / (2 * length_mm) for n in range(1, n_modes + 1)]
    )


def compute_resonances(geometry: Dict[str, Any]) -> np.ndarray:
    """Compute resonant frequencies for a geometry using TMM.

    Args:
        geometry: benchmark geometry entry from :data:`BENCHMARK_GEOMETRIES`.

    Returns:
        Array of TMM-computed resonance frequencies in Hz (may be shorter than
        requested when higher modes do not converge).
    """
    inst = tmm_instrument_from_radii(
        radii_mm=np.array(geometry["radii_mm"]),
        bore_length_mm=geometry["length_mm"],
        hole_positions_mm=[], hole_diameters_mm=[], hole_lengths_mm=[],
        outer_diameter_mm=22.0, closed_top=geometry["closed_top"], cone_step=0.5,
    )

    resonances: List[float] = []
    for n in range(1, 11):
        if geometry["closed_top"]:
            target_wl = 4.0 * geometry["length_mm"] / (2 * n - 1)
        else:
            target_wl = 2.0 * geometry["length_mm"] / n
        try:
            wl = inst.find_resonance(
                target_wl, [], n_register=1 if geometry["closed_top"] else 2
            )
            freq = inst.frequency_from_wavelength(wl)
            if freq > 0:
                resonances.append(freq)
        except Exception:
            break
    return np.array(resonances)


def _cents_error(actual: float, theoretical: float) -> float:
    """Absolute pitch error in cents between two frequencies."""
    return abs(1200 * math.log2(actual / theoretical))


def run_single_benchmark(args: Tuple[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Run the benchmark for one geometry. Designed for Dask.

    Args:
        args: ``(geometry_name, geometry)`` tuple for a Dask map.

    Returns:
        A result dict with theoretical/TMM frequencies, per-mode cents errors,
        and the generated STL file (if any).
    """
    geom_name, geometry = args
    t0 = time.time()

    try:
        theo_freqs = theoretical_frequencies(geometry, 10)
        tmm_freqs = compute_resonances(geometry)

        errors = [
            _cents_error(tmm_freqs[i], theo_freqs[i])
            for i in range(min(len(theo_freqs), len(tmm_freqs)))
            if theo_freqs[i] > 0
        ]

        stl_created = False
        stl_error: Optional[str] = None
        stl_path = os.path.join(
            os.path.dirname(__file__), "..", "web", "public", "stl", "benchmarks",
            f"{geom_name}.stl",
        )
        os.makedirs(os.path.dirname(stl_path), exist_ok=True)
        try:
            radii_mm = np.array(geometry["radii_mm"])
            solid = generate_variable_bore_instrument(
                bore_profile=list(
                    zip(np.linspace(0, geometry["length_mm"], len(radii_mm)), radii_mm)
                ),
                wall_thickness=2.0,
                bore_length=geometry["length_mm"],
                holes=[],
                closed_top=geometry["closed_top"],
            )
            export_stl(solid, stl_path)
            stl_created = True
        except Exception as e:
            stl_error = str(e)

        mean_error_cents = float(np.mean(errors)) if errors else None
        return {
            "geometry": geometry["instrument_name"],
            "description": geometry["description"],
            "end_condition": geometry["end_condition"],
            "closed_top": geometry["closed_top"],
            "instrument_type": geometry["instrument_type"],
            "instrument_subtype": geometry["instrument_subtype"],
            "theoretical_frequencies": theo_freqs.tolist(),
            "tmm_frequencies": tmm_freqs.tolist(),
            "errors_cents": [float(e) for e in errors],
            "mean_error_cents": mean_error_cents,
            "max_error_cents": float(np.max(errors)) if errors else None,
            "n_modes_found": len(tmm_freqs),
            "passed": (
                mean_error_cents is not None
                and mean_error_cents <= FIXTURE_TOLERANCE_CENTS
            ),
            "time_s": round(time.time() - t0, 3),
            "stl_file": f"benchmarks/{geom_name}.stl" if stl_created else None,
            "stl_error": stl_error if not stl_created else None,
            "status": "ok",
        }
    except Exception as e:
        return {
            "geometry": geometry["instrument_name"],
            "status": f"error: {e}",
            "time_s": round(time.time() - t0, 3),
        }


def add_to_instrument_library(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Compute new instrument-library entries from benchmark results.

    Reads existing names from ``web/src/data/instruments.ts`` (without
    importing it) and returns entries for successful benchmark geometries that
    are not yet in the library. Does not modify the file.

    Args:
        results: list of ``run_single_benchmark`` result dicts.

    Returns:
        List of instrument entry dicts to add (name, tags, download_url, ...).
    """
    instruments_path = os.path.join(
        os.path.dirname(__file__), "..", "web", "src", "data", "instruments.ts"
    )
    existing_names: set = set()
    with open(instruments_path, "r") as f:
        for line in f:
            m = re.match(r'name: "([^"]+)"', line)
            if m:
                existing_names.add(m.group(1))

    new_instruments: List[Dict[str, Any]] = []
    for r in results:
        if r.get("status") != "ok" or r["geometry"] in existing_names:
            continue
        new_instruments.append({
            "name": r["geometry"],
            "family": "Wind",
            "subcategory": r.get("instrument_type", "Unknown"),
            "type_label": r.get("instrument_subtype", "Unknown"),
            "range": "N/A",
            "key": "N/A",
            "source": "Inria 2026 Benchmark (V1)",
            "demakein_preset": None,
            "image_url": "",
            "audio_url": "",
            "download_url": r.get("stl_file", ""),
            "tags": ["benchmark", "inria-2026", "v1"],
            "difficulty": "N/A",
            "description": (
                f"Benchmark instrument: {r['description']}. "
                "TMM validation against theoretical resonances."
            ),
            "resources": None,
        })
        existing_names.add(r["geometry"])
    return new_instruments


def main() -> None:
    """Run the full V1 benchmark across all geometries on a Dask cluster."""
    print("=" * 72)
    print("  V1 BENCHMARK: Inria 2026 Pipe Impedance (TMM + Dask)")
    print("=" * 72)

    print("\nStarting Dask LocalCluster...")
    cluster = LocalCluster(
        n_workers=4, threads_per_worker=4, processes=True,
        dashboard_address=":8787", silence_logs=False,
    )
    client = Client(cluster)
    try:
        workers = client.scheduler_info().get("workers", {})
        print(f"  Workers: {len(workers)}")
        for w in workers.values():
            print(f"    {w.get('name', '?')}: nthreads={w.get('nthreads', '?')}")
        print(f"  Dashboard: {client.dashboard_link}")

        tasks = [(name, geom) for name, geom in BENCHMARK_GEOMETRIES.items()]
        print(f"\nSubmitting {len(tasks)} tasks to Dask...")
        t0 = time.time()
        futures = [client.submit(run_single_benchmark, task) for task in tasks]
        results = [f.result() for f in futures]
        total_time = time.time() - t0

        out_path = os.path.join(os.path.dirname(__file__), "..", "v1_benchmark_results.json")
        with open(out_path, "w") as f:
            json.dump({
                "timestamp": time.time(),
                "solver": "tmm_acoustics.py (TMM)",
                "speed_of_sound_mm_s": SPEED_OF_SOUND,
                "geometries": list(BENCHMARK_GEOMETRIES.keys()),
                "results": results,
                "summary": {
                    "total_geometries": len(BENCHMARK_GEOMETRIES),
                    "total_time_s": total_time,
                    "successful": sum(1 for r in results if r.get("status") == "ok"),
                    "passed": sum(1 for r in results if r.get("passed")),
                    "fixture_tolerance_cents": FIXTURE_TOLERANCE_CENTS,
                },
            }, f, indent=2)
        print(f"\nResults saved to: {out_path}")

        print("\nAdding to instrument library...")
        new_instruments = add_to_instrument_library(results)
        if new_instruments:
            print(f"  {len(new_instruments)} new instruments would be added:")
            for inst in new_instruments:
                print(f"  + {inst['name']}")
        else:
            print("  No new instruments (already in library)")

        print(f"\n{'=' * 72}")
        print("  SUMMARY")
        print(f"{'=' * 72}")
        print(f"  Total geometries: {len(BENCHMARK_GEOMETRIES)}")
        print(f"  Total time: {total_time:.1f}s")
        ok_count = sum(1 for r in results if r.get("status") == "ok")
        print(f"  Successful: {ok_count}/{len(results)}")
        for r in results:
            if r.get("status") == "ok":
                tag = "PASS" if r.get("passed") else "FAIL"
                print(
                    f"  {r['geometry']:50s} {tag} mean={r.get('mean_error_cents') or 0.0:7.2f}c "
                    f"max={r.get('max_error_cents') or 0.0:7.2f}c modes={r.get('n_modes_found')} "
                    f"stl={r.get('stl_file')}"
                )
            else:
                print(f"  {r.get('geometry', 'unknown'):50s} FAILED: {r.get('status')}")
    finally:
        client.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
