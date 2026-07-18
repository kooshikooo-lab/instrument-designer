const API_BASE = "http://localhost:8000";

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

export async function checkHealth(): Promise<{ status: string; version: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function getPresets(): Promise<Record<string, string>> {
  const res = await fetch(`${API_BASE}/presets`);
  const data = await res.json();
  return data.presets;
}

export async function startDesign(preset: string, transpose: number = 0): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/design`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset, transpose }),
  });
  return res.json();
}

export async function getDesignStatus(jobId: string): Promise<DesignJob> {
  const res = await fetch(`${API_BASE}/design/${jobId}/status`);
  return res.json();
}

export function getDesignDownloadUrl(jobId: string): string {
  return `${API_BASE}/design/${jobId}/download`;
}

export async function exportStep(params: StepExportParams): Promise<Blob> {
  const res = await fetch(`${API_BASE}/export/step`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`STEP export failed: ${res.statusText}`);
  return res.blob();
}

export async function computeImpedance(preset: string): Promise<{
  frequencies: number[];
  impedanceMagnitude: number[];
  impedanceReal: number[];
  impedanceImag: number[];
}> {
  const res = await fetch(`${API_BASE}/impedance/compute`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset }),
  });
  if (!res.ok) throw new Error(`Impedance computation failed: ${res.statusText}`);
  return res.json();
}

export async function getPrecomputedImpedance(preset: string): Promise<{
  frequencies: number[];
  impedance_magnitude: number[];
}> {
  const res = await fetch(`${API_BASE}/impedance/precomputed/${preset}`);
  if (!res.ok) throw new Error(`Precomputed impedance not found: ${preset}`);
  return res.json();
}

export interface SimulateSoundParams {
  preset: string;
  duration?: number;
  player_type?: string;
  temperature?: number;
}

export async function simulateSound(params: SimulateSoundParams): Promise<Blob> {
  const res = await fetch(`${API_BASE}/simulate/sound`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(params),
  });
  if (!res.ok) throw new Error(`Sound simulation failed: ${res.statusText}`);
  return res.blob();
}

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
  const res = await fetch(`${API_BASE}/analyze/audio`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset, top_peaks: topPeaks ?? 10 }),
  });
  if (!res.ok) throw new Error(`Audio analysis failed: ${res.statusText}`);
  return res.json();
}
