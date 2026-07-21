import { useState, useMemo } from "react";
import { WIKI_ARTICLES, WIKI_CATEGORIES } from "../../data/wiki-articles";
import type { WikiArticle, WikiCategory } from "../../data/wiki-articles";

interface WikiIndexProps {
  onSelectArticle: (articleId: string) => void;
}

export function WikiIndex({ onSelectArticle }: WikiIndexProps) {
  const [search, setSearch] = useState("");
  const [activeCategory, setActiveCategory] = useState<WikiCategory | "">("");

  const filtered = useMemo(() => {
    let articles = WIKI_ARTICLES;
    if (activeCategory) {
      articles = articles.filter((a) => a.category === activeCategory);
    }
    if (search.trim()) {
      const q = search.toLowerCase();
      articles = articles.filter(
        (a) =>
          a.title.toLowerCase().includes(q) ||
          a.category.toLowerCase().includes(q) ||
          a.subcategory.toLowerCase().includes(q) ||
          a.tags.some((t) => t.toLowerCase().includes(q))
      );
    }
    return articles;
  }, [search, activeCategory]);

  const grouped = useMemo(() => {
    const groups: Record<string, WikiArticle[]> = {};
    for (const a of filtered) {
      if (!groups[a.category]) groups[a.category] = [];
      groups[a.category].push(a);
    }
    return groups;
  }, [filtered]);

  const categoryCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const a of WIKI_ARTICLES) {
      counts[a.category] = (counts[a.category] || 0) + 1;
    }
    return counts;
  }, []);

  return (
    <div className="p-6 max-w-5xl space-y-5">
      <div>
        <h2 className="text-lg font-semibold text-neutral-100 mb-1">Knowledge Base</h2>
        <p className="text-sm text-neutral-500">
          {WIKI_ARTICLES.length} articles on instruments, 3D printing, acoustics, and more
        </p>
      </div>

      {/* Search */}
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
          type="text"
          placeholder="Search articles..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full bg-neutral-800 border border-neutral-700 rounded-lg pl-9 pr-3 py-2 text-sm text-neutral-100 placeholder:text-neutral-500 focus:outline-none focus:border-brand-500"
        />
      </div>

      {/* Category pills */}
      <div className="flex flex-wrap gap-2">
        <button
          onClick={() => setActiveCategory("")}
          className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
            activeCategory === ""
              ? "bg-brand-600/30 text-brand-400 border border-brand-600/50"
              : "bg-neutral-800 text-neutral-400 border border-neutral-700 hover:text-neutral-200"
          }`}
        >
          All ({WIKI_ARTICLES.length})
        </button>
        {WIKI_CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setActiveCategory(activeCategory === cat ? "" : cat)}
            className={`text-xs px-3 py-1.5 rounded-full transition-colors ${
              activeCategory === cat
                ? "bg-brand-600/30 text-brand-400 border border-brand-600/50"
                : "bg-neutral-800 text-neutral-400 border border-neutral-700 hover:text-neutral-200"
            }`}
          >
            {cat} ({categoryCounts[cat] || 0})
          </button>
        ))}
      </div>

      {/* Articles grid */}
      {filtered.length === 0 ? (
        <div className="text-center py-16 text-neutral-500 text-sm">
          No articles found. Try a different search or category.
        </div>
      ) : (
        Object.entries(grouped).map(([category, articles]) => (
          <div key={category}>
            <h3 className="text-sm font-semibold text-neutral-200 mb-3 pb-2 border-b border-neutral-800">
              {category}
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
              {articles.map((a) => (
                <ArticleCard key={a.id} article={a} onSelect={onSelectArticle} />
              ))}
            </div>
          </div>
        ))
      )}
    </div>
  );
}

function ArticleCard({
  article,
  onSelect,
}: {
  article: WikiArticle;
  onSelect: (id: string) => void;
}) {
  const difficultyColor =
    article.difficulty === "Beginner"
      ? "bg-green-900/40 text-green-400"
      : article.difficulty === "Intermediate"
      ? "bg-yellow-900/40 text-yellow-400"
      : "bg-red-900/40 text-red-400";

  const categoryIcon =
    article.category === "Instruments"
      ? "M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"
      : article.category === "3D Printing"
      ? "M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z"
      : article.category === "Acoustics"
      ? "M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z"
      : article.category === "Design"
      ? "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
      : "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z";

  return (
    <button
      onClick={() => onSelect(article.id)}
      className="text-left bg-neutral-900 border border-neutral-800 rounded-lg p-4 hover:border-neutral-700 hover:bg-neutral-800/50 transition-all group"
    >
      <div className="flex items-start gap-3">
        <div className="w-8 h-8 rounded bg-neutral-800 flex items-center justify-center flex-shrink-0 group-hover:bg-brand-600/20 transition-colors">
          <svg
            className="w-4 h-4 text-neutral-500 group-hover:text-brand-400 transition-colors"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d={categoryIcon} />
          </svg>
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-neutral-100 group-hover:text-brand-400 transition-colors line-clamp-2">
            {article.title}
          </div>
          <div className="text-xs text-neutral-500 mt-1">{article.subcategory}</div>
          <div className="flex items-center gap-2 mt-2">
            <span className={`text-[10px] px-1.5 py-0.5 rounded ${difficultyColor}`}>
              {article.difficulty}
            </span>
            <span className="text-[10px] text-neutral-600">{article.lastUpdated}</span>
          </div>
        </div>
      </div>
    </button>
  );
}
