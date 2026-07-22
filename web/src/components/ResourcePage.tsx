import { useState } from "react";
import type { InstrumentResources } from "../data/instruments";

interface Props {
  resources: InstrumentResources;
  instrumentName: string;
}

export default function ResourcePage({ resources, instrumentName }: Props) {
  const [openFaq, setOpenFaq] = useState<number | null>(null);
  const [feedbackText, setFeedbackText] = useState("");
  const [submitted, setSubmitted] = useState(false);
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    tips: true,
    build_notes: true,
    gallery: false,
    links: true,
    faq: false,
    feedback: false,
  });

  const toggle = (key: string) => setOpenSections((s) => ({ ...s, [key]: !s[key] }));

  const handleSubmitFeedback = () => {
    if (!feedbackText.trim()) return;
    setSubmitted(true);
    setFeedbackText("");
    setTimeout(() => setSubmitted(false), 3000);
  };

  return (
    <div className="space-y-0 text-sm">
      {/* Table of Contents */}
      <div className="border border-neutral-700 rounded bg-neutral-900/50 p-4 mb-6">
        <div className="text-xs font-mono text-neutral-400 uppercase tracking-wider mb-2">Contents</div>
        <div className="space-y-1 font-mono text-xs">
          {resources.tips && resources.tips.length > 0 && (
            <div className="text-brand-400 hover:underline cursor-pointer" onClick={() => { toggle("tips"); document.getElementById("wiki-tips")?.scrollIntoView({ behavior: "smooth" }); }}>
              1. Tips
            </div>
          )}
          {resources.build_notes && resources.build_notes.length > 0 && (
            <div className="text-brand-400 hover:underline cursor-pointer" onClick={() => { toggle("build_notes"); document.getElementById("wiki-build")?.scrollIntoView({ behavior: "smooth" }); }}>
              2. Build Notes
            </div>
          )}
          {resources.illustrations && resources.illustrations.length > 0 && (
            <div className="text-brand-400 hover:underline cursor-pointer" onClick={() => { toggle("gallery"); document.getElementById("wiki-gallery")?.scrollIntoView({ behavior: "smooth" }); }}>
              3. Gallery
            </div>
          )}
          {resources.links && resources.links.length > 0 && (
            <div className="text-brand-400 hover:underline cursor-pointer" onClick={() => { toggle("links"); document.getElementById("wiki-links")?.scrollIntoView({ behavior: "smooth" }); }}>
              4. External Resources
            </div>
          )}
          {resources.faq && resources.faq.length > 0 && (
            <div className="text-brand-400 hover:underline cursor-pointer" onClick={() => { toggle("faq"); document.getElementById("wiki-faq")?.scrollIntoView({ behavior: "smooth" }); }}>
              5. FAQ
            </div>
          )}
          <div className="text-brand-400 hover:underline cursor-pointer" onClick={() => { toggle("feedback"); document.getElementById("wiki-feedback")?.scrollIntoView({ behavior: "smooth" }); }}>
            6. Community Notes
          </div>
        </div>
      </div>

      {/* 1. Tips */}
      {resources.tips && resources.tips.length > 0 && (
        <section id="wiki-tips" className="scroll-mt-4">
          <button onClick={() => toggle("tips")} className="w-full flex items-center gap-2 py-2 border-b border-neutral-700 hover:border-neutral-500 transition-colors group">
            <span className="text-xs font-mono text-neutral-500 group-hover:text-brand-400 transition-colors">{openSections.tips ? "▼" : "▶"}</span>
            <span className="font-mono text-sm text-neutral-200 group-hover:text-white">1. Tips</span>
            <span className="text-xs text-neutral-600 font-mono ml-auto">{resources.tips.length} items</span>
          </button>
          {openSections.tips && (
            <div className="pl-4 border-l border-neutral-800 py-3 space-y-2">
              {resources.tips.map((tip, idx) => (
                <div key={idx} className="flex gap-3 font-mono text-xs leading-relaxed text-neutral-400">
                  <span className="text-neutral-600 flex-shrink-0">{idx + 1}.</span>
                  <span>{tip}</span>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 2. Build Notes */}
      {resources.build_notes && resources.build_notes.length > 0 && (
        <section id="wiki-build" className="scroll-mt-4">
          <button onClick={() => toggle("build_notes")} className="w-full flex items-center gap-2 py-2 border-b border-neutral-700 hover:border-neutral-500 transition-colors group">
            <span className="text-xs font-mono text-neutral-500 group-hover:text-brand-400 transition-colors">{openSections.build_notes ? "▼" : "▶"}</span>
            <span className="font-mono text-sm text-neutral-200 group-hover:text-white">2. Build Notes</span>
            <span className="text-xs text-neutral-600 font-mono ml-auto">{resources.build_notes.length} entries</span>
          </button>
          {openSections.build_notes && (
            <div className="pl-4 border-l border-neutral-800 py-3 space-y-3">
              {resources.build_notes.map((note, idx) => (
                <div key={idx} className="font-mono text-xs leading-relaxed text-neutral-400 bg-neutral-900/50 border border-neutral-800 rounded p-3">
                  {note}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 3. Gallery */}
      {resources.illustrations && resources.illustrations.length > 0 && (
        <section id="wiki-gallery" className="scroll-mt-4">
          <button onClick={() => toggle("gallery")} className="w-full flex items-center gap-2 py-2 border-b border-neutral-700 hover:border-neutral-500 transition-colors group">
            <span className="text-xs font-mono text-neutral-500 group-hover:text-brand-400 transition-colors">{openSections.gallery ? "▼" : "▶"}</span>
            <span className="font-mono text-sm text-neutral-200 group-hover:text-white">3. Gallery</span>
            <span className="text-xs text-neutral-600 font-mono ml-auto">{resources.illustrations.length} images</span>
          </button>
          {openSections.gallery && (
            <div className="pl-4 border-l border-neutral-800 py-3 space-y-3">
              {resources.illustrations.map((ill, idx) => (
                <div key={idx} className="border border-neutral-800 rounded overflow-hidden">
                  <a href={ill.url} target="_blank" rel="noopener noreferrer">
                    <img src={ill.url} alt={ill.alt} className="w-full max-h-64 object-cover hover:opacity-80 transition-opacity" />
                  </a>
                  <div className="p-2 font-mono text-xs text-neutral-500">{ill.caption}</div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 4. External Resources */}
      {resources.links && resources.links.length > 0 && (
        <section id="wiki-links" className="scroll-mt-4">
          <button onClick={() => toggle("links")} className="w-full flex items-center gap-2 py-2 border-b border-neutral-700 hover:border-neutral-500 transition-colors group">
            <span className="text-xs font-mono text-neutral-500 group-hover:text-brand-400 transition-colors">{openSections.links ? "▼" : "▶"}</span>
            <span className="font-mono text-sm text-neutral-200 group-hover:text-white">4. External Resources</span>
            <span className="text-xs text-neutral-600 font-mono ml-auto">{resources.links.length} links</span>
          </button>
          {openSections.links && (
            <div className="pl-4 border-l border-neutral-800 py-3">
              <table className="w-full font-mono text-xs">
                <thead>
                  <tr className="text-neutral-500 border-b border-neutral-800">
                    <th className="text-left py-1.5 font-medium">Title</th>
                    <th className="text-left py-1.5 font-medium">Type</th>
                    <th className="text-left py-1.5 font-medium hidden sm:table-cell">Description</th>
                  </tr>
                </thead>
                <tbody>
                  {resources.links.map((link, idx) => (
                    <tr key={idx} className="border-b border-neutral-800/50 hover:bg-neutral-900/50">
                      <td className="py-2 pr-3">
                        <a href={link.url} target="_blank" rel="noopener noreferrer" className="text-brand-400 hover:underline">
                          {link.title} ↗
                        </a>
                      </td>
                      <td className="py-2 pr-3 text-neutral-500">{link.type}</td>
                      <td className="py-2 text-neutral-500 hidden sm:table-cell">{link.description || "—"}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </section>
      )}

      {/* 5. FAQ */}
      {resources.faq && resources.faq.length > 0 && (
        <section id="wiki-faq" className="scroll-mt-4">
          <button onClick={() => toggle("faq")} className="w-full flex items-center gap-2 py-2 border-b border-neutral-700 hover:border-neutral-500 transition-colors group">
            <span className="text-xs font-mono text-neutral-500 group-hover:text-brand-400 transition-colors">{openSections.faq ? "▼" : "▶"}</span>
            <span className="font-mono text-sm text-neutral-200 group-hover:text-white">5. FAQ</span>
            <span className="text-xs text-neutral-600 font-mono ml-auto">{resources.faq.length} questions</span>
          </button>
          {openSections.faq && (
            <div className="pl-4 border-l border-neutral-800 py-3 space-y-1">
              {resources.faq.map((item, idx) => (
                <div key={idx}>
                  <button
                    onClick={() => setOpenFaq(openFaq === idx ? null : idx)}
                    className="w-full flex items-center gap-2 py-2 text-left font-mono text-xs"
                  >
                    <span className="text-neutral-600">Q{idx + 1}.</span>
                    <span className="text-neutral-300">{item.question}</span>
                    <span className="ml-auto text-neutral-600">{openFaq === idx ? "−" : "+"}</span>
                  </button>
                  {openFaq === idx && (
                    <div className="pl-6 pb-2 font-mono text-xs text-neutral-500 leading-relaxed">
                      A: {item.answer}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* 6. Community Notes */}
      <section id="wiki-feedback" className="scroll-mt-4">
        <button onClick={() => toggle("feedback")} className="w-full flex items-center gap-2 py-2 border-b border-neutral-700 hover:border-neutral-500 transition-colors group">
          <span className="text-xs font-mono text-neutral-500 group-hover:text-brand-400 transition-colors">{openSections.feedback ? "▼" : "▶"}</span>
          <span className="font-mono text-sm text-neutral-200 group-hover:text-white">6. Community Notes</span>
        </button>
        {openSections.feedback && (
          <div className="pl-4 border-l border-neutral-800 py-3">
            {submitted && (
              <div className="border border-green-700 rounded bg-green-900/20 p-3 mb-3 font-mono text-xs text-green-400">
                ✓ Feedback submitted. Thank you.
              </div>
            )}
            <div className="font-mono text-xs text-neutral-500 mb-2">
              Add your experience building the {instrumentName}:
            </div>
            <textarea
              placeholder="Notes, tips, or corrections..."
              value={feedbackText}
              onChange={(e) => setFeedbackText(e.target.value)}
              rows={4}
              className="w-full bg-neutral-900 border border-neutral-700 rounded p-3 font-mono text-xs text-neutral-300 placeholder:text-neutral-600 focus:outline-none focus:border-brand-500/50 resize-none"
            />
            <div className="flex justify-end mt-2">
              <button
                onClick={handleSubmitFeedback}
                disabled={!feedbackText.trim()}
                className="px-4 py-1.5 bg-brand-600 hover:bg-brand-500 disabled:bg-neutral-800 disabled:text-neutral-600 text-xs text-white font-mono rounded transition-colors"
              >
                Submit
              </button>
            </div>
          </div>
        )}
      </section>

      {/* Empty State */}
      {!resources.tips && !resources.build_notes && !resources.illustrations && !resources.links && !resources.faq && (
        <div className="text-center py-16 font-mono">
          <div className="text-2xl mb-3">[ ]</div>
          <div className="text-xs text-neutral-500">No resources available for {instrumentName}.</div>
          <div className="text-xs text-neutral-600 mt-1">Be the first to contribute.</div>
        </div>
      )}
    </div>
  );
}
