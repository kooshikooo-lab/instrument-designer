"""Canonical tuning-error metrics (one source of truth).

Convention (see docs/ARCHITECTURE_DECISIONS.md, ADR: absolute-RMS primary metric):

- ``final_rms_cents``  absolute RMS of cents errors -- the primary accuracy metric.
  Median correction is deliberately NOT applied here: it allows an optimizer to
  score 0c by making every note uniformly wrong.
- ``scale_rms_cents``  RMS of cents errors after subtracting the median offset
  (evenness / scale-fit quality; subordinate diagnostic).
- ``median_offset_cents``  global tuning offset (median of cents errors).
- ``peak_error_cents``  maximum |cents error| (absolute).

All functions accept raw cents deviations relative to the target frequencies.
"""

from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple, Union

import numpy as np


def compute_metrics(cents: Sequence[float]) -> dict:
    """Compute the canonical metric dict from raw cents deviations.

    Invalid / non-finite readings are excluded unless every reading is
    invalid, in which case all metrics are set to 1e10 (penalty sentinel).
    """
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return {
            "final_rms_cents": 1e10,
            "scale_rms_cents": 1e10,
            "median_offset_cents": 0.0,
            "peak_error_cents": 1e10,
        }
    rms = float(np.sqrt(np.mean(finite ** 2)))
    offset = float(np.median(finite))
    scale_rms = float(np.sqrt(np.mean((finite - offset) ** 2)))
    peak = float(np.max(np.abs(finite)))
    return {
        "final_rms_cents": rms,
        "scale_rms_cents": scale_rms,
        "median_offset_cents": offset,
        "peak_error_cents": peak,
    }


def rms_cents(cents: Sequence[float]) -> float:
    """Absolute RMS of cents errors (primary accuracy metric)."""
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 1e10
    return float(np.sqrt(np.mean(finite ** 2)))


def scale_rms_cents(cents: Sequence[float]) -> float:
    """RMS of cents errors after removing the median offset (evenness)."""
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 1e10
    return float(np.sqrt(np.mean((finite - np.median(finite)) ** 2)))


def median_offset_cents(cents: Sequence[float]) -> float:
    """Median cents error (global tuning offset)."""
    arr = np.asarray(cents, dtype=float)
    finite = arr[np.isfinite(arr)]
    if finite.size == 0:
        return 0.0
    return float(np.median(finite))


def cents_from_frequencies(actual, target) -> list:
    """Convert frequency pairs to cents deviations (1200*log2(f_actual/f_target))."""
    out = []
    for a, t in zip(actual, target):
        if a is not None and t is not None and math.isfinite(float(a)) and float(a) > 0 and float(t) > 0:
            out.append(1200.0 * math.log2(float(a) / float(t)))
        else:
            out.append(1e10)
    return out


# ---------------------------------------------------------------------------
# Intonation pass tiers
# ---------------------------------------------------------------------------
# Literature-grounded cents thresholds; rationale and sources in
# docs/PHYSICS_PRINCIPLES.md ("Intonation pass standards"). The RMS tier is
# the primary accuracy gate; the per-note max gate catches register-break
# outliers that RMS alone masks (e.g. a bad register hole buried in an
# otherwise even scale).
#
#   sane            150c RMS  screening only -- keeps an optimizer/test from
#                            failing on the uniform-10mm baseline (~77c) or a
#                            numerically-exploded run (tuned floor is ~6c).
#   acceptable      10c RMS, 25c max  -- design acceptance for conventional
#                            instruments (Selmer R&D accepts 10-20c peaks;
#                            woodwind practice treats up to ~+/-20c as normal).
#   professional     5c RMS, 15c max  -- flagship quality (numerically tuned
#                            clarinet: most resonances < 5c, mean ~2c).
#   unconventional  20c RMS, 40c max  -- looser bar for novel/folded shapes
#                            (metamaterial caps, folded low-clarinet register
#                            holes); still inside the 20-50c band where notes
#                            start to sound out of tune.
#
#   FIXTURE_TOLERANCE_CENTS       5c mean   single-resonance physics fixtures
#                                            (our 180mm pipe: 2.5c vs theory).
#   CROSS_SOFTWARE_MEAN_ABS_CENTS 10c mean  TMM vs chalumier agreement; also
#                                            the practical simulation ceiling
#                                            (recorder modeling: all < 15c).
SANE_RMS_CENTS = 150.0
ACCEPTABLE_RMS_CENTS = 10.0
ACCEPTABLE_MAX_ABS_CENTS = 25.0
PROFESSIONAL_RMS_CENTS = 5.0
PROFESSIONAL_MAX_ABS_CENTS = 15.0
UNCONVENTIONAL_RMS_CENTS = 20.0
UNCONVENTIONAL_MAX_ABS_CENTS = 40.0
FIXTURE_TOLERANCE_CENTS = 5.0
CROSS_SOFTWARE_MEAN_ABS_CENTS = 10.0

INTONATION_TIERS: dict[str, Tuple[float, Optional[float]]] = {
    "sane": (SANE_RMS_CENTS, None),
    "acceptable": (ACCEPTABLE_RMS_CENTS, ACCEPTABLE_MAX_ABS_CENTS),
    "professional": (PROFESSIONAL_RMS_CENTS, PROFESSIONAL_MAX_ABS_CENTS),
    "unconventional": (UNCONVENTIONAL_RMS_CENTS, UNCONVENTIONAL_MAX_ABS_CENTS),
}


def intonation_passes(
    rms: Union[float, None],
    max_abs: Optional[float] = None,
    tier: str = "acceptable",
) -> bool:
    """Whether intonation metrics meet a pass tier (see ``INTONATION_TIERS``).

    Args:
        rms: absolute RMS cents error (primary gate).
        max_abs: optional per-note max |cents error|; if the tier defines a
            max limit and ``max_abs`` is supplied it must also pass.
        tier: one of ``INTONATION_TIERS`` keys.

    ``None`` / non-finite values never pass.
    """
    if tier not in INTONATION_TIERS:
        raise KeyError(f"unknown intonation tier: {tier!r}")
    rms_lim, max_lim = INTONATION_TIERS[tier]
    try:
        if not (math.isfinite(float(rms)) and float(rms) <= rms_lim):
            return False
    except (TypeError, ValueError):
        return False
    if max_lim is None or max_abs is None:
        return True
    try:
        return math.isfinite(float(max_abs)) and float(max_abs) <= max_lim
    except (TypeError, ValueError):
        return False
