import { useState } from "react";
import type { InstrumentResources } from "../data/instruments";

interface Props {
  resources: InstrumentResources;
  instrumentName: string;
}

const LINK_TYPE_ICONS: Record<string, string> = {
  video: "▶",
  book: "📖",
  tutorial: "🔧",
  article: "📄",
  forum: "💬",
  shop: "🛒",
  other: "🔗",
};

const LINK_TYPE_COLORS: Record<string, string> = {
  video: "bg-red-600/20 text-red-400",
  book: "bg-blue-600/20 text-blue-400",
  tutorial: "bg-green-600/20 text-green-400",
  article: "bg-yellow-600/20 text-yellow-400",
  forum: "bg-purple-600/20 text-purple-400",
  shop: "bg-orange-600/20 text-orange-400",
  other: "bg-neutral-600/20 text-neutral-400",
};

export default function ResourcePage({ resources, instrumentName }: Props) {
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [feedbackName, setFeedbackName] = useState("");
  const [feedbackText, setFeedbackText] = useState("");
  const [submitted, setSubmitted] = useState(false);

  const handleSubmitFeedback = () => {
    if (!feedbackText.trim()) return;
    setSubmitted(true);
    setFeedbackName("");
    setFeedbackText("");
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <div className="space-y-6">
      {/* Tips */}
      {resources.tips && resources.tips.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-neutral-200 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-yellow-500">💡</span> Tips &amp; Tricks
          </h3>
          <div className="space-y-2">
            {resources.tips.map((tip, idx) => (
              <div key={idx} className="bg-yellow-600/5 border border-yellow-600/10 rounded-lg px-4 py-3 text-sm text-neutral-300">
                {tip}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Build Notes */}
      {resources.build_notes && resources.build_notes.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-neutral-200 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-blue-500">🔨</span> Build Notes
          </h3>
          <div className="space-y-2">
            {resources.build_notes.map((note, idx) => (
              <div key={idx} className="bg-blue-600/5 border border-blue-600/10 rounded-lg px-4 py-3 text-sm text-neutral-300">
                {note}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Illustrations */}
      {resources.illustrations && resources.illustrations.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-neutral-200 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-green-500">🖼</span> Illustrations
          </h3>
          <div className="grid grid-cols-2 gap-3">
            {resources.illustrations.map((ill, idx) => (
              <a
                key={idx}
                href={ill.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group block rounded-lg overflow-hidden border border-neutral-800 hover:border-neutral-600 transition-colors"
              >
                <img
                  src={ill.url}
                  alt={ill.alt}
                  className="w-full h-40 object-cover group-hover:scale-105 transition-transform duration-200"
                />
                <div className="px-3 py-2 bg-neutral-800/50">
                  <p className="text-xs text-neutral-400">{ill.caption}</p>
                </div>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* Links */}
      {resources.links && resources.links.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-neutral-200 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-cyan-500">🔗</span> Resources
          </h3>
          <div className="grid grid-cols-1 gap-2">
            {resources.links.map((link, idx) => (
              <a
                key={idx}
                href={link.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-3 bg-neutral-800/50 hover:bg-neutral-800 rounded-lg px-4 py-3 transition-colors group"
              >
                <span className="text-lg">{LINK_TYPE_ICONS[link.type] || "🔗"}</span>
                <div className="flex-1 min-w-0">
                  <div className="text-sm text-neutral-200 group-hover:text-white truncate">{link.title}</div>
                  {link.description && (
                    <div className="text-xs text-neutral-500 truncate">{link.description}</div>
                  )}
                </div>
                <span className={`text-xs px-2 py-0.5 rounded-full ${LINK_TYPE_COLORS[link.type] || LINK_TYPE_COLORS.other}`}>
                  {link.type}
                </span>
              </a>
            ))}
          </div>
        </section>
      )}

      {/* FAQ */}
      {resources.faq && resources.faq.length > 0 && (
        <section>
          <h3 className="text-sm font-semibold text-neutral-200 uppercase tracking-wider mb-3 flex items-center gap-2">
            <span className="text-purple-500">❓</span> FAQ
          </h3>
          <div className="space-y-2">
            {resources.faq.map((item, idx) => (
              <div key={idx} className="border border-neutral-800 rounded-lg overflow-hidden">
                <button
                  onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                  className="w-full flex items-center justify-between px-4 py-3 text-sm text-neutral-200 hover:bg-neutral-800/50 transition-colors"
                >
                  <span className="font-medium text-left">{item.question}</span>
                  <svg
                    className={`w-4 h-4 text-neutral-500 transition-transform ${openFaq === idx ? "rotate-180" : ""}`}
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                    strokeWidth={2}
                  >
                    <path strokeLinecap="round" strokeLinejoin="round" d="M19 9l-7 7-7-7" />
                  </svg>
                </button>
                {openFaq === idx && (
                  <div className="px-4 pb-3 text-sm text-neutral-400 border-t border-neutral-800 pt-3">
                    {item.answer}
                  </div>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      {/* User Feedback */}
      <section>
        <h3 className="text-sm font-semibold text-neutral-200 uppercase tracking-wider mb-3 flex items-center gap-2">
          <span className="text-pink-500">💬</span> Community Feedback
        </h3>
        {submitted && (
          <div className="bg-green-600/10 border border-green-600/20 rounded-lg px-4 py-3 text-sm text-green-400 mb-3">
            Feedback submitted! Thank you for sharing your experience with {instrumentName}.
          </div>
        )}
        <div className="bg-neutral-800/30 rounded-lg p-4 space-y-3">
          <input
            type="text"
            placeholder="Your name (optional)"
            value={feedbackName}
            onChange={(e) => setFeedbackName(e.target.value)}
            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-brand-500"
          />
          <textarea
            placeholder="Share your experience, tips, or questions about this instrument..."
            value={feedbackText}
            onChange={(e) => setFeedbackText(e.target.value)}
            rows={3}
            className="w-full bg-neutral-800 border border-neutral-700 rounded-lg px-3 py-2 text-sm text-neutral-200 placeholder:text-neutral-600 focus:outline-none focus:border-brand-500 resize-none"
          />
          <button
            onClick={handleSubmitFeedback}
            disabled={!feedbackText.trim()}
            className="px-4 py-2 bg-brand-600 hover:bg-brand-500 disabled:bg-neutral-700 disabled:text-neutral-500 text-sm text-white rounded-lg transition-colors"
          >
            Submit Feedback
          </button>
        </div>
      </section>

      {/* Empty State */}
      {!resources.tips && !resources.build_notes && !resources.illustrations && !resources.links && !resources.faq && (
        <div className="text-center py-12 text-neutral-500">
          <p className="text-sm">No resources available yet for this instrument.</p>
          <p className="text-xs mt-2">Be the first to contribute tips, links, or feedback!</p>
        </div>
      )}
    </div>
  );
}
