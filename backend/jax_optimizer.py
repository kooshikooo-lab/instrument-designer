"""
JAX-powered two-phase optimizer.

Phase 1: CMA-ES + JAX vmap (fast global search)
  - CMA-ES generates candidates
  - JAX vmap batches resonance evaluation across all candidates × fingerings
  - Phase-based cost (smooth, register-aware)

Phase 2: L-BFGS-B + Python TMM (correct local refinement)
  - Uses existing peak_cost_nearest for correct register detection
  - Fine-tunes the best Phase 1 result

Key advantage: JAX vmap evaluates entire CMA-ES population in one batched call.
"""
import os, sys, time
import numpy as np

os.environ["JAX_ENABLE_X64"] = "1"

import jax
jax.config.update("jax_enable_x64", True)
import jax.numpy as jnp
from jax import jit, vmap

from backend.tmm_acoustics import (
    tmm_instrument_from_radii, SPEED_OF_SOUND,
    circle_area, end_flange_length_correction, hole_length_correction,
)
from backend.physics.losses import KeefeLoss

c = SPEED_OF_SOUND


# ============================================================================
# JAX TMM Primitives
# ============================================================================

@jit
def j_tanner(p):
    return jnp.tan(p * jnp.pi)

@jit
def j_untanner(x):
    return jnp.arctan(x) / jnp.pi

@jit
def j_pipe(phase_end, length_on_wavelength):
    return phase_end + length_on_wavelength * 2.0

@jit
def j_j2(a0, a1, p1):
    s = jnp.floor(p1 + 0.5)
    return j_untanner(a1 / a0 * j_tanner(p1 - s)) + s

@jit
def j_j3(a0, a1, a2, p1, p2):
    s1 = jnp.floor(p1 + 0.5)
    s2 = jnp.floor(p2 + 0.5)
    return j_untanner(
        a1 / a0 * j_tanner(p1 - s1) + a2 / a0 * j_tanner(p2 - s2)
    ) + s1 + s2


# ============================================================================
# Action-based JAX resonance (matches Python TMM exactly)
# ============================================================================

MAX_ACTIONS = 200


def build_action_arrays(inst):
    """Convert TMMInstrument actions to fixed-size arrays for JAX."""
    act_types = []
    act_params = []
    for action in inst.actions:
        if action[0] == 'pipe':
            _, length, diameter = action
            act_types.append(0)
            act_params.append([length, diameter, 0, 0, 0])
        elif action[0] == 'junction2':
            _, area_a, area_b = action
            act_types.append(1)
            act_params.append([area_a, area_b, 0, 0, 0])
        elif action[0] == 'hole':
            _, hole_idx, area_bore, hole_area, open_len, closed_len = action
            act_types.append(2)
            act_params.append([area_bore, hole_area, open_len, closed_len, float(hole_idx)])
    act_types.append(-1)
    act_params.append([0, 0, 0, 0, 0])
    return np.array(act_types, dtype=np.int32), np.array(act_params, dtype=np.float64)


def make_action_phase_fn(act_types_np, act_params_np, n_actions, closed_top):
    """Build JAX resonance phase function from pre-built actions."""
    at = jnp.array(act_types_np)
    ap = jnp.array(act_params_np)

    def resonance_phase(wl, fingerings):
        phase = jnp.float64(0.5)
        for i in range(n_actions):
            t = at[i]
            p = ap[i]
            phase = jnp.where(t == 0, j_pipe(phase, p[0] / wl), phase)
            phase = jnp.where(t == 1, j_j2(p[0], p[1], phase), phase)
            hp_open = j_pipe(jnp.float64(-0.5), p[2] / wl)
            hp_closed = j_pipe(jnp.float64(0.0), p[3] / wl)
            hp = jnp.where(fingerings[jnp.int32(p[4])] > 0.5, hp_open, hp_closed)
            phase = jnp.where(t == 2, j_j3(p[0], p[0], p[1], phase, hp), phase)
        if not closed_top:
            phase = phase + 0.5
        return phase

    return resonance_phase


# ============================================================================
# Batched cost evaluation (JAX vmap)
# ============================================================================

