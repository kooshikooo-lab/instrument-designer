from __future__ import annotations

import numpy as np

from backend.tmm_acoustics import SPEED_OF_SOUND, TMMInstrument
from backend.physics.losses import KeefeLoss
from backend.sound_analysis import analyze_wav

_c = SPEED_OF_SOUND
N_TIER3_RADII = 6


def design_scale(fundamental_hz: float,
                 harmonic_frequencies: list[float] | None = None,
                 label: str = "",
                 hole_count: int = 6,
                 n_candidates: int = 2) -> dict:
    """Design an instrument scale rooted at the given fundamental.

    Delegates to the generative agent's NSGA-II optimizer.
    """
    from backend.generative_agent import get_agent, _result_to_dict

    agent = get_agent()
    result_gr = agent.design_from_sound(
        fundamental_hz=fundamental_hz,
        label=label,
        n_candidates=n_candidates,
    )
    result = _result_to_dict(result_gr)
    result["tier"] = 2
    result["analysis"] = {
        "fundamental_hz": fundamental_hz,
        "n_harmonics_detected": len(harmonic_frequencies or []),
        "harmonic_frequencies": harmonic_frequencies or [],
    }
    return result


def build_target_envelope(analysis: dict, n_harmonics: int = 8) -> np.ndarray:
    """Build a target impedance-magnitude envelope from the sound analysis."""
    harm_f = np.array(analysis.get("harmonic_frequencies", []))
    harm_m = np.array(analysis.get("harmonic_amplitudes", []))
    fundamental = analysis.get("fundamental_hz", 440.0)

    if len(harm_f) < 2:
        f_targets = np.array([n * fundamental for n in range(1, n_harmonics + 1)])
        m_targets = 1.0 / np.arange(1, n_harmonics + 1, dtype=float)
        return f_targets, m_targets / m_targets[0]

    all_n = np.arange(1, n_harmonics + 1)
    max_n = int(harm_f[-1] / fundamental)
    freqs_full = np.array([n * fundamental for n in range(1, max_n + 1)])
    mags_full = np.zeros(max_n)
    for n in range(1, max_n + 1):
        idx = np.argmin(np.abs(harm_f / fundamental - n))
        closest_n = round(harm_f[idx] / fundamental)
        if abs(closest_n - n) <= 1 and n <= len(harm_m):
            mags_full[n - 1] = harm_m[idx]
        else:
            mags_full[n - 1] = np.interp(n * fundamental, harm_f, harm_m,
                                         left=0, right=0)

    mags_full = mags_full[:n_harmonics]
    if mags_full[0] > 0:
        mags_full = mags_full / mags_full[0]

    return freqs_full[:n_harmonics], mags_full


def estimate_harmonic_magnitudes(inst: TMMInstrument,
                                 n_harmonics: int = 8,
                                 loss_model: KeefeLoss | None = None) -> np.ndarray:
    """Estimate relative impedance peak magnitudes for a TMMInstrument."""
    if loss_model is None:
        loss_model = KeefeLoss()

    f0 = _c / (2.0 * inst.length) if not inst.closed_top else _c / (4.0 * inst.length)

    total_weight = 0.0
    weighted_radius = 0.0
    for action in inst.actions:
        if action[0] == "pipe":
            _, seg_length, seg_diameter = action
            radius = seg_diameter / 2.0
            if radius > 0 and seg_length > 0:
                w = seg_length / max(radius, 0.1)
                weighted_radius += radius * w
                total_weight += w
    eff_radius = weighted_radius / max(total_weight, 1e-6)

    magnitudes = np.ones(n_harmonics)

    for h in range(1, n_harmonics + 1):
        freq = f0 * h
        wl = _c / freq

        cum_loss = 1.0
        for action in inst.actions:
            if action[0] == "pipe":
                _, seg_length, seg_diameter = action
                radius = seg_diameter / 2.0
                if radius > 0 and seg_length > 0:
                    lf = loss_model.bore_loss(seg_length, radius, wl)
                    if isinstance(lf, (complex, np.complexfloating)):
                        cum_loss *= abs(lf)
                    else:
                        cum_loss *= float(lf)

        k_r = (2 * np.pi * freq * eff_radius / _c)
        rad_loss = np.exp(-0.5 * k_r ** 2)
        round_trip = cum_loss ** 2 * rad_loss
        magnitudes[h - 1] = min(1.0, max(0.001, round_trip))

    if magnitudes[0] > 0:
        magnitudes = magnitudes / magnitudes[0]
    return magnitudes


def _timbre_cost(radii: np.ndarray,
                 hole_positions: list[float],
                 hole_diameters: list[float],
                 bore_length: float,
                 n_holes: int,
                 closed_top: bool,
                 target_mags: np.ndarray,
                 n_harmonics: int,
                 loss_model: KeefeLoss) -> float:
    """Cost: RMS deviation between target and estimated harmonic magnitudes."""
    n_segments = max(N_TIER3_RADII * 2, 10)
    pos = np.linspace(0, bore_length, n_segments)
    cp_pos = np.linspace(0, bore_length, N_TIER3_RADII)
    diameters = np.interp(pos, cp_pos, radii) * 2.0

    try:
        inst = TMMInstrument(
            inner_positions=pos.tolist(),
            inner_diameters=diameters.tolist(),
            outer_diameters=[d + 14.0 for d in diameters],
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=[3.75] * n_holes,
            closed_top=closed_top,
            loss_model=loss_model,
        )
        estimated = estimate_harmonic_magnitudes(inst, n_harmonics, loss_model)
    except Exception:
        return 1e10

    n = min(len(estimated), len(target_mags))
    if n < 2:
        return 1e10
    return float(np.sqrt(np.mean((estimated[:n] - target_mags[:n]) ** 2)))


