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

// ─── Chalumier API ──────────────────────────────────────────────────────

export interface ChalumierStatus {
  available: boolean;
  jar_path: string | null;
  chalumier_dir: string;
  examples_exist: boolean;
}

export interface ChalumierDesignResult {
  success: boolean;
  log: string;
  bore_profile: number[][];
  hole_positions: number[];
  hole_diameters: number[];
  length: number;
  svg_path: string;
  json_path: string;
  output_dir: string;
}

export interface ChalumierDesignJob {
  job_id: string;
  status: string;
  progress: string[];
  result?: ChalumierDesignResult;
  error?: string;
}

export async function getChalumierStatus(): Promise<ChalumierStatus> {
  const res = await apiGet("/chalumier/status");
  if (!res.ok) throw new Error("Failed to get chalumier status");
  return res.json();
}

export async function getChalumierPresets(): Promise<Record<string, string>> {
  const res = await apiGet("/chalumier/presets");
  if (!res.ok) throw new Error("Failed to get chalumier presets");
  const data = await res.json();
  return data.presets;
}

export async function getChalumierChalContent(presetKey: string): Promise<{ preset: string; filename: string; content: string }> {
  const res = await apiGet(`/chalumier/presets/${presetKey}/chal`);
  if (!res.ok) throw new Error("Failed to get .chal content");
  return res.json();
}

export async function startChalumierDesign(preset: string): Promise<{ job_id: string }> {
  const res = await apiPost("/chalumier/design", { preset });
  if (!res.ok) throw new Error(`Chalumier design start failed: ${res.statusText}`);
  return res.json();
}

export async function getChalumierDesignStatus(jobId: string): Promise<ChalumierDesignJob> {
  const res = await apiGet(`/chalumier/design/${jobId}/status`);
  if (!res.ok) throw new Error("Chalumier design status failed");
  return res.json();
}

export async function buildChalumier(): Promise<{ success: boolean; log: string }> {
  const res = await apiPost("/chalumier/build", {});
  if (!res.ok) throw new Error("Chalumier build request failed");
  return res.json();
}