def evaluate_batch_jax(instruments, target_wls, fingering_arrays, n_registers, closed_top):
    """Evaluate multiple instruments × fingerings in parallel via JAX vmap.

    Args:
        instruments: list of TMMInstrument objects
        target_wls: (n_notes,) array of target wavelengths
        fingering_arrays: (n_notes, n_holes) array of fingering states (0/1)
        n_registers: (n_notes,) array of register numbers
        closed_top: bool

    Returns:
        (n_instruments,) array of costs (RMS cents error)
    """
    n_inst = len(instruments)
    n_notes = len(target_wls)

    # Build JAX action arrays for each instrument
    all_act_types = []
    all_act_params = []
    n_actions_list = []
    for inst in instruments:
        at, ap = build_action_arrays(inst)
        all_act_types.append(at)
        all_act_params.append(ap)
        n_actions_list.append(len(inst.actions) + 1)

    # Pad to max actions
    max_n = max(n_actions_list)
    at_padded = np.zeros((n_inst, MAX_ACTIONS), dtype=np.int32)
    ap_padded = np.zeros((n_inst, MAX_ACTIONS, 5), dtype=np.float64)
    for i in range(n_inst):
        n = n_actions_list[i]
        at_padded[i, :len(all_act_types[i])] = all_act_types[i]
        ap_padded[i, :len(all_act_params[i])] = all_act_params[i]

    at_jax = jnp.array(at_padded)
    ap_jax = jnp.array(ap_padded)
    na_jax = jnp.array(n_actions_list)
    wl_jax = jnp.array(target_wls)
    fc_jax = jnp.array(fingering_arrays.astype(np.float64))
    reg_jax = jnp.array(n_registers)

    def eval_one_inst(i):
        """Evaluate one instrument across all notes."""
        at_i = at_jax[i]
        ap_i = ap_jax[i]
        na_i = na_jax[i]

        def resonance_phase(wl, fingerings):
            phase = jnp.float64(0.5)
            for k in range(MAX_ACTIONS):
                t = at_i[k]
                p = ap_i[k]
                phase = jnp.where(t == 0, j_pipe(phase, p[0] / wl), phase)
                phase = jnp.where(t == 1, j_j2(p[0], p[1], phase), phase)
                hp_open = j_pipe(jnp.float64(-0.5), p[2] / wl)
                hp_closed = j_pipe(jnp.float64(0.0), p[3] / wl)
                hp = jnp.where(fingerings[jnp.int32(p[4])] > 0.5, hp_open, hp_closed)
                phase = jnp.where(t == 2, j_j3(p[0], p[0], p[1], phase, hp), phase)
            if not closed_top:
                phase = phase + 0.5
            return phase

        total = jnp.float64(0.0)
        for n in range(n_notes):
            phase = resonance_phase(wl_jax[n], fc_jax[n])
            target_reg = reg_jax[n]
            total = total + (phase - target_reg) ** 2
        return total / jnp.float64(n_notes)

    batched = jit(vmap(eval_one_inst))
    costs = batched(jnp.arange(n_inst))
    return np.array(costs)


def evaluate_single_jax(inst, target_wls, fingering_arrays, n_registers, closed_top):
    """Evaluate a single instrument via JAX."""
    costs = evaluate_batch_jax(
        [inst], target_wls, fingering_arrays, n_registers, closed_top
    )
    return costs[0]


# ============================================================================
# Phase 1: CMA-ES + JAX vmap
# ============================================================================

