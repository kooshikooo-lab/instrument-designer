import { useState } from "react";
import { Sidebar } from "./components/Sidebar";
import { InstrumentBrowser } from "./components/InstrumentBrowser";
import { InstrumentDetail } from "./components/InstrumentDetail";
import { DesignTab } from "./components/DesignTab";
import { ResourcesTab } from "./components/ResourcesTab";

export default function App() {
  const [activeTab, setActiveTab] = useState("library");
  const [selectedInstrument, setSelectedInstrument] = useState<string | null>(
    null
  );

  const handleGenerateFromLibrary = (preset: string) => {
    setActiveTab("design");
    console.log("Generate from library:", preset);
  };

  return (
    <div className="flex h-screen bg-neutral-950">
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} />

      {activeTab === "library" && (
        <div className="flex flex-1 overflow-hidden">
          <InstrumentBrowser
            onSelect={setSelectedInstrument}
            selectedName={selectedInstrument}
          />
          <InstrumentDetail
            name={selectedInstrument}
            onGenerate={handleGenerateFromLibrary}
          />
        </div>
      )}

      {activeTab === "design" && <DesignTab />}

      {activeTab === "resources" && <ResourcesTab />}
    </div>
  );
}
