import { useState } from "react";
import type { InstrumentResources } from "../data/instruments";

interface Props {
  resources: InstrumentResources;
  instrumentName: string;
}

const LINK_TYPE_ICONS: Record<string, { emoji: string; gradient: string }> = {
  video: { emoji: "🎬", gradient: "from-red-500 to-pink-500" },
  book: { emoji: "📚", gradient: "from-blue-500 to-indigo-500" },
  tutorial: { emoji: "🔨", gradient: "from-green-500 to-emerald-500" },
  article: { emoji: "📰", gradient: "from-amber-500 to-orange-500" },
  forum: { emoji: "💬", gradient: "from-purple-500 to-violet-500" },
  shop: { emoji: "🛒", gradient: "from-orange-500 to-yellow-500" },
  other: { emoji: "🔗", gradient: "from-neutral-500 to-gray-500" },
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
    <div className="space-y-10">
      {/* Hero Tips Section */}
      {resources.tips && resources.tips.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-400 to-orange-500 flex items-center justify-center text-white text-lg shadow-lg shadow-amber-500/20">
              💡
            </div>
            <div>
              <h3 className="text-lg font-bold text-neutral-100">Expert Tips</h3>
              <p className="text-xs text-neutral-500">Proven techniques from the community</p>
            </div>
          </div>
          <div className="space-y-3">
            {resources.tips.map((tip, idx) => (
              <div key={idx} className="relative group">
                <div className="absolute inset-0 bg-gradient-to-r from-amber-500/10 to-transparent rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="relative flex gap-4 p-4 rounded-2xl border border-neutral-800/50 hover:border-amber-500/20 transition-all duration-300">
                  <div className="flex-shrink-0 w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center">
                    <span className="text-sm font-bold text-amber-400">{idx + 1}</span>
                  </div>
                  <p className="text-sm text-neutral-300 leading-relaxed pt-1">{tip}</p>
                </div>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Build Notes - Editorial Style */}
      {resources.build_notes && resources.build_notes.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-blue-400 to-cyan-500 flex items-center justify-center text-white text-lg shadow-lg shadow-blue-500/20">
              🔧
            </div>
            <div>
              <h3 className="text-lg font-bold text-neutral-100">Build Notes</h3>
              <p className="text-xs text-neutral-500">Technical documentation</p>
            </div>
          </div>
          <div className="bg-gradient-to-br from-blue-500/5 to-cyan-500/5 rounded-2xl border border-blue-500/10 p-6">
            <div className="space-y-4">
              {resources.build_notes.map((note, idx) => (
                <div key={idx} className="flex gap-4">
                  <div className="flex-shrink-0 w-1 bg-gradient-to-b from-blue-500 to-cyan-500 rounded-full" />
                  <p className="text-sm text-neutral-300 leading-relaxed">{note}</p>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* Gallery - Magazine Spread */}
      {resources.illustrations && resources.illustrations.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-green-400 to-emerald-500 flex items-center justify-center text-white text-lg shadow-lg shadow-green-500/20">
              🖼️
            </div>
            <div>
              <h3 className="text-lg font-bold text-neutral-100">Gallery</h3>
              <p className="text-xs text-neutral-500">Visual references</p>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-4">
            {resources.illustrations.map((ill, idx) => (
              <a
                key={idx}
                href={ill.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group relative overflow-hidden rounded-2xl border border-neutral-800 hover:border-green-500/40 transition-all duration-500 aspect-video"
              >
                <img
                  src={ill.url}
                  alt={ill.alt}
                  className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700"
                />
                <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-transparent" />
                <div className="absolute bottom-0 left-0 right-0 p-4">
                  <p className="text-sm text-white/90 font-medium">{ill.caption}</p>
                </div>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Resources - Magazine Grid */}
      {resources.links && resources.links.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyan-400 to-blue-500 flex items-center justify-center text-white text-lg shadow-lg shadow-cyan-500/20">
              🔗
            </div>
            <div>
              <h3 className="text-lg font-bold text-neutral-100">Resources</h3>
              <p className="text-xs text-neutral-500">Curated links and references</p>
            </div>
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {resources.links.map((link, idx) => {
              const config = LINK_TYPE_ICONS[link.type] || LINK_TYPE_ICONS.other;
              return (
                <a
                  key={idx}
                  href={link.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="group relative overflow-hidden rounded-2xl border border-neutral-800 hover:border-neutral-600 p-5 transition-all duration-300 hover:shadow-xl hover:shadow-neutral-900/50"
                >
                  <div className={`absolute top-0 right-0 w-24 h-24 bg-gradient-to-br ${config.gradient} opacity-10 rounded-bl-[60px] group-hover:opacity-20 transition-opacity`} />
                  <div className="relative">
                    <div className="flex items-start gap-3">
                      <span className="text-2xl">{config.emoji}</span>
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-semibold text-neutral-200 group-hover:text-white transition-colors truncate">
                          {link.title}
                        </h4>
                        {link.description && (
                          <p className="text-xs text-neutral-500 mt-1.5 line-clamp-2 leading-relaxed">
                            {link.description}
                          </p>
                        )}
                      </div>
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <span className={`text-[10px] px-2 py-0.5 rounded-full bg-gradient-to-r ${config.gradient} text-white font-medium`}>
                        {link.type}
                      </span>
                      <span className="text-[10px] text-neutral-600 group-hover:text-neutral-500 transition-colors">
                        Visit →
                      </span>
                    </div>
                  </div>
                </a>
              );
            })}
          </div>
        </section>
      )}

      {/* FAQ - Accordion */}
      {resources.faq && resources.faq.length > 0 && (
        <section>
          <div className="flex items-center gap-3 mb-5">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-400 to-pink-500 flex items-center justify-center text-white text-lg shadow-lg shadow-purple-500/20">
              ❓
            </div>
            <div>
              <h3 className="text-lg font-bold text-neutral-100">FAQ</h3>
              <p className="text-xs text-neutral-500">Frequently asked questions</p>
            </div>
          </div>
          <div className="space-y-3">
            {resources.faq.map((item, idx) => (
              <div
                key={idx}
                className={`rounded-2xl border overflow-hidden transition-all duration-300 ${
                  openFaq === idx
                    ? "border-purple-500/30 bg-gradient-to-br from-purple-500/5 to-transparent shadow-lg shadow-purple-500/5"
                    : "border-neutral-800 hover:border-neutral-700"
                }`}
              >
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full flex items-center justify-between px-5 py-4 text-left"
                >
                  <span className="text-sm font-medium text-neutral-200 pr-4">{item.question}</span>
                  <svg
                    className={`w-5 h-5 text-neutral-500 transition-transform duration-300 flex-shrink-0 ${
                      openFaq === idx ? "rotate-180 text-purple-400" : ""
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
                  <div className="px-5 pb-5 text-sm text-neutral-400 border-t border-neutral-800/50 pt-4 leading-relaxed">
                    {item.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Community Feedback - Clean Form */}
      <section>
        <div className="flex items-center gap-3 mb-5">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-pink-400 to-rose-500 flex items-center justify-center text-white text-lg shadow-lg shadow-pink-500/20">
            💬
          </div>
          <div>
            <h3 className="text-lg font-bold text-neutral-100">Share Your Experience</h3>
            <p className="text-xs text-neutral-500">Help others build this instrument</p>
          </div>
        </div>
        {submitted && (
          <div className="bg-green-500/10 border border-green-500/20 rounded-2xl px-5 py-4 text-sm text-green-400 mb-4 flex items-center gap-3">
            <span className="text-lg">✓</span>
            Thank you! Your feedback helps the community.
          </div>
        )}
        <div className="bg-gradient-to-br from-neutral-900 to-neutral-800 rounded-2xl border border-neutral-800 p-5 space-y-4">
          <textarea
            placeholder={`What was your experience building the ${instrumentName}? Any tips for others?`}
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            rows={4}
            className="w-full bg-neutral-800/50 border border-neutral-700 rounded-xl px-4 py-3 text-sm text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-pink-500/50 focus:ring-1 focus:ring-pink-500/20 resize-none transition-all"
          />
          <div className="flex justify-end">
            <button
              onClick={handleSubmitFeedback}
              disabled={!feedbackText.trim()}
              className="px-6 py-2.5 bg-gradient-to-r from-pink-600 to-rose-600 hover:from-pink-500 hover:to-rose-500 disabled:from-neutral-800 disabled:to-neutral-800 disabled:text-neutral-600 text-sm text-white rounded-xl transition-all font-medium shadow-lg shadow-pink-600/20"
            >
              Submit Feedback
            </button>
          </div>
        </div>
      </section>

      {/* Empty State */}
      {!resources.tips && !resources.build_notes && !resources.illustrations && !resources.links && !resources.faq && (
        <div className="text-center py-20">
          <div className="w-20 h-20 mx-auto mb-5 rounded-3xl bg-gradient-to-br from-neutral-800 to-neutral-900 flex items-center justify-center text-4xl shadow-xl">
            🎵
          </div>
          <h4 className="text-lg font-semibold text-neutral-300 mb-2">No Resources Yet</h4>
          <p className="text-sm text-neutral-500 max-w-xs mx-auto">
            Be the first to contribute tips, links, or feedback for the {instrumentName}.
          </p>
        </div>
      )}
    </div>
  );
}
