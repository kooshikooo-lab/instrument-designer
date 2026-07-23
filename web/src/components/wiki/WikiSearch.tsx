import { useState, useRef, useEffect, useMemo } from "react";
import type { WikiArticle } from "../../data/wiki-articles";

interface WikiSearchProps {
  articles: WikiArticle[];
  onSelect: (articleId: string) => void;
}

export function WikiSearch({ articles, onSelect }: WikiSearchProps) {
  const [query, setQuery] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const [isOpen, setIsOpen] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);

  const results = useMemo(() => {
    if (!query.trim()) return [];
    const q = query.toLowerCase();
    return articles
      .filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.category.toLowerCase().includes(q) ||
          a.tags.some((t) => t.toLowerCase().includes(q)) ||
          a.content.toLowerCase().includes(q)
      )
      .slice(0, 10);
  }, [query, articles]);

  const grouped = useMemo(() => {
    const groups: Record<string, WikiArticle[]> = {};
    for (const r of results) {
      if (!groups[r.category]) groups[r.category] = [];
      groups[r.category].push(r);
    }
    return groups;
  }, [results]);

  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  useEffect(() => {
    if (!listRef.current) return;
    const item = listRef.current.children[selectedIndex] as HTMLElement;
    if (item) item.scrollIntoView({ block: "nearest" });
  }, [selectedIndex]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      e.preventDefault();
      if (results[selectedIndex]) {
        onSelect(results[selectedIndex].id);
        setIsOpen(false);
        setQuery("");
      }
    } else if (e.key === "Escape") {
      setIsOpen(false);
      inputRef.current?.blur();
    }
  };

  return (
    <div className="relative">
      <div className="relative">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          ref={inputRef}
          type="text"
          placeholder="Search wiki articles..."
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => query.trim() && setIsOpen(true)}
          onBlur={() => setTimeout(() => setIsOpen(false), 200)}
          onKeyDown={handleKeyDown}
          className="w-full bg-neutral-800 border border-neutral-700 rounded-lg pl-9 pr-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:border-brand-500"
        />
      </div>

      {isOpen && results.length > 0 && (
        <div
          ref={listRef}
          className="absolute z-50 mt-1 w-full bg-neutral-800 border border-neutral-700 rounded-lg shadow-xl max-h-80 overflow-y-auto"
        >
          {Object.entries(grouped).map(([category, articles]) => {
            let globalIndex = 0;
            for (const cat of Object.keys(grouped)) {
              if (cat === category) break;
              globalIndex += grouped[cat].length;
            }
            return (
              <div key={category}>
                <div className="px-3 py-1.5 text-[10px] font-semibold text-neutral-500 uppercase tracking-wider bg-neutral-850 sticky top-0">
                  {category}
                </div>
                {articles.map((a) => {
                  const idx = globalIndex++;
                  return (
                    <button
                      key={a.id}
                      onMouseDown={(e) => {
                        e.preventDefault();
                        onSelect(a.id);
                        setIsOpen(false);
                        setQuery("");
                      }}
                      onMouseEnter={() => setSelectedIndex(idx)}
                      className={`w-full text-left px-3 py-2 text-sm transition-colors ${
                        idx === selectedIndex
                          ? "bg-brand-600/20 text-brand-400"
                          : "text-neutral-300 hover:bg-neutral-700"
                      }`}
                    >
                      <div className="font-medium">{a.title}</div>
                      <div className="text-xs text-neutral-500 mt-0.5">
                        {a.subcategory} · {a.difficulty}
                      </div>
                    </button>
                  );
                })}
              </div>
            );
          })}
        </div>
      )}

      {isOpen && query.trim() && results.length === 0 && (
        <div className="absolute z-50 mt-1 w-full bg-neutral-800 border border-neutral-700 rounded-lg shadow-xl p-4 text-center text-sm text-neutral-500">
          No articles found for "{query}"
        </div>
      )}
    </div>
  );
}
