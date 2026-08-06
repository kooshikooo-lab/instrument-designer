"""
Benchmarking + optimization harness, companion to metamaterial_elements.py,
brass_scaffold.py, bore_builder.py, and folded_bore_elements.py.

Two things live here:

1. A small set of standard metrics for evaluating ANY wind-instrument
   design (traditional bore, folded low-clarinet, metamaterial-augmented
   -- the metrics don't care how the ABCD chain was built, only what it
   predicts). This is deliberately decoupled from geometry generation so
   the same harness applies across your traditional and novel-shape work.

2. A tested two-phase optimizer (global search + local polish) using
   only scipy, since jax/pymoo aren't installed in this sandbox. A JAX
   and a pymoo version of the same pattern are sketched at the bottom,
   annotated as UNTESTED HERE -- they mirror the tested scipy logic
   function-for-function, meant to plug into your existing JAX branch
   and pymoo-based NSGA-II infrastructure directly.
"""

import numpy as np
from scipy.optimize import differential_evolution, minimize

from brass_scaffold import input_impedance, find_impedance_peaks, radiation_impedance, cents
from bore_builder import build_fingering_chain


# ---------------------------------------------------------------------
# 1. Benchmark metrics
# ---------------------------------------------------------------------

def intonation_rms_cents(actual_freqs, target_freqs):
    """RMS cents deviation across a fingering chart. This is the metric
    your project's 'intonation accuracy' objective should be computing --
    per your own bug history, double check this isn't silently reducing
    to a scale-evenness metric instead (i.e. confirm target_freqs are
    fixed external targets like ET, not derived from the actual_freqs
    themselves)."""
    actual = np.asarray(actual_freqs, dtype=float)
    target = np.asarray(target_freqs, dtype=float)
    dev_cents = 1200 * np.log2(actual / target)
    return float(np.sqrt(np.mean(dev_cents**2))), dev_cents


def peak_quality_factor(f_scan, Zin, f_peak, half_power_frac=1 / np.sqrt(2)):
    """Q = f_peak / bandwidth, bandwidth measured where |Z| drops to
    half_power_frac of the peak value on either side. Higher Q = more
    sharply defined pitch (easier to center, less pitch flexibility);
    lower Q = easier to bend/lip but harder to lock in. Neither is
    strictly 'better' -- report both directions and let the player/
    design goal decide the target range."""
    mag = np.abs(Zin)
    i_peak = np.argmin(np.abs(f_scan - f_peak))
    peak_val = mag[i_peak]
    threshold = peak_val * half_power_frac

    i_lo = i_peak
    while i_lo > 0 and mag[i_lo] > threshold:
        i_lo -= 1
    i_hi = i_peak
    while i_hi < len(mag) - 1 and mag[i_hi] > threshold:
        i_hi += 1

    bandwidth = f_scan[i_hi] - f_scan[i_lo]
    if bandwidth <= 0:
        return float('inf')
    return f_peak / bandwidth


def harmonicity_cents(peaks):
    """Given a fingering's impedance peaks (in ascending frequency order),
    report each upper peak's deviation in cents from the nearest integer
    multiple of the fundamental. Large deviations flag registers that
    will be hard to overblow cleanly / poor register-key behavior."""
    if len(peaks) < 2:
        return []
    f0 = peaks[0][0]
    devs = []
    for i, (f_i, _) in enumerate(peaks[1:], start=2):
        nearest_n = round(f_i / f0)
        if nearest_n == 0:
            continue
        target = nearest_n * f0
        devs.append((nearest_n, 1200 * np.log2(f_i / target)))
    return devs


def peak_isolation_check(peaks, min_separation_cents=50):
    """Flags any pair of adjacent peaks closer than min_separation_cents
    -- a sign of the kind of coupled/spurious-resonance behavior found
    during development of bore_builder.py (an undersized tonehole
    produced a spurious low resonance stronger than the intended note).
    Returns list of (f1, f2, separation_cents) for flagged pairs."""
    flagged = []
    for i in range(len(peaks) - 1):
        f1, f2 = peaks[i][0], peaks[i + 1][0]
        sep = 1200 * np.log2(f2 / f1)
        if sep < min_separation_cents:
            flagged.append((f1, f2, sep))
    return flagged


def tolerance_sensitivity(eval_fn, nominal_params, param_index, delta,
                           metric_fn):
    """Central-difference sensitivity of metric_fn(eval_fn(params)) to a
    small perturbation in one parameter -- use delta = your printer's
    real repeatability (e.g. 0.0001 m = 0.1mm) to get a directly
    actionable 'cents of intonation risk per printer tolerance unit'
    number, rather than an abstract derivative."""
    p_plus = list(nominal_params)
    p_minus = list(nominal_params)
    p_plus[param_index] += delta
    p_minus[param_index] -= delta
    m_plus = metric_fn(eval_fn(p_plus))
    m_minus = metric_fn(eval_fn(p_minus))
    return (m_plus - m_minus) / (2 * delta)


# ---------------------------------------------------------------------
# 2. Two-phase optimizer (global + local), scipy-only, tested
# ---------------------------------------------------------------------

