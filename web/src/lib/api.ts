/* Typed wrappers around the FluxMedia backend API. */

export interface QualityOption {
  id: string;
  label: string;
  tag: string;
  size: string | null;
}

export interface MediaMeta {
  title: string;
  uploader: string;
  views: number;
  likes: number;
  duration: string;
  date: string;
  thumbnail: string;
  qualities: QualityOption[];
}

export interface JobState {
  status: string;
  progress: number;
  speed: number;
  eta: number;
  logs: string[];
  file?: string;
  file_url?: string;
}

export interface FileEntry {
  id: string;
  name: string;
  path: string;
  relative_path: string;
  type: string;
  ext: string;
  size: string;
  size_bytes: number;
  date: string;
}

export interface DiagCheck {
  name: string;
  status: string;
  desc: string;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      (data as { detail?: string }).detail || `Request failed (${res.status})`,
    );
  }
  return data as T;
}

async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path);
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new Error(
      (data as { detail?: string }).detail || `Request failed (${res.status})`,
    );
  }
  return data as T;
}

export async function analyze(url: string): Promise<MediaMeta> {
  const data = await postJson<{ status: string; metadata: MediaMeta }>(
    "/api/analyze",
    { url },
  );
  if (data.status !== "success" || !data.metadata) {
    throw new Error("Could not analyze this link.");
  }
  return data.metadata;
}

export interface DownloadStart {
  jobId: string | null;
  duplicate?: { where: string; title: string | null; timestamp: string | null };
  message?: string;
}

export async function startDownload(
  url: string,
  qualityId: string,
  viaBrowser = false,
  force = false,
  subtitleLangs = "",
): Promise<DownloadStart> {
  const data = await postJson<{
    status: string;
    job_id: string | null;
    message?: string;
    duplicate?: DownloadStart["duplicate"];
  }>("/api/download", {
    url,
    type: qualityId === "audio" ? "audio" : "video",
    quality: qualityId,
    browser: viaBrowser,
    force,
    subtitle_langs: subtitleLangs || undefined,
  });
  if (data.status === "duplicate") {
    return { jobId: null, duplicate: data.duplicate, message: data.message };
  }
  if (data.status !== "success" || !data.job_id) {
    throw new Error("Could not start the download.");
  }
  return { jobId: data.job_id };
}

export async function getJob(jobId: string): Promise<JobState> {
  const data = await getJson<{ status: string; job: JobState }>(
    `/api/job/${jobId}`,
  );
  return data.job;
}

export async function listFiles(
  query = "",
): Promise<{ files: FileEntry[]; download_dir: string }> {
  const q = query.trim()
    ? `&q=${encodeURIComponent(query.trim())}`
    : "";
  const data = await getJson<{
    status: string;
    files: FileEntry[];
    download_dir: string;
  }>(`/api/files?category=all${q}`);
  return { files: data.files ?? [], download_dir: data.download_dir ?? "" };
}

export async function deleteFile(path: string): Promise<void> {
  const res = await fetch(`/api/files?path=${encodeURIComponent(path)}`, {
    method: "DELETE",
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(
      (data as { detail?: string }).detail || "Could not delete the file.",
    );
  }
}

export interface LogLine {
  timestamp: string;
  severity: string;
  component: string;
  message: string;
}

export async function getLogs(lines = 300): Promise<LogLine[]> {
  const data = await getJson<{ status: string; logs: LogLine[] }>(
    `/api/logs?lines=${lines}`,
  );
  return data.logs ?? [];
}

export async function getDiagnostics(): Promise<{
  score: number;
  checks: DiagCheck[];
}> {
  const data = await getJson<{ score: number; checks: DiagCheck[] }>(
    "/api/diagnostics",
  );
  return { score: data.score ?? 0, checks: data.checks ?? [] };
}

export async function getStats(): Promise<{
  total_downloads: number;
  completed: number;
  failed: number;
  total_size: string;
}> {
  const data = await getJson<{
    total_downloads: number;
    completed: number;
    failed: number;
    total_size: string;
  }>("/api/stats");
  return data;
}

export interface FfmpegInfo {
  available: boolean;
  version: string | null;
  path: string | null;
}

export async function checkFfmpeg(): Promise<FfmpegInfo> {
  return getJson<FfmpegInfo>("/api/convert/check");
}

export interface ConvertArgs {
  input_path: string;
  output_format: string;
  quality?: string;
  resolution?: string | null;
  audio_bitrate?: string;
}

export async function startConvert(
  args: ConvertArgs,
): Promise<{ job_id: string; message: string; output_path: string }> {
  return postJson<{ status: string; job_id: string; message: string; output_path: string }>(
    "/api/convert",
    args,
  );
}

export interface PlaylistEntry {
  index: number;
  title: string;
  url: string;
  duration: number | null;
}

export interface PlaylistInfo {
  title: string;
  count: number;
  truncated: boolean;
  entries: PlaylistEntry[];
}

export async function listPlaylist(url: string, limit = 50): Promise<PlaylistInfo> {
  const data = await postJson<{
    status: string;
    title: string;
    count: number;
    truncated: boolean;
    entries: PlaylistEntry[];
  }>("/api/playlist", { url, limit });
  if (data.status !== "success") throw new Error("Could not read playlist.");
  return {
    title: data.title,
    count: data.count,
    truncated: !!data.truncated,
    entries: data.entries ?? [],
  };
}

export async function getSettings(): Promise<Record<string, unknown>> {
  const data = await getJson<{ status: string; settings: Record<string, unknown> }>(
    "/api/settings",
  );
  return data.settings ?? {};
}

export async function updateSettings(
  settings: Record<string, unknown>,
): Promise<Record<string, unknown>> {
  const data = await postJson<{ status: string; settings: Record<string, unknown> }>(
    "/api/settings",
    { settings },
  );
  return data.settings ?? {};
}

export function formatViews(views: number): string {
  if (!views || views <= 0) return "Unknown views";
  if (views >= 1_000_000_000) return `${(views / 1_000_000_000).toFixed(1)}B views`;
  if (views >= 1_000_000) return `${(views / 1_000_000).toFixed(1)}M views`;
  if (views >= 1_000) return `${(views / 1_000).toFixed(1)}K views`;
  return `${views} views`;
}

export function formatSpeed(bytesPerSec: number): string {
  if (!bytesPerSec || bytesPerSec <= 0) return "";
  if (bytesPerSec >= 1024 ** 2) return `${(bytesPerSec / 1024 ** 2).toFixed(1)} MB/s`;
  if (bytesPerSec >= 1024) return `${(bytesPerSec / 1024).toFixed(0)} KB/s`;
  return `${bytesPerSec} B/s`;
}

export function formatEta(seconds: number): string {
  if (!seconds || seconds <= 0) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m <= 0) return `${s}s left`;
  return `${m}m ${s}s left`;
}
