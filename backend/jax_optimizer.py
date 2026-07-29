"""
JAX-enhanced bore optimizer.

Strategy (matching sequential_refined from benchmark_all.py):
  Phase 0: Sequential hole placement (smart initialization)
  Phase 1: 4-stage L-BFGS-B refinement (bore → radii → holes → all)
  Phase 2: (optional) CMA-ES global polish with tight bounds

Uses Python TMM throughout (proven correct, sub-3c RMS).
JAX is used only for fast batch evaluation in Phase 2.
"""
import os, sys, time, math
import numpy as np

os.environ["JAX_ENABLE_X64"] = "1"

try:
    import jax
    jax.config.update("jax_enable_x64", True)
    _HAVE_JAX = True
except Exception:
    _HAVE_JAX = False

from scipy.optimize import minimize as sp_min
from backend.tmm_acoustics import (
    tmm_instrument_from_radii, SPEED_OF_SOUND,
)

c = SPEED_OF_SOUND


# ============================================================================
# Cost evaluation (matches benchmark_all.py eval_all exactly)
# ============================================================================

def eval_all(radii=None, bore_length=None, hp=None, hd=None, hl=None, closed_top=False, targets=None, n_reg=None,
             w_int=1.0, bore_radius=None, w_mono=0.3, fingerings=None, bore_profile=None):
    """Blended intonation + timbre cost.

    Either radii + bore_length (legacy flat array) or bore_profile (SplineBore)
    can be provided for the bore geometry.

    w_int=1.0: pure intonation (default, backward compatible)
    w_int=0.0: pure timbre (bore smoothness + hole radiation consistency)
    w_mono: weight for bore monotonicity penalty (part of timbre cost)
    fingerings: optional list of fingering patterns per target note
    bore_profile: optional SplineBore instance for variable-radius bore
    """
    from backend.pareto_optimizer import compute_timbre_cost

    # Handle SplineBore: convert to radii array for TMM evaluation
    if bore_profile is not None:
        radii = bore_profile.to_radii_array()
        bore_length = bore_profile.bore_length

    inst = tmm_instrument_from_radii(
        radii, bore_length, hp, hd, hl,
        outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
    )
    if n_reg is None:
        n_reg = 1 if closed_top else 2

    # Build fingerings from cumulative open holes (default)
    n_holes = len(hp)
    if fingerings is None:
        fingerings = []
        for k in range(n_holes):
            f = ['open'] * (k + 1) + ['closed'] * (n_holes - k - 1)
            fingerings.append(f)
        if closed_top:
            fingerings.insert(0, ['closed'] * n_holes)

    tw = [c / f for f in targets]
    freqs = inst.compute_fingered_frequencies(tw, fingerings, n_reg)

    cents = []
    for a, t in zip(freqs, targets):
        cents.append(1200.0 * math.log2(a / t) if a > 0 and math.isfinite(a) else 1e10)
    ca = np.array(cents)
    if np.any(np.abs(ca) > 1e5):
        return 1e10
    intonation_cost = float(np.sqrt(np.mean(ca ** 2)))

    if w_int >= 1.0:
        return intonation_cost

    timbre_cost = compute_timbre_cost(
        radii, hd, bore_radius if bore_radius else 7.25, w_mono=w_mono,
    )
    return w_int * intonation_cost + (1.0 - w_int) * timbre_cost


def safe_eval(radii=None, bore_length=None, hp=None, hd=None, hl=None, closed_top=False, targets=None, n_reg=None,
              w_int=1.0, bore_radius=None, w_mono=0.3, fingerings=None, bore_profile=None):
    try:
        return eval_all(radii=radii, bore_length=bore_length, hp=hp, hd=hd, hl=hl,
                        closed_top=closed_top, targets=targets, n_reg=n_reg,
                        w_int=w_int, bore_radius=bore_radius, w_mono=w_mono,
                        fingerings=fingerings, bore_profile=bore_profile)
    except Exception:
        return 1e10


# ============================================================================
# Phase 0: Sequential hole placement (from benchmark_all.py)
# ============================================================================

