"""
Benchmark: end-to-end test of unconventional bore shape modeling.

Pipeline (generate -> acoustic -> STL) and scale-based parametric
bore shape optimization for all bore types.
"""

import sys, os, time, json, math
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.physics.bore_generators import (
    BORE_SHAPE_GENERATORS, BORE_TYPE_META, bore_profile_to_diameter,
)
from backend.physics.bore_optimizer import (
    two_phase_optimize_bore_parameters, _compute_resonances, _best_scale_cost, _generate_radii, BORE_TYPE_META as BORE_META,
)
from woodwind_designer.engine.instrument_library import save_novel_instrument

_c = SPEED_OF_SOUND


def build_ascending_fingerings(n_holes: int, n_notes: int) -> list[list[str]]:
    fingerings = []
    for i in range(min(n_notes, n_holes + 1)):
        fng = ["closed"] * n_holes
        for j in range(min(i, n_holes)):
            fng[j] = "open"
        fingerings.append(fng)
    while len(fingerings) < n_notes:
        fingerings.append(["open"] * n_holes)
    return fingerings


def build_equally_spaced_holes(length_mm: float, n_holes: int) -> list[float]:
    if n_holes == 0:
        return []
    spacing = length_mm / (n_holes + 1)
    return [spacing * (i + 1) for i in range(n_holes)]


def benchmark_pipeline(
    bore_type: str, fingerings: list[list[str]], hole_positions: list[float],
    hole_diameters: list[float], closed_top: bool,
    bore_length_mm: float = 600.0, radius_params: dict | None = None,
) -> dict:
    """Pipeline test: generate bore -> acoustic model -> resonance -> STL."""
    t0 = time.time()
    gen = BORE_SHAPE_GENERATORS[bore_type]
    meta = BORE_TYPE_META[bore_type]
    n_holes = len(hole_positions)
    result: dict = {
        "bore_type": bore_type, "label": meta["label"],
        "bore_length_mm": bore_length_mm, "n_holes": n_holes, "steps": {},
    }

    rp = dict(radius_params or {})
    t1 = time.time()
    radii = _generate_radii(bore_type, bore_length_mm, rp, n_cp=50)
    result["steps"]["generate"] = {"time_s": round(time.time() - t1, 4), "n_radii": len(radii)}

    t2 = time.time()
    try:
        hl = [3.75] * n_holes
        inst = tmm_instrument_from_radii(
            radii_mm=np.asarray(radii), bore_length_mm=bore_length_mm,
            hole_positions_mm=hole_positions, hole_diameters_mm=hole_diameters,
            hole_lengths_mm=hl, closed_top=closed_top,
        )
        result["steps"]["acoustic_model"] = {"time_s": round(time.time() - t2, 4), "success": True}
    except Exception as e:
        result["steps"]["acoustic_model"] = {"time_s": round(time.time() - t2, 4), "success": False, "error": str(e)}
        result["total_time_s"] = round(time.time() - t0, 2)
        result["overall"] = "FAIL"
        return result

    t3 = time.time()
    try:
        freqs = _compute_resonances(inst, fingerings, closed_top, len(fingerings), bore_length_mm)
        valid = [f for f in freqs if f > 0]
        scale_rms, scale_name, _ = _best_scale_cost(freqs)
        result["steps"]["resonance"] = {
            "time_s": round(time.time() - t3, 4),
            "n_valid_resonances": len(valid),
            "scale_fit_rms_cents": round(scale_rms, 3),
            "best_scale": scale_name,
        }
    except Exception as e:
        result["steps"]["resonance"] = {"time_s": round(time.time() - t3, 4), "success": False, "error": str(e)}

    t4 = time.time()
    try:
        profile = bore_profile_to_diameter(radii, n_samples=32, length_mm=bore_length_mm)
        result["steps"]["cad_profile"] = {"time_s": round(time.time() - t4, 4), "n_profile_points": len(profile)}
    except Exception as e:
        result["steps"]["cad_profile"] = {"time_s": round(time.time() - t4, 4), "success": False, "error": str(e)}

    t5 = time.time()
    try:
        from backend.cadquery_export import generate_variable_bore_instrument, export_stl
        holes = [(hole_positions[i], hole_diameters[i]) for i in range(n_holes)]
        solid = generate_variable_bore_instrument(
            bore_length=bore_length_mm, bore_profile=profile,
            wall_thickness=3.0, holes=holes, closed_top=closed_top,
        )
        stl_path = os.path.join(
            os.path.dirname(__file__), "..", "test_output", "unconventional",
            f"{bore_type}_benchmark.stl",
        )
        os.makedirs(os.path.dirname(stl_path), exist_ok=True)
        stl_t = export_stl(solid, stl_path)
        result["steps"]["stl_export"] = {"time_s": round(stl_t, 4), "path": stl_path}
    except Exception as e:
        result["steps"]["stl_export"] = {"time_s": round(time.time() - t5, 4), "success": False, "error": str(e)}

    result["total_time_s"] = round(time.time() - t0, 2)
    stl_ok = result.get("steps", {}).get("stl_export", {}).get("path") is not None
    acoustic_ok = result.get("steps", {}).get("acoustic_model", {}).get("success", False)
    result["overall"] = "PASS" if (stl_ok and acoustic_ok) else "FAIL"
    return result


