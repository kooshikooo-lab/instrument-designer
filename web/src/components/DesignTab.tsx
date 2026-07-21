import { useState, useEffect, type ReactNode } from "react";
import { DEMAKEIN_PRESETS, DEMAKEIN_PRESET_GROUPS } from "../data/instruments";
import { TUNING_PRESETS, TUNING_CATEGORIES } from "../data/tuning-presets";
import { checkHealth, startDesign, getDesignStatus, getDesignDownloadUrl, exportStep, startOptimization, getOptimizationStatus, getOptimizationPresets } from "../utils/api";
import type { PitchResult } from "../utils/pitch";
import type { OptimizationResult, OptimizationPreset } from "../utils/api";
import STLViewer from "./STLViewer";
import ParametricGenerator from "./ParametricGenerator";
import ImpedancePlot from "./ImpedancePlot";
import TonePlayer from "./TonePlayer";
import MicrophoneAnalyzer from "./MicrophoneAnalyzer";
import PresetInfo from "./PresetInfo";

function CollapsibleSection({
  title,
  children,
  defaultOpen = true,
  badge,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
  badge?: string;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left"
      >
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-neutral-200">{title}</h3>
          {badge && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-brand-600/20 text-brand-400 font-medium">
              {badge}
            </span>
          )}
        </div>
        <svg
          className={`w-4 h-4 text-neutral-500 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="px-5 pb-5 space-y-4">{children}</div>}
    </div>
  );
}

interface DesignTabProps {
  initialPreset?: string;
  onPresetUsed?: () => void;
}

export function DesignTab({ initialPreset, onPresetUsed }: DesignTabProps) {
  const [preset, setPreset] = useState(initialPreset || "");
  const [transpose, setTranspose] = useState(0);
  const [serverUrl, setServerUrl] = useState("http://localhost:8000");
  const [connected, setConnected] = useState<boolean | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [status, setStatus] = useState("");
  const [progress, setProgress] = useState<string[]>([]);
  const [running, setRunning] = useState(false);
  const [generatedBlob, setGeneratedBlob] = useState<Blob | null>(null);
  const [generatedFilename, setGeneratedFilename] = useState<string>("");
  const [stepExporting, setStepExporting] = useState(false);
  const [serverBlob, setServerBlob] = useState<Blob | null>(null);
  const [serverFilename, setServerFilename] = useState<string>("");
  const [measuredPitch, setMeasuredPitch] = useState<PitchResult | null>(null);
  const [tuningPreset, setTuningPreset] = useState<string>("");
  const [tuningCategory, setTuningCategory] = useState<string>("");

  const [optPresets, setOptPresets] = useState<Record<string, OptimizationPreset>>({});
  const [optTargetKey, setOptTargetKey] = useState<string>("");
  const [optManualFreqs, setOptManualFreqs] = useState("");
  const [optPopSize, setOptPopSize] = useState(30);
  const [optGen, setOptGen] = useState(20);
  const [optCP, setOptCP] = useState(12);
  const [optRunning, setOptRunning] = useState(false);
  const [_optJobId, setOptJobId] = useState<string | null>(null);
  const [optStatus, setOptStatus] = useState("");
  const [optProgress, setOptProgress] = useState<string[]>([]);
  const [optResult, setOptResult] = useState<OptimizationResult | null>(null);

  useEffect(() => {
    getOptimizationPresets().then((p) => setOptPresets(p)).catch(() => {});
  }, []);

  useEffect(() => {
    if (initialPreset) {
      setPreset(initialPreset);
      onPresetUsed?.();
    }
  }, [initialPreset]);

  const testConnection = async () => {
    try {
      const data = await checkHealth();
      setConnected(data.status === "ok");
    } catch {
      setConnected(false);
    }
  };

  const runDesign = async () => {
    if (!preset) return;
    setRunning(true);
    setProgress([]);
    setStatus("Starting design...");
    try {
      const { job_id } = await startDesign(preset, transpose);
      setJobId(job_id);
      setStatus(`Job ${job_id} started`);

      const poll = setInterval(async () => {
        const result = await getDesignStatus(job_id);
        setProgress(result.progress);
        setStatus(result.status);
        if (result.status === "completed" || result.status === "failed") {
          clearInterval(poll);
          setRunning(false);
          if (result.status === "completed") {
            try {
              const res = await fetch(getDesignDownloadUrl(job_id));
              const blob = await res.blob();
              setServerBlob(blob);
              setServerFilename(`${preset}-design.stl`);
            } catch {
              console.error("Failed to auto-load STL into viewer");
            }
          }
        }
      }, 1000);
    } catch (e) {
      setStatus(`Error: ${e}`);
      setRunning(false);
    }
  };

  const handleStepExport = async () => {
    setStepExporting(true);
    try {
      const blob = await exportStep({
        preset: preset || "custom",
        length: 200,
        bore_diameter: 20,
        wall_thickness: 3,
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${preset || "custom"}-bore.step`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (e) {
      console.error("STEP export failed:", e);
    } finally {
      setStepExporting(false);
    }
  };

  const parsedManualFreqs = (): number[] => {
    return optManualFreqs.split(",").map((s) => parseFloat(s.trim())).filter((n) => !isNaN(n) && n > 0);
  };

  const getTargetFrequencies = (): number[] => {
    if (optTargetKey && optPresets[optTargetKey]) {
      return optPresets[optTargetKey].frequencies;
    }
    if (optManualFreqs.trim()) {
      return parsedManualFreqs();
    }
    return [];
  };

  const runOptimization = async () => {
    const targets = getTargetFrequencies();
    if (targets.length < 2) return;
    setOptRunning(true);
    setOptProgress([]);
    setOptResult(null);
    setOptStatus("Starting optimization...");
    try {
      const { job_id } = await startOptimization({
        target_frequencies: targets,
        pop_size: optPopSize,
        n_generations: optGen,
        n_control_points: optCP,
      });
      setOptJobId(job_id);
      setOptStatus(`Job ${job_id} started`);
      const poll = setInterval(async () => {
        const result = await getOptimizationStatus(job_id);
        setOptProgress(result.progress);
        setOptStatus(result.status);
        if (result.status === "completed" || result.status === "failed") {
          clearInterval(poll);
          setOptRunning(false);
          if (result.status === "completed" && result.result) {
            setOptResult(result.result);
          }
        }
      }, 1000);
    } catch (e) {
      setOptStatus(`Error: ${e}`);
      setOptRunning(false);
    }
  };

  return (
    <div className="p-6 max-w-6xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-neutral-100">Design Instrument</h2>
        <p className="text-sm text-neutral-500">Configure and generate a 3D-printable instrument design</p>
      </div>

      <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5 space-y-4">
        <h3 className="text-sm font-medium text-neutral-200">Design Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Preset</label>
            <select
              value={preset}
              onChange={(e) => setPreset(e.target.value)}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            >
              <option value="">Select a preset...</option>
              {DEMAKEIN_PRESET_GROUPS.map((group) => (
                <optgroup key={group.label} label={group.label}>
                  {group.presets.map((p) => (
                    <option key={p.key} value={p.key}>{p.name}</option>
                  ))}
                </optgroup>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Transpose (semitones)</label>
            <input
              type="number"
              min={-24}
              max={24}
              value={transpose}
              onChange={(e) => setTranspose(Number(e.target.value))}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>
      </div>

      <CollapsibleSection title="Tuning System" defaultOpen={false} badge={tuningPreset ? TUNING_PRESETS.find(t => t.name === tuningPreset)?.category : undefined}>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Category</label>
            <select
              value={tuningCategory}
              onChange={(e) => { setTuningCategory(e.target.value); setTuningPreset(""); }}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            >
              <option value="">All categories</option>
              {TUNING_CATEGORIES.map((cat) => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Tuning Preset</label>
            <select
              value={tuningPreset}
              onChange={(e) => setTuningPreset(e.target.value)}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            >
              <option value="">Select a tuning...</option>
              {TUNING_PRESETS
                .filter((t) => !tuningCategory || t.category === tuningCategory)
                .map((t) => (
                  <option key={t.name} value={t.name}>{t.name}</option>
                ))}
            </select>
          </div>
        </div>
        {tuningPreset && (() => {
          const t = TUNING_PRESETS.find((tp) => tp.name === tuningPreset);
          if (!t) return null;
          return (
            <div className="bg-neutral-950 rounded-lg p-3 space-y-2">
              <p className="text-xs text-neutral-400">{t.description}</p>
              <div className="flex flex-wrap gap-1.5">
                {t.labels.map((label, i) => (
                  <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-300 font-mono">
                    {label}
                  </span>
                ))}
              </div>
              <div className="text-[10px] text-neutral-500">
                {t.notes_per_octave} notes/octave{t.cents_per_step !== null ? ` ┬À ${t.cents_per_step.toFixed(1)} cents/step` : " ┬À non-equal"}
              </div>
            </div>
          );
        })()}
      </CollapsibleSection>

      <CollapsibleSection title="Remote Server" defaultOpen={false} badge={connected === true ? "Connected" : connected === false ? "Disconnected" : undefined}>
        <div className="flex gap-3 items-end">
          <div className="flex-1">
            <label className="text-xs text-neutral-500 block mb-1">Server URL</label>
            <input
              type="text"
              value={serverUrl}
              onChange={(e) => setServerUrl(e.target.value)}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <button
            onClick={testConnection}
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-100 rounded-lg transition-colors"
          >
            Test
          </button>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected === true ? "bg-green-500" : connected === false ? "bg-red-500" : "bg-neutral-600"}`} />
          <span className="text-xs text-neutral-500">
            {connected === true ? "Connected" : connected === false ? "Not connected" : "Not tested"}
          </span>
        </div>
      </CollapsibleSection>

      <div className="flex gap-3">
        <button
          onClick={runDesign}
          disabled={!preset || running}
          className="px-6 py-2.5 bg-brand-600 hover:bg-brand-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-lg transition-colors font-medium"
        >
          {running ? "Designing..." : "Run Design"}
        </button>
        {jobId && status === "completed" && (
          <a
            href={getDesignDownloadUrl(jobId)}
            className="px-6 py-2.5 bg-green-600 hover:bg-green-500 text-sm text-white rounded-lg transition-colors font-medium"
          >
            Download STL
          </a>
        )}
        {generatedBlob && (
          <a
            href={URL.createObjectURL(generatedBlob)}
            download={generatedFilename}
            className="px-6 py-2.5 bg-green-600 hover:bg-green-500 text-sm text-white rounded-lg transition-colors font-medium"
          >
            Download Generated
          </a>
        )}
        <button
          onClick={handleStepExport}
          disabled={stepExporting}
          className="px-6 py-2.5 bg-blue-600 hover:bg-blue-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-lg transition-colors font-medium"
        >
          {stepExporting ? "Exporting..." : "Export STEP"}
        </button>
      </div>

      {(progress.length > 0 || status) && (
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5 space-y-2">
          <h3 className="text-sm font-medium text-neutral-200">Progress</h3>
          <div className="text-xs text-neutral-400 mb-2">Status: {status}</div>
          <div className="bg-neutral-950 rounded-lg p-3 max-h-60 overflow-auto font-mono text-xs text-neutral-400 space-y-0.5">
            {progress.map((line, i) => (
              <div key={i}>{line}</div>
            ))}
          </div>
        </div>
      )}

      {(serverBlob || generatedBlob) && (
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-neutral-200">
              3D Preview {serverBlob ? "(Server Design)" : "(Parametric)"}
            </h3>
            <div className="flex gap-2">
              <button
                onClick={() => {
                  const blob = serverBlob || generatedBlob;
                  const name = serverFilename || generatedFilename;
                  if (!blob) return;
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = name;
                  a.click();
                  URL.revokeObjectURL(url);
                }}
                className="px-3 py-1.5 bg-green-600 hover:bg-green-500 text-xs text-white rounded-lg transition-colors"
              >
                Download STL
              </button>
              {serverBlob && (
                <button
                  onClick={async () => {
                    try {
                      const res = await fetch(getDesignDownloadUrl(jobId!));
                      const blob = await res.blob();
                      const arrayBuffer = await blob.arrayBuffer();
                      const uint8 = new Uint8Array(arrayBuffer);
                      let binary = "";
                      for (let i = 0; i < uint8.length; i++) binary += String.fromCharCode(uint8[i]);
                      const base64 = btoa(binary);
                      const dataUrl = `data:application/octet-stream;base64,${base64}`;
                      const a = document.createElement("a");
                      a.href = dataUrl;
                      a.download = serverFilename;
                      a.click();
                    } catch (e) {
                      console.error(e);
                    }
                  }}
                  className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-xs text-white rounded-lg transition-colors"
                >
                  Open Externally
                </button>
              )}
            </div>
          </div>
          <div className="h-[400px] rounded-lg overflow-hidden bg-neutral-950">
            <STLViewer file={serverBlob ? new File([serverBlob], serverFilename) : generatedBlob ? new File([generatedBlob], generatedFilename) : null} />
          </div>
        </div>
      )}

      <CollapsibleSection title="Bore Optimization (NSGA-II)" defaultOpen={false} badge="Evolutionary">
        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Target Frequency Preset</label>
              <select
                value={optTargetKey}
                onChange={(e) => setOptTargetKey(e.target.value)}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
              >
                <option value="">Manual entry...</option>
                {Object.entries(optPresets).map(([key, p]) => (
                  <option key={key} value={key}>{p.name}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Manual Frequencies (Hz, comma-separated)</label>
              <input
                type="text"
                value={optManualFreqs}
                onChange={(e) => setOptManualFreqs(e.target.value)}
                placeholder="261.6, 784.8, 1308.0..."
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>
          {optTargetKey && optPresets[optTargetKey] && (
            <div className="flex flex-wrap gap-1.5">
              {optPresets[optTargetKey].frequencies.map((f, i) => (
                <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-neutral-800 text-neutral-300 font-mono">
                  {f.toFixed(1)} Hz
                </span>
              ))}
            </div>
          )}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Population</label>
              <input
                type="number" min={4} max={200}
                value={optPopSize}
                onChange={(e) => setOptPopSize(Number(e.target.value))}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Generations</label>
              <input
                type="number" min={1} max={500}
                value={optGen}
                onChange={(e) => setOptGen(Number(e.target.value))}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
              />
            </div>
            <div>
              <label className="text-xs text-neutral-500 block mb-1">Control Points</label>
              <input
                type="number" min={4} max={30}
                value={optCP}
                onChange={(e) => setOptCP(Number(e.target.value))}
                className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
              />
            </div>
          </div>
          <button
            onClick={runOptimization}
            disabled={optRunning || getTargetFrequencies().length < 2}
            className="px-6 py-2.5 bg-purple-600 hover:bg-purple-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-lg transition-colors font-medium"
          >
            {optRunning ? "Optimizing..." : "Run Optimization"}
          </button>
          {(optProgress.length > 0 || optStatus) && (
            <div>
              <div className="text-xs text-neutral-400 mb-1">Status: {optStatus}</div>
              <div className="bg-neutral-950 rounded-lg p-3 max-h-40 overflow-auto font-mono text-xs text-neutral-400 space-y-0.5">
                {optProgress.map((line, i) => (<div key={i}>{line}</div>))}
              </div>
            </div>
          )}
          {optResult && (
            <div className="space-y-3">
              <h4 className="text-sm font-medium text-neutral-200">Results</h4>
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-neutral-950 rounded-lg p-3">
                  <div className="text-[10px] text-neutral-500">Frequency Accuracy</div>
                  <div className="text-sm text-neutral-100 font-mono">
                    {optResult.best_candidates[0]?.objectives?.frequency_accuracy?.toFixed(2) ?? "?"}¢
                  </div>
                </div>
                <div className="bg-neutral-950 rounded-lg p-3">
                  <div className="text-[10px] text-neutral-500">Evaluations</div>
                  <div className="text-sm text-neutral-100 font-mono">{optResult.n_evaluations}</div>
                </div>
                <div className="bg-neutral-950 rounded-lg p-3">
                  <div className="text-[10px] text-neutral-500">Bore Length</div>
                  <div className="text-sm text-neutral-100 font-mono">{(optResult.bore_length * 1000).toFixed(0)} mm</div>
                </div>
              </div>
              {optResult.best_candidates[0]?.bore_profile && (
                <div>
                  <h5 className="text-xs text-neutral-500 mb-1">Bore Profile</h5>
                  <div className="bg-neutral-950 rounded-lg p-3 overflow-x-auto">
                    <table className="w-full text-[10px] font-mono text-neutral-300">
                      <thead>
                        <tr className="text-neutral-500">
                          <th className="text-left pr-4">Position (mm)</th>
                          <th className="text-left pr-4">Radius (mm)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {optResult.best_candidates[0].bore_profile.map((p, i) => (
                          <tr key={i}>
                            <td className="pr-4">{(p.position * 1000).toFixed(1)}</td>
                            <td className="pr-4">{(p.radius * 1000).toFixed(2)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
              {optResult.best_candidates[0]?.matched_frequencies && (
                <div>
                  <h5 className="text-xs text-neutral-500 mb-1">Matched Frequencies</h5>
                  <div className="bg-neutral-950 rounded-lg p-3 overflow-x-auto">
                    <table className="w-full text-[10px] font-mono text-neutral-300">
                      <thead>
                        <tr className="text-neutral-500">
                          <th className="text-left pr-4">Target (Hz)</th>
                          <th className="text-left pr-4">Actual (Hz)</th>
                          <th className="text-left pr-4">Error (cents)</th>
                        </tr>
                      </thead>
                      <tbody>
                        {optResult.best_candidates[0].matched_frequencies.map((m, i) => (
                          <tr key={i}>
                            <td className="pr-4">{m.target.toFixed(1)}</td>
                            <td className="pr-4">{m.actual.toFixed(1)}</td>
                            <td className={`pr-4 ${Math.abs(m.error_cents) > 20 ? "text-red-400" : Math.abs(m.error_cents) > 5 ? "text-yellow-400" : "text-green-400"}`}>
                              {m.error_cents.toFixed(1)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </CollapsibleSection>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-5">
          <CollapsibleSection title="Acoustic Impedance" defaultOpen={false} badge={preset ? "Data available" : undefined}>
            <ImpedancePlot preset={preset || undefined} measuredPitch={measuredPitch} />
          </CollapsibleSection>

          <CollapsibleSection title="Live Measurement" defaultOpen={false}>
            <MicrophoneAnalyzer onPitch={setMeasuredPitch} />
          </CollapsibleSection>
        </div>

        <div className="space-y-5">
          {preset && <PresetInfo preset={preset} />}

          {preset && (
            <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5 space-y-4">
              <h3 className="text-sm font-medium text-neutral-200">Sound Preview</h3>
              <TonePlayer
                range={preset === "didgeridoo" ? "D2-D3" : preset === "ocarina" ? "C5-C7" : "C4-C6"}
                instrumentName={DEMAKEIN_PRESETS[preset] || preset}
              />
            </div>
          )}

          <CollapsibleSection title="Parametric Generator" defaultOpen={false} badge="Expert">
            <ParametricGenerator
              instrumentKey={preset}
              onGenerated={(blob, filename) => {
                setGeneratedBlob(blob);
                setGeneratedFilename(filename);
              }}
            />
          </CollapsibleSection>
        </div>
      </div>

      <CollapsibleSection title="How It Works" defaultOpen={false}>
        <ol className="text-xs text-neutral-400 space-y-2 list-decimal list-inside">
          <li>Select a preset (e.g. Penny Whistle, Recorder, Reedpipe)</li>
          <li>Adjust transpose to change the instrument's key</li>
          <li>Connect to the FastAPI server running Demakein + OpenWInD</li>
          <li>Run the design - the server optimizes bore shape and hole placement</li>
          <li>Download the generated STL files for 3D printing</li>
          <li>Export STEP files via Build123d for CAD editing</li>
        </ol>
      </CollapsibleSection>
    </div>
  );
}
