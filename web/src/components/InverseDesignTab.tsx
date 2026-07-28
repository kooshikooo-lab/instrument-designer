import { useState, useRef, type ReactNode } from "react";
import { MATERIALS, type BorePoint } from "./InstrumentModel";
import InstrumentModel from "./InstrumentModel";
import {
  inverseUpload,
  inverseAnalyze,
  inverseDesign,
  inverseHealth,
} from "../utils/api";
import type {
  InverseAnalysis,
  InverseDesignResult,
  InverseCandidate,
  Tier3Result,
  FinalGeometry,
} from "../utils/api";

function Section({
  title,
  children,
  defaultOpen = true,
}: {
  title: string;
  children: ReactNode;
  defaultOpen?: boolean;
}) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-5 text-left"
      >
        <h3 className="text-sm font-medium text-neutral-200">{title}</h3>
        <svg
          className={`w-4 h-4 text-neutral-500 transition-transform ${open ? "rotate-180" : ""}`}
          fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
        </svg>
      </button>
      {open && <div className="px-5 pb-5 space-y-4">{children}</div>}
    </div>
  );
}

function Spec({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between bg-neutral-950 rounded px-2 py-1">
      <span className="text-neutral-500">{label}</span>
      <span className="text-neutral-300">{value}</span>
    </div>
  );
}

function SpectrumPreview({ analysis }: { analysis: InverseAnalysis }) {
  const freqs = analysis.spectrum_frequencies;
  const mags = analysis.spectrum_magnitudes;
  const maxMag = Math.max(...mags, 1e-6);
  const width = 600;
  const height = 120;

  const points = freqs.map((f, i) => {
    const x = (f / (freqs[freqs.length - 1] || 1)) * width;
    const y = height - (mags[i] / maxMag) * height;
    return `${x},${y}`;
  });

  return (
    <div className="bg-neutral-950 rounded-lg p-3">
      <div className="text-[10px] text-neutral-500 mb-1">Spectrum (magnitude vs frequency)</div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-24">
        <polyline points={points.join(" ")} fill="none" stroke="#22c55e" strokeWidth={1} />
        {analysis.harmonic_frequencies.map((hf, i) => {
          const x = (hf / (freqs[freqs.length - 1] || 1)) * width;
          return (
            <line key={i} x1={x} y1={0} x2={x} y2={height} stroke="#ef4444" strokeWidth={1} opacity={0.4} />
          );
        })}
      </svg>
    </div>
  );
}

function EnvelopePreview({ magnitudes, label }: { magnitudes: number[]; label: string }) {
  const maxM = Math.max(...magnitudes, 1e-6);
  const width = 300;
  const height = 80;

  return (
    <div className="bg-neutral-950 rounded-lg p-2">
      <div className="text-[9px] text-neutral-500 mb-1">{label}</div>
      <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-16">
        {magnitudes.map((m, i) => {
          const x = (i / Math.max(magnitudes.length - 1, 1)) * width;
          const y = height - (m / maxM) * height;
          const barH = (m / maxM) * height;
          return <rect key={i} x={x - 1} y={y} width={Math.max(2, width / magnitudes.length - 1)} height={barH} fill="#3b82f6" rx={1} />;
        })}
      </svg>
    </div>
  );
}

