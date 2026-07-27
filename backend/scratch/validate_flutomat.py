"""
Validate our flute calculator against Flutomat NG algorithm.

Flutomat NG uses Benade's acoustic model with these corrections:
- Speed of sound: V = 331.3 * sqrt(1 + TempC / 273.15)
- End correction: C_end = 0.6133 * bore_radius
- Closed hole correction: C_c = 0.25 * wall * (hole_d / bore_d)^2
- Effective hole height: t_e = wall + 0.75 * hole_d
- Embouchure correction: C_emb = (bore/Demb)^2 * 10.84 * wall * Demb / (bore + 2*wall)

Position calculation uses quadratic solution from Benade's impedance matching.
"""
import numpy as np
from typing import List, Dict, Tuple

# Standard frequencies (A4=440Hz)
NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

def note_to_freq(note: str, octave: int) -> float:
    """Convert note name + octave to frequency in Hz."""
    semitone = NOTE_NAMES.index(note) - 9  # A=0
    return 440.0 * (2.0 ** ((semitone + (octave - 4) * 12) / 12.0))

def speed_of_sound(temp_c: float = 20.0) -> float:
    """Speed of sound in m/s (Flutomat formula)."""
    return 331.3 * np.sqrt(1.0 + temp_c / 273.15)


def flutomat_calculate(
    bore_diameter: float,  # mm
    wall_thickness: float,  # mm
    embouchure_diameter: float,  # mm
    hole_diameters: List[float],  # mm, 6 holes
    hole_frequencies: List[float],  # Hz, 6 holes
    end_frequency: float,  # Hz, fundamental (all holes closed)
    temperature_c: float = 20.0,
) -> Dict:
    """
    Replicate Flutomat NG's quadratic position calculation.
    
    All inputs in mm, frequencies in Hz.
    Returns distances from open end in mm.
    """
    # Convert to cm for Flutomat's internal units (cm)
    bore = bore_diameter / 10.0  # cm
    wall = wall_thickness / 10.0  # cm
    emb_d = embouchure_diameter / 10.0  # cm
    hole_ds = [d / 10.0 for d in hole_diameters]  # cm
    sos = speed_of_sound(temperature_c) * 100  # cm/s
    
    # Constants
    END_CORRECTION_FACTOR = 0.6133
    HOLE_HEIGHT_FACTOR = 0.75
    
    # 1. Calculate corrections
    end_correction = END_CORRECTION_FACTOR * (bore / 2.0)
    
    closed_hole_corrections = []
    for i in range(6):
        ratio = hole_ds[i] / bore
        cc = 0.25 * wall * ratio * ratio
        closed_hole_corrections.append(cc)
    
    # 2. Calculate effective acoustic end (Xend)
    target_L_end = sos * 0.5 / end_frequency
    acoustic_end_x = target_L_end - end_correction
    for cc in closed_hole_corrections:
        acoustic_end_x -= cc
    
    # 3. Calculate first hole position (quadratic)
    te_1 = wall + HOLE_HEIGHT_FACTOR * hole_ds[0]
    L1 = sos * 0.5 / hole_frequencies[0]
    for i in range(1, 6):
        L1 -= closed_hole_corrections[i]
    
    d1_ratio_sq = (hole_ds[0] / bore) ** 2
    a1 = d1_ratio_sq
    b1 = -(acoustic_end_x + L1) * d1_ratio_sq
    c1 = acoustic_end_x * L1 * d1_ratio_sq + te_1 * (L1 - acoustic_end_x)
    
    disc1 = b1 * b1 - 4 * a1 * c1
    if disc1 < 0:
        raise ValueError(f"Discriminant negative for hole 1: {disc1}")
    
    xf1 = (-b1 - np.sqrt(disc1)) / (2 * a1)
    
    # 4. Calculate subsequent holes
    acoustic_positions = [xf1]
    for n in range(1, 6):
        te_n = wall + HOLE_HEIGHT_FACTOR * hole_ds[n]
        L_n = sos * 0.5 / hole_frequencies[n]
        for i in range(n + 1, 6):
            L_n -= closed_hole_corrections[i]
        
        prev_pos = acoustic_positions[n - 1]
        bore_d_ratio_sq = (bore / hole_ds[n]) ** 2
        
        a_n = 2.0
        b_n = -prev_pos - 3.0 * L_n + te_n * bore_d_ratio_sq
        c_n = prev_pos * (L_n - te_n * bore_d_ratio_sq) + L_n * L_n
        
        disc_n = b_n * b_n - 4.0 * a_n * c_n
        if disc_n < 0:
            raise ValueError(f"Discriminant negative for hole {n+1}: {disc_n}")
        
        xf_n = (-b_n - np.sqrt(disc_n)) / (2.0 * a_n)
        acoustic_positions.append(xf_n)
    
    # 5. Embouchure position
    bore_demb_ratio_sq = (bore / emb_d) ** 2
    emb_correction = bore_demb_ratio_sq * 10.84 * wall * emb_d / (bore + 2.0 * wall)
    
    # 6. Physical positions from open end
    embouchure_pos = acoustic_end_x - emb_correction
    hole_positions = [acoustic_end_x - xf for xf in acoustic_positions]
    
    # Convert back to mm
    return {
        "bore_diameter_mm": bore_diameter,
        "wall_thickness_mm": wall_thickness,
        "temperature_c": temperature_c,
        "speed_of_sound_ms": speed_of_sound(temperature_c),
        "end_correction_mm": end_correction * 10,
        "embouchure_position_mm": embouchure_pos * 10,
        "hole_positions_mm": [p * 10 for p in hole_positions],
        "hole_distances_from_open_mm": [p * 10 for p in hole_positions],
        "acoustic_end_x_cm": acoustic_end_x,
    }


