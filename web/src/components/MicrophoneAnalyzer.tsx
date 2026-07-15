import { useCallback, useEffect, useRef, useState } from "react";
import { useMicrophone } from "../hooks/useMicrophone";
import { detectPitch, freqToNote } from "../utils/pitch";
import type { PitchResult } from "../utils/pitch";
import SpectrumPlot from "./SpectrumPlot";

interface MicrophoneAnalyzerProps {
  onPitch?: (pitch: PitchResult | null) => void;
}

export default function MicrophoneAnalyzer({ onPitch }: MicrophoneAnalyzerProps) {
  const { state, start, stop, getAnalyser, getAudioContext } = useMicrophone();
  const [pitch, setPitch] = useState<PitchResult | null>(null);
  const [peakFreq, setPeakFreq] = useState<number | null>(null);
  const rafRef = useRef<number>(0);

  const analyze = useCallback(() => {
    const analyser = getAnalyser();
    const audioCtx = getAudioContext();
    if (!analyser || !audioCtx) return;

    const p = detectPitch(analyser, audioCtx.sampleRate);
    setPitch(p);
    onPitch?.(p);

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Float32Array(bufferLength);
    analyser.getFloatFrequencyData(dataArray);

    const binWidth = audioCtx.sampleRate / analyser.fftSize;
    let maxVal = -Infinity;
    let maxIdx = 0;
    for (let i = 2; i < bufferLength; i++) {
      if (dataArray[i] > maxVal) {
        maxVal = dataArray[i];
        maxIdx = i;
      }
    }
    setPeakFreq(maxIdx * binWidth);

    rafRef.current = requestAnimationFrame(analyze);
  }, [getAnalyser, getAudioContext, onPitch]);

  useEffect(() => {
    if (state.active) {
      rafRef.current = requestAnimationFrame(analyze);
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [state.active, analyze]);

  const handleToggle = () => {
    if (state.active) {
      stop();
      setPitch(null);
      setPeakFreq(null);
      onPitch?.(null);
    } else {
      start();
    }
  };

  const peakNote = peakFreq ? freqToNote(peakFreq) : null;

  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden">
      <div className="p-3 border-b border-neutral-800 flex items-center justify-between">
        <span className="text-sm font-medium text-neutral-300">Microphone Analysis</span>
        <button
          onClick={handleToggle}
          className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-colors ${
            state.active
              ? "bg-red-600 hover:bg-red-700 text-white"
              : "bg-neutral-700 hover:bg-neutral-600 text-neutral-200"
          }`}
        >
          {state.active ? "Stop" : "Start Mic"}
        </button>
      </div>

      {state.error && (
        <div className="px-3 py-2 bg-red-900/20 border-b border-red-900/30">
          <p className="text-xs text-red-400">{state.error}</p>
        </div>
      )}

      <SpectrumPlot
        getAnalyser={getAnalyser}
        getAudioContext={getAudioContext}
        active={state.active}
      />

      {state.active && (
        <div className="p-3 grid grid-cols-2 gap-3 text-xs">
          <div className="bg-neutral-800 rounded-lg p-2">
            <div className="text-neutral-500 mb-1">Detected Pitch</div>
            <div className="text-lg font-mono text-cyan-400">
              {pitch ? `${pitch.note}${pitch.octave}` : "---"}
            </div>
            <div className="text-neutral-400 font-mono">
              {pitch ? `${pitch.frequency.toFixed(1)} Hz` : "--- Hz"}
            </div>
          </div>
          <div className="bg-neutral-800 rounded-lg p-2">
            <div className="text-neutral-500 mb-1">Deviation</div>
            <div className={`text-lg font-mono ${
              pitch ? (Math.abs(pitch.cents) < 10 ? "text-green-400" : Math.abs(pitch.cents) < 30 ? "text-yellow-400" : "text-red-400") : "text-neutral-500"
            }`}>
              {pitch ? `${pitch.cents > 0 ? "+" : ""}${pitch.cents} ct` : "--- ct"}
            </div>
            <div className="text-neutral-400 font-mono">
              {peakFreq ? `Peak: ${peakFreq.toFixed(0)} Hz` : "Peak: --- Hz"}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
