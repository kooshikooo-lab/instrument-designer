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


def test_inverse_design_backward_compat():
    """inverse_design.py re-exports all public names."""
    from backend.inverse_design import (
        analyze_wav,
        synthesize_harmonic,
        save_synthetic_wav,
        validate_physical_series,
        design_scale,
        match_timbre,
        design_from_sound,
        build_target_envelope,
        estimate_harmonic_magnitudes,
    )


def test_pareto_optimizer_has_nsga2():
    """pareto_optimizer.py exports nsga2_minimize."""
    from backend.pareto_optimizer import nsga2_minimize, run_pareto, pareto_sweep
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


if __name__ == "__main__":
    test_geometry_module()
    print("  geometry: OK")
    test_sound_analysis_module()
    print("  sound_analysis: OK")
    test_design_from_wav_imports()
    print("  design_from_wav imports: OK")
    test_inverse_design_backward_compat()
    print("  inverse_design backward-compat: OK")
    test_pareto_optimizer_has_nsga2()
    print("  pareto_optimizer nsga2: OK")
    test_design_from_unconventional()
    print("  design_from_unconventional: OK")
    print("\nAll architecture reorganization tests passed!")
