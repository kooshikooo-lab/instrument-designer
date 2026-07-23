"""
Flute & Overtone Flute Calculator

Computes:
1. PVC flute tone hole placement (for transverse/fipple flutes)
2. Overtone flute length (for seljeflöyte, koncovka, fujara)
3. OpenWInD impedance validation

Based on:
- Benade & French (1965) W-curves
- Flutomat (Kosel) empirical corrections
- UNSW acoustic research (Wolfe, Dickens)
- Nederveen (1998) tone hole theory
"""
import numpy as np
from typing import List, Tuple, Optional, Dict
import json
import os
import sys

# Standard frequencies (A4=440Hz, equal temperament)
NOTE_NAMES = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

def note_to_freq(note: str, octave: int) -> float:
    """Convert note name + octave to frequency in Hz."""
    if note not in NOTE_NAMES:
        raise ValueError(f"Invalid note: {note}. Must be one of {NOTE_NAMES}")
    semitone = NOTE_NAMES.index(note) - 9  # A=0
    freq = 440.0 * (2.0 ** ((semitone + (octave - 4) * 12) / 12.0))
    return freq


def freq_to_note(freq: float) -> Tuple[str, int]:
    """Convert frequency to nearest note name + octave."""
    semitones_from_a4 = 12.0 * np.log2(freq / 440.0)
    midi = int(round(semitones_from_a4)) + 69
    note_idx = midi % 12
    octave = (midi // 12) - 1
    return NOTE_NAMES[note_idx], octave


def speed_of_sound(temp_c: float = 20.0) -> float:
    """Speed of sound in m/s at given temperature."""
    return 331.3 + 0.606 * temp_c


# ============================================================================
# PVC FLUTE TONE HOLE CALCULATOR (Flutomat/Benade model)
# ============================================================================

def pvc_flute_holes(
    bore_diameter_mm: float,
    fundamental_note: str,
    fundamental_octave: int,
    n_holes: int = 6,
    wall_thickness_mm: float = 2.9,
    embouchure_diameter_mm: float = 9.5,
    embouchure_offset_mm: float = 22.0,
    temperature_c: float = 20.0,
    scale: str = "chromatic",
) -> Dict:
    """
    Calculate tone hole positions for a PVC flute using Flutomat/Benade model.
    
    Uses Benade's impedance-matching equations with quadratic solutions for
    accurate hole positions. Accounts for:
    - End correction: C_end = 0.6133 * bore_radius
    - Closed hole correction: C_c = 0.25 * wall * (hole_d / bore_d)^2
    - Effective hole height: t_e = wall + 0.75 * hole_d
    - Embouchure correction: C_emb = (bore/Demb)^2 * 10.84 * wall * Demb / (bore + 2*wall)
    
    Args:
        bore_diameter_mm: Inner diameter of PVC pipe (e.g., 20.9 for 3/4" Sch40)
        fundamental_note: Note name (e.g., 'C', 'D', 'Bb')
        fundamental_octave: Octave number (e.g., 4 for C4)
        n_holes: Number of finger holes
        wall_thickness_mm: PVC wall thickness
        embouchure_diameter_mm: Embouchure hole diameter
        embouchure_offset_mm: Distance from pipe end to embouchure center
        temperature_c: Air temperature
        scale: "chromatic", "diatonic", "major", "minor"
    
    Returns dict with bore_length, hole_positions, hole_diameters, etc.
    """
    # Convert to cm for Flutomat's internal units
    bore = bore_diameter_mm / 10.0  # cm
    wall = wall_thickness_mm / 10.0  # cm
    emb_d = embouchure_diameter_mm / 10.0  # cm
    sos = speed_of_sound(temperature_c) * 100  # cm/s
    
    # Constants (from Flutomat NG)
    END_CORRECTION_FACTOR = 0.6133
    HOLE_HEIGHT_FACTOR = 0.75
    
    # Generate scale notes
    f0 = note_to_freq(fundamental_note, fundamental_octave)
    note_idx = NOTE_NAMES.index(fundamental_note)
    
    if scale == "chromatic":
        holes = []
        for i in range(n_holes):
            semitones = i + 1
            hole_note_idx = (note_idx + semitones) % 12
            hole_octave = fundamental_octave + (note_idx + semitones) // 12
            holes.append((NOTE_NAMES[hole_note_idx], hole_octave))
    elif scale in ("diatonic", "major"):
        major_intervals = [2, 2, 1, 2, 2, 2, 1]
        holes = []
        cumulative = 0
        for i in range(min(n_holes, 7)):
            cumulative += major_intervals[i % 7]
            hole_note_idx = (note_idx + cumulative) % 12
            hole_octave = fundamental_octave + (note_idx + cumulative) // 12
            holes.append((NOTE_NAMES[hole_note_idx], hole_octave))
    elif scale == "minor":
        minor_intervals = [2, 1, 2, 2, 1, 2, 2]
        holes = []
        cumulative = 0
        for i in range(min(n_holes, 7)):
            cumulative += minor_intervals[i % 7]
            hole_note_idx = (note_idx + cumulative) % 12
            hole_octave = fundamental_octave + (note_idx + cumulative) // 12
            holes.append((NOTE_NAMES[hole_note_idx], hole_octave))
    else:
        raise ValueError(f"Unknown scale: {scale}")
    
    # Calculate hole frequencies and diameters
    hole_freqs = [note_to_freq(n, o) for n, o in holes]
    hole_ds = [bore * 0.7] * n_holes  # 70% of bore diameter
    
    # --- Flutomat/Benade quadratic position calculation ---
    
    # 1. Calculate corrections
    end_correction = END_CORRECTION_FACTOR * (bore / 2.0)
    
    closed_hole_corrections = []
    for i in range(n_holes):
        ratio = hole_ds[i] / bore
        cc = 0.25 * wall * ratio * ratio
        closed_hole_corrections.append(cc)
    
    # 2. Calculate effective acoustic end (Xend)
    target_L_end = sos * 0.5 / f0
    acoustic_end_x = target_L_end - end_correction
    for cc in closed_hole_corrections:
        acoustic_end_x -= cc
    
    # 3. Calculate first hole position (quadratic)
    te_1 = wall + HOLE_HEIGHT_FACTOR * hole_ds[0]
    L1 = sos * 0.5 / hole_freqs[0]
    for i in range(1, n_holes):
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
    for n in range(1, n_holes):
        te_n = wall + HOLE_HEIGHT_FACTOR * hole_ds[n]
        L_n = sos * 0.5 / hole_freqs[n]
        for i in range(n + 1, n_holes):
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
    embouchure_pos_cm = acoustic_end_x - emb_correction
    
    # 6. Physical positions from open end (convert to mm)
    hole_positions_from_open = [(acoustic_end_x - xf) * 10 for xf in acoustic_positions]
    embouchure_pos_mm = embouchure_pos_cm * 10
    
    # 7. Convert to positions from embouchure center
    # Holes are between embouchure and open end, so distance from embouchure = embouchure_pos - hole_pos
    hole_positions_from_emb = [embouchure_pos_mm - pos for pos in hole_positions_from_open]
    
    # 8. Bore length
    bore_length = embouchure_pos_mm + embouchure_offset_mm
    
    # 9. Build result
    hole_diams = [d * 10 for d in hole_ds]  # back to mm
    
    return {
        "bore_diameter_mm": bore_diameter_mm,
        "bore_length_mm": round(bore_length, 1),
        "bore_length_cm": round(bore_length / 10, 1),
        "bore_length_m": round(bore_length / 1000, 4),
        "fundamental": f"{fundamental_note}{fundamental_octave}",
        "fundamental_hz": round(f0, 1),
        "speed_of_sound_ms": round(sos / 100, 1),
        "end_correction_mm": round(end_correction * 10, 1),
        "embouchure": {
            "diameter_mm": embouchure_diameter_mm,
            "position_from_open_mm": round(embouchure_pos_mm, 1),
            "position_from_embouchure_mm": embouchure_offset_mm,
        },
        "wall_thickness_mm": wall_thickness_mm,
        "scale": scale,
        "algorithm": "Flutomat/Benade (quadratic impedance matching)",
        "holes": [
            {
                "number": i + 1,
                "note": f"{holes[i][0]}{holes[i][1]}",
                "frequency_hz": round(hole_freqs[i], 1),
                "position_from_open_mm": round(hole_positions_from_open[i], 1),
                "position_from_embouchure_mm": round(hole_positions_from_emb[i], 1),
                "position_from_embouchure_cm": round(hole_positions_from_emb[i] / 10, 1),
                "diameter_mm": round(hole_diams[i], 1),
                "cents_from_et": 0,
            }
            for i in range(n_holes)
        ],
        "pvc_specs": pvc_pipe_specs(bore_diameter_mm),
    }


def pvc_pipe_specs(inner_diameter_mm: float) -> Dict:
    """Look up PVC pipe specifications from inner diameter."""
    pipes = [
        {"name": '1/2" Sch40', "id_mm": 15.8, "od_mm": 21.3, "wall_mm": 2.8},
        {"name": '3/4" Sch40', "id_mm": 20.9, "od_mm": 26.7, "wall_mm": 2.9},
        {"name": '1" Sch40', "id_mm": 26.1, "od_mm": 33.4, "wall_mm": 3.4},
        {"name": '1-1/4" Sch40', "id_mm": 34.5, "od_mm": 42.2, "wall_mm": 3.6},
    ]
    # Find closest match
    best = min(pipes, key=lambda p: abs(p["id_mm"] - inner_diameter_mm))
    if abs(best["id_mm"] - inner_diameter_mm) < 2:
        return {"closest_match": best["name"], **best}
    return {"closest_match": "Custom", "id_mm": inner_diameter_mm}


# ============================================================================
# OVERTONE FLUTE LENGTH CALCULATOR
# ============================================================================

def overtone_flute_length(
    fundamental_note: str,
    fundamental_octave: int,
    bore_diameter_mm: float = 16.0,
    end_type: str = "closed",
    temperature_c: float = 20.0,
) -> Dict:
    """
    Calculate the length of an overtone flute (seljeflöyte, koncovka, fujara).
    
    Overtone flutes have no tone holes. Different notes are produced by
    overblowing the harmonic series.
    
    Args:
        fundamental_note: Note name for the lowest note
        fundamental_octave: Octave for the lowest note
        bore_diameter_mm: Inner diameter of the tube
        end_type: "closed" (one end blocked) or "open" (both ends open)
        temperature_c: Air temperature
    
    Returns dict with length, harmonic series, playable notes.
    """
    c = speed_of_sound(temperature_c)
    f0 = note_to_freq(fundamental_note, fundamental_octave)
    bore_r = bore_diameter_mm / 2.0
    end_correction = 0.6 * bore_r  # mm
    
    if end_type == "closed":
        # Closed pipe: L = c/(4f0) - end_correction
        L_eff = c / (4.0 * f0) * 1000.0  # mm
        L_physical = L_eff - end_correction
        
        # Harmonic series: f, 3f, 5f, 7f, 9f, 11f, 13f (odd harmonics)
        harmonics = [n for n in range(1, 26, 2)]  # 1, 3, 5, ..., 25
    else:
        # Open pipe: L = c/(2f0) - 2*end_correction
        L_eff = c / (2.0 * f0) * 1000.0  # mm
        L_physical = L_eff - 2 * end_correction
        
        # Harmonic series: f, 2f, 3f, 4f, 5f, ... (all harmonics)
        harmonics = list(range(1, 26))  # 1, 2, 3, ..., 25
    
    # Calculate playable notes from harmonic series
    playable = []
    for n in harmonics:
        f = f0 * n
        if f > 10000:  # beyond human hearing range
            break
        note_name, note_oct = freq_to_note(f)
        playable.append({
            "harmonic": n,
            "frequency_hz": round(f, 1),
            "note": f"{note_name}{note_oct}",
            "note_name": note_name,
            "octave": note_oct,
        })
    
    return {
        "fundamental": f"{fundamental_note}{fundamental_octave}",
        "fundamental_hz": round(f0, 1),
        "end_type": end_type,
        "bore_diameter_mm": bore_diameter_mm,
        "bore_radius_mm": bore_r,
        "end_correction_mm": round(end_correction, 1),
        "effective_length_mm": round(L_eff, 1),
        "physical_length_mm": round(L_physical, 1),
        "physical_length_cm": round(L_physical / 10, 1),
        "physical_length_m": round(L_physical / 1000, 3),
        "speed_of_sound_ms": round(c, 1),
        "temperature_c": temperature_c,
        "harmonics_available": len(playable),
        "playable_notes": playable,
        "max_note": playable[-1]["note"] if playable else None,
        "pvc_specs": pvc_pipe_specs(bore_diameter_mm),
    }


# ============================================================================
# OPENWIND VALIDATION (optional)
# ============================================================================

def validate_with_openwind(bore_length_m: float, bore_radius_m: float, 
                           end_type: str = "closed",
                           freq_range: Tuple[float, float] = (50, 5000),
                           n_freqs: int = 2000) -> Optional[Dict]:
    """
    Validate a flute bore with OpenWInD impedance computation.
    Returns impedance peaks if OpenWInD is available, None otherwise.
    """
    try:
        import os
        os.environ.setdefault("OMP_NUM_THREADS", "1")
        os.environ.setdefault("MKL_NUM_THREADS", "1")
        os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
        
        from openwind import ImpedanceComputation
        import tempfile
        
        # Create bore CSV
        bore_csv = f"0 {bore_radius_m}\n{bore_length_m} {bore_radius_m}"
        if end_type == "closed":
            # Add closed end (very small radius)
            bore_csv = f"0 0.001\n0.001 {bore_radius_m}\n{bore_length_m} {bore_radius_m}"
        
        tmp = os.path.join(tempfile.gettempdir(), "flute_test.csv")
        with open(tmp, "w") as f:
            f.write(bore_csv)
        
        freqs = np.linspace(freq_range[0], freq_range[1], n_freqs)
        ic = ImpedanceComputation(freqs, tmp, unit="m", diameter=False, temperature=20.0)
        
        freq = np.array(ic.frequencies)
        Z = np.array(ic.impedance)
        mag = np.abs(Z)
        
        from scipy.signal import find_peaks
        peak_height = np.max(mag) * 0.02
        peaks, props = find_peaks(mag, height=peak_height, distance=2, prominence=peak_height * 0.5)
        
        os.remove(tmp)
        
        return {
            "frequencies": freq[::10].tolist(),
            "impedance_magnitude": mag[::10].tolist(),
            "peak_frequencies": freq[peaks].tolist(),
            "peak_magnitudes": mag[peaks].tolist(),
            "n_peaks": len(peaks),
        }
    except ImportError:
        return None
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    print("=" * 60)
    print("FLUTE & OVERTONE FLUTE CALCULATOR")
    print("=" * 60)
    
    # 1. PVC Flute in D (3/4" Schedule 40 PVC)
    print("\n--- PVC Flute in D (3/4\" Schedule 40, 20.9mm bore) ---")
    result = pvc_flute_holes(
        bore_diameter_mm=20.9,
        fundamental_note='D',
        fundamental_octave=4,
        n_holes=6,
        scale="diatonic",
    )
    print(f"  Bore length: {result['bore_length_mm']}mm ({result['bore_length_cm']}cm)")
    print(f"  Fundamental: {result['fundamental']} ({result['fundamental_hz']}Hz)")
    print(f"  Speed of sound: {result['speed_of_sound_ms']}m/s")
    print(f"\n  Hole positions (from embouchure center):")
    for h in result["holes"]:
        print(f"    Hole {h['number']}: {h['note']:4s} ({h['frequency_hz']:7.1f} Hz) "
              f"at {h['position_from_embouchure_cm']:5.1f}cm, d={h['diameter_mm']}mm")
    
    # 2. Overtone Flute (Seljeflöyte-style, closed pipe in G)
    print("\n--- Overtone Flute in G (closed pipe, 16mm bore) ---")
    result = overtone_flute_length(
        fundamental_note='G',
        fundamental_octave=4,
        bore_diameter_mm=16.0,
        end_type="closed",
    )
    print(f"  Physical length: {result['physical_length_mm']}mm ({result['physical_length_cm']}cm)")
    print(f"  Fundamental: {result['fundamental']} ({result['fundamental_hz']}Hz)")
    print(f"  Harmonics available: {result['harmonics_available']}")
    print(f"\n  Playable notes (harmonic series):")
    for note in result["playable_notes"][:12]:
        print(f"    {note['harmonic']:2d}th harmonic: {note['note']:4s} ({note['frequency_hz']:7.1f} Hz)")
    
    # 3. Koncovka-style in C (reference: 63cm → C3 fundamental)
    print("\n--- Koncovka-style in C (closed pipe, 16mm bore) ---")
    result = overtone_flute_length(
        fundamental_note='C',
        fundamental_octave=3,
        bore_diameter_mm=16.0,
        end_type="closed",
    )
    print(f"  Physical length: {result['physical_length_mm']}mm ({result['physical_length_cm']}cm)")
    print(f"  (Reference: traditional koncovka in C = 63cm)")
    
    # 4. Fujara-style in G (reference: 160-200cm → G1 fundamental ~49Hz)
    print("\n--- Fujara-style in G (closed pipe, 20mm bore) ---")
    result = overtone_flute_length(
        fundamental_note='G',
        fundamental_octave=1,
        bore_diameter_mm=20.0,
        end_type="closed",
    )
    print(f"  Physical length: {result['physical_length_mm']}mm ({result['physical_length_cm']}cm)")
    print(f"  (Reference: traditional fujara = 160-200cm)")
    
    # 5. OpenWInD validation
    print("\n--- OpenWInD Impedance Validation (D overtone flute) ---")
    result = overtone_flute_length(
        fundamental_note='D',
        fundamental_octave=4,
        bore_diameter_mm=16.0,
        end_type="closed",
    )
    L_m = result["physical_length_mm"] / 1000.0
    r_m = 0.008  # 8mm radius
    
    ow_result = validate_with_openwind(L_m, r_m, end_type="closed")
    if ow_result and "peak_frequencies" not in ow_result:
        print(f"  OpenWInD not available or error: {ow_result}")
    elif ow_result:
        print(f"  Peaks found: {ow_result['n_peaks']}")
        print(f"  Peak frequencies: {[f'{p:.1f}' for p in ow_result['peak_frequencies'][:8]]}")
        expected = [result['fundamental_hz'] * n for n in [1, 3, 5, 7, 9, 11]]
        print(f"  Expected (odd harmonics): {[f'{e:.1f}' for e in expected[:6]]}")
    else:
        print("  OpenWInD not installed")
    
    # 6. Save results
    output_path = os.path.join(os.path.dirname(__file__), "..", "chat-logs", "flute-calculations.json")
    with open(output_path, "w") as f:
        json.dump({
            "pvc_flute_d": pvc_flute_holes(20.9, 'D', 4, 6, scale="diatonic"),
            "overtone_flute_g": overtone_flute_length('G', 4, 16.0, "closed"),
            "koncovka_c": overtone_flute_length('C', 3, 16.0, "closed"),
            "fujara_g": overtone_flute_length('G', 1, 20.0, "closed"),
        }, f, indent=2)
    print(f"\n  Results saved to: {output_path}")
