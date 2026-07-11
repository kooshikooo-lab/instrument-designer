import { useEffect, useRef } from "react";
import { IMPEDANCE_DATA } from "../data/impedance-data";

interface ImpedancePlotProps {
  preset?: string;
  frequencies?: number[];
  impedance?: number[];
  label?: string;
}

export default function ImpedancePlot({
  preset,
  frequencies: propFrequencies,
  impedance: propImpedance,
  label: propLabel,
}: ImpedancePlotProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const presetData = preset ? IMPEDANCE_DATA[preset] : null;

  const frequencies = propFrequencies ?? presetData?.frequencies ?? [];
  const impedance = propImpedance ?? presetData?.impedanceMagnitude ?? [];

  const label = propLabel ?? (presetData ? `Acoustic Impedance (${presetData.preset})` : "Acoustic Impedance");

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || frequencies.length === 0) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const W = canvas.width;
    const H = canvas.height;
    const pad = { top: 30, right: 20, bottom: 40, left: 60 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    const fMin = frequencies[0];
    const fMax = frequencies[frequencies.length - 1];
    const zMin = 0;
    const zMax = Math.max(...impedance) * 1.1;

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
    ctx.font = "10px monospace";
    ctx.textAlign = "right";
    for (let i = 0; i <= 5; i++) {
      const val = zMax - (zMax * i) / 5;
      const y = pad.top + (plotH * i) / 5;
      ctx.fillText(val.toFixed(0), pad.left - 8, y + 3);
    }

    ctx.textAlign = "center";
    const numLabels = 6;
    for (let i = 0; i <= numLabels; i++) {
      const f = fMin + ((fMax - fMin) * i) / numLabels;
      const x = pad.left + (plotW * i) / numLabels;
      ctx.fillText(`${(f / 1000).toFixed(1)}k`, x, H - pad.bottom + 20);
    }

    ctx.fillStyle = "#a3a3a3";
    ctx.font = "11px system-ui";
    ctx.textAlign = "center";
    ctx.fillText(label, W / 2, 18);

    ctx.fillStyle = "#525252";
    ctx.font = "10px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("Frequency (Hz)", W / 2, H - 4);

    ctx.save();
    ctx.translate(12, H / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillText("|Z| (Pa·s/m\u00B3)", 0, 0);
    ctx.restore();

    ctx.beginPath();
    ctx.strokeStyle = "#bc6915";
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";
    for (let i = 0; i < frequencies.length; i++) {
      const x = pad.left + ((frequencies[i] - fMin) / (fMax - fMin)) * plotW;
      const y = pad.top + plotH - ((impedance[i] - zMin) / (zMax - zMin)) * plotH;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();

    const gradient = ctx.createLinearGradient(0, pad.top, 0, pad.top + plotH);
    gradient.addColorStop(0, "rgba(188,105,21,0.15)");
    gradient.addColorStop(1, "rgba(188,105,21,0)");
    ctx.lineTo(pad.left + plotW, pad.top + plotH);
    ctx.lineTo(pad.left, pad.top + plotH);
    ctx.closePath();
    ctx.fillStyle = gradient;
    ctx.fill();
  }, [frequencies, impedance, label]);

  if (frequencies.length === 0) {
    return (
      <div className="bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden p-8 text-center">
        <p className="text-sm text-neutral-500">Select a preset to view acoustic impedance data</p>
      </div>
    );
  }

  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800 overflow-hidden">
      <canvas
        ref={canvasRef}
        width={600}
        height={300}
        className="w-full h-auto"
      />
    </div>
  );
}
