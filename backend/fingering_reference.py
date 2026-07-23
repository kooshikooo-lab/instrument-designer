"""Complete fingering reference for bass clarinet / clarinet family."""
import sys
sys.path.insert(0, 'backend')
from tmm_acoustics import SPEED_OF_SOUND

# Bass clarinet parameters
BORE_RADIUS = 12.5  # mm
BORE_LENGTH = 1211.3  # mm (written D2 fundamental)
REGISTER_HOLE_POS = 80.0  # mm from reed
REGISTER_HOLE_DIA = 2.5  # mm
REGISTER_HOLE_LEN = 3.0  # mm

# Written pitch fundamentals (transposed: bass clarinet sounds major 9th below written)
# Written D2 = 73.416 Hz (sounds C1 = 32.7 Hz)
written_pitches = {
    "D2":  73.416, "D#2": 77.782, "E2":  82.407, "F2":  87.307,
    "F#2": 92.499, "G2":  97.999, "G#2": 103.826, "A2":  110.000,
    "A#2": 116.541, "B2":  123.471, "C3":  130.813, "C#3": 138.591,
    "D3":  146.832, "D#3": 155.563, "E3":  164.814, "F3":  174.614,
    "F#3": 184.997, "G3":  195.998, "G#3": 207.652, "A3":  220.000,
    "A#3": 233.082, "B3":  246.942, "C4":  261.626, "C#4": 277.183,
    "D4":  293.665, "D#4": 311.127, "E4":  329.628, "F4":  349.228,
    "F#4": 369.994, "G4":  391.995, "G#4": 415.305, "A4":  440.000,
    "A#4": 466.164, "B4":  493.883, "C5":  523.251, "C#5": 554.365,
    "D5":  587.330, "D#5": 622.254, "E5":  659.255, "F5":  698.456,
    "F#5": 739.989, "G5":  783.991, "G#5": 830.609, "A5":  880.000,
}

# Standard 12-tonehole fingering chart (written pitch)
# H1 = top (closest to reed), H12 = bottom (closest to bell)
# R = register hole (closed for chalumeau, open for clarion)
# Format: {note: [H1..H12, R]} where 1=open, 0=closed

FINGERING_CHART_CHALUMEAU = {
    # Chalumeau register (written D2 - B4)
    # Low C extension requires H12 (low C key)
    "D2":  [0,0,0,0,0,0,0,0,0,0,0,0, 0],
    "D#2": [0,0,0,0,0,0,1,0,1,0,0,0, 0],  # cross: H7+H9
    "E2":  [0,0,0,0,0,0,1,0,0,0,0,0, 0],
    "F2":  [0,0,0,0,0,1,1,0,0,0,0,0, 0],
    "F#2": [0,0,0,0,1,0,1,1,0,0,0,0, 0],  # cross: H5+H7+H8
    "G2":  [0,0,0,0,1,1,1,0,0,0,0,0, 0],
    "G#2": [0,0,0,1,0,1,1,1,0,0,0,0, 0],  # cross: H4+H6+H7+H8
    "A2":  [0,0,0,1,1,1,1,0,0,0,0,0, 0],
    "A#2": [0,0,1,0,1,1,1,1,0,0,0,0, 0],  # cross: H3+H5+H6+H7+H8
    "B2":  [0,0,1,1,1,1,1,0,0,0,0,0, 0],
    "C3":  [0,1,0,1,1,1,1,1,0,0,1,0, 0],  # H2+H4-H8+H11
    "C#3": [1,0,1,1,1,1,1,0,1,0,0,1, 0],  # H1+H3-H7+H9+H12
    "D3":  [1,1,1,1,1,1,1,0,0,0,0,0, 0],
    "D#3": [1,1,1,1,1,1,1,1,0,0,0,0, 0],
    "E3":  [1,1,1,1,1,1,1,1,1,0,0,0, 0],
    "F3":  [1,1,1,1,1,1,1,1,1,1,0,0, 0],
    "F#3": [1,1,1,1,1,1,1,1,1,1,1,0, 0],
    "G3":  [1,1,1,1,1,1,1,1,1,1,1,1, 0],
    # Notes above G3 use register key + modified chalumeau fingerings
}