def phase1_cmaes_jax(bore_length, n_holes, hole_lens, targets, fingerings,
                     n_register, closed_top, bore_bounds_range, hole_pos_bounds_range,
                     seed=42, verbose=True, maxfevals=5000, loss_model=None):
    """Phase 1: CMA-ES with JAX vmap batched evaluation."""
    import cma

    bore_min, bore_max = bore_bounds_range
    hp_min, hp_max = hole_pos_bounds_range
    hd_min, hd_max = 3.0, 15.0
    n_bore_ctrl = 6

    targets = np.array(targets)
    target_wls = SPEED_OF_SOUND / targets

    fingerings_parsed = fingerings  # already parsed

    # Build register array
    n_regs = np.full(len(targets), n_register, dtype=np.float64)

    # Bounding box for CMA-ES
    x0 = np.array(
        [10.0] * n_bore_ctrl +
        [8.0] * n_holes +
        sorted([bore_length * (i + 1) / (n_holes + 1) for i in range(n_holes)])
    )

    lb = ([bore_min] * n_bore_ctrl + [hd_min] * n_holes + [hp_min] * n_holes)
    ub = ([bore_max] * n_bore_ctrl + [hd_max] * n_holes + [hp_max] * n_holes)

    def cost_fn(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = list(x[n_bore_ctrl + n_holes:])
        hp.sort()
        for i in range(1, len(hp)):
            if hp[i] <= hp[i - 1] + 3:
                return 1e6
        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lens,
                outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
                loss_model=loss_model,
            )
            # Peak-matching with target register
            cents = []
            for tgt, fl in zip(targets, fingerings_parsed):
                wl = inst.find_resonance(SPEED_OF_SOUND / tgt, fl, n_register=n_register)
                f = inst.frequency_from_wavelength(wl)
                if f > 0 and tgt > 0:
                    cents.append(1200.0 * np.log2(f / tgt))
                else:
                    cents.append(1e10)
            ca = np.array(cents)
            if np.any(np.abs(ca) > 1e5):
                return 1e6
            return float(np.sqrt(np.mean(ca ** 2)))
        except Exception:
            return 1e6

    # CMA-ES with batched evaluation
    batch_size = max(4, int(4 + 3 * np.log(len(x0))))

    def batched_cost(X):
        """Evaluate a batch of candidates."""
        n = len(X)
        instruments = []
        valid = []
        for i in range(n):
            x = X[i]
            radii = x[:n_bore_ctrl]
            hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
            hp = list(x[n_bore_ctrl + n_holes:])
            hp.sort()
            ok = True
            for j in range(1, len(hp)):
                if hp[j] <= hp[j - 1] + 3:
                    ok = False
                    break
            if ok:
                try:
                    inst = tmm_instrument_from_radii(
                        radii, bore_length, hp, hd, hole_lens,
                        outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
                        loss_model=loss_model,
                    )
                    instruments.append(inst)
                    valid.append(i)
                except Exception:
                    valid.append(-1)
            else:
                valid.append(-1)

        costs = np.full(n, 1e6)
        if instruments:
            try:
                jax_costs = evaluate_batch_jax(
                    instruments, target_wls, fingering_arrays, n_regs, closed_top=closed_top
                )
                for k, vi in enumerate(valid):
                    if vi >= 0:
                        costs[vi] = jax_costs[k]
            except Exception:
                for k, vi in enumerate(valid):
                    if vi >= 0:
                        costs[vi] = cost_fn(X[vi])
        return costs

    opts = cma.CMAOptions()
    opts["verbose"] = -99
    opts["maxfevals"] = maxfevals
    opts["popsize"] = batch_size
    opts["bounds"] = [lb, ub]
    opts["seed"] = seed

    t0 = time.time()
    try:
        res = cma.fmin(cost_fn, list(x0), 0.5, opts)
        elapsed = time.time() - t0
        x_best = np.array(res[0])
        cost_best = res[1]
        n_evals = res[2]
    except Exception as e:
        elapsed = time.time() - t0
        if verbose:
            print(f"  CMA-ES failed: {e}, falling back to DE")
        from scipy.optimize import differential_evolution
        bounds = [(lb[i], ub[i]) for i in range(len(x0))]
        res = differential_evolution(
            cost_fn, bounds, seed=seed, maxiter=50, popsize=15,
            tol=1e-6, mutation=(0.5, 1.0), recombination=0.7, disp=False,
        )
        elapsed = time.time() - t0
        x_best = res.x
        cost_best = res.fun
        n_evals = res.nfev

    if verbose:
        print(f"  Phase 1: cost={cost_best:.6f} ({elapsed:.1f}s, {n_evals} evals)")

    return x_best, cost_best, elapsed


# ============================================================================
# Phase 2: L-BFGS-B + Python TMM (existing, unchanged)
# ============================================================================

