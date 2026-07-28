"""
Dask-parallelized benchmark: optimize all instruments concurrently.

Uses the Dask scheduler on desktop (tcp://100.69.113.41:8786) with
laptop worker for distributed computation.

Tests:
  1. Serial baseline (all 12 instruments sequential)
  2. Dask parallel (all 12 instruments dispatched to workers)
  3. Multi-run consistency (3 runs per instrument, all parallel)
"""
import sys, os, time, json, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["JAX_ENABLE_X64"] = "1"

from distributed import Client
from backend.benchmark_all import INSTRUMENTS
from backend.jax_optimizer import jax_two_phase_optimize


def optimize_one(name, cfg):
    """Optimize a single instrument. Returns dict with results.
    All imports inside function so Dask scheduler doesn't need them at graph-build time.
    """
    import sys, os, time
    os.environ["JAX_ENABLE_X64"] = "1"
    sys.path.insert(0, r"C:\instrument-designer")
    from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
    from scipy.optimize import minimize as sp_min, differential_evolution
    import numpy as np
    import math

    n_h = len(cfg["targets"]) - (1 if cfg["closed_top"] else 0)
    t0 = time.time()

    try:
        # Inline the sequential_refined approach (no external dependency)
        c = SPEED_OF_SOUND
        targets = sorted(cfg["targets"])
        fundamental = min(targets)
        closed_top = cfg["closed_top"]
        n_reg = 1 if closed_top else 2

        n_cp = 6
        bore_radii = np.full(n_cp, cfg["bore_radius"])
        L_est = c / (4.0 * fundamental) if closed_top else c / (2.0 * fundamental)

        def bore_obj(L):
            try:
                inst = tmm_instrument_from_radii(bore_radii, L, [], [], [],
                    cfg["outer_diameter"], closed_top, 0.5)
                wl = inst.find_resonance(c / fundamental, [], n_reg)
                f = inst.frequency_from_wavelength(wl)
                if f <= 0 or not math.isfinite(f): return 1e10
                return abs(1200.0 * math.log2(f / fundamental))
            except: return 1e10

        r = sp_min(bore_obj, [L_est], method='L-BFGS-B',
                   bounds=[(L_est * 0.7, L_est * 1.3)],
                   options={"maxiter": 50, "ftol": 1e-8})
        bore_length = r.x[0]

        hp, hd, hl = [], [], []
        hole_targets = targets[1:]

        for k, target in enumerate(hole_targets):
            min_p = hp[-1] + 15 if hp else 30
            max_p = bore_length - 30
            if min_p >= max_p: break
            best_pos, best_err = 0, 1e10
            for pos in np.linspace(min_p, max_p, 60):
                try:
                    if closed_top:
                        pl = hp + [pos]
                        dl = hd + [cfg["hole_diameter"]]
                        ll = hl + [cfg["hole_length"]]
                        idx = np.argsort(pl)
                        pl_s = [pl[j] for j in idx]
                        dl_s = [dl[j] for j in idx]
                        ll_s = [ll[j] for j in idx]
                        fing = ["closed"] * len(pl)
                        for j in range(k + 1):
                            fing[list(idx).index(j)] = "open"
                        inst = tmm_instrument_from_radii(bore_radii, bore_length,
                            pl_s, dl_s, ll_s, cfg["outer_diameter"], closed_top, 0.5)
                    else:
                        inst = tmm_instrument_from_radii(bore_radii, bore_length,
                            [pos], [cfg["hole_diameter"]], [cfg["hole_length"]],
                            cfg["outer_diameter"], closed_top, 0.5)
                        fing = ["open"]
                    wl = inst.find_resonance(c / target, fing, n_reg)
                    f = inst.frequency_from_wavelength(wl)
                    err = abs(1200.0 * math.log2(f / target)) if f > 0 else 1e10
                    if err < best_err:
                        best_err, best_pos = err, pos
                except: pass
            hp.append(best_pos)
            hd.append(cfg["hole_diameter"])
            hl.append(cfg["hole_length"])

        idx = np.argsort(hp)
        hp = [hp[j] for j in idx]
        hd = [hd[j] for j in idx]
        hl = [hl[j] for j in idx]

        L = bore_length
        radii = bore_radii.copy()

        def safe_eval(radii, L, hp, hd, hl):
            try:
                inst = tmm_instrument_from_radii(
                    radii, L, hp, hd, hl,
                    22.0, closed_top, 0.5)
                n_rg = 1 if closed_top else 2
                n_hl = len(hp)
                fngrs = [["open"]*(kk+1)+["closed"]*(n_hl-kk-1) for kk in range(n_hl)]
                if closed_top:
                    fngrs.insert(0, ["closed"]*n_hl)
                tw = [c / f for f in cfg["targets"]]
                freqs = inst.compute_fingered_frequencies(tw, fngrs, n_rg)
                cents = [1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10 for a, t in zip(freqs, cfg["targets"])]
                ca = np.array(cents)
                if np.any(np.abs(ca) > 1e5): return 1e10
                return float(np.sqrt(np.mean(ca ** 2)))
            except: return 1e10

        # DE for open-open
        if not closed_top and len(hp) > 0:
            n_h = len(hp)
            bore_r = cfg["bore_radius"]
            hd_min = bore_r * 0.4
            hd_max = bore_r * 0.9
            radii_de = np.full(n_cp, bore_r)

            def obj_de(x):
                hp_sorted = []
                hd_sorted = []
                idx_sorted = np.argsort(x[:n_h].tolist())
                for j in idx_sorted:
                    hp_sorted.append(x[j])
                    hd_sorted.append(x[n_h + j])
                return safe_eval(radii_de, L, hp_sorted, hd_sorted, hl)

            de_bounds = []
            for i in range(n_h):
                lo = int(i * L / (n_h * 1.5 + 1))
                hi = int((i + 2) * L / (n_h * 1.5 + 1))
                lo = max(lo, 20)
                hi = min(hi, int(L - 20))
                if hi <= lo: hi = lo + 10
                de_bounds.append((lo, hi))
            for i in range(n_h):
                de_bounds.append((hd_min, hd_max))

            x0_de = np.array(hp + hd)
            for i in range(n_h):
                x0_de[i] = np.clip(x0_de[i], de_bounds[i][0], de_bounds[i][1])
                x0_de[n_h + i] = np.clip(x0_de[n_h + i], hd_min, hd_max)
            result_de = differential_evolution(obj_de, de_bounds, x0=x0_de, seed=42,
                                              maxiter=100, popsize=max(10, n_h * 2),
                                              tol=1e-6, mutation=(0.5, 1.0),
                                              recombination=0.7, polish=True)
            de_idx = np.argsort(result_de.x[:n_h].tolist())
            hp = [result_de.x[j] for j in de_idx]
            hd = [result_de.x[n_h + j] for j in de_idx]

        # 4-stage L-BFGS-B
        GAP = 5.0
        hole_lo = [0.0] * len(hp)
        hole_hi = [0.0] * len(hp)
        for i in range(len(hp)):
            hole_lo[i] = (hp[i-1] + GAP) if i > 0 else 30.0
            hole_hi[i] = (hp[i+1] - GAP) if i < len(hp)-1 else (L*1.3 - 30.0)
            hole_lo[i] = max(hole_lo[i], hp[i] - 20)
            hole_hi[i] = min(hole_hi[i], hp[i] + 20)
            if hole_lo[i] > hole_hi[i]:
                hole_lo[i] = hp[i] - 1
                hole_hi[i] = hp[i] + 1

        bore_r = cfg["bore_radius"]
        rad_lo = max(3.0, bore_r * 0.5)
        rad_hi = min(15.0, bore_r * 2.0)
        hd_min = bore_r * 0.4
        hd_max = bore_r * 0.9

        # Stage 1: bore length
        def obj_bore(x):
            return safe_eval(radii, x[0], hp, hd, hl)
        r = sp_min(obj_bore, [L], method='L-BFGS-B',
                   bounds=[(L*0.85, L*1.15)], options={"maxiter": 100, "ftol": 1e-8})
        L = r.x[0]

        # Stage 2: bore radii
        rad_bounds = [(rad_lo, rad_hi)] * n_cp
        def obj_rad(x):
            return safe_eval(np.maximum(x, rad_lo), L, hp, hd, hl)
        r = sp_min(obj_rad, radii, method='L-BFGS-B', bounds=rad_bounds,
                    options={"maxiter": 200, "ftol": 1e-8})
        radii = np.maximum(r.x, rad_lo)

        # Stage 3: holes + diameters
        n_h = len(hp)
        hole_bounds = [(hole_lo[i], hole_hi[i]) for i in range(n_h)]
        diam_bounds = [(hd_min, hd_max)] * n_h
        if n_h > 0:
            def obj_holes(x):
                return safe_eval(radii, L, x[:n_h].tolist(), x[n_h:].tolist(), hl)
            x0_hd = np.array(hp + hd)
            r = sp_min(obj_holes, x0_hd, method='L-BFGS-B',
                        bounds=hole_bounds + diam_bounds, options={"maxiter": 200, "ftol": 1e-8})
            hp = r.x[:n_h].tolist()
            hd = r.x[n_h:].tolist()

        # Stage 4: simultaneous
        all_bounds = [(L*0.85, L*1.15)] + rad_bounds + hole_bounds + diam_bounds
        def obj_all(x):
            L_i = x[0]
            rad_i = np.maximum(x[1:1+n_cp], rad_lo)
            hp_i = x[1+n_cp:1+n_cp+n_h]
            hd_i = x[1+n_cp+n_h:1+n_cp+2*n_h]
            return safe_eval(rad_i, L_i, hp_i.tolist(), hd_i.tolist(), hl)
        x0 = np.concatenate([[L], radii, np.array(hp), np.array(hd)])
        r = sp_min(obj_all, x0, method='L-BFGS-B', bounds=all_bounds,
                    options={"maxiter": 300, "ftol": 1e-10})
        L = r.x[0]
        radii = np.maximum(r.x[1:1+n_cp], rad_lo)
        hp = r.x[1+n_cp:1+n_cp+n_h].tolist()
        hd = r.x[1+n_cp+n_h:1+n_cp+2*n_h].tolist()

        final_rms = safe_eval(radii, L, hp, hd, hl)
        dt = time.time() - t0

        return {
            "name": name,
            "rms_cents": final_rms,
            "bore_length": L,
            "time_s": round(dt, 2),
            "hole_positions": hp,
            "hole_diameters": hd,
            "status": "ok",
        }
    except Exception as e:
        dt = time.time() - t0
        return {
            "name": name,
            "rms_cents": 9999,
            "time_s": round(dt, 2),
            "status": f"error: {e}",
        }


