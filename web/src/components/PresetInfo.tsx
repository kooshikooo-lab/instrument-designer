import { IMPEDANCE_DATA } from "../data/impedance-data";
import { DEMAKEIN_PRESETS } from "../data/instruments";

interface PresetInfoProps {
  preset: string;
}

const INSTRUMENT_SPECS: Record<string, Record<string, string>> = {
  recorder: {
    Type: "Fipple flute (duct flute)",
    Key: "C (soprano)",
    Range: "C5 - D7",
    Material: "PLA / PETG / Resin",
    Wall: "2.0 mm",
    Holes: "8 (thumb + 7 finger)",
    Source: "Laminar jet (flue)",
  },
  folk_whistle: {
    Type: "Fipple flute (tin whistle style)",
    Key: "D",
    Range: "D5 - E7",
    Material: "PLA / PETG",
    Wall: "1.5 mm",
    Holes: "6 finger holes",
    Source: "Laminar jet (flue)",
  },
  flute: {
    Type: "Transverse flute",
    Key: "C",
    Range: "C4 - C7",
    Material: "PLA / PETG",
    Wall: "2.0 mm",
    Holes: "6 tone holes",
    Source: "Edge tone (embouchure)",
  },
  reedpipe: {
    Type: "Single reed pipe",
    Key: "G",
    Range: "G3 - G5",
    Material: "PLA / Wood",
    Wall: "2.5 mm",
    Holes: "4 finger holes",
    Source: "Single reed (cane/synthetic)",
  },
  shawm: {
    Type: "Double reed (shawm/dulcit)",
    Key: "C",
    Range: "C4 - C6",
    Material: "PLA / Resin",
    Wall: "2.0 mm",
    Holes: "6 finger holes + thumb",
    Source: "Double reed (cane)",
  },
  didgeridoo: {
    Type: "Drone pipe",
    Key: "D",
    Range: "D2 - D3 (drone)",
    Material: "PLA / Wood",
    Wall: "4.0 mm",
    Holes: "None (open tube)",
    Source: "Lip buzz (brass-like)",
  },
};

export default function PresetInfo({ preset }: PresetInfoProps) {
  const specs = INSTRUMENT_SPECS[preset];
  const presetName = DEMAKEIN_PRESETS[preset] || preset;
  const impedanceData = IMPEDANCE_DATA[preset];

  if (!specs) return null;

  const fundamentalFreq = impedanceData?.frequencies[0] ?? 0;
  const peakFreqs: number[] = [];
  if (impedanceData) {
    const { frequencies, impedanceMagnitude } = impedanceData;
    for (let i = 2; i < impedanceMagnitude.length - 2; i++) {
      if (
        impedanceMagnitude[i] > impedanceMagnitude[i - 1] &&
        impedanceMagnitude[i] > impedanceMagnitude[i + 1] &&
        impedanceMagnitude[i] > impedanceMagnitude[i - 2] &&
        impedanceMagnitude[i] > impedanceMagnitude[i + 2]
      ) {
        peakFreqs.push(frequencies[i]);
      }
    }
  }

  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-4 space-y-3">
      <div className="flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-amber-500" />
        <h3 className="text-sm font-medium text-neutral-200">{presetName}</h3>
      </div>

      <div className="grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
        {Object.entries(specs).map(([key, value]) => (
          <div key={key} className="contents">
            <span className="text-neutral-500">{key}</span>
            <span className="text-neutral-300 font-mono">{value}</span>
          </div>
        ))}
      </div>

      {peakFreqs.length > 0 && (
        <div className="border-t border-neutral-800 pt-2">
          <div className="text-[10px] text-neutral-500 mb-1">
            Predicted Resonances ({peakFreqs.length} peaks)
          </div>
          <div className="flex flex-wrap gap-1">
            {peakFreqs.slice(0, 12).map((f, i) => {
              const NOTE = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
              const semitones = 12 * Math.log2(f / 440);
              const noteNum = Math.round(semitones) + 69;
              const name = NOTE[((noteNum % 12) + 12) % 12];
              const oct = Math.floor(noteNum / 12) - 1;
              return (
                <span
                  key={i}
                  className="px-1.5 py-0.5 bg-neutral-800 rounded text-[10px] font-mono text-amber-400"
                >
                  {name}{oct} {f.toFixed(0)}
                </span>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
