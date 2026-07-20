import { useState } from "react";

/** JSCAD geometry polygon structure ÔÇö vertices are 3D coordinate arrays. */
interface JSCADGeometry {
  polygons?: { vertices: number[][] }[];
}

/** Convert a JSCAD geometry object to a binary STL ArrayBuffer. */
function geometryToSTL(geometry: JSCADGeometry): ArrayBuffer {
  const polygons = geometry.polygons || [];
  const triangles: number[][][] = [];

  for (const poly of polygons) {
    const verts = poly.vertices;
    for (let i = 1; i < verts.length - 1; i++) {
      triangles.push([verts[0], verts[i], verts[i + 1]]);
    }
  }

  const numTriangles = triangles.length;
  const headerSize = 84;
  const triangleSize = 50;
  const bufferSize = headerSize + numTriangles * triangleSize;
  const buffer = new ArrayBuffer(bufferSize);
  const view = new DataView(buffer);

  for (let i = 0; i < 80; i++) view.setUint8(i, 0);
  view.setUint32(80, numTriangles, true);

  let offset = 84;
  for (const tri of triangles) {
    const v0 = tri[0];
    const v1 = tri[1];
    const v2 = tri[2];
    const e1 = [v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]];
    const e2 = [v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]];
    const nx = e1[1] * e2[2] - e1[2] * e2[1];
    const ny = e1[2] * e2[0] - e1[0] * e2[2];
    const nz = e1[0] * e2[1] - e1[1] * e2[0];
    const len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
    view.setFloat32(offset, nx / len, true); offset += 4;
    view.setFloat32(offset, ny / len, true); offset += 4;
    view.setFloat32(offset, nz / len, true); offset += 4;
    for (const v of [v0, v1, v2]) {
      view.setFloat32(offset, v[0], true); offset += 4;
      view.setFloat32(offset, v[1], true); offset += 4;
      view.setFloat32(offset, v[2], true); offset += 4;
    }
    view.setUint16(offset, 0, true); offset += 2;
  }
  return buffer;
}

interface ParametricGeneratorProps {
  instrumentKey?: string;
  onGenerated: (stlBlob: Blob, filename: string) => void;
}

const PARAMETRIC_PRESETS: Record<string, { name: string; description: string; params: Record<string, { label: string; min: number; max: number; step: number; default: number }> }> = {
  recorder: {
    name: "Recorder Headjoint",
    description: "Generate a parametric recorder headjoint bore",
    params: {
      length: { label: "Length (mm)", min: 30, max: 120, step: 1, default: 65 },
      boreDiameter: { label: "Bore Diameter (mm)", min: 5, max: 25, step: 0.5, default: 12 },
      wallThickness: { label: "Wall Thickness (mm)", min: 1, max: 5, step: 0.25, default: 2 },
      windowWidth: { label: "Window Width (mm)", min: 2, max: 15, step: 0.5, default: 8 },
    },
  },
  ocarina: {
    name: "Ocarina Body",
    description: "Generate a parametric ocarina resonator body",
    params: {
      length: { label: "Length (mm)", min: 50, max: 200, step: 1, default: 100 },
      width: { label: "Width (mm)", min: 30, max: 100, step: 1, default: 60 },
      height: { label: "Height (mm)", min: 20, max: 80, step: 1, default: 40 },
      wallThickness: { label: "Wall Thickness (mm)", min: 1, max: 5, step: 0.25, default: 2 },
    },
  },
  flute: {
    name: "Flute Headjoint",
    description: "Generate a cylindrical flute headjoint",
    params: {
      length: { label: "Length (mm)", min: 100, max: 400, step: 1, default: 250 },
      boreDiameter: { label: "Bore Diameter (mm)", min: 10, max: 30, step: 0.5, default: 19 },
      wallThickness: { label: "Wall Thickness (mm)", min: 0.5, max: 3, step: 0.25, default: 1 },
    },
  },
  default: {
    name: "Custom Bore",
    description: "Generate a generic cylindrical bore",
    params: {
      length: { label: "Length (mm)", min: 50, max: 1000, step: 1, default: 200 },
      boreDiameter: { label: "Bore Diameter (mm)", min: 5, max: 60, step: 0.5, default: 20 },
      wallThickness: { label: "Wall Thickness (mm)", min: 1, max: 8, step: 0.5, default: 3 },
    },
  },
};

