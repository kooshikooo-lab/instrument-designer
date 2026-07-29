"""Match optimization config names to cadquery_export library entries."""
import sys
sys.path.insert(0, '.')
from backend.cadquery_export import INSTRUMENTS

library_names = set(INSTRUMENTS.keys())

# My optimization config names from optimize_all.py
my_configs = [
    "tenor_trombone_Bb", "f_horn_F", "trumpet_Bb", "alto_trombone_Eb", "flugelhorn_Bb",
    "soprano_sax_Bb", "alto_sax_Eb", "baritone_sax_Bb", "tenor_sax_Bb", "sopranino_sax_Eb", "bass_sax_Bb",
    "concert_flute_C", "alto_flute_G", "flute_F", "bass_flute_C", "diatonic_whistle_D",
    "clarinet_Bb", "clarinet_D", "clarinet_A", "clarinet_Eb_soprano",
    "recorder_F", "recorder_C", "recorder_F_alto",
]

print("Matching config names to library entries:")
for cfg_name in my_configs:
    # Find matching library entries
    matches = []
    for lib_name in library_names:
        # Check if config name is in library name or vice versa
        cfg_parts = cfg_name.lower().replace('_', ' ')
        lib_parts = lib_name.lower().replace('_', ' ')
        if any(p in lib_parts for p in cfg_parts.split()) or any(p in cfg_parts for p in lib_parts.split()):
            v = INSTRUMENTS[lib_name]
            bl = v.get('bore_length', '?')
            bd = v.get('bore_diameter', '?')
            wall = v.get('wall_thickness', '?')
            ct = v.get('closed_top', '?')
            n_holes = len(v.get('holes', []))
            matches.append((lib_name, bl, bd, wall, ct, n_holes))

    if matches:
        print(f"\n{cfg_name}:")
        for m in matches:
            print(f"  -> {m[0]}: bore={m[1]}mm, diam={m[2]}mm, wall={m[3]}mm, closed={m[4]}, holes={m[5]}")
    else:
        print(f"\n{cfg_name}: (no library match)")