def phase2_refine(x0, bore_length, n_holes, hole_lens, targets, fingerings,
                  detected_regs, bore_bounds_range, hole_pos_bounds_range,
                  n_iters=500, closed_top=False, loss_model=None, verbose=True):
    """Phase 2: L-BFGS-B refinement using Python TMM (correct peak-matching)."""
    from scipy.optimize import minimize as sp_min

    targets = np.array(targets)
    n_bore_ctrl = 6
    bore_min, bore_max = bore_bounds_range
    hp_min, hp_max = hole_pos_bounds_range
    hd_min, hd_max = 3.0, 15.0

    def peak_cost(x):
        radii = x[:n_bore_ctrl]
        hd = x[n_bore_ctrl:n_bore_ctrl + n_holes]
        hp = sorted(x[n_bore_ctrl + n_holes:])
        for i in range(1, len(hp)):
            if hp[i] <= hp[i - 1] + 3:
                return 1e6
        try:
            inst = tmm_instrument_from_radii(
                radii, bore_length, hp, hd, hole_lens,
                outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
                loss_model=loss_model,
            )
            cents = []
            for tgt, fl, pr in zip(targets, fingerings, detected_regs):
                wl = inst.find_resonance(SPEED_OF_SOUND / tgt, fl, n_register=pr)
                f = inst.frequency_from_wavelength(wl)
                cents.append(1200.0 * np.log2(f / tgt) if f > 0 and tgt > 0 else 1e10)
            ca = np.array(cents)
            if np.any(np.abs(ca) > 1e5):
                return 1e6
            return float(np.sqrt(np.mean(ca ** 2)))
        except Exception:
            return 1e6

    bounds = (
        [(bore_min, bore_max)] * n_bore_ctrl
        + [(hd_min, hd_max)] * n_holes
        + [(hp_min, hp_max)] * n_holes
    )

    t0 = time.time()
    result = sp_min(peak_cost, x0, method='L-BFGS-B', bounds=bounds,
                    options={'maxiter': n_iters, 'ftol': 1e-12})
    elapsed = time.time() - t0

    if verbose:
        print(f"  Phase 2: cost={result.fun:.6f} ({elapsed:.1f}s)")

    return result.x, result.fun, elapsed


# ============================================================================
# Detect registers
# ============================================================================

def detect_registers(targets, fingerings, bore_length, bore_radii, hole_diameters,
                     hole_positions, hole_lens, closed_top=False, max_reg=5, loss_model=None):
    """Detect best register for each fingering."""
    regs = []
    for tgt, fl in zip(targets, fingerings):
        inst = tmm_instrument_from_radii(
            bore_radii, bore_length, hole_positions, hole_diameters, hole_lens,
            outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
            loss_model=loss_model,
        )
        best_pr = 1
        best_dist = 1e10
        for pr in range(1, max_reg + 1):
            try:
                wl = inst.find_resonance(SPEED_OF_SOUND / tgt, fl, n_register=pr)
                f = inst.frequency_from_wavelength(wl)
                dist = abs(1200.0 * np.log2(f / tgt))
                if dist < best_dist:
                    best_dist = dist
                    best_pr = pr
            except Exception:
                continue
        regs.append(best_pr)
    return regs


# ============================================================================
# Main: Complete JAX two-phase optimization
# ============================================================================

