import { useState, useMemo } from "react";
import {
  INSTRUMENTS,
  SUBCATEGORIES,
  TYPE_LABELS,
  TAGS,
  DIFFICULTIES,
} from "../data/instruments";
import { filterInstruments } from "../utils/filters";

interface InstrumentBrowserProps {
  onSelect: (name: string) => void;
  selectedName: string | null;
}

export function InstrumentBrowser({
  onSelect,
  selectedName,
}: InstrumentBrowserProps) {
  const [search, setSearch] = useState("");
  const [subcategory, setSubcategory] = useState("");
  const [typeLabel, setTypeLabel] = useState("");
  const [difficulty, setDifficulty] = useState("");
  const [tags, setTags] = useState<string[]>([]);

  const filtered = useMemo(
    () =>
      filterInstruments(INSTRUMENTS, {
        search,
        subcategory,
        typeLabel,
        difficulty,
        tags,
      }),
    [search, subcategory, typeLabel, difficulty, tags]
  );

  const toggleTag = (tag: string) => {
    setTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  return (
    <div className="w-80 border-r border-neutral-800 flex flex-col bg-neutral-900/30">
      <div className="p-3 border-b border-neutral-800 space-y-2">
        <input
          type="text"
          placeholder="Search instruments..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 placeholder-neutral-500 focus:outline-none focus:border-brand-500"
        />
        <div className="grid grid-cols-2 gap-2">
          <select
            value={subcategory}
            onChange={(e) => setSubcategory(e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Types</option>
            {SUBCATEGORIES.map((s) => (
              <option key={s} value={s}>
                {s}
              </option>
            ))}
          </select>
          <select
            value={typeLabel}
            onChange={(e) => setTypeLabel(e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Families</option>
            {Object.entries(TYPE_LABELS).map(([k, v]) => (
              <option key={k} value={k}>
                {v}
              </option>
            ))}
          </select>
          <select
            value={difficulty}
            onChange={(e) => setDifficulty(e.target.value)}
            className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
          >
            <option value="">All Levels</option>
            {DIFFICULTIES.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>
        <div className="flex flex-wrap gap-1">
          {TAGS.slice(0, 8).map((tag) => (
            <button
              key={tag}
              onClick={() => toggleTag(tag)}
              className={`px-2 py-0.5 rounded-full text-[10px] border transition-colors ${
                tags.includes(tag)
                  ? "bg-brand-600 border-brand-500 text-white"
                  : "bg-neutral-800 border-neutral-700 text-neutral-400 hover:border-neutral-500"
              }`}
            >
              {tag}
            </button>
          ))}
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        {filtered.length === 0 ? (
          <div className="p-4 text-center text-neutral-500 text-sm">
            No instruments match your filters.
          </div>
        ) : (
          filtered.map((inst) => (
            <button
              key={inst.name}
              onClick={() => onSelect(inst.name)}
              className={`w-full text-left px-3 py-2.5 border-b border-neutral-800/50 hover:bg-neutral-800/50 transition-colors ${
                selectedName === inst.name ? "bg-brand-950/30" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-medium text-neutral-100 truncate">
                    {inst.name}
                  </div>
                  <div className="text-xs text-neutral-500 mt-0.5">
                    {inst.family} &middot; {inst.key}
                  </div>
                </div>
                <span
                  className={`px-1.5 py-0.5 rounded text-[10px] font-medium shrink-0 ${
                    inst.difficulty === "beginner"
                      ? "bg-green-900/50 text-green-400"
                      : inst.difficulty === "intermediate"
                      ? "bg-yellow-900/50 text-yellow-400"
                      : "bg-red-900/50 text-red-400"
                  }`}
                >
                  {inst.difficulty}
                </span>
              </div>
            </button>
          ))
        )}
      </div>

      <div className="px-3 py-2 border-t border-neutral-800 text-xs text-neutral-500">
        {filtered.length} of {INSTRUMENTS.length} instruments
      </div>
    </div>
  );
}
