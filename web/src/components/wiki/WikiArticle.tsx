import { useMemo } from "react";
import type { WikiArticle as WikiArticleType } from "../../data/wiki-articles";
import { WIKI_ARTICLES } from "../../data/wiki-articles";

interface WikiArticleProps {
  article: WikiArticleType;
  onNavigate: (articleId: string) => void;
  onBack: () => void;
}

function parseMarkdown(md: string): { headings: { id: string; text: string; level: number }[]; html: string } {
  const headings: { id: string; text: string; level: number }[] = [];
  let html = "";
  const lines = md.split("\n");
  let inCodeBlock = false;
  let inList = false;

  for (const line of lines) {
    if (line.startsWith("```")) {
      if (inList) {
        html += "</ul>";
        inList = false;
      }
      inCodeBlock = !inCodeBlock;
      if (inCodeBlock) {
        html += '<pre class="bg-neutral-900 rounded-lg p-4 my-3 text-sm text-neutral-300 overflow-x-auto font-mono">';
      } else {
        html += "</pre>";
      }
      continue;
    }

    if (inCodeBlock) {
      html += escapeHtml(line) + "\n";
      continue;
    }

    const headingMatch = line.match(/^(#{1,4})\s+(.+)/);
    if (headingMatch) {
      if (inList) {
        html += "</ul>";
        inList = false;
      }
      const level = headingMatch[1].length;
      const text = headingMatch[2].trim();
      const id = text.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/-+$/, "");
      headings.push({ id, text, level });
      const tag = `h${level}`;
      const sizeClass =
        level === 1 ? "text-xl" : level === 2 ? "text-lg" : level === 3 ? "text-base" : "text-sm";
      html += `<${tag} id="${id}" class="font-semibold text-neutral-100 ${sizeClass} mt-6 mb-2 scroll-mt-4">${text}</${tag}>`;
      continue;
    }

    if (line.startsWith("- **")) {
      const match = line.match(/^- \*\*(.+?)\*\*:?\s*(.*)/);
      if (match) {
        html += `<li class="ml-4 mb-1 text-sm text-neutral-300 list-disc"><span class="font-semibold text-neutral-200">${match[1]}</span>${match[2] ? ": " + processInline(match[2]) : ""}</li>`;
        if (!inList) inList = true;
        continue;
      }
    }

    if (line.startsWith("- ")) {
      const text = line.slice(2);
      html += `<li class="ml-4 mb-1 text-sm text-neutral-300 list-disc">${processInline(text)}</li>`;
      if (!inList) inList = true;
      continue;
    }

    if (inList && line.trim() === "") {
      html += "</ul>";
      inList = false;
    }

    if (line.trim() === "") {
      html += "<br/>";
      continue;
    }

    // Table rows
    if (line.startsWith("|")) {
      const cells = line.split("|").filter((c) => c.trim() !== "").map((c) => c.trim());
      if (cells.every((c) => /^[-:]+$/.test(c))) continue; // separator row
      const isHeader = line.includes("**");
      const tag = isHeader ? "th" : "td";
      html += "<tr>" + cells.map((c) => `<${tag} class="px-2 py-1 border border-neutral-700 text-sm text-neutral-300">${processInline(c)}</${tag}>`).join("") + "</tr>";
      continue;
    }

    html += `<p class="text-sm text-neutral-300 mb-2">${processInline(line)}</p>`;
  }

  if (inList) html += "</ul>";
  if (inCodeBlock) html += "</pre>";

  // Wrap table rows
  html = html.replace(/(<tr>.*?<\/tr>\n?)+/g, (match) => `<table class="w-full border-collapse my-3">${match}</table>`);

  return { headings, html };
}

function processInline(text: string): string {
  return text
    .replace(/\*\*(.+?)\*\*/g, '<span class="font-semibold text-neutral-200">$1</span>')
    .replace(/`([^`]+)`/g, '<code class="bg-neutral-900 px-1.5 py-0.5 rounded text-xs text-brand-400 font-mono">$1</code>');
}

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

export function WikiArticle({ article, onNavigate, onBack }: WikiArticleProps) {
  const { headings, html } = useMemo(() => parseMarkdown(article.content), [article.content]);

  const related = useMemo(
    () =>
      article.relatedArticles
        .map((id) => WIKI_ARTICLES.find((a) => a.id === id))
        .filter(Boolean) as WikiArticleType[],
    [article.relatedArticles]
  );

  const difficultyColor =
    article.difficulty === "Beginner"
      ? "bg-green-900/40 text-green-400"
      : article.difficulty === "Intermediate"
      ? "bg-yellow-900/40 text-yellow-400"
      : "bg-red-900/40 text-red-400";

  return (
    <div className="flex h-full">
      {/* Main content */}
      <div className="flex-1 overflow-auto p-8 max-w-3xl">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-xs text-neutral-500 mb-4">
          <button onClick={onBack} className="hover:text-brand-400 transition-colors">
            Wiki
          </button>
          <span>/</span>
          <span>{article.category}</span>
          <span>/</span>
          <span className="text-neutral-400">{article.title}</span>
        </div>

        {/* Title */}
        <h1 className="text-2xl font-bold text-neutral-100 mb-3">{article.title}</h1>

        {/* Meta */}
        <div className="flex items-center gap-3 mb-6">
          <span className={`text-xs px-2 py-0.5 rounded ${difficultyColor}`}>
            {article.difficulty}
          </span>
          <span className="text-xs text-neutral-600">Updated {article.lastUpdated}</span>
          <button className="ml-auto text-xs text-neutral-600 hover:text-brand-400 transition-colors">
            Edit this article
          </button>
        </div>

        {/* Tags */}
        <div className="flex flex-wrap gap-1.5 mb-6">
          {article.tags.map((tag) => (
            <span
              key={tag}
              className="text-[10px] bg-neutral-800 text-neutral-400 px-2 py-0.5 rounded"
            >
              {tag}
            </span>
          ))}
        </div>

        {/* Rendered content */}
        <div
          className="prose-instrument max-w-none"
          dangerouslySetInnerHTML={{ __html: html }}
        />

        {/* Related articles */}
        {related.length > 0 && (
          <div className="mt-10 pt-6 border-t border-neutral-800">
            <h3 className="text-sm font-semibold text-neutral-200 mb-3">Related Articles</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {related.map((r) => (
                <button
                  key={r.id}
                  onClick={() => onNavigate(r.id)}
                  className="text-left bg-neutral-800/50 rounded-lg px-4 py-3 hover:bg-neutral-800 transition-colors group"
                >
                  <div className="text-sm text-neutral-200 group-hover:text-brand-400">
                    {r.title}
                  </div>
                  <div className="text-xs text-neutral-500 mt-0.5">
                    {r.category} · {r.difficulty}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Table of contents sidebar */}
      {headings.length > 0 && (
        <div className="w-56 flex-shrink-0 border-l border-neutral-800 overflow-auto p-4 hidden lg:block">
          <h4 className="text-[10px] font-semibold text-neutral-500 uppercase tracking-wider mb-3">
            On this page
          </h4>
          <nav className="space-y-1">
            {headings.map((h) => (
              <a
                key={h.id}
                href={`#${h.id}`}
                onClick={(e) => {
                  e.preventDefault();
                  document.getElementById(h.id)?.scrollIntoView({ behavior: "smooth", block: "start" });
                }}
                className={`block text-xs text-neutral-400 hover:text-brand-400 transition-colors ${
                  h.level === 1 ? "font-medium" : h.level === 2 ? "ml-3" : "ml-6"
                }`}
              >
                {h.text}
              </a>
            ))}
          </nav>
        </div>
      )}
    </div>
  );
}