def our_calculator_positions(
    bore_diameter_mm: float,
    fundamental_note: str,
    fundamental_octave: int,
    n_holes: int = 6,
    wall_thickness_mm: float = 2.9,
    embouchure_diameter_mm: float = 9.5,
    embouchure_offset_mm: float = 22.0,
    temperature_c: float = 20.0,
    scale: str = "diatonic",
) -> List[float]:
    """
    Get hole positions from our flute_calculator.py module.
    Returns distances from embouchure center in mm.
    """
    import sys
    sys.path.insert(0, '.')
    from backend.flute_calculator import pvc_flute_holes
    
    result = pvc_flute_holes(
        bore_diameter_mm=bore_diameter_mm,
        fundamental_note=fundamental_note,
        fundamental_octave=fundamental_octave,
        n_holes=n_holes,
        wall_thickness_mm=wall_thickness_mm,
        embouchure_diameter_mm=embouchure_diameter_mm,
        embouchure_offset_mm=embouchure_offset_mm,
        temperature_c=temperature_c,
        scale=scale,
    )
    return [h["position_from_embouchure_mm"] for h in result["holes"]]


def run_validation():
    """Compare our calculator with Flutomat NG algorithm."""
    print("=" * 70)
    print("FLUTE CALCULATOR VALIDATION vs FLUTOMAT NG")
    print("=" * 70)
    
    # Test case 1: D4 flute (3/4" PVC)
    print("\n--- Test 1: D4 PVC Flute (3/4\" Schedule 40) ---")
    bore_d = 20.9  # mm
    wall = 2.9  # mm
    emb_d = 9.5  # mm
    
    # D4 major scale frequencies
    f_end = note_to_freq('D', 4)  # 293.66 Hz
    hole_notes = [('E', 4), ('F#', 4), ('G', 4), ('A', 4), ('B', 4), ('C#', 5)]
    hole_freqs = [note_to_freq(n, o) for n, o in hole_notes]
    hole_ds = [bore_d * 0.7] * 6  # 70% of bore
    
    print(f"  Bore: {bore_d}mm, Wall: {wall}mm, Emb: {emb_d}mm")
    print(f"  Fundamental: D4 ({f_end:.1f} Hz)")
    print(f"  Hole frequencies: {[f'{n}{o}' for n,o in hole_notes]}")
    
    # Flutomat NG calculation
    flutomat = flutomat_calculate(
        bore_d, wall, emb_d, hole_ds, hole_freqs, f_end, temperature_c=20.0
    )
    
    # Our calculator
    our_pos = our_calculator_positions(
        bore_d, 'D', 4, n_holes=6, wall_thickness_mm=wall,
        embouchure_diameter_mm=emb_d, temperature_c=20.0
    )
    
    print(f"\n  {'Hole':<8} {'Flutomat (mm)':<15} {'Ours (mm)':<15} {'Diff (mm)':<12} {'Diff %':<8}")
    print(f"  {'-'*60}")
    
    flutomat_holes = flutomat["hole_positions_mm"]
    for i in range(6):
        diff = our_pos[i] - flutomat_holes[i]
        pct = (diff / flutomat_holes[i]) * 100 if flutomat_holes[i] != 0 else 0
        print(f"  {i+1:<8} {flutomat_holes[i]:<15.1f} {our_pos[i]:<15.1f} {diff:<12.1f} {pct:<8.1f}")
    
    # Embouchure
    print(f"\n  Embouchure from end: Flutomat={flutomat['embouchure_position_mm']:.1f}mm")
    
    # Test case 2: C4 flute
    print("\n--- Test 2: C4 PVC Flute ---")
    f_end_c = note_to_freq('C', 4)
    hole_notes_c = [('D', 4), ('E', 4), ('F', 4), ('G', 4), ('A', 4), ('B', 4)]
    hole_freqs_c = [note_to_freq(n, o) for n, o in hole_notes_c]
    
    flutomat_c = flutomat_calculate(
        bore_d, wall, emb_d, hole_ds, hole_freqs_c, f_end_c, temperature_c=20.0
    )
    
    our_pos_c = our_calculator_positions(
        bore_d, 'C', 4, n_holes=6, wall_thickness_mm=wall,
        embouchure_diameter_mm=emb_d, temperature_c=20.0
    )
    
    print(f"  Fundamental: C4 ({f_end_c:.1f} Hz)")
    print(f"\n  {'Hole':<8} {'Flutomat (mm)':<15} {'Ours (mm)':<15} {'Diff (mm)':<12} {'Diff %':<8}")
    print(f"  {'-'*60}")
    
    for i in range(6):
        diff = our_pos_c[i] - flutomat_c["hole_positions_mm"][i]
        pct = (diff / flutomat_c["hole_positions_mm"][i]) * 100 if flutomat_c["hole_positions_mm"][i] != 0 else 0
        print(f"  {i+1:<8} {flutomat_c['hole_positions_mm'][i]:<15.1f} {our_pos_c[i]:<15.1f} {diff:<12.1f} {pct:<8.1f}")
    
    # Test case 3: G4 flute (smaller bore)
    print("\n--- Test 3: G4 Flute (16mm bore) ---")
    bore_g = 16.0
    emb_d_g = 7.0
    f_end_g = note_to_freq('G', 4)
    hole_notes_g = [('A', 4), ('B', 4), ('C', 5), ('D', 5), ('E', 5), ('F#', 5)]
    hole_freqs_g = [note_to_freq(n, o) for n, o in hole_notes_g]
    hole_ds_g = [bore_g * 0.7] * 6
    
    flutomat_g = flutomat_calculate(
        bore_g, wall, emb_d_g, hole_ds_g, hole_freqs_g, f_end_g, temperature_c=20.0
    )
    
    our_pos_g = our_calculator_positions(
        bore_g, 'G', 4, n_holes=6, wall_thickness_mm=wall,
        embouchure_diameter_mm=emb_d_g, temperature_c=20.0
    )
    
    print(f"  Fundamental: G4 ({f_end_g:.1f} Hz)")
    print(f"\n  {'Hole':<8} {'Flutomat (mm)':<15} {'Ours (mm)':<15} {'Diff (mm)':<12} {'Diff %':<8}")
    print(f"  {'-'*60}")
    
    for i in range(6):
        diff = our_pos_g[i] - flutomat_g["hole_positions_mm"][i]
        pct = (diff / flutomat_g["hole_positions_mm"][i]) * 100 if flutomat_g["hole_positions_mm"][i] != 0 else 0
        print(f"  {i+1:<8} {flutomat_g['hole_positions_mm'][i]:<15.1f} {our_pos_g[i]:<15.1f} {diff:<12.1f} {pct:<8.1f}")
    
    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
Our calculator uses a simpler formula (L = c/(2f) - end_correction) which gives
approximate positions. Flutomat NG uses Benade's impedance-matching equations
with quadratic solutions that account for:
  - Closed hole corrections (volume added by holes above first open)
  - Effective hole height (wall + 0.75 * diameter)
  - Embouchure correction (Kosel's empirical fit)
  - Hole-to-hole interactions (lattice correction)

The differences show our simplified model is a good first approximation but
Flutomat's Benade model is more accurate for real instrument building.
""")


if __name__ == "__main__":
    run_validation()
