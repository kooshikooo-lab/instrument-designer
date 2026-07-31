import { useState, useEffect, useCallback } from "react";
import {
  getBoreTypes,
  generateBoreProfile,
  optimizeBoreShape,
  exportVariableBoreStl,
} from "../utils/api";
import type { BoreTypeMeta, BoreProfilePointMM } from "../utils/api";

interface Props {
  closedTop: boolean;
  onStlGenerated?: (blob: Blob, filename: string) => void;
}

type RadiusParams = Record<string, unknown>;

export default function UnconventionalBoreDesigner({ closedTop, onStlGenerated }: Props) {
  const [boreTypes, setBoreTypes] = useState<Record<string, BoreTypeMeta>>({});
  const [boreType, setBoreType] = useState("cylindrical");
  const [boreLength, setBoreLength] = useState(600);
  const [radiusParams, setRadiusParams] = useState<RadiusParams>({ radius_mm: 7.25 });
  const [profile, setProfile] = useState<BoreProfilePointMM[]>([]);
  const [generating, setGenerating] = useState(false);
  const [optimizing, setOptimizing] = useState(false);
  const [optResult, setOptResult] = useState<{ scale_rms_cents: number; best_scale: string; fundamental_hz: number; resonances_hz: number[] } | null>(null);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [holeCount, setHoleCount] = useState(6);
  const [holeDiameter, setHoleDiameter] = useState(7.0);
  const [targetFreqs, setTargetFreqs] = useState("261.6, 293.7, 329.6, 349.2, 392.0, 440.0");

  useEffect(() => {
    getBoreTypes().then(setBoreTypes).catch(() => setError("Failed to load bore types from server"));
  }, []);

  useEffect(() => {
    const meta = boreTypes[boreType];
    if (!meta) return;
    const defaults: RadiusParams = {};
    for (const [key, [min, max, def]] of Object.entries(meta.params)) {
      defaults[key] = def;
    }
    if (boreType === "spline") {
      defaults["control_points"] = [[0, 7.0], [boreLength * 0.25, 8.0], [boreLength * 0.5, 9.0], [boreLength * 0.75, 10.0], [boreLength, 11.0]];
    }
    setRadiusParams(defaults);
  }, [boreType, boreTypes, boreLength]);

  const handleGenerate = useCallback(async () => {
    setGenerating(true);
    try {
      const res = await generateBoreProfile({
        bore_type: boreType,
        bore_length_mm: boreLength,
        radius_params: radiusParams,
      });
      setProfile(res.profile);
    } catch (e) {
      setError(`Generate failed: ${e instanceof Error ? e.message : e}`);
    }
    setGenerating(false);
  }, [boreType, boreLength, radiusParams]);

  const handleOptimize = useCallback(async () => {
    setOptimizing(true);
    setOptResult(null);
    try {
      const targets = targetFreqs.split(",").map(s => parseFloat(s.trim())).filter(n => !isNaN(n) && n > 0);
      const res = await optimizeBoreShape({
        bore_type: boreType,
        bore_length_mm: boreLength,
        radius_params: radiusParams,
        targets,
        hole_count: holeCount,
        hole_diameter_mm: holeDiameter,
        closed_top: closedTop,
      });
      setOptResult({ scale_rms_cents: res.scale_rms_cents, best_scale: res.best_scale, fundamental_hz: res.fundamental_hz, resonances_hz: res.resonances_hz });
    } catch (e) {
      setError(`Optimization failed: ${e instanceof Error ? e.message : e}`);
    }
    setOptimizing(false);
  }, [boreType, boreLength, radiusParams, targetFreqs, holeCount, holeDiameter, closedTop]);

  const handleExportStl = useCallback(async () => {
    if (profile.length < 2) return;
    setExporting(true);
    try {
      const profilePoints = profile.map(p => [p.position_mm, p.diameter_mm]);
      const blob = await exportVariableBoreStl({
        bore_profile: profilePoints,
        wall_thickness: 3.0,
        holes: [],
        closed_top: closedTop,
      });
      onStlGenerated?.(blob, `unconventional_${boreType}.stl`);
    } catch (e) {
      setError(`STL export failed: ${e instanceof Error ? e.message : e}`);
    }
    setExporting(false);
  }, [profile, boreType, closedTop, onStlGenerated]);

  const updateParam = (key: string, value: number) => {
    setRadiusParams(prev => ({ ...prev, [key]: value }));
  };

  const updateSplinePoint = (idx: number, pos: number, rad: number) => {
    const cp = (radiusParams["control_points"] as [number, number][] || []).map(p => [...p]);
    if (cp[idx]) {
      cp[idx] = [pos, rad];
      setRadiusParams(prev => ({ ...prev, ["control_points"]: cp }));
    }
  };

  const meta = boreTypes[boreType];

  return (
    <div className="space-y-4">
      {error && (
        <div className="bg-red-900/30 border border-red-700 rounded-lg px-3 py-2 text-xs text-red-300">
          {error}
          <button className="ml-2 text-red-400 hover:text-red-200" onClick={() => setError(null)}>x</button>
        </div>
      )}
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label className="text-xs text-neutral-500 block mb-1">Bore Shape</label>
          <select
            value={boreType}
            onChange={e => setBoreType(e.target.value)}
            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
          >
            {Object.entries(boreTypes).map(([key, meta]) => (
              <option key={key} value={key}>{meta.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="text-xs text-neutral-500 block mb-1">Bore Length (mm)</label>
          <input
            type="number"
            min={100}
            max={3000}
            value={boreLength}
            onChange={e => setBoreLength(Number(e.target.value))}
            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
          />
        </div>
      </div>

      {meta && boreType !== "spline" && (
        <div className="grid grid-cols-2 gap-4">
          {Object.entries(meta.params).map(([key, [min, max, def]]) => (
            <div key={key}>
              <label className="text-xs text-neutral-500 block mb-1">{key.replace(/_/g, " ")} (mm)</label>
              <div className="flex items-center gap-2">
                <input
                  type="range"
                  min={min}
                  max={max}
                  step={0.5}
                  value={(radiusParams[key] as number) ?? def}
                  onChange={e => updateParam(key, Number(e.target.value))}
                  className="flex-1 accent-brand-500"
                />
                <span className="text-xs text-neutral-400 font-mono w-10 text-right">
                  {(radiusParams[key] as number) ?? def}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}

      {boreType === "spline" && (
        <div className="space-y-2">
          <p className="text-xs text-neutral-500">Control Points (position_mm, radius_mm)</p>
          {(radiusParams["control_points"] as [number, number][] || []).map((cp, i) => (
            <div key={i} className="flex gap-2 items-center">
              <span className="text-xs text-neutral-500 w-4">{i + 1}</span>
              <input
                type="number"
                value={Math.round(cp[0])}
                onChange={e => updateSplinePoint(i, Number(e.target.value), cp[1])}
                className="w-full bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
                placeholder="Position (mm)"
              />
              <input
                type="number"
                value={cp[1]}
                step={0.5}
                onChange={e => updateSplinePoint(i, cp[0], Number(e.target.value))}
                className="w-full bg-neutral-800 border border-neutral-700 rounded px-2 py-1 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
                placeholder="Radius (mm)"
              />
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-white text-xs rounded-lg transition-colors disabled:opacity-50"
        >
          {generating ? "Generating..." : "Generate Profile"}
        </button>
      </div>

      {profile.length > 0 && (
        <div className="bg-neutral-950 rounded-lg p-3 space-y-2">
          <div className="flex items-center justify-between">
            <h4 className="text-xs font-medium text-neutral-300">Bore Profile ({profile.length} pts)</h4>
            <div className="flex gap-2">
              <button
                onClick={handleExportStl}
                disabled={exporting}
                className="px-3 py-1 bg-neutral-800 hover:bg-neutral-700 text-neutral-300 text-[10px] rounded border border-neutral-700 transition-colors disabled:opacity-50"
              >
                {exporting ? "Exporting..." : "Export STL"}
              </button>
            </div>
          </div>
          <svg viewBox="0 0 300 100" className="w-full h-24 bg-neutral-950 rounded">
            {(() => {
              const pts = profile;
              if (pts.length < 2) return null;
              const minD = Math.min(...pts.map(p => p.diameter_mm)) * 0.8;
              const maxD = Math.max(...pts.map(p => p.diameter_mm)) * 1.2;
              const rangeD = maxD - minD || 1;
              const maxL = pts[pts.length - 1].position_mm;
              const scaleX = 290 / maxL;
              const scaleY = 80 / rangeD;
              const pathD = pts.map((p, i) => {
                const x = 5 + p.position_mm * scaleX;
                const y = 90 - ((p.diameter_mm - minD) * scaleY + 5);
                return `${i === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
              }).join(" ");
              return (
                <>
                  <path d={pathD} fill="none" stroke="#22c55e" strokeWidth="2" />
                  <path d={pathD} fill="none" stroke="#22c55e" strokeWidth="0.5" strokeDasharray="3,3" transform="translate(0, 0)" />
                </>
              );
            })()}
          </svg>
        </div>
      )}

      <div className="border-t border-neutral-800 pt-4 space-y-4">
        <h4 className="text-xs font-medium text-neutral-300">Optimization</h4>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Target Frequencies (Hz)</label>
            <input
              value={targetFreqs}
              onChange={e => setTargetFreqs(e.target.value)}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-xs text-neutral-100 font-mono focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Hole Count</label>
            <input
              type="number"
              min={1}
              max={24}
              value={holeCount}
              onChange={e => setHoleCount(Number(e.target.value))}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Hole Diameter (mm)</label>
            <input
              type="number"
              min={2}
              max={20}
              step={0.5}
              value={holeDiameter}
              onChange={e => setHoleDiameter(Number(e.target.value))}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div className="flex items-end">
            <button
              onClick={handleOptimize}
              disabled={optimizing}
              className="w-full px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-neutral-200 text-xs rounded-lg border border-neutral-700 transition-colors disabled:opacity-50"
            >
              {optimizing ? "Optimizing..." : "Optimize Bore"}
            </button>
          </div>
        </div>
        {optResult && (
          <div className="bg-neutral-950 rounded-lg p-3 space-y-2">
            <div className="flex items-center gap-3">
              <span className="text-xs text-neutral-500">Scale RMS:</span>
              <span className={`text-sm font-mono ${optResult.scale_rms_cents < 20 ? "text-green-400" : optResult.scale_rms_cents < 50 ? "text-yellow-400" : "text-red-400"}`}>
                {optResult.scale_rms_cents.toFixed(2)} cents
              </span>
              <span className="text-xs text-neutral-400">({optResult.best_scale})</span>
            </div>
            <div className="text-[10px] text-neutral-400">
              Fundamental: {optResult.fundamental_hz.toFixed(1)} Hz
            </div>
            <div className="text-[10px] text-neutral-500">
              Resonances: {optResult.resonances_hz.filter(f => f > 0).map(f => `${f.toFixed(1)} Hz`).join(", ") || "none"}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
