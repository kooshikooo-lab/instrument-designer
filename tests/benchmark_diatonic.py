"""
Diatonic scale prototype benchmark.

The idea: confirm acoustic design on a diatonic instrument first,
then extend to chromatic. Easier to build, easier to play, validates
the TMM model before tackling full complexity.

Tests:
1. Chalumeau in C (diatonic, 6 holes, C4-A4)
2. Bass chalumeau in Bb (diatonic, 8 holes, Bb2-G3)
3. Soprano saxophone in Bb (diatonic, 7 holes, Bb4-G5)
4. Alto saxophone in Eb (diatonic, 7 holes, Eb4-D5)
"""

import sys, os, time
import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.tmm_acoustics import tmm_instrument_from_radii, SPEED_OF_SOUND
from backend.tmm_optimizer_v2 import TMMBoreOptimizerJAX


# ============================================================================
# Diatonic instrument configurations
# ============================================================================

INSTRUMENTS = {
    # --- CHALUMEAU: diatonic C major, 6 holes ---
    "chalumeau_C_diatonic": {
        "description": "Chalumeau in C — diatonic major scale, 6 holes",
        "pipe_type": "closed-open",
        "targets": [261.6, 293.7, 329.6, 349.2, 392.0, 440.0],  # C4 D4 E4 F4 G4 A4
        "names": ["C4", "D4", "E4", "F4", "G4", "A4"],
        "bore_length": 300.0,
        "bore_radius": 7.25,
        "outer_diameter": 22.0,
        "hole_positions": [50.0, 90.0, 130.0, 170.0, 210.0, 250.0],
        "hole_diameters": [7.0] * 6,
        "hole_lengths": [3.75] * 6,
        "fingering_sets": [
            ["closed", "closed", "closed", "closed", "closed", "closed"],  # C4
            ["open",   "closed", "closed", "closed", "closed", "closed"],  # D4
            ["open",   "open",   "closed", "closed", "closed", "closed"],  # E4
            ["open",   "open",   "open",   "closed", "closed", "closed"],  # F4
            ["open",   "open",   "open",   "open",   "closed", "closed"],  # G4
            ["open",   "open",   "open",   "open",   "open",   "closed"],  # A4
        ],
        "n_register": 1,
    },

    # --- BASS CHALUMEAU: diatonic Bb major, 8 holes ---
    "bass_chalumeau_Bb": {
        "description": "Bass chalumeau in Bb — diatonic major scale, 8 holes",
        "pipe_type": "closed-open",
        "targets": [233.1, 261.6, 293.7, 311.1, 349.2, 392.0, 440.0, 466.2],  # Bb2 C3 D3 Eb3 F3 G3 A3 Bb3
        "names": ["Bb2", "C3", "D3", "Eb3", "F3", "G3", "A3", "Bb3"],
        "bore_length": 600.0,
        "bore_radius": 9.5,
        "outer_diameter": 28.0,
        "hole_positions": [60.0, 120.0, 180.0, 240.0, 300.0, 360.0, 420.0, 520.0],
        "hole_diameters": [8.0] * 8,
        "hole_lengths": [4.0] * 8,
        "fingering_sets": [
            ["closed"] * 8,                                                # Bb2
            ["open",   "closed", "closed", "closed", "closed", "closed", "closed", "closed"],  # C3
            ["open",   "open",   "closed", "closed", "closed", "closed", "closed", "closed"],  # D3
            ["open",   "open",   "open",   "closed", "closed", "closed", "closed", "closed"],  # Eb3
            ["open",   "open",   "open",   "open",   "closed", "closed", "closed", "closed"],  # F3
            ["open",   "open",   "open",   "open",   "open",   "closed", "closed", "closed"],  # G3
            ["open",   "open",   "open",   "open",   "open",   "open",   "closed", "closed"],  # A3
            ["open",   "open",   "open",   "open",   "open",   "open",   "open",   "closed"],  # Bb3
        ],
        "n_register": 1,
    },

    # --- SOPRANO SAX: diatonic Bb major, 7 holes ---
    "soprano_sax_Bb_diatonic": {
        "description": "Soprano sax in Bb — diatonic major scale, 7 holes, conical bore",
        "pipe_type": "open-open",
        "targets": [466.2, 523.3, 587.3, 622.3, 698.5, 784.0, 880.0, 932.3],  # Bb4 C5 D5 Eb5 F5 G5 A5 Bb5
        "names": ["Bb4", "C5", "D5", "Eb5", "F5", "G5", "A5", "Bb5"],
        "bore_length": 600.0,
        "bore_radius": 6.0,
        "outer_diameter": 20.0,
        "hole_positions": [60.0, 130.0, 200.0, 270.0, 340.0, 410.0, 520.0],
        "hole_diameters": [6.5] * 7,
        "hole_lengths": [3.0] * 7,
        "fingering_sets": [
            ["closed"] * 7,                                                # Bb4
            ["open",   "closed", "closed", "closed", "closed", "closed", "closed"],  # C5
            ["open",   "open",   "closed", "closed", "closed", "closed", "closed"],  # D5
            ["open",   "open",   "open",   "closed", "closed", "closed", "closed"],  # Eb5
            ["open",   "open",   "open",   "open",   "closed", "closed", "closed"],  # F5
            ["open",   "open",   "open",   "open",   "open",   "closed", "closed"],  # G5
            ["open",   "open",   "open",   "open",   "open",   "open",   "closed"],  # A5
            ["open",   "open",   "open",   "open",   "open",   "open",   "open"],     # Bb5
        ],
        "n_register": 1,
    },

    # --- ALTO SAX: diatonic Eb major, 7 holes ---
    "alto_sax_Eb_diatonic": {
        "description": "Alto sax in Eb — diatonic major scale, 7 holes, conical bore",
        "pipe_type": "open-open",
        "targets": [311.1, 349.2, 392.0, 415.3, 466.2, 523.3, 587.3, 622.3],  # Eb4 F4 G4 Ab4 Bb4 C5 D5 Eb5
        "names": ["Eb4", "F4", "G4", "Ab4", "Bb4", "C5", "D5", "Eb5"],
        "bore_length": 1100.0,
        "bore_radius": 8.5,
        "outer_diameter": 26.0,
        "hole_positions": [80.0, 190.0, 300.0, 410.0, 520.0, 630.0, 900.0],
        "hole_diameters": [7.5] * 7,
        "hole_lengths": [3.5] * 7,
        "fingering_sets": [
            ["closed"] * 7,                                                # Eb4
            ["open",   "closed", "closed", "closed", "closed", "closed", "closed"],  # F4
            ["open",   "open",   "closed", "closed", "closed", "closed", "closed"],  # G4
            ["open",   "open",   "open",   "closed", "closed", "closed", "closed"],  # Ab4
            ["open",   "open",   "open",   "open",   "closed", "closed", "closed"],  # Bb4
            ["open",   "open",   "open",   "open",   "open",   "closed", "closed"],  # C5
            ["open",   "open",   "open",   "open",   "open",   "open",   "closed"],  # D5
            ["open",   "open",   "open",   "open",   "open",   "open",   "open"],     # Eb5
        ],
        "n_register": 1,
    },
}


