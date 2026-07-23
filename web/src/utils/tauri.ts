const API_BASE = "http://localhost:8000";

export function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI__" in window;
}

export function getApiBase(): string {
  return API_BASE;
}

// ── Tauri-native commands (used when running in Tauri) ──────────────

async function invokeTauri<T>(cmd: string, args?: Record<string, unknown>): Promise<T> {
  // @ts-expect-error Tauri API injected at runtime
  return window.__TAURI__.core.invoke(cmd, args);
}

export async function tauriStartServer(port = 8000): Promise<string> {
  return invokeTauri<string>("server_start", { port });
}

export async function tauriStopServer(): Promise<string> {
  return invokeTauri<string>("server_stop");
}

export async function tauriServerRunning(): Promise<boolean> {
  return invokeTauri<boolean>("server_status");
}

export async function tauriHttpGet(url: string): Promise<string> {
  return invokeTauri<string>("http_get", { url });
}

export async function tauriHttpPost(url: string, body: unknown): Promise<string> {
  return invokeTauri<string>("http_post", { url, body });
}

export async function tauriSaveFileDialog(
  defaultName: string,
  filterName: string,
  filterExt: string,
): Promise<string | null> {
  return invokeTauri<string | null>("save_file_dialog", {
    defaultName,
    filterName,
    filterExt,
  });
}

export async function tauriOpenFileDialog(
  filterName: string,
  filterExt: string,
): Promise<string | null> {
  return invokeTauri<string | null>("open_file_dialog", {
    filterName,
    filterExt,
  });
}

export async function tauriSaveStl(path: string, data: number[]): Promise<void> {
  return invokeTauri("save_stl_to_disk", { path, data });
}

export async function tauriReadStl(path: string): Promise<number[]> {
  return invokeTauri("read_stl_from_disk", { path });
}
