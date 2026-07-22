import { useState, useRef, useCallback, useEffect } from "react";

interface Props {
  className?: string;
}

/**
 * Real-time frequency spectrum analyzer using Web Audio API
 * Shows live microphone input or audio playback spectrum
 */
export default function SpectrumAnalyzer({ className = "" }: Props) {
  const [isActive, setIsActive] = useState(false);
  const [peaks, setPeaks] = useState<{ freq: number; amp: number }[]>([]);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const animFrameRef = useRef<number>(0);
  const streamRef = useRef<MediaStream | null>(null);

  const draw = useCallback(() => {
    if (!canvasRef.current || !analyserRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const analyser = analyserRef.current;
    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);
    analyser.getByteFrequencyData(dataArray);

    const width = canvas.width;
    const height = canvas.height;

    ctx.fillStyle = "rgba(17, 17, 17, 0.9)";
    ctx.fillRect(0, 0, width, height);

    const barWidth = width / bufferLength * 2.5;
    let x = 0;
    const newPeaks: { freq: number; amp: number }[] = [];

    for (let i = 0; i < bufferLength; i++) {
      const barHeight = (dataArray[i] / 255) * height;

      // Gradient color based on frequency
      const hue = (i / bufferLength) * 280;
      const saturation = 70;
      const lightness = 45 + (dataArray[i] / 255) * 20;

      ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness}%)`;
      ctx.fillRect(x, height - barHeight, barWidth - 1, barHeight);

      // Top cap
      ctx.fillStyle = `hsl(${hue}, ${saturation}%, ${lightness + 15}%)`;
      ctx.fillRect(x, height - barHeight - 3, barWidth - 1, 2);

      // Track peaks
      if (dataArray[i] > 180) {
        const freq = (i * (audioCtxRef.current?.sampleRate || 44100)) / bufferLength / 2;
        newPeaks.push({ freq: Math.round(freq), amp: dataArray[i] / 255 });
      }

      x += barWidth;
    }

    // Draw frequency labels
    ctx.fillStyle = "#666";
    ctx.font = "10px monospace";
    const freqs = [100, 500, 1000, 2000, 5000, 10000];
    freqs.forEach(f => {
      const bin = (f * 2 * bufferLength) / (audioCtxRef.current?.sampleRate || 44100);
      const xPos = (bin / bufferLength) * width;
      if (xPos < width) {
        ctx.fillText(`${f >= 1000 ? `${f / 1000}k` : f}`, xPos, height - 5);
      }
    });

    setPeaks(newPeaks.slice(0, 5));
    animFrameRef.current = requestAnimationFrame(draw);
  }, []);

  const startAnalysis = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;

      const ctx = new AudioContext();
      audioCtxRef.current = ctx;

      const source = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 2048;
      analyser.smoothingTimeConstant = 0.8;
      source.connect(analyser);
      analyserRef.current = analyser;

      setIsActive(true);
      animFrameRef.current = requestAnimationFrame(draw);
    } catch (e) {
      console.error("Microphone access denied:", e);
    }
  }, [draw]);

  const stopAnalysis = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close();
    }
    cancelAnimationFrame(animFrameRef.current);
    setIsActive(false);
    setPeaks([]);
  }, []);

  useEffect(() => {
    return () => {
      stopAnalysis();
    };
  }, [stopAnalysis]);

  return (
    <div className={`bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden ${className}`}>
      <div className="flex items-center justify-between px-4 py-2.5 border-b border-neutral-800">
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${isActive ? "bg-green-500 animate-pulse" : "bg-neutral-600"}`} />
          <span className="text-xs font-medium text-neutral-400">Spectrum Analyzer</span>
        </div>
        <button
          onClick={isActive ? stopAnalysis : startAnalysis}
          className={`px-3 py-1 rounded text-xs font-medium transition-colors ${
            isActive
              ? "bg-red-600/20 text-red-400 hover:bg-red-600/30"
              : "bg-brand-600/20 text-brand-400 hover:bg-brand-600/30"
          }`}
        >
          {isActive ? "Stop" : "Start"}
        </button>
      </div>

      <canvas
        ref={canvasRef}
        width={512}
        height={128}
        className="w-full"
        style={{ imageRendering: "pixelated" }}
      />

      {peaks.length > 0 && (
        <div className="px-4 py-2 border-t border-neutral-800">
          <div className="flex flex-wrap gap-1.5">
            {peaks.map((p, i) => (
              <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-amber-500/10 text-amber-400 font-mono">
                {p.freq}Hz ({(p.amp * 100).toFixed(0)}%)
              </span>
            ))}
          </div>
        </div>
      )}

      {!isActive && (
        <div className="px-4 py-6 text-center">
          <div className="text-xs text-neutral-500">
            Click "Start" to analyze audio from your microphone
          </div>
          <div className="text-[10px] text-neutral-600 mt-1">
            Useful for tuning and frequency analysis
          </div>
        </div>
      )}
    </div>
  );
}