def make_two_note_design(base_length, r_bore, hole_position, hole_radius,
                          f_scan):
    """Toy design: one cylindrical bore, one tonehole. Returns the
    fundamental (closed) and second-note (hole open) impedance peaks.
    Stand-in for a real fingering-chart evaluation -- swap this out for
    your actual bore/fingering-chart builder; the optimizer code below
    doesn't care what's inside this function."""
    toneholes = [{'position': hole_position, 'radius': hole_radius,
                  'chimney': 0.003}]
    base = [('cyl', base_length, r_bore)]
    Zload = radiation_impedance(f_scan, r_bore, flanged=False)

    T_closed = build_fingering_chain(f_scan, base, toneholes, [False])
    Zin_closed = input_impedance(T_closed, Zload)
    peaks_closed = find_impedance_peaks(f_scan, Zin_closed, band=(f_scan[0], f_scan[-1]))

    T_open = build_fingering_chain(f_scan, base, toneholes, [True])
    Zin_open = input_impedance(T_open, Zload)
    peaks_open = find_impedance_peaks(f_scan, Zin_open, band=(f_scan[0], f_scan[-1]))

    f0_closed = peaks_closed[0][0] if peaks_closed else np.nan
    f0_open = peaks_open[0][0] if peaks_open else np.nan
    return f0_closed, f0_open


def objective(params, f_scan, targets):
    base_length, hole_position, hole_radius = params
    if not (0.05 < hole_position < base_length - 0.02):
        return 1e6  # keep the hole inside the bore, away from either end
    f0_closed, f0_open = make_two_note_design(base_length, 0.0075,
                                               hole_position, hole_radius,
                                               f_scan)
    if np.isnan(f0_closed) or np.isnan(f0_open):
        return 1e6
    rms, _ = intonation_rms_cents([f0_closed, f0_open], targets)
    return rms


if __name__ == "__main__":
    f_scan = np.linspace(30, 1500, 4000)
    targets = [150.0, 220.0]  # two arbitrary target pitches, Hz

    bounds = [(0.30, 0.80),    # base_length
              (0.08, 0.60),    # hole_position (constrained further in objective)
              (0.001, 0.006)]  # hole_radius

    print("Phase 1: global search (differential_evolution)...")
    result_global = differential_evolution(
        objective, bounds, args=(f_scan, targets),
        maxiter=25, popsize=12, seed=0, polish=False, tol=1e-3,
    )
    print(f"  global best: L={result_global.x[0]*100:.1f}cm "
          f"hole_pos={result_global.x[1]*100:.1f}cm "
          f"hole_r={result_global.x[2]*1000:.1f}mm "
          f"-> RMS {result_global.fun:.1f} cents")

    print("\nPhase 2: local polish (L-BFGS-B, finite-difference gradient)...")
    result_local = minimize(
        objective, result_global.x, args=(f_scan, targets),
        method='L-BFGS-B', bounds=bounds,
        options={'maxiter': 50, 'eps': 1e-5},
    )
    print(f"  local best:  L={result_local.x[0]*100:.1f}cm "
          f"hole_pos={result_local.x[1]*100:.1f}cm "
          f"hole_r={result_local.x[2]*1000:.1f}mm "
          f"-> RMS {result_local.fun:.2f} cents")

    # --- benchmark the final design ---
    L, hp, hr = result_local.x
    f0_closed, f0_open = make_two_note_design(L, 0.0075, hp, hr, f_scan)
    rms, devs = intonation_rms_cents([f0_closed, f0_open], targets)
    print(f"\nFinal design intonation: closed={f0_closed:.1f}Hz "
          f"({devs[0]:+.1f}c), open={f0_open:.1f}Hz ({devs[1]:+.1f}c)")

    # tolerance sensitivity: how much does hole_position tolerance matter?
    # NOTE: using the same coarse f_scan grid for finite-difference
    # sensitivity gave a spurious exact 0.0 here on the first pass --
    # 4000 points over 30-1500Hz is ~0.37Hz/bin, coarser than the actual
    # frequency shift from a 0.1mm position change, so the peak-finder
    # kept snapping to the same bin. Use a finer local grid around the
    # note of interest for the sensitivity check specifically.
    f_fine = np.linspace(f0_open - 5, f0_open + 5, 4000)

    def eval_fn_fine(params):
        L_, hp_, hr_ = params
        return make_two_note_design(L_, 0.0075, hp_, hr_, f_fine)

    def metric_open_note(freqs):
        return freqs[1]

    sens = tolerance_sensitivity(eval_fn_fine, [L, hp, hr], 1, 0.0001, metric_open_note)
    print(f"\nSensitivity of the open-note frequency to hole position: "
          f"{sens:.1f} Hz per meter of position error")
    print(f"  -> at 0.1mm printer tolerance, expect roughly "
          f"{abs(sens) * 1e-4:.3f} Hz ("
          f"{abs(1200*np.log2(1+ (sens*1e-4)/f0_open)):.2f} cents) of "
          f"open-note drift from print repeatability alone")