def sequential_placement(cfg):
    """Sequential hole placement — same as benchmark_all.py sequential()."""
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

    from scipy.optimize import minimize as sp_min
    r = sp_min(bore_obj, [L_est], method='L-BFGS-B',
               bounds=[(L_est * 0.7, L_est * 1.3)],
               options={"maxiter": 50, "ftol": 1e-8})
    bore_length = r.x[0]

    hp, hd, hl = [], [], []
    hole_targets = targets[1:]

    for k, target in enumerate(hole_targets):
        min_p = hp[-1] + 15 if hp else 30
        max_p = bore_length - 30
        if min_p >= max_p:
            break

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

    rms = safe_eval(bore_radii, bore_length, hp, hd, hl, closed_top, targets, n_reg)
    return rms, bore_length, bore_radii, hp, hd, hl


# ============================================================================
# Phase 1: 4-stage L-BFGS-B refinement (from benchmark_all.py sequential_refined)
# ============================================================================

def refine_sequential(cfg: dict, verbose: bool = False, use_jax_bore: bool = False, w_int: float = 1.0, w_mono: float = 0.3, n_cp: int = 6):
    """Sequential + DE global re-optim + 4-stage L-BFGS-B refinement.

    Matches benchmark_all.py sequential_refined exactly.
    When use_jax_bore=True, Stage 2 (bore-radii) uses JAX autodiff instead
    of finite differences.

    w_int: weight for intonation (1.0=pure intonation, 0.0=pure timbre).
    w_mono: weight for bore monotonicity penalty (part of timbre cost).
    """
    from scipy.optimize import differential_evolution

    rms_seq, L_seq, bore_radii, hp, hd, hl = sequential_placement(cfg)
    t0 = time.time()

    n_h = len(hp)
    L = L_seq
    if len(bore_radii) != n_cp:
        if len(bore_radii) < n_cp:
            radii = np.concatenate([bore_radii, np.full(n_cp - len(bore_radii), bore_r)])
        else:
            radii = bore_radii[:n_cp].copy()
    else:
        radii = bore_radii.copy()
    closed_top = cfg["closed_top"]
    targets = cfg["targets"]
    bore_r = cfg["bore_radius"]

    hd_min = bore_r * 0.4
    hd_max = bore_r * 0.9

    def safe_eval_local(radii, L, hp, hd, hl):
        return safe_eval(radii, L, hp, hd, hl, closed_top, targets,
                         w_int=w_int, bore_radius=bore_r, w_mono=w_mono)

    # DE global re-optimization for open-open instruments
    if not closed_top and n_h > 0:
        if verbose:
            print("    Phase 2b: Global hole re-optimization (DE)")
        radii_de = np.full(n_cp, bore_r)

        def obj_de(x):
            hp_sorted = []
            hd_sorted = []
            idx_sorted = np.argsort(x[:n_h].tolist())
            for j in idx_sorted:
                hp_sorted.append(x[j])
                hd_sorted.append(x[n_h + j])
            return safe_eval_local(radii_de, L, hp_sorted, hd_sorted, hl)

        de_bounds = []
        for i in range(n_h):
            lo = int(i * L / (n_h * 1.5 + 1))
            hi = int((i + 2) * L / (n_h * 1.5 + 1))
            lo = max(lo, 20)
            hi = min(hi, int(L - 20))
            if hi <= lo:
                hi = lo + 10
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
        if verbose:
            print(f"      RMS={result_de.fun:.2f}c  Holes: {[f'{p:.0f}mm/{d:.1f}mm' for p, d in zip(hp, hd)]}")

    # Non-crossing bounds
    GAP = 5.0
    hole_lo, hole_hi = [0.0] * n_h, [0.0] * n_h
    for i in range(n_h):
        hole_lo[i] = (hp[i - 1] + GAP) if i > 0 else 30.0
        hole_hi[i] = (hp[i + 1] - GAP) if i < n_h - 1 else (L * 1.3 - 30.0)
        hole_lo[i] = max(hole_lo[i], hp[i] - 20)
        hole_hi[i] = min(hole_hi[i], hp[i] + 20)
        if hole_lo[i] > hole_hi[i]:
            hole_lo[i] = hp[i] - 1
            hole_hi[i] = hp[i] + 1

    rad_lo = max(3.0, bore_r * 0.5)
    rad_hi = min(15.0, bore_r * 2.0)
    rad_bounds = [(rad_lo, rad_hi)] * n_cp

    # Stage 1: Bore length only
    def obj_bore_length(x):
        return safe_eval_local(radii, x[0], hp, hd, hl)
    r = sp_min(obj_bore_length, [L], method='L-BFGS-B',
               bounds=[(L * 0.85, L * 1.15)], options={"maxiter": 100, "ftol": 1e-8})
    L = r.x[0]

    # Stage 2: Bore-radii only
    if n_cp > 0:
        use_jax = use_jax_bore and closed_top  # JAX phase cost only reliable for n_reg=1
        if use_jax:
            radii, cost_jax, n_evals = jax_stage2_refine(
                radii, L, hp, hd, hl, closed_top, targets,
                rad_lo, rad_bounds, cfg["outer_diameter"], n_cp,
            )
            if verbose:
                print(f"      JAX Stage 2: RMS={cost_jax:.4f}c ({n_evals} evals)")
        else:
            def obj_radii(x):
                return safe_eval_local(np.maximum(x, rad_lo), L, hp, hd, hl)
            r = sp_min(obj_radii, radii, method='L-BFGS-B',
                        bounds=rad_bounds, options={"maxiter": 200, "ftol": 1e-8})
            radii = np.maximum(r.x, rad_lo)

    # Stage 3: Hole positions + diameters
    if n_h > 0:
        hole_bounds = [(hole_lo[i], hole_hi[i]) for i in range(n_h)]
        hole_diam_bounds = [(hd_min, hd_max)] * n_h

        def obj_holes_and_diams(x):
            return safe_eval_local(radii, L, x[:n_h].tolist(), x[n_h:].tolist(), hl)
        x0_hd = np.array(hp + hd)
        all_hole_bounds = hole_bounds + hole_diam_bounds
        r = sp_min(obj_holes_and_diams, x0_hd, method='L-BFGS-B',
                    bounds=all_hole_bounds, options={"maxiter": 200, "ftol": 1e-8})
        hp = r.x[:n_h].tolist()
        hd = r.x[n_h:].tolist()

    # Stage 4: Simultaneous fine-tune
    hole_bounds = [(hole_lo[i], hole_hi[i]) for i in range(n_h)] if n_h > 0 else []
    hole_diam_bounds = [(hd_min, hd_max)] * n_h if n_h > 0 else []
    all_bounds = [(L * 0.85, L * 1.15)]
    if n_cp > 0:
        all_bounds += rad_bounds
    if n_h > 0:
        all_bounds += hole_bounds
        all_bounds += hole_diam_bounds

    def obj_all(x):
        L_i = x[0]
        rad_i = np.maximum(x[1:1 + n_cp], rad_lo) if n_cp > 0 else radii
        hp_i = x[1 + n_cp:1 + n_cp + n_h]
        hd_i = x[1 + n_cp + n_h:1 + n_cp + 2 * n_h]
        return safe_eval_local(rad_i, L_i, hp_i.tolist(), hd_i.tolist(), hl)

    x0 = np.concatenate([[L], radii, np.array(hp), np.array(hd)])
    r = sp_min(obj_all, x0, method='L-BFGS-B',
                bounds=all_bounds, options={"maxiter": 300, "ftol": 1e-10})
    L = r.x[0]
    radii = np.maximum(r.x[1:1 + n_cp], rad_lo) if n_cp > 0 else radii
    hp = r.x[1 + n_cp:1 + n_cp + n_h].tolist()
    hd = r.x[1 + n_cp + n_h:1 + n_cp + 2 * n_h].tolist()

    rms = safe_eval_local(radii, L, hp, hd, hl)
    return rms, L, radii, hp, hd, hl, time.time() - t0


