import { useState } from "react";
import type { Instrument } from "./data/instruments";
import { Sidebar } from "./components/Sidebar";
import { InstrumentBrowser } from "./components/InstrumentBrowser";
import { InstrumentDetail } from "./components/InstrumentDetail";
import { DesignTab } from "./components/DesignTab";
import { ResourcesTab } from "./components/ResourcesTab";

type Tab = "library" | "design" | "resources";

export default function App() {
  const [tab, setTab] = useState<Tab>("library");
  const [selected, setSelected] = useState<Instrument | null>(null);

  const handleGenerateFromLibrary = (_preset: string) => {
    setSelected(null);
    setTab("design");
  };

  return (
    <div className="flex h-screen bg-neutral-950">
      <Sidebar active={tab} onNavigate={(t) => setTab(t as Tab)} />
      <main className="flex-1 overflow-hidden flex flex-col">
        <header className="border-b border-neutral-800 px-6 py-3 flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 rounded-lg bg-brand-600 flex items-center justify-center text-white font-bold text-sm">
              ID
            </div>
            <h1 className="text-lg font-semibold text-neutral-100">Instrument Designer</h1>
          </div>
          <span className="text-xs text-neutral-500 ml-auto">Web App v1.0.0</span>
        </header>
        <div className="flex-1 overflow-auto">
          {tab === "library" && (
            <div className="flex h-full">
              <div className={`${selected ? "w-[420px]" : "w-full"} transition-all duration-300 border-r border-neutral-800 overflow-auto`}>
                <InstrumentBrowser onSelect={setSelected} />
              </div>
              {selected && (
                <div className="flex-1 overflow-auto">
                  <InstrumentDetail
                    instrument={selected}
                    onClose={() => setSelected(null)}
                    onGenerate={handleGenerateFromLibrary}
                  />
                </div>
              )}
            </div>
          )}
          {tab === "design" && <DesignTab />}
          {tab === "resources" && <ResourcesTab />}
        </div>
      </main>
    </div>
  );
}
