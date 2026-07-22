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

const DIFFICULTY_CONFIG: Record<string, { color: string; bg: string }> = {
  Beginner: { color: "text-green-400", bg: "bg-green-500" },
  Intermediate: { color: "text-amber-400", bg: "bg-amber-500" },
  Advanced: { color: "text-orange-400", bg: "bg-orange-500" },
  Expert: { color: "text-red-400", bg: "bg-red-500" },
};

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

  const diffConfig = DIFFICULTY_CONFIG[i.difficulty] || DIFFICULTY_CONFIG.Intermediate;

  return (
    <div className="flex flex-col h-full">
      {/* Magazine Hero Header */}
      <div className="relative bg-gradient-to-br from-neutral-900 via-neutral-950 to-black">
        {i.image_url && (
          <>
            <img
              src={i.image_url}
              alt={i.name}
              className="absolute inset-0 w-full h-full object-cover opacity-20"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/80 to-neutral-950/40" />
          </>
        )}

        {/* Close */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 z-10 w-10 h-10 rounded-full bg-black/30 backdrop-blur-md flex items-center justify-center text-neutral-400 hover:text-white hover:bg-black/50 transition-all"
        >
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Content */}
        <div className="relative px-8 pt-10 pb-8">
          <div className="flex items-center gap-3 mb-4">
            <span className={`w-2 h-2 rounded-full ${diffConfig.bg}`} />
            <span className="text-xs font-medium text-neutral-400 uppercase tracking-widest">{i.difficulty}</span>
            <span className="text-neutral-600">·</span>
            <span className="text-xs text-neutral-500">{i.type_label}</span>
          </div>

          <h1 className="text-3xl font-bold text-white mb-3 tracking-tight">{i.name}</h1>

          <p className="text-neutral-400 text-sm leading-relaxed max-w-2xl">{i.description}</p>

          {/* Quick Stats */}
          <div className="flex gap-6 mt-6">
            <div>
              <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-medium">Key</div>
              <div className="text-lg font-bold text-white mt-0.5">{i.key}</div>
            </div>
            <div>
              <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-medium">Range</div>
              <div className="text-lg font-bold text-white mt-0.5">{i.range}</div>
            </div>
            <div>
              <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-medium">Source</div>
              <div className="text-lg font-bold text-white mt-0.5">{i.source}</div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 px-8 border-b border-neutral-800 bg-neutral-950">
        <button
          onClick={() => setTab("info")}
          className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
            tab === "info"
              ? "border-brand-500 text-brand-400"
              : "border-transparent text-neutral-500 hover:text-neutral-300"
          }`}
        >
          Overview
        </button>
        {hasResources && (
          <button
            onClick={() => setTab("resources")}
            className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
              tab === "resources"
                ? "border-brand-500 text-brand-400"
                : "border-transparent text-neutral-500 hover:text-neutral-300"
            }`}
          >
            Resources
          </button>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-auto">
        {tab === "info" && (
          <div className="p-8 space-y-8">
            {/* Tags */}
            <div className="flex flex-wrap gap-2">
              {i.tags.map((tag) => (
                <span key={tag} className="text-xs bg-neutral-800/80 text-neutral-400 px-3 py-1.5 rounded-full border border-neutral-700/50">
                  {tag}
                </span>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-4 flex-wrap">
              {i.download_url && (
                <a
                  href={i.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2.5 px-6 py-3 bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-500 hover:to-brand-400 text-sm text-white rounded-xl transition-all font-medium shadow-lg shadow-brand-600/20"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  Download STL
                </a>
              )}
              {i.audio_url && (
                <a
                  href={i.audio_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2.5 px-6 py-3 bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-100 rounded-xl transition-colors border border-neutral-700"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Listen
                </a>
              )}
              {i.demakein_preset && (
                <button
                  onClick={() => onGenerate(i.demakein_preset!)}
                  className="inline-flex items-center gap-2.5 px-6 py-3 bg-gradient-to-r from-green-600 to-emerald-600 hover:from-green-500 hover:to-emerald-500 text-sm text-white rounded-xl transition-all font-medium shadow-lg shadow-green-600/20"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Generate This Instrument
                </button>
              )}
            </div>

            {/* AI Art */}
            <div>
              <h3 className="text-sm font-bold text-neutral-200 mb-4 flex items-center gap-2">
                <span className="w-6 h-6 rounded-lg bg-purple-500/20 flex items-center justify-center text-xs">🎨</span>
                AI-Generated Cross-Section
              </h3>
              <AIInstrumentArt instrumentName={i.name} className="w-full h-72 rounded-2xl" />
            </div>

            {/* Sound Player */}
            <div>
              <h3 className="text-sm font-bold text-neutral-200 mb-4 flex items-center gap-2">
                <span className="w-6 h-6 rounded-lg bg-brand-500/20 flex items-center justify-center text-xs">🎵</span>
                Sound Preview
              </h3>
              <InstrumentSoundPlayer range={i.range} />
            </div>

            <TonePlayer range={i.range} instrumentName={i.name} />
          </div>
        )}

        {tab === "resources" && i.resources && (
          <div className="p-8">
            <ResourcePage resources={i.resources} instrumentName={i.name} />
          </div>
        )}
      </div>
    </div>
  );
}
