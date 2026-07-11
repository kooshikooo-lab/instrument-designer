import json
import sys
from pathlib import Path

IMPEDANCE_DIR = Path(__file__).parent.parent / "backend" / "impedance_data"
OUT_FILE = Path(__file__).parent.parent / "web" / "src" / "data" / "impedance-data.ts"

files = sorted(IMPEDANCE_DIR.glob("*.json"))
data = {}

for f in files:
    preset = f.stem
    raw = json.loads(f.read_text())
    # Downsample to ~300 points for browser performance
    skip = max(1, len(raw["frequencies"]) // 300)
    data[preset] = {
        "preset": raw["preset"],
        "temperature": raw["temperature"],
        "frequencies": raw["frequencies"][::skip],
        "impedanceMagnitude": raw["impedance_magnitude"][::skip],
        "impedanceReal": raw["impedance_real"][::skip],
        "impedanceImag": raw["impedance_imag"][::skip],
    }

output = f"""// Auto-generated from OpenWInD pre-computed data
// Do not edit manually - run: python backend/generate_impedance_data.py

export interface ImpedanceData {{
  preset: string;
  temperature: number;
  frequencies: number[];
  impedanceMagnitude: number[];
  impedanceReal: number[];
  impedanceImag: number[];
}}

export const IMPEDANCE_DATA: Record<string, ImpedanceData> = {json.dumps(data, indent=2)};

export const AVAILABLE_IMPEDANCE_PRESETS = Object.keys(IMPEDANCE_DATA);
"""

OUT_FILE.write_text(output)
print(f"Generated {OUT_FILE} with {len(files)} presets")