# ============================================================================
# Stage 2: JAX autodiff bore-radii refinement
# ============================================================================

def jax_stage2_refine(radii, L, hp, hd, hl, closed_top, targets,
                      rad_lo, rad_bounds, outer_diameter=22.0, n_cp=6):
    """Stage 2: bore-radii refinement using JAX automatic differentiation.

    Builds the JAX action chain once (constant during bore-radii optimization),
    creates a JIT-compiled phase cost function, and runs L-BFGS-B with exact
    gradients from jax.grad.

    Returns (radii_optimized, cost, n_evals).
    """
    import jax.numpy as jnp
    from backend.tmm_acoustics_jax import (
        build_chain_for_optimizer, make_phase_cost,
    )

    n_reg = 1 if closed_top else 2
    targets_sorted = sorted(targets)
    wavelengths = [c / f for f in targets_sorted]

    n_holes = len(hp)
    fingering_sets = []
    for k in range(n_holes):
        f = ['open'] * (k + 1) + ['closed'] * (n_holes - k - 1)
        fingering_sets.append(f)
    if closed_top:
        fingering_sets.insert(0, ['closed'] * n_holes)
    else:
        fingering_sets.insert(0, ['closed'] * n_holes)

    n_targets = len(targets_sorted)
    if len(fingering_sets) != n_targets:
        fingering_sets = fingering_sets[:n_targets]

    max_holes = max((len(fs) for fs in fingering_sets), default=0)
    fs_jax = []
    for fs in fingering_sets:
        arr = jnp.zeros(max_holes + 1, dtype=jnp.float32)
        for i, h in enumerate(fs):
            arr = arr.at[i].set(1.0 if h == 'open' else 0.0)
        fs_jax.append(arr)

    chain = build_chain_for_optimizer(
        L, jnp.array(radii), hp, hd, hl, closed_top, n_cp, outer_diameter,
    )

    cost_fn = make_phase_cost(chain, targets_sorted, fs_jax, wavelengths, n_register=n_reg)
    grad_fn = jax.grad(cost_fn)

    radii_jax = jnp.array(np.maximum(radii, rad_lo), dtype=jnp.float64)
    n_evals = [0]
    last_grad = [None]

    def obj(x):
        x_c = jnp.maximum(x, rad_lo)
        val = float(cost_fn(x_c))
        n_evals[0] += 1
        return val

    def jac(x):
        x_c = jnp.maximum(x, rad_lo)
        g = np.array(grad_fn(x_c), dtype=np.float64)
        last_grad[0] = g
        return g

    r = sp_min(obj, radii_jax, jac=jac, method='L-BFGS-B',
               bounds=rad_bounds, options={"maxiter": 200, "ftol": 1e-8})

    return np.maximum(r.x, rad_lo), r.fun, n_evals[0]


