import { useState } from "react";
import type { Instrument } from "../data/instruments";
import TonePlayer from "./TonePlayer";
import ResourcePage from "./ResourcePage";
import AIInstrumentArt from "./AIInstrumentArt";
import InstrumentSoundPlayer from "./InstrumentSoundPlayer";

interface Props {
  instrument: Instrument;
  onClose: () => void;
  onGenerate: (preset: string) => void;
}

type DetailTab = "info" | "resources";

export function InstrumentDetail({ instrument, onClose, onGenerate }: Props) {
  const [tab, setTab] = useState<DetailTab>("info");
  const i = instrument;
  const hasResources = i.resources && (
    (i.resources.tips && i.resources.tips.length > 0) ||
    (i.resources.build_notes && i.resources.build_notes.length > 0) ||
    (i.resources.illustrations && i.resources.illustrations.length > 0) ||
    (i.resources.links && i.resources.links.length > 0) ||
    (i.resources.faq && i.resources.faq.length > 0)
  );

  return (
    <div className="flex flex-col h-full bg-neutral-950">
      {/* Wiki Header */}
      <div className="px-6 py-4 border-b border-neutral-800 bg-neutral-950">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="font-mono text-xs text-neutral-600 mb-1">INSTRUMENT / {i.type_label.toUpperCase()}</div>
            <h1 className="text-xl font-mono font-bold text-neutral-100">{i.name}</h1>
            <p className="text-xs text-neutral-500 mt-1 font-mono">{i.description}</p>
          </div>
          <button
            onClick={onClose}
            className="flex-shrink-0 w-8 h-8 border border-neutral-700 rounded flex items-center justify-center text-neutral-500 hover:text-white hover:border-neutral-500 transition-all font-mono text-xs"
          >
            ✕
          </button>
        </div>

        {/* Metadata bar */}
        <div className="flex gap-6 mt-4 font-mono text-xs">
          <div>
            <span className="text-neutral-600">difficulty: </span>
            <span className="text-neutral-300">{i.difficulty.toLowerCase()}</span>
          </div>
          <div>
            <span className="text-neutral-600">key: </span>
            <span className="text-neutral-300">{i.key}</span>
          </div>
          <div>
            <span className="text-neutral-600">range: </span>
            <span className="text-neutral-300">{i.range}</span>
          </div>
          <div>
            <span className="text-neutral-600">source: </span>
            <span className="text-neutral-300">{i.source}</span>
          </div>
        </div>

        {/* Tags */}
        <div className="flex gap-2 mt-3">
          {i.tags.map((tag) => (
            <span key={tag} className="font-mono text-[10px] text-neutral-500 border border-neutral-800 px-2 py-0.5 rounded">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-0 px-6 border-b border-neutral-800 bg-neutral-950 font-mono text-xs">
        <button
          onClick={() => setTab("info")}
          className={`px-4 py-2.5 border-b-2 transition-colors ${
            tab === "info"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-neutral-600 hover:text-neutral-400"
          }`}
        >
          overview
        </button>
        {hasResources && (
          <button
            onClick={() => setTab("resources")}
            className={`px-4 py-2.5 border-b-2 transition-colors ${
              tab === "resources"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-neutral-600 hover:text-neutral-400"
            }`}
          >
            resources
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {tab === "info" && (
          <div className="p-6 space-y-6">
            {/* Actions */}
            <div className="flex gap-3 flex-wrap">
              {i.download_url && (
                <a
                  href={i.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-500 text-xs text-white font-mono rounded transition-colors"
                >
                  ↓ download STL
                </a>
              )}
              {i.audio_url && (
                <a
                  href={i.audio_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2 border border-neutral-700 hover:border-neutral-500 text-xs text-neutral-300 font-mono rounded transition-colors"
                >
                  ▶ listen
                </a>
              )}
              {i.demakein_preset && (
                <button
                  onClick={() => onGenerate(i.demakein_preset!)}
                  className="inline-flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-xs text-white font-mono rounded transition-colors"
                >
                  ⚡ generate
                </button>
              )}
            </div>

            {/* AI Art */}
            <div>
              <div className="font-mono text-xs text-neutral-600 mb-2 border-b border-neutral-800 pb-1">// cross-section illustration</div>
              <AIInstrumentArt instrumentName={i.name} className="w-full h-64 rounded border border-neutral-800" />
            </div>

            {/* Sound Player */}
            <div>
              <div className="font-mono text-xs text-neutral-600 mb-2 border-b border-neutral-800 pb-1">// sound preview</div>
              <InstrumentSoundPlayer range={i.range} />
            </div>

            {/* Tone Player */}
            <div>
              <div className="font-mono text-xs text-neutral-600 mb-2 border-b border-neutral-800 pb-1">// interactive tone generator</div>
              <TonePlayer range={i.range} instrumentName={i.name} />
            </div>
          </div>
        )}

        {tab === "resources" && i.resources && (
          <div className="p-6">
            <ResourcePage resources={i.resources} instrumentName={i.name} />
          </div>
        )}
      </div>
    </div>
  );
}
