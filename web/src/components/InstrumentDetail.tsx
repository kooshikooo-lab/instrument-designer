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

const DIFFICULTY_COLORS: Record<string, string> = {
  Beginner: "bg-green-500/20 text-green-400 border-green-500/30",
  Intermediate: "bg-amber-500/20 text-amber-400 border-amber-500/30",
  Advanced: "bg-orange-500/20 text-orange-400 border-orange-500/30",
  Expert: "bg-red-500/20 text-red-400 border-red-500/30",
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

  return (
    <div className="flex flex-col h-full">
      {/* Hero Header */}
      <div className="relative">
        {i.image_url ? (
          <div className="h-48 overflow-hidden">
            <img
              src={i.image_url}
              alt={i.name}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-neutral-950 via-neutral-950/60 to-transparent" />
          </div>
        ) : (
          <div className="h-32 bg-gradient-to-br from-brand-600/20 via-neutral-900 to-neutral-950" />
        )}

        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/40 backdrop-blur-sm flex items-center justify-center text-neutral-400 hover:text-white hover:bg-black/60 transition-all"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>

        {/* Title overlay */}
        <div className="absolute bottom-0 left-0 right-0 px-6 pb-4">
          <div className="flex items-end gap-3">
            {i.image_url && (
              <div className="w-16 h-16 rounded-xl overflow-hidden border-2 border-neutral-800 shadow-lg flex-shrink-0 -mb-6">
                <img src={i.image_url} alt="" className="w-full h-full object-cover" />
              </div>
            )}
            <div className="flex-1 min-w-0">
              <h2 className="text-xl font-bold text-white truncate">{i.name}</h2>
              <div className="flex items-center gap-2 mt-1">
                <span className="text-xs text-neutral-400">{i.type_label}</span>
                <span className="text-neutral-600">·</span>
                <span className="text-xs text-neutral-400">{i.key}</span>
                <span className="text-neutral-600">·</span>
                <span className="text-xs text-neutral-400">{i.range}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Tab Bar */}
      <div className="flex gap-1 px-6 pt-8 border-b border-neutral-800">
        <button
          onClick={() => setTab("info")}
          className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
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
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
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
          <div className="p-6 space-y-6">
            <p className="text-neutral-300 leading-relaxed">{i.description}</p>

            {/* Quick Stats */}
            <div className="grid grid-cols-2 gap-3">
              <div className="bg-neutral-900 rounded-xl px-4 py-3 border border-neutral-800">
                <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-medium">Range</div>
                <div className="text-sm text-neutral-100 mt-1">{i.range}</div>
              </div>
              <div className="bg-neutral-900 rounded-xl px-4 py-3 border border-neutral-800">
                <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-medium">Key</div>
                <div className="text-sm text-neutral-100 mt-1">{i.key}</div>
              </div>
              <div className="bg-neutral-900 rounded-xl px-4 py-3 border border-neutral-800">
                <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-medium">Difficulty</div>
                <div className="mt-1.5">
                  <span className={`text-xs px-2.5 py-1 rounded-lg border ${DIFFICULTY_COLORS[i.difficulty] || ""}`}>
                    {i.difficulty}
                  </span>
                </div>
              </div>
              <div className="bg-neutral-900 rounded-xl px-4 py-3 border border-neutral-800">
                <div className="text-[10px] text-neutral-500 uppercase tracking-wider font-medium">Source</div>
                <div className="text-sm text-neutral-100 mt-1 truncate">{i.source}</div>
              </div>
            </div>

            {/* Tags */}
            <div className="flex flex-wrap gap-1.5">
              {i.tags.map((tag) => (
                <span key={tag} className="text-[11px] bg-neutral-800/80 text-neutral-400 px-2.5 py-1 rounded-full border border-neutral-700/50">
                  {tag}
                </span>
              ))}
            </div>

            {/* Actions */}
            <div className="flex gap-3 flex-wrap">
              {i.download_url && (
                <a
                  href={i.download_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-100 rounded-lg transition-colors border border-neutral-700"
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
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-100 rounded-lg transition-colors border border-neutral-700"
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
                  className="inline-flex items-center gap-2 px-4 py-2.5 bg-brand-600 hover:bg-brand-500 text-sm text-white rounded-lg transition-colors font-medium"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  Generate This Instrument
                </button>
              )}
            </div>

            <TonePlayer range={i.range} instrumentName={i.name} />

            {/* AI Instrument Illustration */}
            <div>
              <h4 className="text-xs font-medium text-neutral-400 mb-3 flex items-center gap-2">
                <span className="w-5 h-5 rounded bg-purple-500/20 flex items-center justify-center text-[10px]">🎨</span>
                AI-Generated Cross-Section
              </h4>
              <AIInstrumentArt instrumentName={i.name} className="w-full h-64" />
            </div>

            {/* Sound Preview */}
            <InstrumentSoundPlayer instrumentName={i.name} range={i.range} />
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
