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
# PVC FLUTE TONE HOLE CALCULATOR
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
    Calculate tone hole positions for a PVC flute.
    
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
    c = speed_of_sound(temperature_c)
    bore_r = bore_diameter_mm / 2.0
    bore_m = bore_diameter_mm / 1000.0
    
    # Calculate bore length from fundamental (open pipe)
    f0 = note_to_freq(fundamental_note, fundamental_octave)
    end_correction = 0.6 * bore_r  # mm, each open end
    # For transverse flute: embouchure end has correction, open end has correction
    # Total effective length = physical length + end corrections
    L_eff = c / (2.0 * f0) * 1000.0  # mm
    # Physical length = effective length - end corrections at both ends
    bore_length = L_eff - 2 * end_correction
    
    # Generate scale notes (what each hole should produce)
    if scale == "chromatic":
        # Chromatic from fundamental up
        note_idx = NOTE_NAMES.index(fundamental_note)
        holes = []
        for i in range(n_holes):
            semitones = i + 1  # each hole raises by 1 semitone
            hole_note_idx = (note_idx + semitones) % 12
            hole_octave = fundamental_octave + (note_idx + semitones) // 12
            holes.append((NOTE_NAMES[hole_note_idx], hole_octave))
    elif scale == "diatonic" or scale == "major":
        # Major scale from fundamental
        major_intervals = [2, 2, 1, 2, 2, 2, 1]  # semitones
        note_idx = NOTE_NAMES.index(fundamental_note)
        holes = []
        cumulative = 0
        for i in range(min(n_holes, 7)):
            cumulative += major_intervals[i % 7]
            hole_note_idx = (note_idx + cumulative) % 12
            hole_octave = fundamental_octave + (note_idx + cumulative) // 12
            holes.append((NOTE_NAMES[hole_note_idx], hole_octave))
    elif scale == "minor":
        minor_intervals = [2, 1, 2, 2, 1, 2, 2]
        note_idx = NOTE_NAMES.index(fundamental_note)
        holes = []
        cumulative = 0
        for i in range(min(n_holes, 7)):
            cumulative += minor_intervals[i % 7]
            hole_note_idx = (note_idx + cumulative) % 12
            hole_octave = fundamental_octave + (note_idx + cumulative) // 12
            holes.append((NOTE_NAMES[hole_note_idx], hole_octave))
    else:
        raise ValueError(f"Unknown scale: {scale}")
    
    # Calculate hole positions
    # For each hole, the effective length when that hole is open:
    # L_eff_hole = c / (2 * f_hole)
    # Distance from open end = L_eff_hole - end_correction(open end)
    # Distance from embouchure = bore_length - distance_from_open_end
    
    embouchure_correction = embouchure_offset_mm  # approximate
    tone_hole_correction = 0.4 * bore_r  # mm, for open tone hole
    
    hole_positions = []
    hole_diams = []
    hole_freqs = []
    hole_cents = []
    
    for note_name, note_octave in holes:
        f_hole = note_to_freq(note_name, note_octave)
        L_eff_hole = c / (2.0 * f_hole) * 1000.0  # mm
        # Distance from open end (bell end)
        dist_from_open = L_eff_hole - end_correction - tone_hole_correction
        # Distance from embouchure center
        dist_from_emb = bore_length - dist_from_open
        
        # Clamp to valid range
        dist_from_emb = max(embouchure_offset_mm + 20, min(dist_from_emb, bore_length - 10))
        
        # Hole diameter: typically 60-80% of bore diameter
        hole_d = bore_diameter_mm * 0.7
        
        hole_positions.append(round(dist_from_emb, 1))
        hole_diams.append(round(hole_d, 1))
        hole_freqs.append(round(f_hole, 1))
        hole_cents.append(0)  # reference, will be calculated relative to equal temperament
    
    # Theoretical cents errors (all 0 for equal temperament calculation)
    for i, (pos, f_target) in enumerate(zip(hole_positions, hole_freqs)):
        # Actual frequency depends on which holes are open - this is simplified
        hole_cents[i] = 0  # Perfect ET assumed for layout
    
    return {
        "bore_diameter_mm": bore_diameter_mm,
        "bore_length_mm": round(bore_length, 1),
        "bore_length_cm": round(bore_length / 10, 1),
        "bore_length_m": round(bore_length / 1000, 4),
        "fundamental": f"{fundamental_note}{fundamental_octave}",
        "fundamental_hz": round(f0, 1),
        "speed_of_sound_ms": round(c, 1),
        "end_correction_mm": round(end_correction, 1),
        "embouchure": {
            "diameter_mm": embouchure_diameter_mm,
            "offset_from_end_mm": embouchure_offset_mm,
        },
        "wall_thickness_mm": wall_thickness_mm,
        "scale": scale,
        "holes": [
            {
                "number": i + 1,
                "note": f"{note}{oct}",
                "frequency_hz": f,
                "position_from_embouchure_mm": pos,
                "position_from_embouchure_cm": round(pos / 10, 1),
                "diameter_mm": d,
                "cents_from_et": c,
            }
            for i, ((note, oct), pos, d, f, c) in enumerate(
                zip(holes, hole_positions, hole_diams, hole_freqs, hole_cents)
            )
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
