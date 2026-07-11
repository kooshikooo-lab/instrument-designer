import type { Instrument } from "../data/instruments";

interface Props {
  instrument: Instrument;
  onClose: () => void;
  onGenerate: (preset: string) => void;
}

const DIFFICULTY_COLORS: Record<string, string> = {
  Beginner: "bg-green-600/20 text-green-400",
  Intermediate: "bg-yellow-600/20 text-yellow-400",
  Advanced: "bg-orange-600/20 text-orange-400",
  Expert: "bg-red-600/20 text-red-400",
};

export function InstrumentDetail({ instrument, onClose, onGenerate }: Props) {
  const i = instrument;

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-start gap-4">
        <button onClick={onClose} className="text-neutral-500 hover:text-neutral-300 mt-1">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
        <div className="flex-1">
          <h2 className="text-2xl font-bold text-neutral-100">{i.name}</h2>
          <p className="text-sm text-neutral-400 mt-1">{i.type_label}</p>
        </div>
      </div>

      {i.image_url && (
        <a href={i.image_url} target="_blank" rel="noopener noreferrer">
          <img
            src={i.image_url}
            alt={i.name}
            className="w-full max-h-80 object-cover rounded-xl border border-neutral-800"
          />
        </a>
      )}

      <p className="text-neutral-300 leading-relaxed">{i.description}</p>

      <div className="grid grid-cols-2 gap-3">
        <div className="bg-neutral-800/50 rounded-lg px-4 py-3">
          <div className="text-xs text-neutral-500 uppercase tracking-wider">Range</div>
          <div className="text-sm text-neutral-100 mt-1">{i.range}</div>
        </div>
        <div className="bg-neutral-800/50 rounded-lg px-4 py-3">
          <div className="text-xs text-neutral-500 uppercase tracking-wider">Key</div>
          <div className="text-sm text-neutral-100 mt-1">{i.key}</div>
        </div>
        <div className="bg-neutral-800/50 rounded-lg px-4 py-3">
          <div className="text-xs text-neutral-500 uppercase tracking-wider">Difficulty</div>
          <div className="mt-1">
            <span className={`text-xs px-2 py-0.5 rounded ${DIFFICULTY_COLORS[i.difficulty] || ""}`}>
              {i.difficulty}
            </span>
          </div>
        </div>
        <div className="bg-neutral-800/50 rounded-lg px-4 py-3">
          <div className="text-xs text-neutral-500 uppercase tracking-wider">Source</div>
          <div className="text-sm text-neutral-100 mt-1">{i.source}</div>
        </div>
      </div>

      <div className="flex flex-wrap gap-2">
        {i.tags.map((tag) => (
          <span key={tag} className="text-xs bg-neutral-800 text-neutral-400 px-2 py-1 rounded-full">
            {tag}
          </span>
        ))}
      </div>

      <div className="flex gap-3 flex-wrap">
        {i.download_url && (
          <a
            href={i.download_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-100 rounded-lg transition-colors"
          >
            Download STL
          </a>
        )}
        {i.audio_url && (
          <a
            href={i.audio_url}
            target="_blank"
            rel="noopener noreferrer"
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-100 rounded-lg transition-colors"
          >
            Listen
          </a>
        )}
        {i.demakein_preset && (
          <button
            onClick={() => onGenerate(i.demakein_preset!)}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-sm text-white rounded-lg transition-colors font-medium"
          >
            Generate This Instrument
          </button>
        )}
      </div>
    </div>
  );
}
