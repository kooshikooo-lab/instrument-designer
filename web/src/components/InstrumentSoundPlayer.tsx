import { useState, useRef, useCallback } from "react";

interface Sample {
  name: string;
  url: string;
  note?: string;
  duration?: string;
}

interface Props {
  instrumentName?: string;
  range?: string;
  samples?: Sample[];
}

export default function InstrumentSoundPlayer({ range }: Props) {
  const [playing, setPlaying] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current) {
      audioCtxRef.current = new AudioContext();
    }
    return audioCtxRef.current;
  }, []);

  const playTone = useCallback(async (frequency: number, duration: number = 2) => {
    try {
      const ctx = getAudioContext();
      const oscillator = ctx.createOscillator();
      const gainNode = ctx.createGain();

      oscillator.type = "sine";
      oscillator.frequency.setValueAtTime(frequency, ctx.currentTime);

      gainNode.gain.setValueAtTime(0.3, ctx.currentTime);
      gainNode.gain.exponentialRampToValueAtTime(0.01, ctx.currentTime + duration);

      oscillator.connect(gainNode);
      gainNode.connect(ctx.destination);

      oscillator.start();
      oscillator.stop(ctx.currentTime + duration);

      setPlaying(`${frequency}`);
      setTimeout(() => setPlaying(null), duration * 1000);
    } catch (e) {
      setError("Audio playback failed");
      setTimeout(() => setError(null), 2000);
    }
  }, [getAudioContext]);

  const noteToFreq = (note: string): number => {
    const notes: Record<string, number> = {
      C3: 130.81, D3: 146.83, E3: 164.81, F3: 174.61, G3: 196.00, A3: 220.00, B3: 246.94,
      C4: 261.63, D4: 293.66, E4: 329.63, F4: 349.23, G4: 392.00, A4: 440.00, B4: 493.88,
      C5: 523.25, D5: 587.33, E5: 659.25, F5: 698.46, G5: 783.99, A5: 880.00, B5: 987.77,
      Bb3: 233.08, Eb4: 311.13, Ab4: 415.30, Bb4: 466.16, Eb5: 622.25,
    };
    return notes[note] || 440;
  };

  const demoNotes = range === "Soprano"
    ? ["C5", "D5", "E5", "F5", "G5", "A5", "B5", "C5"]
    : range === "Alto"
    ? ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    : range === "Tenor"
    ? ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"]
    : range === "Bass"
    ? ["C3", "D3", "E3", "F3", "G3", "A3", "B3", "C4"]
    : ["C4", "D4", "E4", "F4", "G4", "A4", "B4", "C5"];

  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-4">
      <div className="flex items-center gap-2 mb-3">
        <div className="w-6 h-6 rounded bg-brand-500/20 flex items-center justify-center">
          <svg className="w-3.5 h-3.5 text-brand-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
          </svg>
        </div>
        <h4 className="text-xs font-medium text-neutral-300">Sound Preview</h4>
      </div>

      {error && (
        <div className="text-xs text-red-400 mb-2">{error}</div>
      )}

      <div className="flex flex-wrap gap-1.5">
        {demoNotes.map((note, i) => {
          const freq = noteToFreq(note);
          const isPlaying = playing === `${freq}`;
          return (
            <button
              key={`${note}-${i}`}
              onClick={() => playTone(freq, 1.5)}
              disabled={isPlaying}
              className={`px-3 py-2 rounded-lg text-xs font-mono transition-all ${
                isPlaying
                  ? "bg-brand-600 text-white scale-95"
                  : "bg-neutral-800 text-neutral-400 hover:bg-neutral-700 hover:text-neutral-200 border border-neutral-700"
              }`}
            >
              {note}
            </button>
          );
        })}
      </div>

      <p className="text-[10px] text-neutral-600 mt-3">
        Demo tones are synthesized sine waves. Click notes to hear pitch.
      </p>
    </div>
  );
}
