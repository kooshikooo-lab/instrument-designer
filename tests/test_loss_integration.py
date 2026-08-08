import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.tmm_acoustics import tmm_instrument_from_radii
from backend.physics.losses import KeefeLoss


def test_loss_integration():
    loss_model = KeefeLoss()
    inst = tmm_instrument_from_radii(
        np.array([7.5]*6),
        320.0,
        [60, 100, 140, 180, 220, 260, 300],
        [5.0]*7,
        [3.5]*7,
        loss_model=loss_model,
    )

    wl_guess = 346100 / 523.25
    wl = inst.find_resonance(wl_guess, ['open']*7, n_register=2)
    freq = inst.frequency_from_wavelength(wl)
    assert abs(freq - 523.25) < 50.0, f"Resonance freq {freq:.1f} Hz too far from target 523.25 Hz"

    factor = loss_model.bore_loss(100.0, 7.5, 661.0)
    assert factor is not None, "bore_loss returned None"
    assert np.isfinite(factor), f"bore_loss returned non-finite: {factor}"
    assert abs(factor) > 0, "Loss factor magnitude must be > 0"
    assert abs(factor) < 1, f"Loss factor magnitude {abs(factor):.4f} too large (expected < 1)"


if __name__ == "__main__":
    test_loss_integration()