def verify_instrument(radii_mm, cfg, label=""):
    inst = tmm_instrument_from_radii(
        radii_mm, cfg["bore_length"],
        cfg["hole_positions"], cfg["hole_diameters"], cfg["hole_lengths"],
        cfg["outer_diameter"],
        closed_top=(cfg["pipe_type"] == "closed-open"),
        cone_step=0.5,
    )
    target_wavelengths = [SPEED_OF_SOUND / f for f in cfg["targets"]]
    freqs = inst.compute_fingered_frequencies(target_wavelengths, cfg["fingering_sets"], cfg["n_register"])

    print(f"\n  {label}")
    print(f"  {'Note':<8} {'Target':>10} {'Actual':>10} {'Cents':>8}")
    print(f"  {'-'*8} {'-'*10} {'-'*10} {'-'*8}")

    cents_errors = []
    for name, target, actual in zip(cfg["names"], cfg["targets"], freqs):
        err = 1200.0 * np.log2(actual / target) if actual > 0 else 1e10
        cents_errors.append(err)
        print(f"  {name:<8} {target:>10.1f} {actual:>10.1f} {err:>+8.1f}")

    cents_arr = np.array(cents_errors)
    if np.any(np.abs(cents_arr) > 1e5):
        print(f"  FAILED")
        return 1e10, 1e10

    offset = np.median(cents_arr)
    corrected = cents_arr - offset
    rms = float(np.sqrt(np.mean(corrected ** 2)))
    peak = float(np.max(np.abs(corrected)))
    print(f"  RMS: {rms:.2f} cents | Peak: {peak:.2f} cents | Offset: {offset:+.1f}")
    return rms, peak


