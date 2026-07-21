import { useMemo } from "react";

interface BoreProfileViewProps {
  boreProfile: number[][];
  holePositions?: number[];
  holeDiameters?: number[];
}

export default function BoreProfileView({ boreProfile, holePositions = [], holeDiameters = [] }: BoreProfileViewProps) {
  const svg = useMemo(() => {
    if (boreProfile.length < 2) return null;

    const W = 560;
    const H = 180;
    const pad = { top: 20, right: 30, bottom: 30, left: 40 };
    const plotW = W - pad.left - pad.right;
    const plotH = H - pad.top - pad.bottom;

    const maxPos = Math.max(...boreProfile.map((p) => p[0]));
    const maxRad = Math.max(...boreProfile.map((p) => p[1])) * 1.3;

    const sx = (pos: number) => pad.left + (pos / maxPos) * plotW;
    const sy = (rad: number) => pad.top + plotH / 2 - (rad / maxRad) * (plotH / 2);

    const topPath = boreProfile.map((p, i) => `${i === 0 ? "M" : "L"}${sx(p[0])},${sy(p[1])}`).join(" ");

    const bottomPath = boreProfile.map((p, i) => {
      const y = pad.top + plotH - (sy(p[1]) - pad.top);
      return `${i === 0 ? "M" : "L"}${sx(p[0])},${y}`;
    }).join(" ");

    const centerLineY = pad.top + plotH / 2;

    const lastPt = boreProfile[boreProfile.length - 1];
    const firstPt = boreProfile[0];
    const fillTop = `${topPath} L${sx(lastPt[0])},${sy(lastPt[1])} L${sx(firstPt[0])},${sy(firstPt[1])} Z`;
    const fillBottom = `${bottomPath} L${sx(lastPt[0])},${pad.top + plotH - (sy(lastPt[1]) - pad.top)} L${sx(firstPt[0])},${pad.top + plotH - (sy(firstPt[1]) - pad.top)} Z`;

    return { W, H, pad, topPath, bottomPath, centerLineY, sx, sy, maxPos, maxRad, fillTop, fillBottom };
  }, [boreProfile]);

  if (!svg) return null;

  const { W, H, pad, topPath, bottomPath, centerLineY, sx, maxPos, maxRad, fillTop, fillBottom } = svg;

  return (
    <div className="bg-neutral-950 rounded-lg overflow-hidden">
      <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-auto">
        <rect x="0" y="0" width={W} height={H} fill="#0a0a0a" />

        <line x1={pad.left} y1={centerLineY} x2={W - pad.right} y2={centerLineY} stroke="#262626" strokeWidth="0.5" strokeDasharray="4,4" />

        <path d={fillTop} fill="rgba(188,105,21,0.08)" />
        <path d={fillBottom} fill="rgba(188,105,21,0.08)" />

        <path d={topPath} fill="none" stroke="#bc6915" strokeWidth="1.5" />
        <path d={bottomPath} fill="none" stroke="#bc6915" strokeWidth="1.5" />

        {holePositions.map((pos, i) => {
          if (pos > maxPos) return null;
          const x = sx(pos);
          const halfDia = ((holeDiameters[i] || 0.004) / 2 / maxRad) * (H - pad.top - pad.bottom) / 2;
          return (
            <g key={i}>
              <line x1={x} y1={centerLineY - halfDia} x2={x} y2={centerLineY + halfDia} stroke="#22d3ee" strokeWidth="2" />
              <circle cx={x} cy={centerLineY - halfDia} r="1.5" fill="#22d3ee" />
              <circle cx={x} cy={centerLineY + halfDia} r="1.5" fill="#22d3ee" />
            </g>
          );
        })}

        {[0, 0.25, 0.5, 0.75, 1].map((frac) => {
          const x = pad.left + frac * (W - pad.left - pad.right);
          return (
            <text key={frac} x={x} y={H - 6} textAnchor="middle" fill="#525252" fontSize="8" fontFamily="monospace">
              {(frac * maxPos * 1000).toFixed(0)}
            </text>
          );
        })}

        <text x={W / 2} y={H - 0} textAnchor="middle" fill="#525252" fontSize="8" fontFamily="system-ui">
          Position (mm)
        </text>

        <text x={6} y={centerLineY} textAnchor="middle" fill="#525252" fontSize="7" fontFamily="monospace" dominantBaseline="middle">
          0
        </text>
        <text x={6} y={pad.top + 4} textAnchor="middle" fill="#525252" fontSize="7" fontFamily="monospace">
          +R
        </text>
        <text x={6} y={pad.top + (H - pad.top - pad.bottom) - 4} textAnchor="middle" fill="#525252" fontSize="7" fontFamily="monospace">
          -R
        </text>
      </svg>
    </div>
  );
}