def main():
    print("=" * 72)
    print("  DASK-PARALLELIZED INSTRUMENT OPTIMIZATION BENCHMARK")
    print("=" * 72)

    # Connect to Dask
    print("\nConnecting to Dask scheduler...")
    client = Client("tcp://100.69.113.41:9797", timeout=15)
    time.sleep(1)
    info = client.scheduler_info()
    workers = info.get("workers", {})
    print(f"  Scheduler: {info.get('address', '?')}")
    print(f"  Workers: {len(workers)}")
    for addr, w in workers.items():
        print(f"    {addr}: nthreads={w.get('nthreads', '?')}")
    print(f"  Dashboard: {client.dashboard_link}")

    instruments = list(INSTRUMENTS.items())

    # ── Test 1: Serial baseline ──────────────────────────────────────────
    print("\n" + "─" * 72)
    print("  TEST 1: Serial baseline (all 12 instruments)")
    print("─" * 72)
    t0 = time.time()
    serial_results = []
    for name, cfg in instruments:
        r = optimize_one(name, cfg)
        serial_results.append(r)
        tag = "OK" if r["rms_cents"] < 3 else "FAIL"
        print(f"  [{tag}] {name:30s}  {r['rms_cents']:8.4f}c  {r['time_s']:5.1f}s  L={r.get('bore_length', 0):.1f}mm")
    serial_total = time.time() - t0
    print(f"\n  Serial total: {serial_total:.1f}s")

    # ── Test 2: Dask parallel (all 12 instruments) ──────────────────────
    print("\n" + "─" * 72)
    print("  TEST 2: Dask parallel (all 12 instruments)")
    print("─" * 72)
    t0 = time.time()
    futures = {name: client.submit(optimize_one, name, cfg) for name, cfg in instruments}
    parallel_results = []
    for name, future in futures.items():
        r = future.result()
        parallel_results.append(r)
        tag = "OK" if r["rms_cents"] < 3 else "FAIL"
        print(f"  [{tag}] {name:30s}  {r['rms_cents']:8.4f}c  {r['time_s']:5.1f}s  L={r.get('bore_length', 0):.1f}mm")
    parallel_total = time.time() - t0
    print(f"\n  Parallel total: {parallel_total:.1f}s")
    print(f"  Speedup: {serial_total / parallel_total:.2f}x")

    # ── Test 3: Multi-run consistency (3 runs per instrument) ───────────
    print("\n" + "─" * 72)
    print("  TEST 3: Consistency (3 runs per instrument, all parallel)")
    print("─" * 72)
    t0 = time.time()
    multi_futures = []
    for run_i in range(3):
        for name, cfg in instruments:
            multi_futures.append((run_i, client.submit(optimize_one, name, cfg)))
    
    multi_results = {}
    for run_i, future in multi_futures:
        r = future.result()
        key = f"{r['name']}_run{run_i}"
        multi_results[key] = r

    # Aggregate by instrument
    from collections import defaultdict
    agg = defaultdict(list)
    for key, r in multi_results.items():
        name = r["name"]
        agg[name].append(r["rms_cents"])

    print(f"\n  {'Instrument':30s}  {'Min':>8s}  {'Max':>8s}  {'Mean':>8s}  {'Std':>8s}")
    print(f"  {'─'*30}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}")
    for name in [n for n, _ in instruments]:
        vals = agg[name]
        import numpy as np
        arr = np.array(vals)
        print(f"  {name:30s}  {arr.min():8.4f}  {arr.max():8.4f}  {arr.mean():8.4f}  {arr.std():8.4f}")
    multi_total = time.time() - t0
    print(f"\n  Multi-run total: {multi_total:.1f}s (36 optimizations)")

    # ── Summary ──────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print("  SUMMARY")
    print("=" * 72)
    print(f"  Instruments:    {len(instruments)}")
    print(f"  Serial total:   {serial_total:.1f}s")
    print(f"  Parallel total: {parallel_total:.1f}s")
    print(f"  Speedup:        {serial_total / parallel_total:.2f}x")
    print(f"  Multi-run:      {multi_total:.1f}s (36 optimizations)")
    ok_count = sum(1 for r in parallel_results if r["rms_cents"] < 3)
    print(f"  Pass rate:      {ok_count}/{len(instruments)} (< 3c RMS)")
    print(f"  Workers:        {len(workers)}")

    # Save results
    out_path = os.path.join(os.path.dirname(__file__), "benchmark_results.json")
    with open(out_path, "w") as f:
        json.dump({
            "serial": serial_results,
            "parallel": parallel_results,
            "multi_run": {k: v for k, v in multi_results.items()},
            "summary": {
                "instruments": len(instruments),
                "serial_total_s": serial_total,
                "parallel_total_s": parallel_total,
                "speedup": serial_total / parallel_total,
                "multi_run_total_s": multi_total,
                "workers": len(workers),
                "pass_rate": f"{ok_count}/{len(instruments)}",
            },
        }, f, indent=2)
    print(f"\n  Results saved to: {out_path}")

    client.close()
    print("\nDone!")


if __name__ == "__main__":
    main()