# ============================================================================
# Run benchmarks
# ============================================================================

all_results = {}

for name, cfg in INSTRUMENTS.items():
    print("\n" + "#" * 70)
    print(f"# {cfg['description']}")
    print(f"# Bore: {cfg['bore_length']:.0f}mm x {cfg['bore_radius']:.1f}mm r | "
          f"{len(cfg['hole_positions'])} holes | {cfg['pipe_type']}")
    print("#" * 70)

    min_r = cfg["bore_radius"] * 0.5
    max_r = cfg["bore_radius"] * 1.5

    t0 = time.time()
    opt = TMMBoreOptimizerJAX(
        target_frequencies=cfg["targets"],
        fingering_sets=cfg["fingering_sets"],
        n_control_points=20,
        bore_length=cfg["bore_length"],
        min_radius=min_r,
        max_radius=max_r,
        hole_positions=cfg["hole_positions"],
        hole_diameters=cfg["hole_diameters"],
        hole_lengths=cfg["hole_lengths"],
        closed_top=(cfg["pipe_type"] == "closed-open"),
        outer_diameter=cfg["outer_diameter"],
        n_register=cfg["n_register"],
    )
    result = opt.run(verbose=True, maxiter=600)
    elapsed = time.time() - t0

    print(f"\n  Wall time: {elapsed:.1f}s")
    rms, peak = verify_instrument(np.array(result["best_radii"]), cfg, "Result")
    all_results[name] = {"rms": rms, "peak": peak, "time": elapsed}


# ============================================================================
# Summary
# ============================================================================

print("\n" + "#" * 70)
print("# DIATONIC PROTOTYPE SUMMARY")
print("#" * 70)
print(f"\n  {'Instrument':<30} {'RMS':>8} {'Peak':>8} {'Time':>8} {'Status'}")
print(f"  {'-'*30} {'-'*8} {'-'*8} {'-'*8} {'-'*10}")
for name, data in all_results.items():
    rms = data["rms"]
    status = "PASS" if rms < 3.0 else ("CLOSE" if rms < 10.0 else "FAIL")
    print(f"  {name:<30} {rms:>7.2f} {data['peak']:>7.1f} {data['time']:>7.1f}s  {status}")

print(f"""
  DESIGN PHILOSOPHY:
  1. Confirm acoustic design on diatonic first (fewer notes, simpler)
  2. Validate TMM model matches physical expectations
  3. Then extend to chromatic (more holes, keys, register system)
  4. Apply same approach across families (chalumeau -> sax -> clarinet)

  BASS CHALUMEAU as BASS CLARINET PROTOTYPE:
  - 600mm bore models the lower joint of a bass clarinet
  - 8 diatonic holes validates hole sizing at low frequencies
  - Next: add U-bend, bell, and register key for full bass clarinet
  - Key benefit: simpler to build and play, confirms the TMM model
    at bass frequencies before tackling 1800mm bore + 21 keys
""")