FINGERING_CHART_CLARION = {
    # Clarion register (register hole OPEN, written B4+)
    # Written B4 (sounds A3) = 1st clarion note
    "B4":  [0,0,1,1,1,1,1,0,0,0,0,0, 1],  # B2 fingering + register
    "C5":  [0,1,0,1,1,1,1,1,0,0,1,0, 1],  # C3 + register
    "C#5": [1,0,1,1,1,1,1,0,1,0,0,1, 1],  # C#3 + register
    "D5":  [1,1,1,1,1,1,1,0,0,0,0,0, 1],  # D3 + register
    "D#5": [1,1,1,1,1,1,1,1,0,0,0,0, 1],
    "E5":  [1,1,1,1,1,1,1,1,1,0,0,0, 1],
    "F5":  [1,1,1,1,1,1,1,1,1,1,0,0, 1],
    "F#5": [1,1,1,1,1,1,1,1,1,1,1,0, 1],
    "G5":  [1,1,1,1,1,1,1,1,1,1,1,1, 1],
    # Altissimo: many alternate fingerings exist
}

# Hole positions from working 7-hole optimization (sequential, reed→bell)
# These are the PRIMARY hole positions (H1-H7)
BASE_HOLE_POSITIONS = [176, 293, 338, 445, 532, 610, 636]  # mm from reed

# Additional holes for chromatic cross-fingerings (H8-H12)
# H8, H9 = corrective chromatic holes (between H5-H7)
# H10 = additional corrective
# H11 = vent for C3
# H12 = low C extension (near bell)
EXTENDED_HOLE_POSITIONS = BASE_HOLE_POSITIONS + [700, 760, 820, 880, 940]

# Graduated hole diameters (top→bottom): typical professional clarinet
# Top holes smaller for tuning stability, bottom holes larger for venting
GRADUATED_DIAMETERS = [10.5, 11.0, 11.5, 12.0, 13.0, 14.0, 15.0, 15.5, 16.0, 16.5, 17.0, 18.0]
HOLE_LENGTHS = [5.0] * 12  # chimney height in mm

# Convert fingering chart to string format for optimizer
def chart_to_strings(chart_dict):
    """Convert binary chart to ['open'/'closed'] format."""
    result = []
    for note in sorted(chart_dict.keys(), key=lambda n: written_pitches.get(n, 0)):
        row = ["open" if x else "closed" for x in chart_dict[note]]
        result.append(row)
    return result

CHALUMEAU_CHART_STR = chart_to_strings(FINGERING_CHART_CHALUMEAU)
CLARION_CHART_STR = chart_to_strings(FINGERING_CHART_CLARION)

if __name__ == "__main__":
    print("=" * 80)
    print("BASS CLARINET FINGERING REFERENCE")
    print("=" * 80)
    print(f"Bore: {BORE_LENGTH:.1f}mm × {BORE_RADIUS:.1f}mm radius")
    print(f"Register hole: {REGISTER_HOLE_POS:.1f}mm, {REGISTER_HOLE_DIA:.1f}mm dia, {REGISTER_HOLE_LEN:.1f}mm len")
    print(f"Written range: D2 (73.4Hz) to G5 (784Hz) + altissimo")
    print(f"Sounding range: C1 (32.7Hz) to F4 (349Hz) + altissimo")
    print()
    
    print("CHALUMEAU REGISTER (register hole CLOSED):")
    print("-" * 80)
    for note, freq in written_pitches.items():
        if note in FINGERING_CHART_CHALUMEAU:
            row = FINGERING_CHART_CHALUMEAU[note]
            holes_str = "".join("O" if x else "X" for x in row[:12])
            reg = "O" if row[12] else "X"
            print(f"  {note:>4} ({freq:>7.2f} Hz):  {holes_str}  R={reg}")
    
    print()
    print("CLARION REGISTER (register hole OPEN):")
    print("-" * 80)
    for note, freq in written_pitches.items():
        if note in FINGERING_CHART_CLARION:
            row = FINGERING_CHART_CLARION[note]
            holes_str = "".join("O" if x else "X" for x in row[:12])
            reg = "O" if row[12] else "X"
            print(f"  {note:>4} ({freq:>7.2f} Hz):  {holes_str}  R={reg}")
    
    print()
    print("HOLE POSITIONS (mm from reed):")
    print("-" * 80)
    for i, pos in enumerate(EXTENDED_HOLE_POSITIONS):
        d = GRADUATED_DIAMETERS[i] if i < len(GRADUATED_DIAMETERS) else 11.0
        print(f"  H{i+1:2d}: {pos:>4.0f}mm  dia={d:.1f}mm")
    
    print()
    print("REGISTER HOLE: R @ 80mm (2.5mm dia, 3mm len) - CLOSED for chalumeau")