"""
Manufacturing tolerance sensitivity analysis (Phase 1h-e).

Perturbs optimized bore profiles with Gaussian noise to simulate
3D-printing dimensional errors. Measures how intonation degrades
under realistic manufacturing tolerances.

Phase 2 (3D printing) needs to know:
  - Which instruments are most sensitive to bore errors?
  - What print accuracy is required to maintain <3c intonation?
  - Is SLA ±0.05-0.1mm tolerance sufficient?
"""
import sys, time, json, math
from pathlib import Path
from datetime import datetime, timezone

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.benchmark_all import INSTRUMENTS
from backend.jax_optimizer import refine_sequential, eval_all, tmm_instrument_from_radii


def measure_sensitivity(
    name: str,
    cfg: dict,
    noise_mm: float = 0.1,
    n_trials: int = 50,
    seed: int = 42,
) -> dict:
    """Monte Carlo: perturb optimized bore profile, re-evaluate intonation."""
    rng = np.random.RandomState(seed)
    targets = cfg["targets"]
    closed_top = cfg["closed_top"]
    bore_r = cfg["bore_radius"]

    # Optimize
    t0 = time.time()
    try:
        result = refine_sequential(cfg, verbose=False, use_jax_bore=True, w_int=1.0)
    except Exception as e:
        return {"error": str(e)[:100], "noise_mm": noise_mm}

    rms_base = result[0]
    L = result[1]
    radii = np.array(result[2])
    hp = result[3]
    hd = result[4]
    hl = result[5]

    n_h = len(hp)
    bore_length = L

    # Baseline cost (re-evaluate to confirm)
    baseline_cost = rms_base

    # Monte Carlo perturbation
    costs = []
    for _ in range(n_trials):
        noise = rng.normal(0, noise_mm, size=radii.shape)
        perturbed = radii + noise
        perturbed = np.maximum(perturbed, 0.5)

        cost = eval_all(
            perturbed, bore_length, hp, hd, hl, closed_top, targets, w_int=1.0,
        )
        costs.append(cost)

    costs = np.array(costs)
    dt = time.time() - t0

    n_within_1 = int(np.sum(costs < 1.0))
    n_within_3 = int(np.sum(costs < 3.0))
    sensitivity = float(np.mean(costs) / max(baseline_cost, 1e-10))

    return {
        "instrument": name,
        "type": "closed" if closed_top else "open",
        "noise_mm": noise_mm,
        "n_trials": n_trials,
        "baseline_cost": float(baseline_cost),
        "mean_cost": float(np.mean(costs)),
        "std_cost": float(np.std(costs)),
        "max_cost": float(np.max(costs)),
        "p5_cost": float(np.percentile(costs, 5)),
        "p95_cost": float(np.percentile(costs, 95)),
        "n_within_1c": n_within_1,
        "n_within_3c": n_within_3,
        "pct_within_1c": round(100 * n_within_1 / n_trials, 1),
        "pct_within_3c": round(100 * n_within_3 / n_trials, 1),
        "sensitivity_factor": sensitivity,
        "time_s": round(dt, 1),
    }


def main():
    print("=" * 72)
    print("Manufacturing Tolerance Sensitivity Analysis (Phase 1h-e)")
    print("=" * 72)

    tolerances = [0.05, 0.1]  # mm std dev

    all_results = {}

    for noise_mm in tolerances:
        print(f"\n--- Tolerance: +/-{noise_mm}mm std ---")
        print(f"{'Instrument':<22} {'Type':<7} {'Base':>6} {'Mean':>6} {'P95':>6} "
              f"{'<1c':>5} {'<3c':>5} {'Sens':>6}")
        print(f"{'-'*22} {'-'*7} {'-'*6} {'-'*6} {'-'*6} {'-'*5} {'-'*5} {'-'*6}")

        for name, cfg in INSTRUMENTS.items():
            if cfg.get("_chromatic", False):
                continue

            result = measure_sensitivity(name, cfg, noise_mm=noise_mm, n_trials=50)

            if "error" in result:
                print(f"{name:<22} {'':7}  FAIL  {result['error'][:30]}")
                continue

            key = f"{name}_{noise_mm}"
            all_results[key] = result

            print(f"{name:<22} {result['type']:<7} "
                  f"{result['baseline_cost']:>5.2f}c "
                  f"{result['mean_cost']:>5.2f}c "
                  f"{result['p95_cost']:>5.2f}c "
                  f"{result['pct_within_1c']:>4.0f}% "
                  f"{result['pct_within_3c']:>4.0f}% "
                  f"{result['sensitivity_factor']:>5.1f}x")

    # Summary
    print("\n" + "=" * 72)
    print("SUMMARY")
    print("=" * 72)

    for noise_mm in tolerances:
        print(f"\nTolerance ±{noise_mm}mm:")
        robust = []
        sensitive = []
        for name, cfg in INSTRUMENTS.items():
            if cfg.get("_chromatic", False):
                continue
            key = f"{name}_{noise_mm}"
            if key in all_results:
                r = all_results[key]
                if r["pct_within_3c"] == 100:
                    robust.append(name)
                if r["sensitivity_factor"] > 10.0:
                    sensitive.append((name, r))

        if robust:
            print(f"  Robust (100% within 3c): {', '.join(robust)}")
        if sensitive:
            print(f"  Sensitive (>10x degradation):")
            for n, r in sorted(sensitive, key=lambda x: -x[1]["sensitivity_factor"]):
                print(f"    {n}: {r['sensitivity_factor']:.1f}x, "
                      f"mean={r['mean_cost']:.2f}c, p95={r['p95_cost']:.2f}c")

    # Save
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out = Path(__file__).parent / f"tolerance_sensitivity_{ts}.json"
    with open(out, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nSaved to {out}")


if __name__ == "__main__":
    main()