def _optimize_bore_type_dask(
    repo_root: str, bore_type: str, params: dict, fingerings: list[list[str]],
    hole_positions: list[float], hole_diameters: list[float],
    pop_size: int, n_generations: int, optimize_holes: bool,
) -> dict:
    """Run one bore-type optimization inside a Dask worker.

    All imports are local so the scheduler never needs the repo on its own
    sys.path. Returns a JSON-safe dict (instrument objects are stripped).
    """
    import sys
    if repo_root and repo_root not in sys.path:
        sys.path.insert(0, repo_root)
    from backend.physics.bore_optimizer import two_phase_optimize_bore_parameters

    r = two_phase_optimize_bore_parameters(
        bore_type=bore_type,
        fingerings=fingerings, hole_positions=hole_positions,
        hole_diameters=hole_diameters,
        bore_length_mm=600.0, radius_params=params,
        closed_top=True, pop_size=pop_size, n_generations=n_generations,
        optimize_holes=optimize_holes,
    )
    clean = {k: v for k, v in r.items() if k != "best_instrument"}
    for phase in ("phase1", "phase2"):
        if isinstance(clean.get(phase), dict):
            clean[phase] = {k: v for k, v in clean[phase].items() if k != "instrument"}
    return clean


def _sync_worker_modules(client) -> bool:
    """Copy bore_generators/bore_optimizer to workers where missing.

    The collaborator's worker checkout lacks ``backend/physics/bore_generators.py``
    and ``backend/physics/bore_optimizer.py`` (deliberately diverged branch).
    This writes both files into the worker's ``backend/physics/`` package dir so
    the ``backend.physics.bore_optimizer`` subpackage import resolves, without
    requiring any checkout change. Returns True if every worker can import the
    module afterward.
    """
    local_dir = os.path.join(os.path.dirname(__file__), "physics")
    files = ["bore_generators.py", "bore_optimizer.py"]
    sources = {}
    for fn in files:
        p = os.path.join(local_dir, fn)
        if not os.path.isfile(p):
            raise FileNotFoundError(f"missing local module: {p}")
        with open(p, "r", encoding="utf-8") as f:
            sources[fn] = f.read()

    def _ensure(payload: dict) -> dict:
        import os
        try:
            import backend
        except Exception as e:
            return {"ok": False, "error": f"import backend: {e}"}
        phys = os.path.join(backend.__path__[0], "physics")
        os.makedirs(phys, exist_ok=True)
        for fn, content in payload.items():
            target = os.path.join(phys, fn)
            same = False
            if os.path.isfile(target):
                try:
                    with open(target, "r", encoding="utf-8") as f:
                        same = f.read() == content
                except Exception:
                    same = False
            if not same:
                with open(target, "w", encoding="utf-8") as f:
                    f.write(content)
        try:
            import backend.physics.bore_optimizer as bo
            return {"ok": True, "backend": backend.__path__[0], "bore_optimizer": bo.__file__}
        except Exception as e:
            return {"ok": False, "error": f"import backend.physics.bore_optimizer: {e}"}

    results = client.run(_ensure, sources)
    ok = True
    for addr, r in results.items():
        if r.get("ok"):
            print(f"    {addr}: synced -> {r.get('bore_optimizer')}")
        else:
            ok = False
            print(f"    {addr}: FAILED {r.get('error')}")
    return ok


