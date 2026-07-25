import { ensureBackendRunning } from "./tauri";

let apiBasePromise: Promise<string> | null = null;

function getApiBaseUrl(): Promise<string> {
  if (!apiBasePromise) {
    apiBasePromise = ensureBackendRunning();
  }
  return apiBasePromise;
}

// ── Transport abstraction ────────────────────────────────────────────

async function apiGet(path: string): Promise<Response> {
  const base = await getApiBaseUrl();
  return fetch(`${base}${path}`);
}

async function apiPost(path: string, body: unknown): Promise<Response> {
  const base = await getApiBaseUrl();
  return fetch(`${base}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

async function apiPostBinary(path: string, body: unknown): Promise<Blob> {
  const base = await getApiBaseUrl();
  const res = await fetch(`${base}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`Binary POST failed: ${res.statusText}`);
  return res.blob();
}

export async function apiDownloadUrl(path: string): Promise<string> {
  const base = await getApiBaseUrl();
  return `${base}${path}`;
}

// ── Types ────────────────────────────────────────────────────────────

export interface DesignJob {
  job_id: string;
  status: string;
  progress: string[];
  result?: { output_dir: string; files: string[] };
}

// ── Health ───────────────────────────────────────────────────────────

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const res = await apiGet("/health");
  return res.json();
}

// ── Presets ──────────────────────────────────────────────────────────

export async function getPresets(): Promise<Record<string, string>> {
  const res = await apiGet("/presets");
  const data = await res.json();
  return data.presets;
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

export async function getDesignDownloadUrl(jobId: string): Promise<string> {
  const base = await getApiBaseUrl();
  return `${base}/design/${jobId}/download`;
}

// ── STEP Export ──────────────────────────────────────────────────────

export interface StepExportParams {
  bore_profile: [number, number][];
  wall_thickness?: number;
  tone_holes?: { position: number; diameter: number; chimney_height?: number }[];
}

export async function exportStep(params: StepExportParams): Promise<Blob> {
  return apiPostBinary("/export/step", params);
}

// ── CadQuery Export ────────────────────────────────────────────────

export interface CadQueryExportParams {
  preset?: string;
  bore_length?: number;
  bore_diameter?: number | number[];
  wall_thickness?: number;
  holes?: number[][];
  closed_top?: boolean;
}

export async function listCadqueryInstruments(): Promise<Record<string, {
  bore_length: number;
  bore_diameter: number | number[];
  closed_top: boolean;
  holes: number;
  display_name: string;
  family: string;
  subcategory: string;
  verified: boolean;
  description: string;
}>> {
  const res = await apiGet("/export/cadquery/instruments");
  return res.json();
}

export async function exportCadquery(params: CadQueryExportParams): Promise<Blob> {
  return apiPostBinary("/export/cadquery", params);
}

// ── Impedance ────────────────────────────────────────────────────────

export async function computeImpedance(preset: string): Promise<{
  frequencies: number[];
  impedanceMagnitude: number[];
  impedanceReal: number[];
  impedanceImag: number[];
}> {
  const res = await apiPost("/impedance/compute", { preset });
  if (!res.ok) throw new Error(`Impedance computation failed: ${res.statusText}`);
  return res.json();
}

export async function getPrecomputedImpedance(preset: string): Promise<{
  frequencies: number[];
  impedance_magnitude: number[];
}> {
  const res = await apiGet(`/impedance/precomputed/${preset}`);
  if (!res.ok) throw new Error(`Precomputed impedance not found: ${preset}`);
  return res.json();
}

// ── Sound Simulation ─────────────────────────────────────────────────

export interface SimulateSoundParams {
  preset: string;
  duration?: number;
  player_type?: string;
  temperature?: number;
}

export async function simulateSound(params: SimulateSoundParams): Promise<Blob> {
  const res = await apiPost("/simulate/sound", params);
  if (!res.ok) throw new Error(`Sound simulation failed: ${res.statusText}`);
  return res.blob();
}

// ── Audio Analysis ──────────────────────────────────────────────────

export interface ImpedancePeak {
  frequency: number;
  magnitude: number;
  note: string;
  octave: number;
  cents: number;
}

export interface AnalyzeAudioResult {
  preset: string;
  peaks: ImpedancePeak[];
  frequencies: number[];
  impedance_magnitude: number[];
}

export async function analyzeAudio(preset: string, topPeaks?: number): Promise<AnalyzeAudioResult> {
  const res = await apiPost("/analyze/audio", { preset, top_peaks: topPeaks ?? 10 });
  if (!res.ok) throw new Error(`Audio analysis failed: ${res.statusText}`);
  return res.json();
}

// ─── Optimization API ────────────────────────────────────────────────────

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

export async function evaluateBoreDesign(variables: number[], boreLength: number, targetFrequencies: number[], temperature?: number): Promise<{
  bore_profile: BoreProfilePoint[];
  matched_frequencies: MatchedFrequency[];
  all_peak_frequencies: number[];
  all_peak_magnitudes: number[];
  frequencies: number[];
  impedance_magnitude: number[];
}> {
  const res = await apiPost("/optimize/evaluate", { variables, bore_length: boreLength, target_frequencies: targetFrequencies, temperature });
  if (!res.ok) throw new Error(`Bore evaluation failed: ${res.statusText}`);
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

// ─── Sequential Optimization (Bordeaux Method) ─────────────────────

export interface SequentialOptimizeRequest {
  target_frequencies: number[];
  fingering_sets: string[][];
  bore_radius: number;
  outer_diameter: number;
  closed_top: boolean;
  n_register: number;
  hole_diameter: number;
  hole_length: number;
  bore_length_bounds: number[];
  n_bore_cp?: number;
  bore_radius_bounds?: number[];
}

export interface SequentialOptimizationJob {
  job_id: string;
  status: string;
  progress: string[];
  result?: {
    success: boolean;
    bore_length_mm: number;
    bore_radii: number[];
    n_bore_cp: number;
    hole_positions: number[];
    hole_diameters: number[];
    hole_lengths: number[];
    final_rms_cents: number;
    peak_error_cents: number;
    wall_time: number;
    matched_frequencies: MatchedFrequency[];
  };
  error?: string;
}

export async function startSequentialOptimization(req: SequentialOptimizeRequest): Promise<{ job_id: string }> {
  const res = await apiPost("/optimize/sequential", req);
  if (!res.ok) throw new Error(`Sequential optimization start failed: ${res.statusText}`);
  return res.json();
}

export async function getSequentialOptimizationStatus(jobId: string): Promise<SequentialOptimizationJob> {
  const res = await apiGet(`/optimize/sequential/${jobId}/status`);
  if (!res.ok) throw new Error(`Sequential optimization status failed: ${res.statusText}`);
  return res.json();
}

export async function getDesignDeskInstruments(): Promise<Record<string, string>> {
  const res = await apiGet("/design-desk/instruments");
  if (!res.ok) throw new Error("Failed to get design desk instruments");
  const data = await res.json();
  return data.instruments;
}

// ── SVG Export ──────────────────────────────────────────────────────

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