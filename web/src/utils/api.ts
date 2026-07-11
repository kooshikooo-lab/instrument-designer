const API_BASE = "http://localhost:8000";

export async function checkHealth(): Promise<{ status: string }> {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}

export async function getPresets(): Promise<Record<string, string>> {
  const res = await fetch(`${API_BASE}/presets`);
  return res.json();
}

export async function startDesign(
  preset: string,
  transpose: number
): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/design`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ preset, transpose }),
  });
  return res.json();
}

export async function getDesignStatus(
  jobId: string
): Promise<{ status: string; progress: string[] }> {
  const res = await fetch(`${API_BASE}/design/${jobId}`);
  return res.json();
}

export function getDesignDownloadUrl(jobId: string): string {
  return `${API_BASE}/design/${jobId}/download`;
}
