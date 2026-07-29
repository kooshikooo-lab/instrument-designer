"""
Inverse design: sound → instrument design (backward-compat re-export layer).

All implementation has been moved to ``sound_analysis.py`` (Tier 1),
``design_from_wav.py`` (Tiers 2 + 3), and ``pareto_optimizer.py``
(shared optimizer).  This module re-exports every public name so that
existing imports continue to work.

Usage:
    from backend.inverse_design import (
        analyze_wav,                # → sound_analysis
        design_scale,               # → design_from_wav
        match_timbre,               # → design_from_wav
        design_from_sound,          # → design_from_wav
        synthesize_harmonic,        # → sound_analysis
        save_synthetic_wav,         # → sound_analysis
        validate_physical_series,   # → sound_analysis
        build_target_envelope,      # → design_from_wav
        estimate_harmonic_magnitudes,  # → design_from_wav
    )
"""
from __future__ import annotations

from backend.design_from_wav import (         # noqa: F401
    design_scale,
    match_timbre,
    design_from_sound,
    build_target_envelope,
    estimate_harmonic_magnitudes,
    N_TIER3_RADII,
)

from backend.sound_analysis import (          # noqa: F401
    analyze_wav,
    synthesize_harmonic,
    save_synthetic_wav,
    validate_physical_series,
    MIN_HARMONIC_RATIO,
    HARMONIC_TOLERANCE,
    MIN_FUNDAMENTAL_HZ,
    MAX_FUNDAMENTAL_HZ,
)