# ============================================================================
# Robust bore optimization (manufacturing-aware)
# ============================================================================

def refine_robust(radii, L, hp, hd, hl, closed_top, targets, bore_r,
                  noise_mm=0.05, n_samples=16, w_int=1.0, w_mono=0.3, verbose=False):
    """Robust bore optimization: minimize expected cost under manufacturing noise.

    Instead of optimizing for a perfect bore, optimize for the best *expected*
    intonation given Gaussian bore-radius perturbations (simulating SLA/FDM
    print tolerance).

    Uses Monte Carlo sampling with FIXED noise directions (squared-gradient
    estimator) so the objective is deterministic — L-BFGS-B converges properly.

    Parameters
    ----------
    noise_mm : float
        Std dev of Gaussian noise added to bore radii (mm).
    n_samples : int
        Number of noise samples per evaluation.
    w_int : float
        Intonation weight (1.0 = pure intonation).
    w_mono : float
        Weight for bore monotonicity penalty (part of timbre cost).

    Returns
    -------
    tuple : (radii_robust, mean_cost, std_cost, nominal_cost, time_s)
    """
    n_cp = len(radii)
    t0 = time.time()

    # Pre-generate fixed noise samples (same for every evaluation)
    rng = np.random.RandomState(42)
    noise_bank = rng.normal(0, noise_mm, size=(n_samples, n_cp))

    def safe_eval_local(r, L_i, hp_i, hd_i, hl_i):
        return safe_eval(r, L_i, hp_i, hd_i, hl_i, closed_top, targets,
                         w_int=w_int, bore_radius=bore_r, w_mono=w_mono)

    def robust_cost(radii_v):
        """Expected cost over fixed noise samples."""
        costs = np.zeros(n_samples)
        for s in range(n_samples):
            perturbed = np.maximum(radii_v + noise_bank[s], 0.5)
            costs[s] = safe_eval_local(perturbed, L, hp, hd, hl)
        return np.mean(costs)

    # Baseline: nominal cost
    nominal_cost = safe_eval_local(radii, L, hp, hd, hl)

    # L-BFGS-B on the robust objective
    rad_lo = max(3.0, bore_r * 0.5)
    rad_hi = min(15.0, bore_r * 2.0)
    rad_bounds = [(rad_lo, rad_hi)] * n_cp

    r = sp_min(robust_cost, radii, method='L-BFGS-B',
               bounds=rad_bounds, options={"maxiter": 100, "ftol": 1e-8})
    radii_robust = np.maximum(r.x, rad_lo)

    # Evaluate final robust cost with separate noise bank
    rng_final = np.random.RandomState(99)
    noise_bank_final = rng_final.normal(0, noise_mm, size=(50, n_cp))
    costs_final = np.zeros(50)
    for s in range(50):
        perturbed = np.maximum(radii_robust + noise_bank_final[s], 0.5)
        costs_final[s] = safe_eval_local(perturbed, L, hp, hd, hl)

    mean_cost = float(np.mean(costs_final))
    std_cost = float(np.std(costs_final))
    nominal_robust = float(safe_eval_local(radii_robust, L, hp, hd, hl))
    dt = time.time() - t0

    if verbose:
        print(f"      Robust refinement: nominal={nominal_robust:.4f}c "
              f"mean={mean_cost:.4f}c (+/-{std_cost:.4f}c) "
              f"vs baseline nominal={nominal_cost:.4f}c ({dt:.1f}s)")

    return radii_robust, mean_cost, std_cost, nominal_robust, dt