export default function ParametricGenerator({ instrumentKey, onGenerated }: ParametricGeneratorProps) {
  const presetKey = instrumentKey && PARAMETRIC_PRESETS[instrumentKey] ? instrumentKey : "default";
  const preset = PARAMETRIC_PRESETS[presetKey];
  const [params, setParams] = useState<Record<string, number>>(
    Object.fromEntries(Object.entries(preset.params).map(([k, v]) => [k, v.default]))
  );
  const [generating, setGenerating] = useState(false);
  const [status, setStatus] = useState("");

  const handleGenerate = async () => {
    setGenerating(true);
    setStatus("Generating parametric model...");

    try {
      const jscad = await import("@jscad/modeling");
      const { booleans, primitives } = jscad;
      const { subtract } = booleans;

      let result: JSCADGeometry;

      if (presetKey === "recorder") {
        const outer = primitives.cylinder({ radius: params.boreDiameter / 2 + params.wallThickness, height: params.length, segments: 64 });
        const inner = primitives.cylinder({ radius: params.boreDiameter / 2, height: params.length + 1, segments: 64 });
        result = subtract(outer, inner);
      } else if (presetKey === "ocarina") {
        const outer = primitives.cuboid({ size: [params.width, params.height, params.length] });
        const inner = primitives.cuboid({ size: [params.width - params.wallThickness * 2, params.height - params.wallThickness * 2, params.length - params.wallThickness * 2] });
        result = subtract(outer, inner);
      } else {
        const outer = primitives.cylinder({ radius: params.boreDiameter / 2 + params.wallThickness, height: params.length, segments: 64 });
        const inner = primitives.cylinder({ radius: params.boreDiameter / 2, height: params.length + 1, segments: 64 });
        result = subtract(outer, inner);
      }

      setStatus("Converting to STL...");
      const stlData = geometryToSTL(result);
      const blob = new Blob([stlData], { type: "application/octet-stream" });
      const filename = `${presetKey}-${Date.now()}.stl`;
      onGenerated(blob, filename);
      setStatus("Generated successfully!");
    } catch (err) {
      setStatus(`Error: ${err instanceof Error ? err.message : "Generation failed"}`);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="bg-neutral-800 rounded-xl p-4 border border-neutral-700 space-y-4">
      <div>
        <h3 className="text-sm font-semibold text-brand-400">{preset.name}</h3>
        <p className="text-xs text-neutral-400 mt-1">{preset.description}</p>
      </div>
      <div className="grid grid-cols-2 gap-3">
        {Object.entries(preset.params).map(([key, param]) => (
          <div key={key}>
            <label className="text-xs text-neutral-400 block mb-1">{param.label}</label>
            <input
              type="number"
              value={params[key]}
              min={param.min}
              max={param.max}
              step={param.step}
              onChange={(e) => setParams({ ...params, [key]: parseFloat(e.target.value) || param.default })}
              className="w-full bg-neutral-900 border border-neutral-600 rounded-lg px-3 py-1.5 text-sm text-white focus:border-brand-500 focus:outline-none"
            />
          </div>
        ))}
      </div>
      <button
        onClick={handleGenerate}
        disabled={generating}
        className="w-full bg-brand-600 hover:bg-brand-500 disabled:bg-neutral-600 text-white font-medium py-2 rounded-lg text-sm transition-colors"
      >
        {generating ? "Generating..." : "Generate STL"}
      </button>
      {status && (
        <p className={`text-xs ${status.startsWith("Error") ? "text-red-400" : "text-neutral-400"}`}>
          {status}
        </p>
      )}
    </div>
  );
}
