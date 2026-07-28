import { useState, useEffect, type ReactNode } from "react";
import { MATERIALS, type BorePoint } from "./InstrumentModel";
import InstrumentModel from "./InstrumentModel";
import { generativeSuggest, generativeRandom, generativeHybrid, getGenerativeKnowledge } from "../utils/api";
import type { GenerativeResult, GenerativeCandidate, KnowledgeBase } from "../utils/api";

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

function CandidateCard({
  candidate,
  index,
}: {
  candidate: GenerativeCandidate;
  index: number;
}) {
  const material = MATERIALS[candidate.material as keyof typeof MATERIALS] || MATERIALS.brass;
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
      {/* 3D Preview */}
      <div className="h-48">
        <InstrumentModel
          boreProfile={boreProfile}
          holes={holes}
          material={material}
          showHoles
          height={192}
        />
      </div>

      {/* Info */}
      <div className="p-4 space-y-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-2">
            <span className="text-xs text-neutral-600 font-mono">#{index + 1}</span>
            <h4 className="text-sm font-medium text-neutral-100">
              {candidate.name}
            </h4>
            <p className="text-xs text-neutral-500 mt-0.5">{candidate.description}</p>
          </div>
          <span className={`text-xs px-2 py-0.5 rounded-full font-mono ${
            candidate.feasibility === "known" ? "bg-green-900/30 text-green-400" :
            candidate.feasibility === "moderate" ? "bg-yellow-900/30 text-yellow-400" :
            candidate.feasibility === "hard" ? "bg-orange-900/30 text-orange-400" :
            "bg-purple-900/30 text-purple-400"
          }`}>
            {candidate.feasibility}
          </span>
        </div>

        {/* Specs */}
        <div className="grid grid-cols-2 gap-2 text-[10px] font-mono">
          <Spec label="Bore" value={`${candidate.bore_type} (${candidate.bore_radius_mm.toFixed(1)}mm)`} />
          <Spec label="Material" value={candidate.material} />
          <Spec label="Scale" value={candidate.scale} />
          <Spec label="Closed top" value={String(candidate.closed_top)} />
          <Spec label="Holes" value={String(candidate.hole_positions_mm.length)} />
          <Spec label="Length" value={`${candidate.bore_length_mm.toFixed(0)}mm`} />
        </div>

        {/* Scores */}
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
              {candidate.timbre_cost < 1e5
                ? candidate.timbre_cost.toFixed(6)
                : "—"}
            </span>
          </div>
          <div>
            <span className="text-neutral-500">Time: </span>
            <span className="font-mono text-neutral-300">{candidate.opt_time_s.toFixed(1)}s</span>
          </div>
        </div>

        {/* LLM Reasoning */}
        {candidate.llm_reasoning && (
          <div className="bg-neutral-900 rounded-lg p-3 text-[10px] text-neutral-400 italic leading-relaxed">
            {candidate.llm_reasoning}
          </div>
        )}

        {/* Pareto front mini-view */}
        {candidate.pareto_front && candidate.pareto_front.length > 1 && (
          <div className="bg-neutral-900 rounded-lg p-2">
            <div className="text-[9px] text-neutral-500 mb-1">Pareto front ({candidate.pareto_front.length} points)</div>
            <div className="flex items-end gap-[2px] h-12">
              {candidate.pareto_front.map((pt, i) => {
                const h = Math.min(100, Math.max(10, 100 - pt.intonation * 10));
                return (
                  <div
                    key={i}
                    className="flex-1 rounded-t-sm bg-brand-600/60 hover:bg-brand-500 transition-colors cursor-pointer relative group"
                    style={{ height: `${h}%` }}
                    title={`Intl: ${pt.intonation.toFixed(2)}¢, Timbre: ${pt.timbre.toFixed(6)}`}
                  />
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Spec({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between bg-neutral-900 rounded px-2 py-1">
      <span className="text-neutral-500">{label}</span>
      <span className="text-neutral-300">{value}</span>
    </div>
  );
}

function HybridExplorer({
  knowledge,
  onGenerate,
}: {
  knowledge: KnowledgeBase | null;
  onGenerate: (mouthpiece: string, body: string) => void;
}) {
  if (!knowledge) return null;

  return (
    <Section title="Hybrid Explorer" defaultOpen={false}>
      <p className="text-xs text-neutral-500">
        Combine mouthpiece and body from different instrument families.
      </p>
      <div className="grid gap-3">
        {knowledge.hybrids.map((hybrid) => (
          <button
            key={hybrid.name}
            onClick={() => onGenerate(hybrid.mouthpiece_family, hybrid.body_family)}
            className="w-full text-left bg-neutral-950 rounded-lg border border-neutral-800 p-3 hover:border-brand-600 transition-colors"
          >
            <div className="flex items-center justify-between mb-1">
              <h4 className="text-sm font-medium text-neutral-200">{hybrid.name}</h4>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${
                hybrid.feasibility === "moderate" ? "bg-yellow-900/30 text-yellow-400" :
                hybrid.feasibility === "easy" ? "bg-green-900/30 text-green-400" :
                "bg-purple-900/30 text-purple-400"
              }`}>
                {hybrid.feasibility}
              </span>
            </div>
            <p className="text-[10px] text-neutral-500 mb-2">{hybrid.description}</p>
            <div className="flex flex-wrap gap-1">
              {hybrid.challenges.slice(0, 3).map((c, i) => (
                <span key={i} className="text-[9px] px-1.5 py-0.5 rounded bg-neutral-900 text-neutral-400">
                  {c.length > 40 ? c.slice(0, 40) + "…" : c}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>
    </Section>
  );
}

function ScaleSelector({
  scales,
  onSelect,
}: {
  scales: string[];
  onSelect: (scale: string) => void;
}) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {scales.map((s) => (
        <button
          key={s}
          onClick={() => onSelect(s)}
          className="text-[10px] px-2 py-1 rounded-lg bg-neutral-800 hover:bg-neutral-700 text-neutral-300 transition-colors"
        >
          {s.replace(/_/g, " ")}
        </button>
      ))}
    </div>
  );
}

// ═══════════════════════════════════════════════════════════════════════
// Main Generative Tab
// ═══════════════════════════════════════════════════════════════════════

export default function GenerativeTab() {
  const [query, setQuery] = useState("");
  const [nCandidates, setNCandidates] = useState(3);
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<GenerativeResult | null>(null);
  const [knowledge, setKnowledge] = useState<KnowledgeBase | null>(null);
  const [activeTab, setActiveTab] = useState<"suggest" | "hybrid" | "random">("suggest");

  useEffect(() => {
    getGenerativeKnowledge()
      .then(setKnowledge)
      .catch(() => {});
  }, []);

  const handleSuggest = async () => {
    if (!query.trim()) return;
    setRunning(true);
    try {
      const res = await generativeSuggest(query, nCandidates);
      setResult(res);
    } catch (e) {
      console.error("Generative suggest failed:", e);
    } finally {
      setRunning(false);
    }
  };

  const handleRandom = async () => {
    setRunning(true);
    try {
      const res = await generativeRandom();
      setResult(res);
    } catch (e) {
      console.error("Generative random failed:", e);
    } finally {
      setRunning(false);
    }
  };

  const handleHybrid = async (mouthpiece: string, body: string) => {
    setRunning(true);
    setActiveTab("hybrid");
    try {
      const res = await generativeHybrid(mouthpiece, body);
      setResult(res);
    } catch (e) {
      console.error("Hybrid design failed:", e);
    } finally {
      setRunning(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSuggest();
    }
  };

  return (
    <div className="p-6 max-w-6xl space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-lg font-semibold text-neutral-100">Generative Instrument Designer</h2>
        <p className="text-sm text-neutral-500">
          AI-guided instrument design with physics-based Pareto optimization
        </p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-neutral-900 rounded-xl p-1 border border-neutral-800">
        {([
          { key: "suggest", label: "Design by Prompt" },
          { key: "hybrid", label: "Hybrid Explorer" },
          { key: "random", label: "Random Design" },
        ] as const).map((tab) => (
          <button
            key={tab.key}
            onClick={() => {
              setActiveTab(tab.key);
              if (tab.key === "random") setResult(null);
            }}
            className={`flex-1 px-4 py-2 text-sm rounded-lg transition-colors ${
              activeTab === tab.key
                ? "bg-brand-600 text-white"
                : "text-neutral-400 hover:text-neutral-200"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Design by Prompt */}
      {activeTab === "suggest" && (
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5 space-y-4">
          <h3 className="text-sm font-medium text-neutral-200">Design Prompt</h3>
          <p className="text-xs text-neutral-500">
            Describe the instrument you want to design. Be specific about family, bore type, tuning system, or features.
          </p>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder='e.g. "quarter-tone bass clarinet with conical bore and microtonal scale"'
            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-4 py-3 text-sm text-neutral-100 focus:outline-none focus:border-brand-500 resize-none h-20"
          />
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-xs text-neutral-500">Candidates:</label>
              <input
                type="number"
                min={1}
                max={5}
                value={nCandidates}
                onChange={(e) => setNCandidates(Number(e.target.value))}
                className="w-16 bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-sm text-neutral-100 focus:outline-none focus:border-brand-500 text-center"
              />
            </div>
            <button
              onClick={handleSuggest}
              disabled={!query.trim() || running}
              className="px-6 py-2 bg-brand-600 hover:bg-brand-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-lg transition-colors font-medium"
            >
              {running ? "Optimizing..." : "Generate & Optimize"}
            </button>
            {result && (
              <span className="text-xs text-neutral-500">
                {result.n_candidates} candidates • {result.total_time_s.toFixed(0)}s
                {result.llm_used ? " • LLM guided" : " • Physics engine"}
              </span>
            )}
          </div>
        </div>
      )}

      {/* Hybrid Explorer */}
      {activeTab === "hybrid" && (
        <HybridExplorer knowledge={knowledge} onGenerate={handleHybrid} />
      )}

      {/* Random */}
      {activeTab === "random" && (
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5 space-y-4 text-center">
          <p className="text-sm text-neutral-400">
            Generate a completely novel, randomly designed instrument with Pareto optimization.
          </p>
          <button
            onClick={handleRandom}
            disabled={running}
            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-brand-600 hover:from-purple-500 hover:to-brand-500 disabled:from-neutral-800 disabled:to-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-xl transition-all font-medium"
          >
            {running ? "Generating..." : "🎲 Random Instrument"}
          </button>
        </div>
      )}

      {/* LLM reasoning */}
      {result?.llm_response && (
        <div className="bg-neutral-900 border border-neutral-800 rounded-xl p-5">
          <h3 className="text-sm font-medium text-neutral-200 mb-2">LLM Design Reasoning</h3>
          <p className="text-xs text-neutral-400 italic leading-relaxed">{result.llm_response}</p>
        </div>
      )}

      {/* Scale selector (when scales known) */}
      {knowledge && activeTab === "suggest" && (
        <Section title="Available Scales" defaultOpen={false}>
          <ScaleSelector
            scales={knowledge.scales}
            onSelect={(s) => setQuery((q) => `${q} use ${s} scale`.trim())}
          />
        </Section>
      )}

      {/* Results grid */}
      {result && result.candidates.length > 0 && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-medium text-neutral-200">
              Results ({result.candidates.length} candidates)
            </h3>
            {result.best && (
              <span className="text-xs text-green-400 font-mono">
                Best: {result.best.name} — {result.best.intonation_rms_cents.toFixed(2)}¢
              </span>
            )}
          </div>
          <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
            {result.candidates.map((c, i) => (
              <CandidateCard key={i} candidate={c} index={i} />
            ))}
          </div>
        </div>
      )}

      {/* Knowledge explorer */}
      {knowledge && (
        <Section title="Instrument Knowledge Base" defaultOpen={false}>
          <div className="grid grid-cols-2 gap-4 max-h-96 overflow-y-auto">
            {Object.entries(knowledge.families).map(([key, fam]) => (
              <div key={key} className="bg-neutral-950 rounded-lg p-3 border border-neutral-800">
                <h4 className="text-sm font-medium text-neutral-200 mb-1">{fam.family}</h4>
                <p className="text-[10px] text-neutral-500 mb-2">{fam.description}</p>
                <div className="flex flex-wrap gap-1">
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-neutral-900 text-neutral-400">
                    {fam.bore_type}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-neutral-900 text-neutral-400">
                    {fam.excitation}
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-neutral-900 text-neutral-400">
                    {fam.closed_top ? "closed" : "open"} top
                  </span>
                  <span className="text-[9px] px-1.5 py-0.5 rounded bg-neutral-900 text-neutral-400">
                    {fam.typical_hole_count[0]}-{fam.typical_hole_count[1]} holes
                  </span>
                </div>
              </div>
            ))}
          </div>
        </Section>
      )}
    </div>
  );
}
