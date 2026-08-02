import { isTauri, tauriHttpGet, tauriHttpPost } from "./tauri";

const API_BASE = "http://localhost:8000";

// ── Transport abstraction ────────────────────────────────────────────

async function apiGet(path: string): Promise<Response> {
  if (isTauri()) {
    const json = await tauriHttpGet(`${API_BASE}${path}`);
    return new Response(json, { status: 200, headers: { "Content-Type": "application/json" } });
  }
  return fetch(`${API_BASE}${path}`);
}

async function apiPost(path: string, body: unknown): Promise<Response> {
  if (isTauri()) {
    const json = await tauriHttpPost(`${API_BASE}${path}`, body);
    return new Response(json, { status: 200, headers: { "Content-Type": "application/json" } });
  }
  return fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

// ── Types ────────────────────────────────────────────────────────────

export interface DesignJob {
  job_id: string;
  status: string;
  progress: string[];
  result?: { output_dir: string; files: string[] };
}

export interface StepExportParams {
  preset: string;
  length: number;
  bore_diameter: number;
  wall_thickness: number;
  segments?: number;
}

// ── Health ───────────────────────────────────────────────────────────

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const res = await apiGet("/health");
  return res.json();
}

// ── Design ───────────────────────────────────────────────────────────

export async function startDesign(preset: string, transpose: number = 0, quick: boolean = false): Promise<{ job_id: string }> {
  const res = await apiPost("/design", { preset, transpose, quick });
  return res.json();
}

export async function getDesignStatus(jobId: string): Promise<DesignJob> {
  const res = await apiGet(`/design/${jobId}/status`);
  return res.json();
}

export function getDesignDownloadUrl(jobId: string): string {
  return `${API_BASE}/design/${jobId}/download`;
}

// ── STEP Export ──────────────────────────────────────────────────────

export async function exportStep(params: StepExportParams): Promise<Blob> {
  const res = await apiPost("/export/step", params);
  if (!res.ok) throw new Error(`STEP export failed: ${res.statusText}`);
  return res.blob();
}

// ─── Optimization API ─────────────────────────────────────────────────────

export interface OptimizeRequest {
  target_frequencies: number[];
  n_control_points?: number;
  bore_length?: number | null;
  min_radius?: number;
  max_radius?: number;
  pop_size?: number;
  n_generations?: number;
  temperature?: number;
}

export interface MatchedFrequency {
  target: number;
  actual: number;
  error_hz: number;
  error_cents: number;
}

export interface BoreProfilePoint {
  position: number;
  radius: number;
}

export interface OptimizationDesign {
  bore_profile: BoreProfilePoint[];
  objectives: {
    frequency_accuracy: number;
    scale_evenness: number;
    projection: number;
  };
  matched_frequencies: MatchedFrequency[];
  variables?: number[];
}

export interface OptimizationResult {
  pareto_front: number[][];
  designs: OptimizationDesign[];
  best_candidates: OptimizationDesign[];
  n_evaluations: number;
  n_generations?: number;
  bore_length: number;
  freq_range: number[];
  seed: number;
}

export interface OptimizationJob {
  job_id: string;
  status: string;
  progress: string[];
  result?: OptimizationResult;
  error?: string;
}

export interface OptimizationPreset {
  name: string;
  frequencies: number[];
  type?: string;
  fundamental?: number;
}

export async function startOptimization(req: OptimizeRequest): Promise<{ job_id: string }> {
  const res = await apiPost("/optimize/start", req);
  if (!res.ok) throw new Error(`Optimization start failed: ${res.statusText}`);
  return res.json();
}

export async function getOptimizationStatus(jobId: string): Promise<OptimizationJob> {
  const res = await apiGet(`/optimize/${jobId}/status`);
  if (!res.ok) throw new Error(`Optimization status failed: ${res.statusText}`);
  return res.json();
}

export async function getOptimizationPresets(): Promise<Record<string, OptimizationPreset>> {
  const res = await apiGet("/optimize/presets");
  if (!res.ok) throw new Error(`Failed to load optimization presets`);
  const data = await res.json();
  return data.presets;
}

// ── Cache Stats ────────────────────────────────────────────────────

export async function getCacheStats(): Promise<{ cache_size: number; status: string }> {
  const res = await apiGet("/optimize/cache/stats");
  if (!res.ok) throw new Error(`Cache stats failed`);
  return res.json();
}

export async function clearCache(): Promise<{ status: string }> {
  const res = await apiPost("/optimize/cache/clear", {});
  if (!res.ok) throw new Error(`Cache clear failed`);
  return res.json();
}

// ─── SVG Export ─────────────────────────────────────────────────────────

export async function exportBoreSvg(
  boreProfile: [number, number][],
  title?: string,
  holePositions?: number[],
  holeDiameters?: number[],
  boreLength?: number,
  view?: "side" | "cross",
): Promise<string> {
  const res = await apiPost("/export/svg", {
    bore_profile: boreProfile,
    title: title ?? "Instrument Bore Profile",
    hole_positions: holePositions,
    hole_diameters: holeDiameters,
    bore_length: boreLength,
    view: view ?? "side",
  });
  if (!res.ok) throw new Error("SVG export failed");
  return res.text();
}

export function downloadSvg(svgContent: string, filename: string) {
  const blob = new Blob([svgContent], { type: "image/svg+xml" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

export async function listCadqueryInstruments(): Promise<Record<string, {
  bore_length: number;
  bore_diameter: number;
  closed_top: boolean;
  holes: number;
  display_name: string;
  family: string;
  subcategory: string;
  verified: boolean;
  description: string;
}>> {
  const res = await apiGet("/export/cadquery/instruments");
  if (!res.ok) throw new Error("Failed to list CadQuery instruments");
  return res.json();
}

export async function exportCadquery(params: {
  preset?: string;
  bore_length?: number;
  bore_diameter?: number | number[];
  wall_thickness?: number;
  holes?: number[][];
  closed_top?: boolean;
}): Promise<Blob> {
  const res = await apiPost("/export/cadquery", params);
  if (!res.ok) throw new Error("CadQuery export failed");
  return res.blob();
}