def benchmark_optimization(
    fingerings: list[list[str]], hole_positions: list[float],
    hole_diameters: list[float], pop_size: int = 12, n_generations: int = 12,
    optimize_holes: bool = True, use_dask: bool = False, scheduler: str = "tcp://100.69.113.41:8786",
) -> list[dict]:
    """Run two-phase parametric optimization on closed-top bore types.

    With ``use_dask=True``, each bore type is dispatched to a Dask worker
    (all 7 types are independent); otherwise they run sequentially in-process.
    """
    opt_tests = [
        ("cylindrical", {"radius_mm": 7.25}),
        ("parabolic", {"radius_min_mm": 4.0, "radius_max_mm": 10.0}),
        ("exponential", {"radius_start_mm": 4.0, "radius_end_mm": 10.0}),
        ("bessel", {"radius_start_mm": 4.0, "radius_end_mm": 10.0}),
        ("spiral", {"base_radius_mm": 8.0, "amplitude_mm": 2.0, "cycles": 3.0}),
        ("ridged", {"base_radius_mm": 8.0, "ridge_depth_mm": 1.5, "n_ridges": 5}),
        ("stepped", {"radius_start_mm": 5.0, "radius_end_mm": 10.0, "n_steps": 4}),
    ]
    repo_root = os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

    client = None
    if use_dask:
        from distributed import Client
        print(f"\nConnecting to Dask scheduler: {scheduler}")
        client = Client(scheduler, timeout=30)
        info = client.scheduler_info()
        workers = info.get("workers", {})
        print(f"  Workers: {len(workers)}")
        for addr, w in workers.items():
            print(f"    {addr}: nthreads={w.get('nthreads', '?')}")
        print(f"  Dashboard: {client.dashboard_link}")
        print("  Ensuring worker modules...")
        if not _sync_worker_modules(client):
            print("  ERROR: could not sync bore_optimizer to workers; aborting Dask run.")
            client.close()
            return []

    results_list = []
    futures = []
    if client is not None:
        print(f"\nDispatching {len(opt_tests)} bore-type optimizations to workers...")
        for bore_type, params in opt_tests:
            futures.append(client.submit(
                _optimize_bore_type_dask,
                repo_root, bore_type, params, fingerings, hole_positions,
                hole_diameters, pop_size, n_generations, optimize_holes,
            ))
    for i, (bore_type, params) in enumerate(opt_tests):
        label = BORE_TYPE_META[bore_type]["label"]
        print(f"\n-- Optimizing: {label} --")
        try:
            if client is not None:
                r = futures[i].result(timeout=3600)
            else:
                r = two_phase_optimize_bore_parameters(
                    bore_type=bore_type,
                    fingerings=fingerings, hole_positions=hole_positions,
                    hole_diameters=hole_diameters,
                    bore_length_mm=600.0, radius_params=params,
                    closed_top=True, pop_size=pop_size, n_generations=n_generations,
                    optimize_holes=optimize_holes,
                )
            print(f"  Initial: {r['initial_cost_rms_cents']:.1f} cents")
            print(f"  Fundamental: {r['fundamental_hz']} Hz")
            print(f"  Best scale: {r['best_scale']} ({r['scale_rms_cents']:.1f} cents RMS)")
            print(f"  DE:      {r['de_cost_rms_cents']:.1f} cents ({r['phase1_time_s']:.2f}s)")
            print(f"  Refined: {r['final_cost_rms_cents']:.1f} cents ({r['refine_time_s']:.2f}s)")
            print(f"  Length:  {r['bore_length_mm']:.1f}mm")
            print(f"  Params:  {r['optimized_params']}")
            if r.get('hole_offsets'):
                print(f"  Hole offsets: {r['hole_offsets']}")
            results_list.append(r)
            save_novel_instrument(r, label=BORE_META.get(r['bore_type'], {}).get('label', r['bore_type']))
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"  FAILED: {e}")

    if client is not None:
        client.close()
    return results_list