function CandidateCard({
  candidate,
  index,
  tier3Result,
}: {
  candidate: InverseCandidate;
  index: number;
  tier3Result?: Tier3Result | null;
}) {
  const boreProfile: BorePoint[] = candidate.bore_radii.map((r, i) => ({
    position: (i / (candidate.bore_radii.length - 1)) * candidate.bore_length_mm / 1000,
    radius: r / 1000,
  }));
  const holes = candidate.hole_positions_mm.map((p, i) => ({
    position: p / 1000,
    diameter: (candidate.hole_diameters_mm[i] || 7) / 1000,
    open: true,
  }));

  const scoreColor =
    candidate.intonation_rms_cents < 1 ? "text-green-400" :
    candidate.intonation_rms_cents < 5 ? "text-yellow-400" :
    candidate.intonation_rms_cents < 25 ? "text-orange-400" : "text-red-400";

  return (
    <div className="bg-neutral-950 rounded-xl border border-neutral-800 overflow-hidden">
      <div className="h-40">
        <InstrumentModel
          boreProfile={boreProfile}
          holes={holes}
          material={MATERIALS.brass}
          showHoles
          height={160}
        />
      </div>
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-600 font-mono">#{index + 1}</span>
            <h4 className="text-sm font-medium text-neutral-100">{candidate.name}</h4>
          </div>
          <span className="text-xs text-neutral-500 font-mono">{candidate.opt_time_s.toFixed(1)}s</span>
        </div>

        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
          <Spec label="Bore" value={`${candidate.bore_type} (${candidate.bore_radius_mm.toFixed(1)}mm)`} />
          <Spec label="Length" value={`${candidate.bore_length_mm.toFixed(0)}mm`} />
          <Spec label="Holes" value={String(candidate.hole_positions_mm.length)} />
          <Spec label="Closed top" value={String(candidate.closed_top)} />
        </div>

        <div className="flex gap-4 text-xs">
          <div>
            <span className="text-neutral-500">Intonation: </span>
            <span className={`font-mono font-medium ${scoreColor}`}>
              {candidate.intonation_rms_cents < 1e5
                ? `${candidate.intonation_rms_cents.toFixed(2)}¢`
                : "—"}
            </span>
          </div>
          <div>
            <span className="text-neutral-500">Timbre: </span>
            <span className="font-mono text-neutral-300">
              {candidate.timbre_cost < 1e5 ? candidate.timbre_cost.toFixed(6) : "—"}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

function FinalGeometryCard({ geometry }: { geometry: FinalGeometry }) {
  const boreProfile: BorePoint[] = geometry.bore_radii.map((r, i) => ({
    position: (i / (geometry.bore_radii.length - 1)) * geometry.bore_length_mm / 1000,
    radius: r / 1000,
  }));
  const holes = geometry.hole_positions_mm.map((p, i) => ({
    position: p / 1000,
    diameter: (geometry.hole_diameters_mm[i] || 7) / 1000,
    open: true,
  }));

  return (
    <div className="bg-neutral-950 rounded-xl border border-neutral-800 overflow-hidden">
      <div className="h-48">
        <InstrumentModel
          boreProfile={boreProfile}
          holes={holes}
          material={MATERIALS.brass}
          showHoles
          height={192}
        />
      </div>
      <div className="p-4 space-y-3">
        <h4 className="text-sm font-medium text-neutral-100">Final Geometry</h4>
        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
          <Spec label="Bore length" value={`${geometry.bore_length_mm.toFixed(0)}mm`} />
          <Spec label="Bore radii" value={`${geometry.bore_radii.length} CPs`} />
          <Spec label="Holes" value={String(geometry.hole_positions_mm.length)} />
          <Spec label="Intonation" value={`${geometry.intonation_rms_cents.toFixed(2)}¢`} />
          <Spec label="Timbre match" value={geometry.timbre_match_cost.toFixed(6)} />
        </div>
      </div>
    </div>
  );
}

function Tier3ResultCard({ tier3 }: { tier3: Tier3Result }) {
  return (
    <div className="bg-neutral-950 rounded-xl border border-neutral-800 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-neutral-100">Timbre Optimization</h4>
        <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${
          tier3.tier3_success ? "bg-green-900/30 text-green-400" : "bg-red-900/30 text-red-400"
        }`}>
          {tier3.tier3_success ? "Improved" : "No improvement"}
        </span>
      </div>

      <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
        <Spec label="Initial cost" value={tier3.tier3_cost_initial.toFixed(6)} />
        <Spec label="Optimized cost" value={tier3.tier3_cost_optimized.toFixed(6)} />
      </div>

      <div className="grid grid-cols-2 gap-4">
        <EnvelopePreview
          magnitudes={tier3.target_envelope_magnitudes}
          label="Target envelope (from sound)"
        />
        {tier3.estimated_envelope_optimized.length > 0 && (
          <EnvelopePreview
            magnitudes={tier3.estimated_envelope_optimized}
            label="Optimized envelope"
          />
        )}
      </div>
    </div>
  );
}

export default function InverseDesignTab() {
  const [file, setFile] = useState<File | null>(null);
  const [uploadedPath, setUploadedPath] = useState<string>("");
  const [nCandidates, setNCandidates] = useState(2);
  const [holeCount, setHoleCount] = useState(6);
  const [runTier3, setRunTier3] = useState(true);
  const [label, setLabel] = useState("");

  const [running, setRunning] = useState(false);
  const [phase, setPhase] = useState<"idle" | "uploading" | "analyzing" | "designing" | "done" | "error">("idle");
  const [statusMsg, setStatusMsg] = useState("");

  const [analysis, setAnalysis] = useState<InverseAnalysis | null>(null);
  const [result, setResult] = useState<InverseDesignResult | null>(null);
  const [error, setError] = useState<string>("");
  const [serverOk, setServerOk] = useState<boolean | null>(null);

  const fileRef = useRef<HTMLInputElement>(null);

  const handleHealthCheck = async () => {
    try {
      const h = await inverseHealth();
      setServerOk(h.status === "ok");
    } catch {
      setServerOk(false);
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    if (f) setFile(f);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const f = e.dataTransfer.files?.[0];
    if (f && f.name.endsWith(".wav")) setFile(f);
  };

  const handleRun = async () => {
    if (!file) return;
    setRunning(true);
    setError("");
    setAnalysis(null);
    setResult(null);

    try {
      // Upload
      setPhase("uploading");
      setStatusMsg("Uploading WAV file...");
      const uploadRes = await inverseUpload(file);
      setUploadedPath(uploadRes.filepath);

      // Analyze
      setPhase("analyzing");
      setStatusMsg("Analyzing audio (Tier 1)...");
      const analyzeRes = await inverseAnalyze(uploadRes.filepath);
      setAnalysis(analyzeRes.analysis);

      // Full design
      setPhase("designing");
      setStatusMsg("Designing instrument (Tiers 2 & 3)...");
      const designRes = await inverseDesign({
        filepath: uploadRes.filepath,
        n_candidates: nCandidates,
        hole_count: holeCount,
        run_tier3: runTier3,
        label: label || undefined,
      });
      setResult(designRes);
      setPhase("done");
      setStatusMsg("Done");
    } catch (e) {
      setPhase("error");
      setError(e instanceof Error ? e.message : String(e));
      setStatusMsg("Failed");
    } finally {
      setRunning(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadedPath("");
    setAnalysis(null);
    setResult(null);
    setError("");
    setPhase("idle");
    setStatusMsg("");
    if (fileRef.current) fileRef.current.value = "";
  };

  const tier1 = result?.tier1 || null;
  const tier2 = result?.tier2 || null;
  const tier3 = result?.tier3 || null;
  const finalGeo = result?.final_geometry || null;

  const tierColors = {
    idle: "text-neutral-600",
    uploading: "text-brand-400",
    analyzing: "text-yellow-400",
    designing: "text-blue-400",
    done: "text-green-400",
    error: "text-red-400",
  };

  return (
    <div className="p-6 max-w-6xl space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-neutral-100">Inverse Design from Sound</h2>
        <p className="text-sm text-neutral-500">
          Upload a WAV recording to design an instrument that reproduces its sound
        </p>
      </div>

      {/* Server health */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-neutral-500">Server:</span>
        {serverOk === null ? (
          <button onClick={handleHealthCheck} className="text-xs text-brand-400 hover:underline">Check connection</button>
        ) : serverOk ? (
          <span className="text-xs text-green-400">Online</span>
        ) : (
          <span className="text-xs text-red-400">Unreachable</span>
        )}
      </div>

      {/* Upload */}
      <div
        onDrop={handleDrop}
        onDragOver={(e) => e.preventDefault()}
        className="bg-neutral-900 rounded-xl border-2 border-dashed border-neutral-700 p-8 text-center"
      >
        {!file ? (
          <div className="space-y-3">
            <svg className="w-10 h-10 mx-auto text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 9V4.5M9 9H4.5M9 9L3.75 3.75M9 15v4.5M9 15H4.5M9 15l-5.25 5.25M15 9h4.5M15 9V4.5M15 9l5.25-5.25M15 15h4.5M15 15v4.5m0-4.5l5.25 5.25" />
            </svg>
            <p className="text-sm text-neutral-400">Drop a WAV file here, or</p>
            <button
              onClick={() => fileRef.current?.click()}
              className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-sm text-white rounded-lg transition-colors"
            >
              Select WAV File
            </button>
            <input
              ref={fileRef}
              type="file"
              accept=".wav"
              onChange={handleFileChange}
              className="hidden"
            />
          </div>
        ) : (
          <div className="space-y-2">
            <p className="text-sm text-neutral-200">{file.name}</p>
            <p className="text-[10px] text-neutral-500">{(file.size / 1024).toFixed(1)} KB</p>
            <button
              onClick={() => { setFile(null); if (fileRef.current) fileRef.current.value = ""; }}
              className="text-xs text-neutral-500 hover:text-neutral-300 underline"
            >
              Remove
            </button>
          </div>
        )}
      </div>

      {/* Config */}
      <Section title="Configuration" defaultOpen={true}>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Candidates</label>
            <input
              type="number" min={1} max={5}
              value={nCandidates}
              onChange={(e) => setNCandidates(Number(e.target.value))}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Hole count</label>
            <input
              type="number" min={2} max={12}
              value={holeCount}
              onChange={(e) => setHoleCount(Number(e.target.value))}
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            />
          </div>
          <div className="flex items-end">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={runTier3}
                onChange={(e) => setRunTier3(e.target.checked)}
                className="rounded bg-neutral-800 border-neutral-700"
              />
              <span className="text-xs text-neutral-500">Run Tier 3 (timbre)</span>
            </label>
          </div>
          <div>
            <label className="text-xs text-neutral-500 block mb-1">Label (optional)</label>
            <input
              type="text"
              value={label}
              onChange={(e) => setLabel(e.target.value)}
              placeholder="My design"
              className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 focus:outline-none focus:border-brand-500"
            />
          </div>
        </div>
      </Section>

      {/* Run button + status */}
      <div className="flex items-center gap-4">
        <button
          onClick={handleRun}
          disabled={!file || running}
          className="px-6 py-2 bg-brand-600 hover:bg-brand-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-lg transition-colors font-medium"
        >
          {running ? "Running..." : "Design from Sound"}
        </button>
        {result && (
          <button
            onClick={handleReset}
            className="px-4 py-2 text-sm text-neutral-400 hover:text-neutral-200 border border-neutral-700 rounded-lg transition-colors"
          >
            New Design
          </button>
        )}
        <span className={`text-xs font-mono ${tierColors[phase]}`}>
          {phase === "idle" ? "" : `${phase}${statusMsg ? `: ${statusMsg}` : ""}`}
        </span>
      </div>

      {/* Tier progress indicators */}
      {phase !== "idle" && (
        <div className="flex gap-2">
          {(["uploading", "analyzing", "designing", "done"] as const).map((p) => {
            const idx = ["uploading", "analyzing", "designing", "done"].indexOf(p);
            const cur = ["uploading", "analyzing", "designing", "done"].indexOf(phase === "error" ? "done" : phase);
            const active = idx <= cur;
            const isError = phase === "error" && idx === cur;
            return (
              <div key={p} className={`flex items-center gap-1 px-2 py-1 rounded text-[10px] font-mono ${
                isError ? "bg-red-900/30 text-red-400" :
                active && idx < 3 ? "bg-brand-900/30 text-brand-400" :
                active && idx === 3 ? "bg-green-900/30 text-green-400" :
                "bg-neutral-800 text-neutral-600"
              }`}>
                <span>{idx === 0 ? "📤" : idx === 1 ? "🔍" : idx === 2 ? "⚙" : "✅"}</span>
                <span>{p === "uploading" ? "Upload" : p === "analyzing" ? "Analyze" : p === "designing" ? "Design" : "Complete"}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-900/20 border border-red-800 rounded-xl p-4">
          <p className="text-xs text-red-400 font-mono">{error}</p>
        </div>
      )}

      {/* Tier 1 Results */}
      {tier1 && (
        <Section title={`Tier 1: Sound Analysis`}>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 text-[11px] font-mono">
            <Spec label="Fundamental" value={`${tier1.fundamental_hz.toFixed(2)} Hz`} />
            <Spec label="Confidence" value={(tier1.confidence * 100).toFixed(1) + "%"} />
            <Spec label="Duration" value={`${tier1.duration_s.toFixed(2)}s`} />
            <Spec label="Harmonics" value={String(tier1.n_harmonics)} />
          </div>
          <SpectrumPreview analysis={{
            ...tier1,
            spectrum_frequencies: [],
            spectrum_magnitudes: [],
            envelope_frequencies: [],
            envelope_magnitudes: [],
          }} />
          {tier1.harmonic_frequencies.length > 0 && (
            <div>
              <div className="text-[10px] text-neutral-500 mb-1">Detected Harmonics</div>
              <div className="flex flex-wrap gap-1">
                {tier1.harmonic_frequencies.map((f, i) => (
                  <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-neutral-800 text-neutral-300 font-mono">
                    H{i + 1}: {f.toFixed(1)} Hz
                  </span>
                ))}
              </div>
            </div>
          )}
        </Section>
      )}

      {/* Tier 2 Results */}
      {tier2 && tier2.candidates && tier2.candidates.length > 0 && (
        <Section title={`Tier 2: Scale Design (${tier2.n_candidates} candidates, ${tier2.total_time_s.toFixed(0)}s)`}>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {tier2.candidates.map((c, i) => (
              <CandidateCard key={i} candidate={c} index={i} tier3Result={tier3} />
            ))}
          </div>
          {tier2.best && (
            <p className="text-xs text-green-400">
              Best: {tier2.best.name} — {tier2.best.intonation_rms_cents.toFixed(2)}¢
            </p>
          )}
        </Section>
      )}

      {/* Tier 3 Results */}
      {tier3 && (
        <Section title="Tier 3: Timbre Matching">
          <Tier3ResultCard tier3={tier3} />
        </Section>
      )}

      {/* Final Geometry */}
      {finalGeo && (
        <Section title="Final Combined Geometry">
          <FinalGeometryCard geometry={finalGeo} />
        </Section>
      )}

      {/* No results yet with analysis */}
      {analysis && !result && phase === "analyzing" && (
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5">
          <p className="text-sm text-neutral-400">
            Analysis complete. Running full design...
          </p>
        </div>
      )}
    </div>
  );
}
