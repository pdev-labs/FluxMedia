/* Typed client for the classic LAN portal server (server/classic_portal.py).
   Contract: POST /api/auth, GET /api/meta (public), tokened file APIs. */

export type FileType = "video" | "audio" | "image" | "document" | "other";

export interface PortalMeta {
  profile_name: string;
  profile_image_url: string;
  theme_tone: string;
  password_protected: boolean;
}

export interface PortalFile {
  id: string;
  name: string;
  type: FileType;
  size: number;
  duration: number | null;
  thumbnail_url: string;
  added_at: string;
}

const TOKEN_KEY = "flux.portal.token";

export function getStoredToken(): string {
  try {
    return window.localStorage.getItem(TOKEN_KEY) ?? "";
  } catch {
    return "";
  }
}

export function storeToken(token: string): void {
  try {
    window.localStorage.setItem(TOKEN_KEY, token);
  } catch {
    /* private mode — session-only */
  }
}

export function clearToken(): void {
  try {
    window.localStorage.removeItem(TOKEN_KEY);
  } catch {
    /* ignore */
  }
}

export function withToken(url: string, token: string): string {
  if (!token) return url;
  return url + (url.includes("?") ? "&" : "?") + "token=" + encodeURIComponent(token);
}

export async function postAuth(password: string): Promise<string> {
  const res = await fetch("/api/auth", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ password }),
  });
  const data = (await res.json().catch(() => ({}))) as {
    token?: string;
    error?: string;
  };
  if (!res.ok || !data.token) throw new Error(data.error || "Login failed.");
  return data.token;
}

export async function getMeta(): Promise<PortalMeta> {
  const res = await fetch("/api/meta");
  if (!res.ok) throw new Error("Server unreachable.");
  return (await res.json()) as PortalMeta;
}

export async function getFiles(token: string): Promise<PortalFile[]> {
  // FIND-03: fetch() calls use the Authorization header so the token
  // stays out of URLs/logs. Media tags (<video>/<audio>/<img>/<track>)
  // cannot set headers, so withToken() query auth remains for those.
  const res = await fetch("/api/files", {
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  });
  if (res.status === 401) throw new Error("unauthorized");
  if (!res.ok) throw new Error("Could not load files.");
  return (await res.json()) as PortalFile[];
}

export function fileUrl(id: string, token: string): string {
  return withToken(`/api/file/${encodeURIComponent(id)}`, token);
}

export function thumbnailUrl(f: PortalFile, token: string): string {
  if (!f.thumbnail_url) return "";
  return withToken(f.thumbnail_url, token);
}

export function subtitlesUrl(id: string, token: string): string {
  return withToken(`/api/subtitles/${encodeURIComponent(id)}`, token);
}

export function formatSize(bytes: number): string {
  if (!bytes || bytes <= 0) return "—";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 ** 2) return `${(bytes / 1024).toFixed(1)} KB`;
  if (bytes < 1024 ** 3) return `${(bytes / 1024 ** 2).toFixed(1)} MB`;
  return `${(bytes / 1024 ** 3).toFixed(2)} GB`;
}

export function formatDuration(seconds: number | null): string {
  if (seconds === null || seconds === undefined || seconds < 0) return "";
  const m = Math.floor(seconds / 60);
  const s = Math.floor(seconds % 60);
  if (m >= 60) return `${Math.floor(m / 60)}:${String(m % 60).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}
