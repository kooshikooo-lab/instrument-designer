import fs from "fs";
import path from "path";

const IMPEDANCE_DIR = path.join(__dirname, "..", "backend", "impedance_data");
const OUT_FILE = path.join(__dirname, "..", "web", "src", "data", "impedance-data.ts");

const files = fs.readdirSync(IMPEDANCE_DIR).filter((f: string) => f.endsWith(".json"));

const data: Record<string, any> = {};
for (const file of files) {
  const preset = file.replace(".json", "");
  const raw = JSON.parse(fs.readFileSync(path.join(IMPEDANCE_DIR, file), "utf-8"));
  // Downsample to ~300 points for browser performance
  const skipFactor = Math.max(1, Math.floor(raw.frequencies.length / 300));
  data[preset] = {
    preset: raw.preset,
    temperature: raw.temperature,
    frequencies: raw.frequencies.filter((_: any, i: number) => i % skipFactor === 0),
    impedanceMagnitude: raw.impedance_magnitude.filter((_: any, i: number) => i % skipFactor === 0),
    impedanceReal: raw.impedance_real.filter((_: any, i: number) => i % skipFactor === 0),
    impedanceImag: raw.impedance_imag.filter((_: any, i: number) => i % skipFactor === 0),
  };
}

const output = `// Auto-generated from OpenWInD pre-computed data
// Do not edit manually - run: python backend/generate_impedance_data.py

export interface ImpedanceData {
  preset: string;
  temperature: number;
  frequencies: number[];
  impedanceMagnitude: number[];
  impedanceReal: number[];
  impedanceImag: number[];
}

export const IMPEDANCE_DATA: Record<string, ImpedanceData> = ${JSON.stringify(data, null, 2)};

export const AVAILABLE_IMPEDANCE_PRESETS = Object.keys(IMPEDANCE_DATA);
`;

fs.writeFileSync(OUT_FILE, output);
console.log(`Generated ${OUT_FILE} with ${files.length} presets`);
