import { useState } from "react";
import { WIKI_ARTICLES, WIKI_CATEGORIES } from "../../data/wiki-articles";
import type { WikiCategory } from "../../data/wiki-articles";
import { WikiSearch } from "./WikiSearch";

interface WikiLayoutProps {
  children: React.ReactNode;
  onNavigateArticle: (articleId: string) => void;
  currentArticleId?: string;
}

export function WikiLayout({ children, onNavigateArticle, currentArticleId }: WikiLayoutProps) {
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});

  const toggleCategory = (cat: string) => {
    setCollapsedCategories((prev) => ({ ...prev, [cat]: !prev[cat] }));
  };

  const articlesByCategory = WIKI_CATEGORIES.map((cat) => ({
    category: cat,
    articles: WIKI_ARTICLES.filter((a) => a.category === cat),
  }));

  const categoryIcon = (cat: WikiCategory) => {
    switch (cat) {
      case "Instruments":
        return "M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2z";
      case "3D Printing":
        return "M19.428 15.428a2 2 0 00-1.022-.547l-2.387-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z";
      case "Acoustics":
        return "M15.536 8.464a5 5 0 010 7.072m2.828-9.9a9 9 0 010 12.728M5.586 15H4a1 1 0 01-1-1v-4a1 1 0 011-1h1.586l4.707-4.707C10.923 3.663 12 4.109 12 5v14c0 .891-1.077 1.337-1.707.707L5.586 15z";
      case "Design":
        return "M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z";
      case "Tuning":
        return "M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z";
    }
  };

  return (
    <div className="flex h-full">
      {/* Left sidebar — category navigation */}
      <aside className="w-56 bg-neutral-900 border-r border-neutral-800 overflow-y-auto flex-shrink-0">
        <div className="p-3 border-b border-neutral-800">
          <WikiSearch articles={WIKI_ARTICLES} onSelect={onNavigateArticle} />
        </div>
        <nav className="p-2">
          {articlesByCategory.map(({ category, articles }) => (
            <div key={category} className="mb-1">
              <button
                onClick={() => toggleCategory(category)}
                className="w-full flex items-center gap-2 px-2 py-1.5 text-xs font-medium text-neutral-400 hover:text-neutral-200 transition-colors rounded"
              >
                <svg
                  className={`w-3.5 h-3.5 transition-transform ${
                    collapsedCategories[category] ? "" : "rotate-90"
                  }`}
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                </svg>
                <svg
                  className="w-3.5 h-3.5 text-neutral-500"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={1.5}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d={categoryIcon(category)} />
                </svg>
                {category}
                <span className="ml-auto text-[10px] text-neutral-600">{articles.length}</span>
              </button>

              {!collapsedCategories[category] && (
                <div className="ml-3 space-y-0.5">
                  {articles.map((a) => (
                    <button
                      key={a.id}
                      onClick={() => onNavigateArticle(a.id)}
                      className={`w-full text-left px-2 py-1 text-xs rounded transition-colors truncate ${
                        currentArticleId === a.id
                          ? "bg-brand-600/20 text-brand-400"
                          : "text-neutral-500 hover:text-neutral-300 hover:bg-neutral-800"
                      }`}
                      title={a.title}
                    >
                      {a.title}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 overflow-hidden flex flex-col">
        <div className="flex-1 overflow-hidden">{children}</div>
      </main>
    </div>
  );
}
