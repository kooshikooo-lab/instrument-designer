import { useState, useEffect } from "react";
import { DEMAKEIN_PRESETS } from "../data/instruments";
import { checkHealth, startDesign, getDesignStatus, getDesignDownloadUrl, exportStep } from "../utils/api";
import STLViewer from "./STLViewer";
import ParametricGenerator from "./ParametricGenerator";
import ImpedancePlot from "./ImpedancePlot";
import TonePlayer from "./TonePlayer";

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

  return (
    <div className="p-6 max-w-4xl space-y-6">
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
              {Object.entries(DEMAKEIN_PRESETS).map(([key, name]) => (
                <option key={key} value={key}>{name}</option>
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

      <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5 space-y-4">
        <h3 className="text-sm font-medium text-neutral-200">Remote Server</h3>
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
      </div>

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

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-neutral-200">Parametric Generator</h3>
          <ParametricGenerator
            instrumentKey={preset}
            onGenerated={(blob, filename) => {
              setGeneratedBlob(blob);
              setGeneratedFilename(filename);
            }}
          />
        </div>
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-neutral-200">3D Preview</h3>
          <STLViewer file={generatedBlob ? new File([generatedBlob], generatedFilename) : null} />
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-sm font-medium text-neutral-200">Acoustic Impedance</h3>
        <ImpedancePlot preset={preset || undefined} />
      </div>

      {preset && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-neutral-200">Sound Preview</h3>
          <TonePlayer
            range={preset === "didgeridoo" ? "D2-D3" : preset === "ocarina" ? "C5-C7" : "C4-C6"}
            instrumentName={DEMAKEIN_PRESETS[preset] || preset}
          />
        </div>
      )}

      <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5">
        <h3 className="text-sm font-medium text-neutral-200 mb-3">How It Works</h3>
        <ol className="text-xs text-neutral-400 space-y-2 list-decimal list-inside">
          <li>Select a preset (e.g. Penny Whistle, Recorder, Reedpipe)</li>
          <li>Adjust transpose to change the instrument's key</li>
          <li>Connect to the FastAPI server running Demakein + OpenWInD</li>
          <li>Run the design - the server optimizes bore shape and hole placement</li>
          <li>Download the generated STL files for 3D printing</li>
          <li>Export STEP files via Build123d for CAD editing</li>
        </ol>
      </div>
    </div>
  );
}
