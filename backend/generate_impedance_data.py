import os
import json
import sys
import numpy as np
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

try:
    import openwind
except ImportError:
    print("ERROR: openwind not installed. Run: pip install openwind")
    sys.exit(1)

BORE_DIR = Path(__file__).parent / "bore_profiles"
OUT_DIR = Path(__file__).parent / "impedance_data"
OUT_DIR.mkdir(exist_ok=True)

BORE_FILES = {
    "recorder": "recorder.csv",
    "folk_whistle": "folk_whistle.csv",
    "flute": "flute.csv",
    "reedpipe": "reedpipe.csv",
    "shawm": "shawm.csv",
    "didgeridoo": "didgeridoo.csv",
}

FREQ_START = 50
FREQ_END = 3000
FREQ_STEP = 2
TEMPERATURE = 25.0


def compute_and_save(preset: str, bore_file: str):
    bore_path = str(BORE_DIR / bore_file)
    if not os.path.exists(bore_path):
        print(f"  SKIP: {bore_path} not found")
        return

    print(f"  Computing impedance for {preset}...")
    frequencies = np.arange(FREQ_START, FREQ_END, FREQ_STEP)

    try:
        result = openwind.ImpedanceComputation(frequencies, bore_path, temperature=TEMPERATURE)

        z = result.impedance
        z_real = np.real(z).tolist()
        z_imag = np.imag(z).tolist()
        z_mag = np.abs(z).tolist()

        data = {
            "preset": preset,
            "frequencies": frequencies.tolist(),
            "impedance_real": z_real,
            "impedance_imag": z_imag,
            "impedance_magnitude": z_mag,
            "temperature": TEMPERATURE,
            "freq_range": [FREQ_START, FREQ_END, FREQ_STEP],
        }

        out_file = OUT_DIR / f"{preset}.json"
        with open(out_file, "w") as f:
            json.dump(data, f)

        print(f"  Saved: {out_file} ({len(frequencies)} points)")

    except Exception as e:
        print(f"  ERROR computing {preset}: {e}")


if __name__ == "__main__":
    print("Pre-computing impedance data with OpenWInD...")
    print(f"Frequency range: {FREQ_START}-{FREQ_END} Hz, step {FREQ_STEP} Hz")
    print(f"Temperature: {TEMPERATURE}C")
    print()

    for preset, bore_file in BORE_FILES.items():
        compute_and_save(preset, bore_file)

    print()
    print("Done! Generated files:")
    for f in sorted(OUT_DIR.glob("*.json")):
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name} ({size_kb:.1f} KB)")
