export function ResourcesTab() {
  return (
    <div className="p-6 max-w-4xl space-y-8">
      <div>
        <h2 className="text-lg font-semibold text-neutral-100">Resources & Design Tips</h2>
        <p className="text-sm text-neutral-500">Everything you need to design and 3D-print musical instruments</p>
      </div>

      <Section title="Design Tips for 3D-Printed Instruments">
        <ul className="space-y-2">
          {[
            "Print with 100% infill for airtight chambers",
            "Use 0.12mm layer height for smooth bore surfaces",
            "Sand internal bore with fine-grit sandpaper (400+)",
            "Test with a known mouthpiece before final tuning",
            "Print bore segments vertically for best surface finish",
            "Use PETG or ABS for instruments that need moisture resistance",
            "Calibrate your printer's flow rate for accurate hole diameters",
            "Use cyanoacrylate (super glue) to bond multi-part instruments",
          ].map((tip, i) => (
            <li key={i} className="text-sm text-neutral-300 flex gap-2">
              <span className="text-brand-500 mt-0.5">-</span>
              {tip}
            </li>
          ))}
        </ul>
      </Section>

      <Section title="Open-Source Projects">
        <div className="grid grid-cols-2 gap-3">
          {[
            { name: "Demakein", url: "https://github.com/pfh/demakein", desc: "Design & make woodwind instruments" },
            { name: "OpenWInD", url: "https://openwind.inria.fr/", desc: "Wind instrument acoustic simulation" },
            { name: "FreeCAD", url: "https://www.freecad.org/", desc: "Parametric 3D CAD modeler" },
            { name: "JSCAD", url: "https://jscad.app/", desc: "Browser-based parametric CAD" },
            { name: "OpenSCAD", url: "https://openscad.org/", desc: "Script-based 3D modeling" },
            { name: "Hovalin", url: "https://github.com/kjj0/hovalin", desc: "3D-printable violin" },
          ].map((p) => (
            <a
              key={p.name}
              href={p.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-neutral-800/50 rounded-lg px-4 py-3 hover:bg-neutral-800 transition-colors"
            >
              <div className="text-sm text-brand-400">{p.name}</div>
              <div className="text-xs text-neutral-500 mt-0.5">{p.desc}</div>
            </a>
          ))}
        </div>
      </Section>

      <Section title="STL Repositories">
        <div className="grid grid-cols-3 gap-2">
          {[
            { name: "Printables", url: "https://www.printables.com" },
            { name: "Thingiverse", url: "https://www.thingiverse.com" },
            { name: "MakerWorld", url: "https://www.makerworld.com" },
            { name: "Cults3D", url: "https://www.cults3d.com" },
            { name: "Thangs", url: "https://thangs.com" },
            { name: "Yeggi", url: "https://www.yeggi.com" },
          ].map((r) => (
            <a
              key={r.name}
              href={r.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-neutral-800/50 rounded-lg px-3 py-2 text-sm text-neutral-300 hover:text-brand-400 hover:bg-neutral-800 transition-colors text-center"
            >
              {r.name}
            </a>
          ))}
        </div>
      </Section>

      <Section title="AI-Powered Design Tools">
        <div className="grid grid-cols-2 gap-2">
          {[
            { name: "Meshy AI", url: "https://www.meshy.ai" },
            { name: "Tripo AI", url: "https://www.tripo3d.ai" },
            { name: "Zoo.dev", url: "https://zoo.dev" },
            { name: "Backflip AI", url: "https://www.backflip.com" },
          ].map((t) => (
            <a
              key={t.name}
              href={t.url}
              target="_blank"
              rel="noopener noreferrer"
              className="bg-neutral-800/50 rounded-lg px-3 py-2 text-sm text-neutral-300 hover:text-brand-400 hover:bg-neutral-800 transition-colors"
            >
              {t.name}
            </a>
          ))}
        </div>
      </Section>

      <Section title="Community">
        <div className="space-y-2">
          {[
            { name: "r/3Dprinting", url: "https://reddit.com/r/3Dprinting" },
            { name: "r/FunctionalPrint", url: "https://reddit.com/r/functionalprint" },
            { name: "FreeCAD Forum", url: "https://forum.freecad.org" },
          ].map((c) => (
            <a
              key={c.name}
              href={c.url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-brand-400 hover:text-brand-300 block"
            >
              {c.name}
            </a>
          ))}
        </div>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div>
      <h3 className="text-sm font-semibold text-neutral-200 mb-3 pb-2 border-b border-neutral-800">{title}</h3>
      {children}
    </div>
  );
}