# ============================================================================
# Main entry point
# ============================================================================

def jax_two_phase_optimize(
    bore_length: float = None,
    n_holes: int = None,
    hole_lens: list = None,
    targets: list = None,
    fingerings: list = None,
    bore_radius: float = 7.25,
    outer_diameter: float = 22.0,
    hole_diameter: float = 7.0,
    hole_length: float = 3.75,
    n_register: int = None,
    closed_top: bool = False,
    bore_bounds_range: tuple = (3.0, 18.0),
    hole_pos_bounds_range: tuple = (10.0, None),
    maxfevals: int = 5000,
    n_iters: int = 500,
    seed: int = 42,
    verbose: bool = True,
    loss_model=None,
    use_jax_bore: bool = False,
    w_int: float = 1.0,
) -> dict:
    """Optimize bore for intonation (and optionally timbre).

    Uses the proven sequential_refined approach from benchmark_all.py.
    Auto-detects n_register from closed_top if not specified.

    w_int: weight for intonation (1.0=pure intonation, 0.0=pure timbre).
           Intermediate values (e.g. 0.9) blend both objectives.
    """
    if n_register is None:
        n_register = 1 if closed_top else 2

    cfg = {
        "closed_top": closed_top,
        "targets": targets,
        "bore_radius": bore_radius,
        "outer_diameter": outer_diameter,
        "hole_diameter": hole_diameter,
        "hole_length": hole_length,
    }

    if verbose:
        print("=" * 70)
        print("  BORE OPTIMIZER (sequential_refined approach)")
        print("=" * 70)
        print(f"  {'Closed-open (clarinet)' if closed_top else 'Open-open (sax/flute)'}")
        print(f"  n_register: {n_register}")
        print(f"  Targets: {[f'{f:.1f}' for f in targets]} Hz")
        print(f"  Holes: {n_holes if n_holes else len(targets) - (1 if closed_top else 0)}")
        print()

    t0 = time.time()

    if verbose:
        mode = "JAX autodiff" if use_jax_bore else "Python TMM + finite diff"
        print(f"  Phase 0+1: Sequential placement + DE re-optim + L-BFGS-B refinement")
        print(f"  Stage 2 mode: {mode}")
    rms, L, radii, hp, hd, hl, t_refine = refine_sequential(
        cfg, verbose=verbose, use_jax_bore=use_jax_bore, w_int=w_int,
    )
    t_total = time.time() - t0

    if verbose:
        print(f"  RMS: {rms:.4f} cents ({t_total:.1f}s)")
        print(f"  Bore length: {L:.1f}mm")
        print(f"  Hole positions: {[f'{p:.1f}' for p in hp]}")
        print(f"  Hole diameters: {[f'{d:.1f}' for d in hd]}")

    # Build final instrument
    n_reg = 1 if closed_top else 2
    inst = tmm_instrument_from_radii(
        radii, L, hp, hd, hl,
        outer_diameter_mm=outer_diameter, closed_top=closed_top, cone_step=0.5,
    )

    return {
        'final_cost': rms,
        'total_time': t_total,
        'bore_length': L,
        'bore_radii': radii.tolist(),
        'hole_positions': hp,
        'hole_diameters': hd,
        'hole_lengths': hl,
        'best_instrument': inst,
    }


