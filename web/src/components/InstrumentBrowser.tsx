import { useState, useMemo } from "react";
import { SUBCATEGORIES, TYPE_LABELS, TAGS } from "../data/instruments";
import type { Instrument } from "../data/instruments";
import { filterInstruments, EMPTY_FILTERS } from "../utils/filters";

interface Props {
  instruments: Instrument[];
  onSelect: (inst: Instrument) => void;
}

export function InstrumentBrowser({ instruments, onSelect }: Props) {
  const [filters, setFilters] = useState(EMPTY_FILTERS);
  const filtered = useMemo(() => filterInstruments(instruments, filters), [instruments, filters]);

  return (
    <div className="p-4 space-y-4">
      <div>
        <h2 className="text-lg font-semibold text-neutral-100 mb-1">Instrument Library</h2>
        <p className="text-sm text-neutral-500">{filtered.length} instruments</p>
      </div>

      <input
        type="text"
        placeholder="Search instruments..."
        value={filters.search}
        onChange={(e) => setFilters((f) => ({ ...f, search: e.target.value }))}
        className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:border-brand-500"
      />

      <div className="grid grid-cols-2 gap-2">
        <select
          value={filters.subcategory}
          onChange={(e) => setFilters((f) => ({ ...f, subcategory: e.target.value }))}
          className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
        >
          <option value="">All Families</option>
          {SUBCATEGORIES.map((s) => <option key={s} value={s}>{s}</option>)}
        </select>
        <select
          value={filters.typeLabel}
          onChange={(e) => setFilters((f) => ({ ...f, typeLabel: e.target.value }))}
          className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
        >
          <option value="">All Types</option>
          {TYPE_LABELS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <select
          value={filters.difficulty}
          onChange={(e) => setFilters((f) => ({ ...f, difficulty: e.target.value }))}
          className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
        >
          <option value="">All Levels</option>
          {["Beginner", "Intermediate", "Advanced", "Expert"].map((d) => <option key={d} value={d}>{d}</option>)}
        </select>
        <select
          value={filters.tag}
          onChange={(e) => setFilters((f) => ({ ...f, tag: e.target.value }))}
          className="bg-neutral-800 border border-neutral-700 rounded-lg px-2 py-1.5 text-xs text-neutral-100 focus:outline-none focus:border-brand-500"
        >
          <option value="">All Tags</option>
          {TAGS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
      </div>

      <div className="space-y-1">
        {filtered.map((inst) => (
          <button
            key={inst.name}
            onClick={() => onSelect(inst)}
            className="w-full text-left px-3 py-2.5 rounded-lg hover:bg-neutral-800 transition-colors group"
          >
            <div className="flex items-start gap-3">
              {inst.image_url ? (
                <img src={inst.image_url} alt="" className="w-10 h-10 rounded object-cover flex-shrink-0" />
              ) : (
                <div className="w-10 h-10 rounded bg-neutral-800 flex items-center justify-center text-neutral-600 text-xs flex-shrink-0">
                  {inst.type_label.charAt(0)}
                </div>
              )}
              <div className="min-w-0">
                <div className="text-sm text-neutral-100 group-hover:text-brand-400 truncate">{inst.name}</div>
                <div className="text-xs text-neutral-500 truncate">{inst.type_label} ┬À {inst.key}</div>
              </div>
              {inst.demakein_preset && (
                <span className="ml-auto text-[10px] bg-brand-600/20 text-brand-400 px-1.5 py-0.5 rounded flex-shrink-0">
                  AUTO
                </span>
              )}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
