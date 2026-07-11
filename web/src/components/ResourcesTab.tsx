export function ResourcesTab() {
  return (
    <div className="p-6 max-w-4xl space-y-6">
      <div>
        <h2 className="text-lg font-semibold text-neutral-100">Resources</h2>
        <p className="text-sm text-neutral-500">
          Tips, tools, and references for instrument design
        </p>
      </div>

      <Section title="Design Tips">
        <ul className="space-y-2">
          <li>
            Start with Demakein presets for proven bore profiles, then
            customize dimensions
          </li>
          <li>
            Use OpenWInD to validate acoustic impedance before printing
          </li>
          <li>
            Print test sections first — bore tolerance varies by printer
          </li>
          <li>
            Use PETG or ABS for final instruments (PLA warps with moisture)
          </li>
          <li>
            Sand the bore interior for smooth airflow (400+ grit)
          </li>
        </ul>
      </Section>

      <Section title="Open-Source CAD Tools">
        <ul className="space-y-2">
          <ToolLink
            name="FreeCAD"
            url="https://www.freecad.org"
            desc="Parametric BREP CAD with Python scripting and OpenCascade kernel"
          />
          <ToolLink
            name="Build123d"
            url="https://github.com/gumyr/build123d"
            desc="Pythonic BREP CAD API built on OpenCascade"
          />
          <ToolLink
            name="OpenSCAD"
            url="https://openscad.org"
            desc="CSG-based programmatic CAD, great for simple tubes"
          />
          <ToolLink
            name="JSCAD"
            url="https://jscad.xyz"
            desc="Parametric CAD in JavaScript, runs in browser"
          />
          <ToolLink
            name="Chili3D"
            url="https://chili3d.com"
            desc="Browser-based CAD with STEP/BREP import/export"
          />
          <ToolLink
            name="Occt-Wasm"
            url="https://github.com/nicholasgasior/occt-wasm"
            desc="OpenCascade compiled to WASM for browser STEP/STL I/O"
          />
        </ul>
      </Section>

      <Section title="STL Repositories">
        <ul className="space-y-2">
          <ToolLink
            name="Thingiverse - Musical Instruments"
            url="https://www.thingiverse.com/tag:musical%20instrument"
            desc="Community-uploaded 3D-printable instruments"
          />
          <ToolLink
            name="Printables - Instruments"
            url="https://www.printables.com/search/models?q=flute"
            desc="High-quality printable instrument models"
          />
          <ToolLink
            name="MyMiniFactory"
            url="https://www.myminifactory.com"
            desc="Curated 3D models including musical instruments"
          />
        </ul>
      </Section>

      <Section title="AI / ML Tools">
        <ul className="space-y-2">
          <ToolLink
            name="OpenWInD"
            url="https://gitlab.com/music-instruments-acoustics/openwind"
            desc="Acoustic impedance simulation and bore optimization"
          />
          <ToolLink
            name="Demakein"
            url="https://github.com/klokeau/Demakein"
            desc="Numerical optimization for woodwind bore design"
          />
          <ToolLink
            name="CadQuery"
            url="https://github.com/CadQuery/cadquery"
            desc="Python parametric CAD scripting with OpenCascade"
          />
          <ToolLink
            name="trimesh"
            url="https://github.com/mikedh/trimesh"
            desc="Python mesh processing: boolean ops, repair, export"
          />
        </ul>
      </Section>

      <Section title="Slicing & Printing">
        <ul className="space-y-2">
          <ToolLink
            name="PrusaSlicer"
            url="https://www.prusa3d.com/prusaslicer/"
            desc="CLI available for automated slicing pipelines"
          />
          <ToolLink
            name="OrcaSlicer"
            url="https://github.com/SoftFever/OrcaSlicer"
            desc="Best CLI for headless slicing with JSON profiles"
          />
          <ToolLink
            name="CuraEngine"
            url="https://github.com/Ultimaker/CuraEngine"
            desc="Standalone slicing engine with Docker microservice patterns"
          />
        </ul>
      </Section>

      <Section title="Community">
        <ul className="space-y-2">
          <ToolLink
            name="r/3DPrintedInstruments"
            url="https://www.reddit.com/r/3DPrintedInstruments/"
            desc="Reddit community for 3D-printed musical instruments"
          />
          <ToolLink
            name="Instructables - Music"
            url="https://www.instructables.com/Music/"
            desc="DIY instrument tutorials and build guides"
          />
        </ul>
      </Section>
    </div>
  );
}

function Section({
  title,
  children,
}: {
  title: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-5">
      <h3 className="text-sm font-medium text-neutral-200 mb-3">{title}</h3>
      <div className="text-xs text-neutral-400 space-y-1">{children}</div>
    </div>
  );
}

function ToolLink({
  name,
  url,
  desc,
}: {
  name: string;
  url: string;
  desc: string;
}) {
  return (
    <li>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="text-brand-400 hover:text-brand-300 underline underline-offset-2"
      >
        {name}
      </a>{" "}
      — {desc}
    </li>
  );
}