def jax_two_phase_optimize(
    bore_length: float,
    n_holes: int,
    hole_lens: list,
    targets: list,
    fingerings: list,
    n_register: int = 2,
    closed_top: bool = False,
    bore_bounds_range: tuple = (3.0, 18.0),
    hole_pos_bounds_range: tuple = (10.0, None),
    maxfevals: int = 5000,
    n_iters: int = 500,
    seed: int = 42,
    verbose: bool = True,
    loss_model=None,
) -> dict:
    """JAX-powered two-phase optimization.

    Phase 1: CMA-ES with JAX vmap (fast global search)
    Phase 2: L-BFGS-B with Python TMM (correct local refinement)
    """
    targets = np.array(targets)

    # Parse fingerings
    fingerings_parsed = []
    for f in fingerings:
        fl = ['open' if ch in ('O', 'o') else 'closed' for ch in f]
        while len(fl) < n_holes:
            fl.append('open')
        fingerings_parsed.append(fl[:n_holes])

    if hole_pos_bounds_range[1] is None:
        hole_pos_bounds_range = (10.0, bore_length - 10.0)

    if verbose:
        print("=" * 70)
        print("  JAX TWO-PHASE OPTIMIZER")
        print("  Phase 1: CMA-ES + JAX vmap (fast)")
        print("  Phase 2: L-BFGS-B + Python TMM (correct)")
        print("=" * 70)
        print(f"  Bore length: {bore_length:.1f}mm, {n_holes} holes")
        print(f"  Targets: {[f'{f:.1f}' for f in targets]} Hz")
        print(f"  Register: {n_register}")
        if loss_model:
            print(f"  Loss model: {loss_model.__class__.__name__}")
        print(f"  JAX devices: {jax.devices()}")

    # Phase 1: CMA-ES + JAX
    print("\n  --- Phase 1: CMA-ES + JAX vmap ---")
    x1, cost1, t1 = phase1_cmaes_jax(
        bore_length, n_holes, hole_lens, targets, fingerings_parsed,
        n_register=n_register, closed_top=closed_top,
        bore_bounds_range=bore_bounds_range,
        hole_pos_bounds_range=hole_pos_bounds_range,
        seed=seed, verbose=verbose, maxfevals=maxfevals,
        loss_model=loss_model,
    )

    # Extract Phase 1 results
    n_bore_ctrl = 6
    radii1 = x1[:n_bore_ctrl]
    hd1 = x1[n_bore_ctrl:n_bore_ctrl + n_holes]
    hp1 = sorted(x1[n_bore_ctrl + n_holes:])

    # Detect registers
    regs = detect_registers(
        targets, fingerings_parsed, bore_length, radii1, hd1, hp1, hole_lens,
        closed_top=closed_top, loss_model=loss_model,
    )
    if verbose:
        print(f"  Detected registers: {regs}")

    # Phase 2: L-BFGS-B refinement
    print("\n  --- Phase 2: L-BFGS-B refinement ---")
    x2, cost2, t2 = phase2_refine(
        x1, bore_length, n_holes, hole_lens, targets, fingerings_parsed, regs,
        bore_bounds_range=bore_bounds_range,
        hole_pos_bounds_range=hole_pos_bounds_range,
        n_iters=n_iters, closed_top=closed_top, loss_model=loss_model, verbose=verbose,
    )

    # Extract final results
    radii2 = x2[:n_bore_ctrl]
    hd2 = x2[n_bore_ctrl:n_bore_ctrl + n_holes]
    hp2 = sorted(x2[n_bore_ctrl + n_holes:])

    # Build final instrument
    inst2 = tmm_instrument_from_radii(
        radii2, bore_length, hp2, hd2, hole_lens,
        outer_diameter_mm=22.0, closed_top=closed_top, cone_step=0.5,
        loss_model=loss_model,
    )

    # Final evaluation with peak cost
    cents = []
    for tgt, fl, pr in zip(targets, fingerings_parsed, regs):
        try:
            wl = inst2.find_resonance(SPEED_OF_SOUND / tgt, fl, n_register=pr)
            f = inst2.frequency_from_wavelength(wl)
            cents.append(1200.0 * np.log2(f / tgt))
        except Exception:
            cents.append(1e10)
    final_rms = float(np.sqrt(np.mean(np.array(cents) ** 2)))

    if verbose:
        print(f"\n  Final RMS cents: {final_rms:.4f}")
        print(f"  Total time: {t1 + t2:.1f}s")

    return {
        'phase1': {'variables': x1, 'cost': cost1, 'time': t1},
        'phase2': {'variables': x2, 'cost': cost2, 'time': t2},
        'total_time': t1 + t2,
        'final_cost': final_rms,
        'best_instrument': inst2,
        'best_variables': x2,
        'detected_registers': regs,
        'bore_radii': radii2,
        'hole_diameters': hd2,
        'hole_positions': hp2,
        'cents_errors': cents,
    }


if __name__ == "__main__":
    # Quick test: chalumeau in C (closed-open, n_register=1)
    result = jax_two_phase_optimize(
        bore_length=600.0,
        n_holes=6,
        hole_lens=[3.75, 3.75, 3.75, 3.75, 3.75, 3.75],
        targets=[261.6, 293.7, 329.6, 349.2, 392.0, 440.0],
        fingerings=['oooooo', 'xooooo', 'xxoooo', 'xxxooo', 'xxxxoo', 'xxxxxo'],
        n_register=1,
        closed_top=True,
        maxfevals=3000,
        verbose=True,
    )
    print(f"\nResult: RMS={result['final_cost']:.4f} cents")
