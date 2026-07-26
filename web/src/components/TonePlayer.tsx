import { useCallback, useRef, useState } from "react";

const NOTE_FREQ: Record<string, number> = {
  C2: 65.41, D2: 73.42, E2: 82.41, F2: 87.31, G2: 98.0, A2: 110.0, B2: 123.47,
  C3: 130.81, D3: 146.83, E3: 164.81, F3: 174.61, G3: 196.0, A3: 220.0, B3: 246.94,
  C4: 261.63, "C#4": 277.18, D4: 293.66, "D#4": 311.13, E4: 329.63, F4: 349.23,
  "F#4": 369.99, G4: 392.0, "G#4": 415.30, A4: 440.0, "A#4": 466.16, B4: 493.88,
  C5: 523.25, "C#5": 554.37, D5: 587.33, "D#5": 622.25, E5: 659.25, F5: 698.46,
  "F#5": 740.0, G5: 783.99, "G#5": 830.61, A5: 880.0, "A#5": 932.33, B5: 987.77,
  C6: 1046.5, "C#6": 1108.7, D6: 1174.66, "D#6": 1244.51, E6: 1318.51, F6: 1396.91,
  "F#6": 1479.98, G6: 1567.98, A6: 1760.0, Bb3: 233.08, Bb4: 466.16, Bb5: 932.33,
  Eb4: 311.13, Eb5: 622.25, Ab4: 415.30, Db4: 277.18,
};

const RANGE_MAP: Record<string, string[]> = {
  "C4-C6": ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6"],
  "C5-C7": ["C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6", "D6", "E6", "F6", "G6", "A6"],
  "D5-D7": ["D5", "E5", "F5", "G5", "A5", "B5", "C6", "D6", "E6", "F6", "G6"],
  "D4-D6": ["D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5"],
  "F4-G6": ["F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6", "D6", "E6", "F6", "G6"],
  "F3-G5": ["F3", "G3", "A3", "B3", "C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5"],
  "D2-D3": ["D2", "E2", "F2", "G2", "A2", "B2", "C3", "D3"],
  "G4-G5": ["G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5"],
  "G4-G6": ["G4", "A4", "B4", "C5", "D5", "E5", "F5", "G5", "A5", "B5", "C6", "D6", "E6", "F6", "G6"],
  "C4-G4": ["C4", "D4", "E4", "F4", "G4"],
  "Bb3-Bb5": ["Bb3", "C4", "D4", "Eb4", "F4", "G4", "A4", "Bb4", "C5", "D5", "Eb5", "F5", "G5", "A5", "Bb5"],
  "Eb4-Eb5": ["Eb4", "F4", "G4", "Ab4", "Bb4", "C5", "D5", "Eb5"],
  "Bb1-Bb2": ["Bb1"],
  "Any pitch": ["C4", "D4", "E4", "F4", "G4"],
};

interface TonePlayerProps {
  range: string;
  instrumentName: string;
  frequencies?: number[];
}

export default function TonePlayer({ range, instrumentName, frequencies }: TonePlayerProps) {
  const ctxRef = useRef<AudioContext | null>(null);
  const clearRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [playing, setPlaying] = useState<string | null>(null);

  const getCtx = useCallback(() => {
    if (!ctxRef.current) ctxRef.current = new AudioContext();
    return ctxRef.current;
  }, []);

  const notes = frequencies && frequencies.length > 0
    ? frequencies.map(f => {
        const closest = Object.entries(NOTE_FREQ).reduce((best, [name, freq]) =>
          Math.abs(freq - f) < Math.abs(best[1] - f) ? [name, freq] : best,
          ["C4", 261.63]);
        return closest[0];
      })
    : RANGE_MAP[range] || ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"];

  const playNote = useCallback(
    (note: string) => {
      const freq = NOTE_FREQ[note];
      if (!freq) return;
      const ctx = getCtx();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      const filter = ctx.createBiquadFilter();

      osc.type = "sine";
      osc.frequency.value = freq;

      filter.type = "lowpass";
      filter.frequency.value = freq * 4;
      filter.Q.value = 1;

      gain.gain.setValueAtTime(0, ctx.currentTime);
      gain.gain.linearRampToValueAtTime(0.3, ctx.currentTime + 0.05);
      gain.gain.exponentialRampToValueAtTime(0.001, ctx.currentTime + 0.8);

      osc.connect(filter);
      filter.connect(gain);
      gain.connect(ctx.destination);

      osc.start(ctx.currentTime);
      osc.stop(ctx.currentTime + 0.8);

      if (clearRef.current) clearTimeout(clearRef.current);
      setPlaying(note);
      clearRef.current = setTimeout(() => setPlaying(null), 300);
    },
    [getCtx]
  );

  const playScale = useCallback(() => {
    notes.forEach((note, i) => {
      setTimeout(() => playNote(note), i * 350);
    });
  }, [notes, playNote]);

  return (
    <div className="bg-neutral-800 rounded-xl p-4 border border-neutral-700 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-sm font-semibold text-brand-400">Tone Preview</h3>
          <p className="text-xs text-neutral-500 mt-0.5">{instrumentName}</p>
        </div>
        <button
          onClick={playScale}
          className="px-3 py-1.5 bg-brand-600 hover:bg-brand-500 text-xs text-white rounded-lg transition-colors font-medium"
        >
          Play Scale
        </button>
      </div>
      <div className="flex flex-wrap gap-1">
        {notes.map((note) => (
          <button
            key={note}
            onClick={() => playNote(note)}
            className={`px-2 py-1.5 rounded text-xs font-mono transition-all ${
              playing === note
                ? "bg-brand-500 text-white scale-110 shadow-lg shadow-brand-500/30"
                : "bg-neutral-700 text-neutral-300 hover:bg-neutral-600 hover:text-white"
            }`}
          >
            {note}
          </button>
        ))}
      </div>
    </div>
  );
}
