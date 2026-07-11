import { INSTRUMENTS } from "../data/instruments";

interface InstrumentDetailProps {
  name: string | null;
  onGenerate: (preset: string) => void;
}

export function InstrumentDetail({ name, onGenerate }: InstrumentDetailProps) {
  const inst = INSTRUMENTS.find((i) => i.name === name);

  if (!inst) {
    return (
      <div className="flex-1 flex items-center justify-center text-neutral-600 text-sm">
        Select an instrument from the library to view details
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-auto p-6 space-y-6">
      <div>
        <h2 className="text-xl font-bold text-neutral-100">{inst.name}</h2>
        <p className="text-sm text-neutral-500 mt-1">{inst.description}</p>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {[
          { label: "Family", value: inst.family },
          { label: "Key", value: inst.key },
          { label: "Range", value: inst.range },
          { label: "Difficulty", value: inst.difficulty },
          { label: "Source", value: inst.source },
          { label: "Category", value: inst.subcategory },
          { label: "Type", value: inst.type_label },
          { label: "Preset", value: inst.demakein_preset || "N/A" },
        ].map(({ label, value }) => (
          <div
            key={label}
            className="bg-neutral-800/50 rounded-lg px-3 py-2 border border-neutral-700/50"
          >
            <div className="text-[10px] text-neutral-500 uppercase tracking-wider">
              {label}
            </div>
            <div className="text-sm text-neutral-200 mt-0.5 capitalize">
              {value}
            </div>
          </div>
        ))}
      </div>

      <div>
        <h3 className="text-xs font-medium text-neutral-500 uppercase tracking-wider mb-2">
          Tags
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {inst.tags.map((tag) => (
            <span
              key={tag}
              className="px-2 py-0.5 bg-neutral-800 border border-neutral-700 rounded-full text-xs text-neutral-300"
            >
              {tag}
            </span>
          ))}
        </div>
      </div>

      <div className="flex gap-3">
        {inst.demakein_preset && (
          <button
            onClick={() => onGenerate(inst.demakein_preset!)}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 text-sm text-white rounded-lg transition-colors font-medium"
          >
            Generate with Demakein
          </button>
        )}
        {inst.download_url && (
          <a
            href={inst.download_url}
            className="px-4 py-2 bg-neutral-800 hover:bg-neutral-700 text-sm text-neutral-100 rounded-lg transition-colors"
          >
            Download STL
          </a>
        )}
      </div>
    </div>
  );
}
