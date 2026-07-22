import { useState } from "react";
import type { InstrumentResources } from "../data/instruments";

interface Props {
  resources: InstrumentResources;
  instrumentName: string;
}

const LINK_TYPE_CONFIG: Record<string, { icon: string; color: string; bg: string }> = {
  video: { icon: "▶", color: "text-red-400", bg: "bg-red-500/10 border-red-500/20" },
  book: { icon: "📖", color: "text-blue-400", bg: "bg-blue-500/10 border-blue-500/20" },
  tutorial: { icon: "🔨", color: "text-green-400", bg: "bg-green-500/10 border-green-500/20" },
  article: { icon: "📄", color: "text-amber-400", bg: "bg-amber-500/10 border-amber-500/20" },
  forum: { icon: "💬", color: "text-purple-400", bg: "bg-purple-500/10 border-purple-500/20" },
  shop: { icon: "🛒", color: "text-orange-400", bg: "bg-orange-500/10 border-orange-500/20" },
  other: { icon: "🔗", color: "text-neutral-400", bg: "bg-neutral-500/10 border-neutral-500/20" },
};

export default function ResourcePage({ resources, instrumentName }: Props) {
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmitFeedback = () => {
    if (!feedbackText.trim()) return;
    setSubmitted(true);
    setFeedbackText("");
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <div className="space-y-8">
      {/* Tips as highlighted cards */}
      {resources.tips && resources.tips.length > 0 && (
        <section>
          <h3 className="text-xs font-bold text-amber-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded bg-amber-500/20 flex items-center justify-center text-sm">💡</span>
            Tips & Tricks
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {resources.tips.map((tip, idx) => (
              <div
                key={idx}
                className="group relative bg-gradient-to-br from-amber-500/5 to-transparent border border-amber-500/10 rounded-xl px-4 py-3.5 hover:border-amber-500/30 transition-all duration-200"
              >
                <div className="absolute top-3 right-3 text-amber-500/20 text-2xl font-bold group-hover:text-amber-500/40 transition-colors">
                  {String(idx + 1).padStart(2, "0")}
                </div>
                <p className="text-sm text-neutral-300 pr-8 leading-relaxed">{tip}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Build Notes as timeline */}
      {resources.build_notes && resources.build_notes.length > 0 && (
        <section>
          <h3 className="text-xs font-bold text-blue-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded bg-blue-500/20 flex items-center justify-center text-sm">🔧</span>
            Build Notes
          </h3>
          <div className="relative pl-6">
            <div className="absolute left-2 top-2 bottom-2 w-px bg-gradient-to-b from-blue-500/40 via-blue-500/20 to-transparent" />
            <div className="space-y-4">
              {resources.build_notes.map((note, idx) => (
                <div key={idx} className="relative">
                  <div className="absolute -left-4 top-1.5 w-3 h-3 rounded-full bg-blue-500/30 border-2 border-blue-500/60" />
                  <div className="bg-blue-500/5 border border-blue-500/10 rounded-lg px-4 py-3 hover:border-blue-500/25 transition-colors">
                    <p className="text-sm text-neutral-300 leading-relaxed">{note}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Illustrations as gallery */}
      {resources.illustrations && resources.illustrations.length > 0 && (
        <section>
          <h3 className="text-xs font-bold text-green-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded bg-green-500/20 flex items-center justify-center text-sm">🖼️</span>
            Gallery
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {resources.illustrations.map((ill, idx) => (
              <a
                key={idx}
                href={ill.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group relative overflow-hidden rounded-xl border border-neutral-800 hover:border-green-500/40 transition-all duration-300"
              >
                <div className="aspect-video bg-neutral-900">
                  <img
                    src={ill.url}
                    alt={ill.alt}
                    className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500"
                  />
                </div>
                <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute bottom-0 left-0 right-0 p-3 translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                  <p className="text-xs text-white/90">{ill.caption}</p>
                </div>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Links as categorized cards */}
      {resources.links && resources.links.length > 0 && (
        <section>
          <h3 className="text-xs font-bold text-cyan-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded bg-cyan-500/20 flex items-center justify-center text-sm">🔗</span>
            Resources
          </h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {resources.links.map((link, idx) => {
              const config = LINK_TYPE_CONFIG[link.type] || LINK_TYPE_CONFIG.other;
              return (
                <a
                  key={idx}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={`group relative rounded-xl border p-4 transition-all duration-200 hover:scale-[1.02] ${config.bg}`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-xl mt-0.5">{config.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-neutral-200 group-hover:text-white transition-colors truncate">
                        {link.title}
                      </div>
                      {link.description && (
                        <div className="text-xs text-neutral-500 mt-1 line-clamp-2 leading-relaxed">
                          {link.description}
                        </div>
                      )}
                    </div>
                  </div>
                  <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <svg className="w-4 h-4 text-neutral-500" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                    </svg>
                  </div>
                </a>
              );
            })}
          </div>
        </section>
      )}

      {/* FAQ as accordion */}
      {resources.faq && resources.faq.length > 0 && (
        <section>
          <h3 className="text-xs font-bold text-purple-400 uppercase tracking-widest mb-4 flex items-center gap-2">
            <span className="w-6 h-6 rounded bg-purple-500/20 flex items-center justify-center text-sm">❓</span>
            FAQ
          </h3>
          <div className="space-y-2">
            {resources.faq.map((item, idx) => (
              <div
                key={idx}
                className={`rounded-xl border overflow-hidden transition-all duration-200 ${
                  openFaq === idx
                    ? "border-purple-500/30 bg-purple-500/5"
                    : "border-neutral-800 hover:border-neutral-700"
                }`}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full flex items-center justify-between px-4 py-3.5 text-left"
                >
                  <span className="text-sm font-medium text-neutral-200">{item.question}</span>
                  <svg
                    className={`w-4 h-4 text-neutral-500 transition-transform duration-200 flex-shrink-0 ml-2 ${
                      openFaq === idx ? "rotate-180" : ""
                    }`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openFaq === idx && (
                  <div className="px-4 pb-4 text-sm text-neutral-400 border-t border-neutral-800/50 pt-3 leading-relaxed">
                    {item.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Community Feedback */}
      <section>
        <h3 className="text-xs font-bold text-pink-400 uppercase tracking-widest mb-4 flex items-center gap-2">
          <span className="w-6 h-6 rounded bg-pink-500/20 flex items-center justify-center text-sm">💬</span>
          Community Feedback
        </h3>
        {submitted && (
          <div className="bg-green-500/10 border border-green-500/20 rounded-xl px-4 py-3 text-sm text-green-400 mb-3">
            ✓ Feedback submitted! Thank you for sharing your experience.
          </div>
        )}
        <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-4 space-y-3">
          <textarea
            placeholder={`Share your experience building the ${instrumentName}...`}
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            rows={3}
            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2.5 text-sm text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-pink-500/50 resize-none transition-colors"
          />
          <div className="flex justify-end">
            <button
              onClick={handleSubmitFeedback}
              disabled={!feedbackText.trim()}
              className="px-5 py-2 bg-pink-600 hover:bg-pink-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-lg transition-colors font-medium"
            >
              Submit
            </button>
          </div>
        </div>
      </section>

      {/* Empty State */}
      {!resources.tips && !resources.build_notes && !resources.illustrations && !resources.links && !resources.faq && (
        <div className="text-center py-16">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-neutral-800/50 flex items-center justify-center text-3xl">
            🎵
          </div>
          <p className="text-sm text-neutral-400">No resources available yet for this instrument.</p>
          <p className="text-xs text-neutral-600 mt-2">Be the first to contribute tips, links, or feedback!</p>
        </div>
      )}
    </div>
  );
}