def match_timbre(best_candidate: dict,
                 analysis: dict,
                 n_gen: int = 20,
                 pop_size: int = 30) -> dict:
    """Tier 3: optimize bore radii to match the sound's harmonic envelope.

    Calls ``optimization.nsga2.nsga2_minimize`` — never instantiates
    pymoo directly.
    """
    from backend.optimization.nsga2 import nsga2_minimize

    target_freqs, target_mags = build_target_envelope(analysis)
    n_harmonics = len(target_mags)

    hole_positions = best_candidate.get("hole_positions_mm", [])
    hole_diameters = best_candidate.get("hole_diameters_mm", [])
    bore_radii_init = best_candidate.get("bore_radii", [7.25] * N_TIER3_RADII)
    bore_length = best_candidate.get("bore_length_mm", 500.0)
    closed_top = False
    n_holes = len(hole_positions)

    if len(bore_radii_init) != N_TIER3_RADII:
        bore_radii_init = [float(np.mean(bore_radii_init))] * N_TIER3_RADII

    loss_model = KeefeLoss()

    cost_init = _timbre_cost(
        np.array(bore_radii_init), hole_positions, hole_diameters,
        bore_length, n_holes, closed_top, target_mags, n_harmonics, loss_model,
    )

    xl = np.array([3.0] * N_TIER3_RADII)
    xu = np.array([15.0] * N_TIER3_RADII)

    cost_fn = lambda r: _timbre_cost(
        r, hole_positions, hole_diameters,
        bore_length, n_holes, closed_top,
        target_mags, n_harmonics, loss_model,
    )

    result = nsga2_minimize(cost_fn, N_TIER3_RADII, xl, xu,
                            pop_size=pop_size, n_gen=n_gen)

    if result is None:
        return {
            "tier3_success": False,
            "tier3_error": "NSGA-II failed",
            "bore_radii_initial": bore_radii_init,
            "target_envelope": target_mags.tolist(),
            "estimated_envelope_initial": [],
        }

    radii_best = result["x"]
    cost_best = result["fun"]

    n_segments = max(N_TIER3_RADII * 2, 10)
    pos = np.linspace(0, bore_length, n_segments)
    cp_pos = np.linspace(0, bore_length, N_TIER3_RADII)
    diameters_best = np.interp(pos, cp_pos, radii_best) * 2.0

    try:
        inst_best = TMMInstrument(
            inner_positions=pos.tolist(),
            inner_diameters=diameters_best.tolist(),
            outer_diameters=[d + 14.0 for d in diameters_best],
            hole_positions=hole_positions,
            hole_diameters=hole_diameters,
            hole_lengths=[3.75] * n_holes,
            closed_top=closed_top,
            loss_model=loss_model,
        )
        estimated_best = estimate_harmonic_magnitudes(inst_best, n_harmonics, loss_model)
    except Exception:
        estimated_best = []

    return {
        "tier3_success": bool(cost_best < cost_init),
        "tier3_cost_initial": float(cost_init),
        "tier3_cost_optimized": float(cost_best),
        "bore_radii_initial": bore_radii_init,
        "bore_radii_optimized": radii_best.tolist(),
        "target_envelope_frequencies": target_freqs.tolist(),
        "target_envelope_magnitudes": target_mags.tolist(),
        "estimated_envelope_initial": [],
        "estimated_envelope_optimized": estimated_best.tolist() if hasattr(estimated_best, 'tolist') else list(estimated_best),
    }


def design_from_sound(filepath: str,
                      n_candidates: int = 2,
                      hole_count: int = 6,
                      run_tier3: bool = True,
                      label: str = "") -> dict:
    """Full three-tier inverse design from a WAV file.

    1. Analyze sound (``sound_analysis.analyze_wav``)
    2. Design scale (``design_scale``)
    3. Match timbre (``match_timbre``)
    """
    analysis = analyze_wav(filepath)
    if analysis["confidence"] < 0.1:
        return {"error": "Could not estimate fundamental", "analysis": analysis}

    fundamental = analysis["fundamental_hz"]
    harm_f = analysis["harmonic_frequencies"]
    display_label = label or f"Inverse: {filepath.split('/')[-1]}"

    tier2 = design_scale(
        fundamental_hz=fundamental,
        harmonic_frequencies=harm_f,
        label=display_label,
        hole_count=hole_count,
        n_candidates=n_candidates,
    )

    result = {
        "tier1": {
            "sample_rate": analysis["sample_rate"],
            "duration_s": analysis["duration_s"],
            "fundamental_hz": fundamental,
            "confidence": analysis["confidence"],
            "n_harmonics": len(harm_f),
            "harmonic_frequencies": harm_f,
            "harmonic_amplitudes": analysis["harmonic_amplitudes"],
        },
        "tier2": tier2,
    }

    if run_tier3 and tier2.get("best") and tier2.get("candidates"):
        best_candidate = tier2["candidates"][0]
        tier3 = match_timbre(best_candidate, analysis)
        result["tier3"] = tier3
        result["final_geometry"] = {
            "bore_length_mm": best_candidate.get("bore_length_mm", 500.0),
            "bore_radii": tier3.get("bore_radii_optimized", []),
            "hole_positions_mm": best_candidate.get("hole_positions_mm", []),
            "hole_diameters_mm": best_candidate.get("hole_diameters_mm", []),
            "intonation_rms_cents": best_candidate.get("intonation_rms_cents", 0),
            "timbre_match_cost": tier3.get("tier3_cost_initial", 0),
        }

    return result
