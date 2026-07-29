"""Verify that the architecture reorganization is wired correctly."""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_geometry_module():
    """geometry.py exports BoreProfile, HoleLayout, InstrumentGeometry."""
    from backend.geometry import BoreProfile, HoleLayout, InstrumentGeometry
    import numpy as np

    bore = BoreProfile(positions=np.array([0, 100]), radii=np.array([5, 10]))
    assert bore.interpolate(50) == 7.5

    holes = HoleLayout(positions=np.array([30, 60]), diameters=np.array([6, 8]))
    assert holes.n_holes == 2

    geom = InstrumentGeometry(
        total_length=100,
        bore=bore,
        holes=holes,
        closed_top=False,
    )
    radii, lengths, hole_specs = geom.to_tmm()
    assert len(radii) == 2
    assert len(hole_specs) == 2
    assert hole_specs[0]["d"] == 6.0


def test_sound_analysis_module():
    """sound_analysis.py exports public functions."""
    from backend.sound_analysis import (
        analyze_wav, synthesize_harmonic, save_synthetic_wav,
        validate_physical_series,
    )
    import tempfile, os

    samples = synthesize_harmonic(440.0, 4, duration_s=0.5)
    assert len(samples) > 0
    assert abs(max(samples)) <= 1.0

    path = os.path.join(tempfile.gettempdir(), "test_sa_440.wav")
    save_synthetic_wav(path, samples)
    assert os.path.getsize(path) > 1000

    analysis = analyze_wav(path)
    assert abs(analysis["fundamental_hz"] - 440.0) < 1.0
    assert analysis["confidence"] > 0.9
    assert len(analysis["harmonic_frequencies"]) >= 1

    valid, msg = validate_physical_series(
        [440.0, 880.0, 1320.0], 440.0
    )
    assert valid


def test_design_from_wav_imports():
    """design_from_wav.py exports the orchestrator functions."""
    from backend.design_from_wav import (
        design_scale, match_timbre, design_from_sound,
        build_target_envelope, estimate_harmonic_magnitudes,
    )


def test_design_from_wav_exports():
    """design_from_wav.py exports the orchestrator functions."""
    from backend.design_from_wav import (
        design_scale, match_timbre, design_from_sound,
        build_target_envelope, estimate_harmonic_magnitudes,
    )


def test_sound_analysis_exports():
    """sound_analysis.py exports all analysis functions."""
    from backend.sound_analysis import (
        analyze_wav, synthesize_harmonic, save_synthetic_wav,
        validate_physical_series,
    )


def test_pareto_optimizer_has_nsga2():
    """pareto_optimizer.py exports nsga2_minimize."""
    from backend.optimization.nsga2 import nsga2_minimize
    from backend.optimization.pareto import run_pareto, pareto_sweep
    import numpy as np

    # Test that nsga2_minimize is callable
    def simple_cost(x):
        return float(np.sum(x ** 2))

    xl = np.array([-1.0, -1.0])
    xu = np.array([1.0, 1.0])
    result = nsga2_minimize(simple_cost, 2, xl, xu, pop_size=10, n_gen=5)
    if result is not None:
        assert "x" in result
        assert "fun" in result
        assert len(result["x"]) == 2


def test_design_from_unconventional():
    """design_from_unconventional.py exports public functions."""
    from backend.design_from_unconventional import (
        design_from_profile, optimize_conical_bore, spline_bore_to_geometry,
    )


def test_acoustic_network():
    """AcousticNetwork conversion chain works."""
    from backend.geometry import BoreProfile, HoleLayout, InstrumentGeometry
    from backend.core.network import AcousticNetwork
    from backend.tmm_acoustics import tmm_instrument_from_network
    import numpy as np

    bore = BoreProfile(positions=np.array([0, 600]), radii=np.array([7, 7]))
    holes = HoleLayout(positions=np.array([100, 200]), diameters=np.array([6, 6]))
    geom = InstrumentGeometry(total_length=600, bore=bore, holes=holes, closed_top=True)

    network = geom.to_network(outer_diameter_mm=22.0)
    assert isinstance(network, AcousticNetwork)
    assert network.n_segments == 2
    assert network.n_holes == 2
    assert network.closed_top is True
    assert network.total_length == 600.0

    inst = tmm_instrument_from_network(network)
    assert len(inst.hole_positions) == 2
    assert inst.length == 600.0
    assert inst.closed_top is True


def test_timbre_proxy_module():
    """timbre_proxy.py exports public functions with correct behavior."""
    from backend.physics.timbre_proxy import (
        bore_smoothness, hole_radiation_consistency, compute_timbre_cost,
    )
    import numpy as np

    # Constant bore → zero smoothness
    assert bore_smoothness(np.array([7.0, 7.0, 7.0])) == 0.0
    assert bore_smoothness(np.array([7.0])) == 0.0

    # Uniform holes → zero consistency
    assert hole_radiation_consistency([6.0, 6.0], 7.0) == 0.0

    # Combined cost
    cost = compute_timbre_cost(np.array([7.0, 7.0, 7.0]), [6.0, 6.0], 7.0)
    assert cost == 0.0


def test_pareto_optimizer_backward_compat():
    """pareto_optimizer.py re-exports all names."""
    from backend.pareto_optimizer import (
        nsga2_minimize, run_pareto, pareto_sweep,
        compute_intonation_cost, evaluate_bi_objective,
        compute_timbre_cost, bore_smoothness, hole_radiation_consistency,
        _bore_smoothness, _hole_radiation_consistency,
    )
    import numpy as np
    # Verify aliases point to the same function
    assert _bore_smoothness is bore_smoothness
    assert _hole_radiation_consistency is hole_radiation_consistency


if __name__ == "__main__":
    test_geometry_module()
    print("  geometry: OK")
    test_sound_analysis_module()
    print("  sound_analysis: OK")
    test_design_from_wav_imports()
    print("  design_from_wav imports: OK")
    test_sound_analysis_exports()
    print("  sound_analysis exports: OK")
    test_design_from_wav_exports()
    print("  design_from_wav exports: OK")
    test_pareto_optimizer_has_nsga2()
    print("  pareto_optimizer nsga2: OK")
    test_design_from_unconventional()
    print("  design_from_unconventional: OK")
    test_acoustic_network()
    print("  acoustic_network: OK")
    test_timbre_proxy_module()
    print("  timbre_proxy: OK")
    test_pareto_optimizer_backward_compat()
    print("  pareto_optimizer backward-compat: OK")
    print("\nAll architecture reorganization tests passed!")
