"""Test variable bore profile optimization."""
import sys, os, time
import pytest
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from backend.tmm_optimizer_sequential import SequentialBoreOptimizer

target_freqs = [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0]
fingerings = [
    ['closed'] * 7,
    ['open', 'closed', 'closed', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'closed', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'closed', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'closed', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'open', 'closed', 'closed'],
    ['open', 'open', 'open', 'open', 'open', 'open', 'closed'],
]


def test_bore_profile_optimization():
    for ncp in [0, 4, 6]:
        opt = SequentialBoreOptimizer(
            target_frequencies=target_freqs,
            fingering_sets=fingerings,
            bore_radius=6.0,
            outer_diameter=20.0,
            closed_top=False,
            n_register=1,
            hole_diameter=6.5,
            hole_length=3.0,
            n_bore_cp=ncp,
        )
        r = opt.run(verbose=False)
        assert r['final_rms_cents'] < 50.0, f"n_cp={ncp}: RMS too high: {r['final_rms_cents']:.4f}c"
        assert r['bore_length_mm'] > 0, f"n_cp={ncp}: bore length must be positive"
        assert len(r['bore_radii']) > 0, f"n_cp={ncp}: bore radii missing"
        assert all(x > 0 for x in r['bore_radii']), f"n_cp={ncp}: all radii must be positive"


if __name__ == "__main__":
    test_bore_profile_optimization()