def robust_optimize(
    targets: list,
    bore_radius: float = 7.25,
    outer_diameter: float = 22.0,
    hole_diameter: float = 7.0,
    hole_length: float = 3.75,
    closed_top: bool = False,
    noise_mm: float = 0.05,
    n_samples: int = 16,
    verbose: bool = True,
    use_jax_bore: bool = False,
    w_int: float = 1.0,
) -> dict:
    """Full optimization pipeline with robust refinement.

    Runs standard sequential_refined, then adds robust refinement that
    accounts for manufacturing noise (Gaussian bore-radius perturbation).

    Parameters
    ----------
    noise_mm : float
        Manufacturing tolerance std dev in mm.
    n_samples : int
        Monte Carlo samples for robust cost evaluation.
    """
    cfg = {
        "closed_top": closed_top,
        "targets": targets,
        "bore_radius": bore_radius,
        "outer_diameter": outer_diameter,
        "hole_diameter": hole_diameter,
        "hole_length": hole_length,
    }

    if verbose:
        print("=" * 70)
        print("  ROBUST BORE OPTIMIZER (manufacturing-aware)")
        print("=" * 70)
        print(f"  Noise tolerance: +/-{noise_mm}mm (std)")
        print(f"  MC samples: {n_samples}")
        print()

    t0 = time.time()

    # Standard optimization first
    rms, L, radii, hp, hd, hl, t_refine = refine_sequential(
        cfg, verbose=verbose, use_jax_bore=use_jax_bore, w_int=w_int,
    )

    if verbose:
        print(f"  Standard result: RMS={rms:.4f}c")
        print(f"  Now running robust refinement ({noise_mm}mm noise)...")

    # Robust refinement
    radii_robust, mean_cost, std_cost, nominal_robust, t_robust = refine_robust(
        radii, L, hp, hd, hl, closed_top, targets, bore_radius,
        noise_mm=noise_mm, n_samples=n_samples, w_int=w_int, verbose=verbose,
    )

    t_total = time.time() - t0

    if verbose:
        print(f"  ---")
        print(f"  Standard:  nominal={rms:.4f}c")
        print(f"  Robust:    nominal={nominal_robust:.4f}c, expected={mean_cost:.4f}c (+/-{std_cost:.4f}c)")
        print(f"  Total time: {t_total:.1f}s")

    inst = tmm_instrument_from_radii(
        radii_robust, L, hp, hd, hl,
        outer_diameter_mm=outer_diameter, closed_top=closed_top, cone_step=0.5,
    )

    return {
        'final_cost': nominal_robust,
        'expected_cost': mean_cost,
        'expected_std': std_cost,
        'standard_cost': rms,
        'total_time': t_total,
        'bore_length': L,
        'bore_radii': radii_robust.tolist(),
        'hole_positions': hp,
        'hole_diameters': hd,
        'hole_lengths': hl,
        'best_instrument': inst,
    }


if __name__ == "__main__":
    targets = [261.6, 293.7, 329.6, 349.2, 392.0, 440.0]

    print("=" * 70)
    print("  A/B TEST: Python TMM (finite diff) vs JAX autodiff")
    print("=" * 70)

    print("\n--- Mode A: Python TMM + finite differences ---")
    t0 = time.time()
    result_a = jax_two_phase_optimize(
        n_holes=6, targets=targets, bore_radius=7.25,
        outer_diameter=22.0, hole_diameter=7.0, hole_length=3.75,
        closed_top=True, verbose=True, use_jax_bore=False,
    )
    t_a = time.time() - t0

    print(f"\n--- Mode B: JAX autodiff ---")
    t0 = time.time()
    result_b = jax_two_phase_optimize(
        n_holes=6, targets=targets, bore_radius=7.25,
        outer_diameter=22.0, hole_diameter=7.0, hole_length=3.75,
        closed_top=True, verbose=True, use_jax_bore=True,
    )
    t_b = time.time() - t0

    print("\n" + "=" * 70)
    print("  A/B COMPARISON")
    print("=" * 70)
    print(f"  Python TMM:  RMS={result_a['final_cost']:.4f}c  time={t_a:.1f}s")
    print(f"  JAX autodiff: RMS={result_b['final_cost']:.4f}c  time={t_b:.1f}s")
    rms_diff = abs(result_a['final_cost'] - result_b['final_cost'])
    speedup = t_a / t_b if t_b > 0 else 0
    print(f"  RMS diff: {rms_diff:.6f}c")
    print(f"  Speedup: {speedup:.2f}x")