def run_all(use_dask: bool = False, scheduler: str = "tcp://100.69.113.41:8786",
            pop_size: int = 12, n_generations: int = 12):
    print("=" * 72)
    print("UNCONVENTIONAL BORE SHAPE BENCHMARK (SCALE-BASED OPTIMIZATION)")
    print("=" * 72)

    n_holes = 7
    n_notes = 8
    hole_positions = build_equally_spaced_holes(600.0, n_holes)
    hole_diameters = [7.0] * n_holes
    fingerings = build_ascending_fingerings(n_holes, n_notes)
    print(f"\nAscending fingerings from bell: {n_notes} notes, {n_holes} holes")
    print(f"Fingerings: {fingerings}")

    bore_tests = [
        ("cylindrical", {"radius_mm": 7.25}, True),
        ("conical", {"radius_start_mm": 4.0, "radius_end_mm": 10.0}, False),
        ("parabolic", {"radius_min_mm": 4.0, "radius_max_mm": 10.0}, True),
        ("exponential", {"radius_start_mm": 4.0, "radius_end_mm": 10.0}, True),
        ("bessel", {"radius_start_mm": 4.0, "radius_end_mm": 10.0}, True),
        ("spline", {"control_points": [(0, 7.0), (150, 8.0), (300, 9.0), (450, 10.0), (600, 11.0)]}, True),
        ("spiral", {"base_radius_mm": 8.0, "amplitude_mm": 2.0, "cycles": 3.0}, True),
        ("ridged", {"base_radius_mm": 8.0, "ridge_depth_mm": 1.5, "n_ridges": 5}, True),
        ("elliptical", {"radius_base_mm": 8.0, "eccentricity": 0.3}, True),
        ("stepped", {"radius_start_mm": 5.0, "radius_end_mm": 10.0, "n_steps": 4}, True),
    ]

    print("\n--- PART 1: Pipeline benchmark ---")
    pipeline_results = {}
    all_pass = True
    for bore_type, params, closed_top in bore_tests:
        label = BORE_TYPE_META[bore_type]["label"]
        print(f"\n-- {label} --")
        r = benchmark_pipeline(
            bore_type, fingerings, hole_positions, hole_diameters, closed_top,
            bore_length_mm=600.0, radius_params=params,
        )
        pipeline_results[bore_type] = r
        status = "OK" if r["overall"] == "PASS" else "FAIL"
        print(f"  Generate:  {r['steps']['generate']['time_s']:.3f}s  ({r['steps']['generate']['n_radii']} pts)")
        if "acoustic_model" in r["steps"]:
            am = r["steps"]["acoustic_model"]
            print(f"  Acoustic:   {am['time_s']:.3f}s  {'OK' if am.get('success', True) else 'FAIL'}")
        if "resonance" in r["steps"]:
            rs = r["steps"]["resonance"]
            if "scale_fit_rms_cents" in rs:
                print(f"  Scale fit:  {rs['scale_fit_rms_cents']:.2f} cents RMS  ({rs['best_scale']})")
        if "cad_profile" in r["steps"]:
            cp = r["steps"]["cad_profile"]
            print(f"  CAD prof:   {cp['time_s']:.3f}s  ({cp.get('n_profile_points', '?')} pts)")
        if "stl_export" in r["steps"]:
            se = r["steps"]["stl_export"]
            if se.get("path"):
                print(f"  STL:        {se['time_s']:.3f}s  -> {se['path']}")
            else:
                print(f"  STL:        FAIL {se.get('error', 'unknown')}")
        print(f"  Total:      {r['total_time_s']:.2f}s  [{status}]")
        if r["overall"] != "PASS":
            all_pass = False

    print(f"\n{'=' * 72}")
    print("--- PART 2: Parametric optimization benchmark (closed-top types) ---")
    opt_results = benchmark_optimization(
        fingerings, hole_positions, hole_diameters,
        pop_size=pop_size, n_generations=n_generations,
        use_dask=use_dask, scheduler=scheduler,
    )

    print(f"\n{'=' * 72}")
    print("OPTIMIZATION SUMMARY")
    print(f"{'=' * 72}")
    print(f"  {'Type':<16} {'Init':>7} {'Final':>7} {'Scale':<18} {'F0':>6} {'Time':>6}")
    print(f"  {'-'*16} {'-'*7} {'-'*7} {'-'*18} {'-'*6} {'-'*6}")
    for r in opt_results:
        init = r["initial_cost_rms_cents"]
        final = r["final_cost_rms_cents"]
        scale = f"{r['best_scale']} ({r['scale_rms_cents']:.0f}¢)"
        f0 = f"{r['fundamental_hz']:.0f}Hz"
        total = r["total_time_s"]
        label = BORE_TYPE_META[r["bore_type"]]["label"]
        print(f"  {label:<16} {init:>7.1f} {final:>7.1f} {scale:<18} {f0:>6} {total:>5.2f}s")

    print(f"\n{'=' * 72}")
    print(f"OVERALL: {'ALL PASSED' if all_pass else 'SOME FAILED'}")
    print(f"{'=' * 72}")

    def _strip_instrument(d):
        if isinstance(d, dict):
            return {k: _strip_instrument(v) for k, v in d.items()
                    if k not in ("best_instrument", "instrument")}
        if isinstance(d, list):
            return [_strip_instrument(v) for v in d]
        return d

    report = {
        "pipeline_results": pipeline_results,
        "optimization_results": [_strip_instrument(r) for r in opt_results],
        "all_pass": all_pass,
        "timestamp": time.time(),
    }
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "test_output", "unconventional", "benchmark_report.json",
    )
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Report saved: {report_path}")
    return all_pass


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="Unconventional bore shape benchmark (scale-based optimization)."
    )
    parser.add_argument("--dask", action="store_true",
                        help="Parallelize Part 2 optimizations across a Dask cluster.")
    parser.add_argument("--scheduler", default="tcp://100.69.113.41:8786",
                        help="Dask scheduler address (default: tcp://100.69.113.41:8786).")
    parser.add_argument("--pop", type=int, default=12, help="DE population size (default: 12).")
    parser.add_argument("--gen", type=int, default=12, help="DE max generations (default: 12).")
    args = parser.parse_args()

    success = run_all(
        use_dask=args.dask, scheduler=args.scheduler,
        pop_size=args.pop, n_generations=args.gen,
    )
    sys.exit(0 if success else 1)
