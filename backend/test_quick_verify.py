"""Quick test of corrected TMM with bell-first fingering."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
import numpy as np

bore_radius = 7.25
bore_length = 300.0
outer_diameter = 22.0
radii = np.full(10, bore_radius)

positions = [50.0, 90.0, 130.0, 170.0, 210.0, 250.0]
diameters = [7.0] * 6
lengths = [3.75] * 6

fingering_sets = [
    ["closed"] * 6,
    ["closed","closed","closed","closed","closed","open"],
    ["closed","closed","closed","closed","open","open"],
    ["closed","closed","closed","open","open","open"],
    ["closed","closed","open","open","open","open"],
    ["closed","open","open","open","open","open"],
    ["open","open","open","open","open","open"],
]

targets = [261.6, 277.2, 293.7, 311.1, 329.6, 349.2, 370.0]
names = ["C4","C#4","D4","Eb4","E4","F4","F#4"]

inst = tmm_instrument_from_radii(
    radii, bore_length, positions, diameters, lengths,
    outer_diameter, closed_top=True, cone_step=0.5,
)

target_wavelengths = [SPEED_OF_SOUND / f for f in targets]
freqs = inst.compute_fingered_frequencies(target_wavelengths, fingering_sets, n_register=1)

print("Bell-first ascending test (corrected TMM):")
fmt = "{:<8} {:>10} {:>10} {:>8}"
print(fmt.format("Note", "Target", "Actual", "Cents"))
print("-" * 40)
cents_errors = []
for name, target, actual in zip(names, targets, freqs):
    err = 1200.0 * np.log2(actual / target) if actual > 0 else 1e10
    cents_errors.append(err)
    print(fmt.format(name, f"{target:.1f}", f"{actual:.1f}", f"{err:+.1f}"))

cents_arr = np.array(cents_errors)
if not np.any(np.abs(cents_arr) > 1e5):
    offset = np.median(cents_arr)
    corrected = cents_arr - offset
    rms = float(np.sqrt(np.mean(corrected ** 2)))
    peak = float(np.max(np.abs(corrected)))
    print(f"\nMedian offset: {offset:+.1f} cents")
    print(f"RMS intonation: {rms:.2f} cents")
    print(f"Peak error: {peak:.2f} cents")
else:
    print("\nFAILED - some notes did not resonate")
