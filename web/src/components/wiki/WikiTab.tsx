import { useState } from "react";
import { WIKI_ARTICLES } from "../../data/wiki-articles";
import { WikiLayout } from "./WikiLayout";
import { WikiIndex } from "./WikiIndex";
import { WikiArticle } from "./WikiArticle";

export function WikiTab() {
  const [selectedArticleId, setSelectedArticleId] = useState<string | null>(null);

  const selectedArticle = selectedArticleId
    ? WIKI_ARTICLES.find((a) => a.id === selectedArticleId) ?? null
    : null;

  return (
    <WikiLayout
      onNavigateArticle={setSelectedArticleId}
      currentArticleId={selectedArticleId ?? undefined}
    >
      {selectedArticle ? (
        <WikiArticle
          article={selectedArticle}
          onNavigate={setSelectedArticleId}
          onBack={() => setSelectedArticleId(null)}
        />
      ) : (
        <WikiIndex onSelectArticle={setSelectedArticleId} />
      )}
    </WikiLayout>
  );
}
