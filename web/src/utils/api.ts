const API_BASE = "http://localhost:8000";

export interface DesignJob {
  job_id: string;
  status: string;
  progress: string[];
  result?: { output_dir: string; files: string[] };
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
