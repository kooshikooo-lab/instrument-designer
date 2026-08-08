"""Regression tests for backend/benchmark_all.py INSTRUMENTS data fixes.

Covers the Kimi K3 audit findings:
- impossible outer diameters (negative wall) on pvc_flute_D / diatonic_D_chalumeau /
  concert_flute_C / alto_flute_G
- fingering charts that silently disagreed with canonical _build_fingerings and
  were discarded by resolve_fingerings (bass_chalumeau_Bb, chalumeau_C)
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.benchmark_all import INSTRUMENTS, resolve_fingerings
from backend.pareto_optimizer import _build_fingerings


def _expected_hole_count(cfg) -> int:
    """Holes the benchmark's sequential pipeline places for a config."""
    return len(cfg["targets"]) - 1


@pytest.mark.parametrize("name", list(INSTRUMENTS))
def test_positive_wall(name):
    cfg = INSTRUMENTS[name]
    assert cfg["outer_diameter"] > 2.0 * cfg["bore_radius"], (
        f"{name}: outer_diameter {cfg['outer_diameter']} must exceed "
        f"bore diameter {2.0 * cfg['bore_radius']}"
    )


@pytest.mark.parametrize("name", list(INSTRUMENTS))
def test_chart_matches_canonical_build(name):
    """Sequential-style charts must equal the canonical build for the placed hole count.

    closed-top: _build_fingerings(n_holes, True)  (all-closed row prepended)
    open: all-closed fundamental row + _build_fingerings(n_holes, False)
    """
    cfg = INSTRUMENTS[name]
    if cfg.get("_chromatic"):
        pytest.skip("chromatic instruments use register-specific charts")
    n_holes = _expected_hole_count(cfg)
    if cfg["closed_top"]:
        expected = _build_fingerings(n_holes, True)
    else:
        expected = [["closed"] * n_holes] + _build_fingerings(n_holes, False)
    assert cfg["fingerings"] == expected, (
        f"{name}: fingering chart does not match the canonical build for "
        f"{n_holes} holes and would be silently discarded by resolve_fingerings"
    )


@pytest.mark.parametrize(
    "name, expected_od",
    [
        ("pvc_flute_D", 26.7),
        ("diatonic_D_chalumeau", 20.0),
        ("concert_flute_C", 24.0),
        ("alto_flute_G", 26.0),
    ],
)
def test_fixed_outer_diameters(name, expected_od):
    assert INSTRUMENTS[name]["outer_diameter"] == expected_od


def test_bass_chalumeau_chart_used_directly():
    """bass_chalumeau_Bb's chart must not be discarded by resolve_fingerings."""
    cfg = INSTRUMENTS["bass_chalumeau_Bb"]
    n_holes = _expected_hole_count(cfg)
    assert resolve_fingerings(cfg, n_holes) is cfg["fingerings"]
