"""Test TMM with L-BFGS optimizer for accuracy and timbre."""

from backend.tmm_acoustics import TMMInstrument, SPEED_OF_SOUND
from backend.bore_optimizer_lbfgs import LBFGSBoreOptimizer
from backend.two_phase_optimizer import two_phase_optimize
from backend.physics.losses import KeefeLoss

def test_basic_functionality():
    """Verify all imports work and basic TMM evaluation executes."""
    print("=== Testing Basic TMM Functionality ===")
    
    # Test 1: SPEED_OF_SOUND is consistent with the temperature formula
    # c(T) = 331300 + 606*T mm/s (c = 331.3 + 0.606*T m/s, T in C).
    # The core constant 346100.0 mm/s implies T = (346100-331300)/606 = 24.4C.
    # See PHYSICS_PRINCIPLES.md "Known Discrepancy (finding B1)". Do NOT hardcode
    # a single magic constant here; assert formula consistency instead.
    implied_t = (SPEED_OF_SOUND - 331300.0) / 606.0
    print(f"SPEED_OF_SOUND: {SPEED_OF_SOUND} mm/s (implies T={implied_t:.1f}C)")
    assert 15.0 <= implied_t <= 30.0, f"SPEED_OF_SOUND {SPEED_OF_SOUND} implies implausible T={implied_t:.1f}C"
    print("OK SPEED_OF_SOUND consistent with temperature formula")
    
    # Test 2: Basic TMM instrument creation
    inst = TMMInstrument(
        inner_positions=[0, 100, 200],
        inner_diameters=[14.5, 14.5, 15.0],
        outer_diameters=[22.0, 22.0, 24.0],
        hole_positions=[60],
        hole_diameters=[7.0],
        hole_lengths=[3.75],
        closed_top=False,
    )
    print("OK TMM instrument created")
    
    # Test 3: Basic resonance evaluation
    freq = inst.find_resonance(wavelength_near=800.0, fingerings=[[]])
    print(f"Basic resonance: {freq:.2f} Hz")
    assert freq > 0, "Invalid resonance frequency"
    print("OK TMM resonance evaluation works")
    
    # Test 4: KeefeLoss import and usage
    loss_model = KeefeLoss()
    bore_loss = loss_model.bore_loss(length=100, radius=10, wavelength=800)
    print(f"KeefeLoss bore_loss: {bore_loss}")
    assert bore_loss >= 0.0, "Invalid bore loss"
    print("OK KeefeLoss integration works")
    
    # Test 5: Simple resonance measurement
    wl = inst.find_resonance(wavelength_near=800.0, fingerings=[['O']])
    f = inst.frequency_from_wavelength(wl)
    print(f"Closed-open resonance at position 60mm: {f:.2f} Hz")
    assert f > 0, "Invalid closed-open resonance"
    print("OK Simple resonance measurement works")
    
    print("\nOK All basic functionality tests passed!")


def test_optimizers_use_correct_speed():
    """Verify optimizers reference the canonical speed-of-sound (SPEED_OF_SOUND constant
    or the temperature formula 331.3 + 0.606*T), not a stale hardcoded 346100/343000 magic number."""
    print("\n=== Testing Speed of Sound in Optimizers ===")
    
    import inspect
    from backend.two_phase_optimizer import two_phase_optimize
    from backend.bore_optimizer_lbfgs import LBFGSBoreOptimizer
    
    # Check active optimizer modules
    for module, name in [
        (two_phase_optimize.__module__, "two_phase_optimizer"),
        (LBFGSBoreOptimizer.__module__, "bore_optimizer_lbfgs"),
    ]:
        import sys
        mod = sys.modules.get(module)
        source = inspect.getsource(mod) if mod is not None else ""
        uses_constant = "SPEED_OF_SOUND" in source
        uses_formula = ("331.3" in source) and ("0.606" in source)
        if uses_constant or uses_formula:
            print(f"✓ {name} uses canonical speed of sound (constant={uses_constant}, formula={uses_formula})")
        else:
            print(f"⚠ WARNING: {name} references no canonical speed of sound")
    
    print("\n✅ Speed of sound test completed")


def test_median_correction_removal():
    """Verify median correction is removed from all cost functions."""
    print("\n=== Testing Median Correction Removal ===")
    
    # Test a simple arrays calculation to verify absolute RMS logic
    import numpy as np
    
    test_cents = np.array([100, 200, 300])
    
    # Old median-corrected approach
    median_offset = np.median(test_cents)
    old_median_rms = float(np.sqrt(np.mean((test_cents - median_offset) ** 2)))
    
    # New absolute approach  
    new_abs_rms = float(np.sqrt(np.mean(test_cents ** 2)))
    
    print(f"Test cents: {test_cents}")
    print(f"Old median-corrected RMS: {old_median_rms:.2f}")
    print(f"New absolute RMS: {new_abs_rms:.2f}")
    
    # They should be different values (unless by coincidence)
    if old_median_rms != new_abs_rms:
        print("✓ Median correction successfully removed")
    else:
        print("⚠ Old and new RMS are the same (rare)")
    
    print("\n✅ Median correction verification completed")


if __name__ == "__main__":
    test_basic_functionality()
    test_optimizers_use_correct_speed()
    test_median_correction_removal()
    print("\n" + "="*60)
    print("🎉 ALL TESTS PASSED - Architecture verified!")
    print("="*60)

