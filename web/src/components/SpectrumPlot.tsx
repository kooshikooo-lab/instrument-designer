import { useEffect, useRef, useCallback } from "react";

interface SpectrumPlotProps {
  getAnalyser: () => AnalyserNode | null;
  getAudioContext: () => AudioContext | null;
  active: boolean;
}

export default function SpectrumPlot({ getAnalyser, getAudioContext, active }: SpectrumPlotProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef<number>(0);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const analyser = getAnalyser();
    const audioCtx = getAudioContext();
    if (!canvas || !analyser || !audioCtx) return;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const pad = { top: 25, right: 15, bottom: 35, left: 50 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    const bufferLength = analyser.frequencyBinCount;
    const dataArray = new Float32Array(bufferLength);
    analyser.getFloatFrequencyData(dataArray);

    const sampleRate = audioCtx.sampleRate;
    const binWidth = sampleRate / analyser.fftSize;

    const fMin = 80;
    const fMax = Math.min(3000, sampleRate / 2);

    let minDb = -90;
    let maxDb = -10;
    for (let i = 1; i < bufferLength; i++) {
      const f = i * binWidth;
      if (f >= fMin && f <= fMax && dataArray[i] > -90) {
        if (dataArray[i] > maxDb) maxDb = dataArray[i];
        if (dataArray[i] < minDb) minDb = dataArray[i];
      }
    }
    maxDb = Math.ceil(maxDb / 10) * 10 + 10;
    minDb = Math.floor(minDb / 10) * 10 - 10;

    ctx.clearRect(0, 0, W, H);
    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, W, H);

    ctx.strokeStyle = "#262626";
    ctx.lineWidth = 1;
    for (let i = 0; i <= 5; i++) {
      const y = pad.top + (plotH * i) / 5;
      ctx.beginPath();
      ctx.moveTo(pad.left, y);
      ctx.lineTo(W - pad.right, y);
      ctx.stroke();
    }

    ctx.fillStyle = "#737373";
    ctx.font = "9px monospace";
    ctx.textAlign = "right";
    for (let i = 0; i <= 5; i++) {
      const val = maxDb - ((maxDb - minDb) * i) / 5;
      const y = pad.top + (plotH * i) / 5;
      ctx.fillText(`${val.toFixed(0)}`, pad.left - 5, y + 3);
    }

    ctx.textAlign = "center";
    ctx.fillStyle = "#737373";
    const logPoints = [100, 200, 500, 1000, 2000];
    for (const f of logPoints) {
      if (f >= fMin && f <= fMax) {
        const x = pad.left + ((Math.log10(f) - Math.log10(fMin)) / (Math.log10(fMax) - Math.log10(fMin))) * plotW;
        ctx.fillText(f >= 1000 ? `${f / 1000}k` : `${f}`, x, H - pad.bottom + 15);
      }
    }

    ctx.fillStyle = "#a3a3a3";
    ctx.font = "10px system-ui";
    ctx.fillText("Live Microphone Spectrum", W / 2, 14);

    ctx.fillStyle = "#525252";
    ctx.font = "9px system-ui";
    ctx.fillText("Frequency (Hz)", W / 2, H - 3);

    ctx.save();
    ctx.translate(10, H / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("dBFS", 0, 0);
    ctx.restore();

    ctx.beginPath();
    ctx.strokeStyle = "#22d3ee";
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";

    let started = false;
    for (let i = 1; i < bufferLength; i++) {
      const f = i * binWidth;
      if (f < fMin || f > fMax) continue;

      const x = pad.left + ((Math.log10(f) - Math.log10(fMin)) / (Math.log10(fMax) - Math.log10(fMin))) * plotW;
      const clamped = Math.max(minDb, Math.min(maxDb, dataArray[i]));
      const y = pad.top + plotH - ((clamped - minDb) / (maxDb - minDb)) * plotH;

      if (!started) {
        ctx.moveTo(x, y);
        started = true;
      } else {
        ctx.lineTo(x, y);
      }
    }
    ctx.stroke();

    const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
    gradient.addColorStop(0, "rgba(34,211,238,0.12)");
    gradient.addColorStop(1, "rgba(34,211,238,0)");
    ctx.lineTo(pad.left + plotW, pad.top + plotH);
    ctx.lineTo(pad.left, pad.top + plotH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();

    rafRef.current = requestAnimationFrame(draw);
  }, [getAnalyser, getAudioContext]);

  useEffect(() => {
    if (active) {
      rafRef.current = requestAnimationFrame(draw);
    }
    return () => cancelAnimationFrame(rafRef.current);
  }, [active, draw]);

  if (!active) {
    return (
      <div className="bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden p-8 text-center">
        <p className="text-sm text-neutral-500">Enable microphone to view live spectrum</p>
      </div>
    );
  }

  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden">
      <canvas
        ref={canvasRef}
        width={600}
        height={250}
        className="w-full h-auto"
      />
    </div>
  );
}
