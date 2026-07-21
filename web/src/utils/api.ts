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

export function apiDownloadUrl(path: string): string {
  return `${API_BASE}${path}`;
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

export function getDesignDownloadUrl(jobId: string): string {
  return `${API_BASE}/design/${jobId}/download`;
}

// ── STEP Export ──────────────────────────────────────────────────────

export async function exportStep(params: StepExportParams): Promise<Blob> {
  const res = await apiPost("/export/step", params);
  if (!res.ok) throw new Error(`STEP export failed: ${res.statusText}`);
  return res.blob();
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

// ── Audio Analysis ───────────────────────────────────────────────────

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

// ─── AI Design Advisor API ──────────────────────────────────────────────

export interface AdvisorSuggestion {
  category: string;
  priority: string;
  title: string;
  description: string;
  action: string;
  impact: string;
}

export interface AdvisorResult {
  score: number;
  grade: string;
  analysis: string;
  suggestions: AdvisorSuggestion[];
  comparison: Record<string, string>;
  llm_analysis: string | null;
}

export interface AdvisorStatus {
  rule_based: boolean;
  llm_available: boolean;
  llm_models: string[];
  ollama_url: string;
  memory_designs: number;
}

export async function getAdvisorStatus(): Promise<AdvisorStatus> {
  const res = await apiGet("/advisor/status");
  if (!res.ok) throw new Error("Failed to get advisor status");
  return res.json();
}

export async function analyzeDesign(
  optimizationResult: Record<string, unknown>,
  targetFrequencies: number[],
  useLlm?: boolean,
  llmModel?: string,
): Promise<AdvisorResult> {
  const res = await apiPost("/advisor/analyze", {
    optimization_result: optimizationResult,
    target_frequencies: targetFrequencies,
    use_llm: useLlm ?? false,
    llm_model: llmModel ?? "llama3.2",
  });
  if (!res.ok) throw new Error("Advisor analysis failed");
  return res.json();
}

export async function storeDesignInMemory(params: {
  instrument_type?: string;
  target_frequencies?: number[];
  bore_profile?: unknown[];
  n_control_points?: number;
  pop_size?: number;
  n_generations?: number;
  frequency_accuracy?: number;
  scale_evenness?: number;
  projection?: number;
  n_evaluations?: number;
  bore_length?: number;
  notes?: string;
}): Promise<{ status: string }> {
  const res = await apiPost("/advisor/store", params);
  if (!res.ok) throw new Error("Failed to store design");
  return res.json();
}

export async function getDesignHistory(limit?: number): Promise<{ designs: Record<string, unknown>[] }> {
  const res = await apiGet(`/advisor/history${limit ? `?limit=${limit}` : ""}`);
  if (!res.ok) throw new Error("Failed to get design history");
  return res.json();
}

// ─── Automated Design Agent (Design Desk) ───────────────────────────────

export interface AutoDesignIteration {
  iteration: number;
  pop_size: number;
  n_generations: number;
  n_control_points: number;
  frequency_accuracy: number;
  n_evaluations: number;
  bore_length: number;
  suggestions: string[];
}

export interface AutoDesignResult {
  instrument_type: string;
  target_frequencies: number[];
  best_accuracy: number;
  iterations: AutoDesignIteration[];
  total_evaluations: number;
  final_bore_profile: unknown[];
  final_bore_length: number;
  success: boolean;
  log: string[];
}

export interface AutoDesignJob {
  job_id: string;
  status: string;
  progress: string[];
  result?: AutoDesignResult;
  error?: string;
}

export async function startAutoDesign(
  instrumentType: string,
  maxIterations?: number,
  targetAccuracy?: number,
): Promise<{ job_id: string }> {
  const res = await apiPost("/design-desk/auto", {
    instrument_type: instrumentType,
    max_iterations: maxIterations ?? 3,
    target_accuracy: targetAccuracy ?? 3.0,
  });
  if (!res.ok) throw new Error(`Auto design start failed: ${res.statusText}`);
  return res.json();
}

export async function getAutoDesignStatus(jobId: string): Promise<AutoDesignJob> {
  const res = await apiGet(`/design-desk/instruments`);
  if (!res.ok) throw new Error("Auto design status check failed");
  const statusRes = await apiGet(`/optimize/${jobId}/status`);
  if (!statusRes.ok) throw new Error("Auto design status failed");
  return statusRes.json();
}

export async function getDesignDeskInstruments(): Promise<Record<string, string>> {
  const res = await apiGet("/design-desk/instruments");
  if (!res.ok) throw new Error("Failed to get design desk instruments");
  const data = await res.json();
  return data.instruments;
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
