/* Temporary download-session URLs.
   When a link is analyzed we mint a session id and put it in the address
   bar (#/youtube/s/<id>), so each paste gets its own URL. Sessions live in
   sessionStorage: switching nav tabs never touches them, and a refresh or
   a shared link restores the URL and re-attaches to the running job. */

export interface SessionData {
  source: string;
  url: string;
  quality: string;
  browser: boolean;
  jobId: string | null;
}

function skey(sid: string): string {
  return `flux:sess:${sid}`;
}

function lkey(source: string): string {
  return `flux:last:${source}`;
}

export function newSid(): string {
  return Math.random().toString(36).slice(2, 10);
}

export function saveSession(sid: string, data: SessionData): void {
  try {
    sessionStorage.setItem(skey(sid), JSON.stringify(data));
    sessionStorage.setItem(lkey(data.source), sid);
  } catch {
    /* storage unavailable — sessions just won't survive refresh */
  }
}

export function loadSession(sid: string): SessionData | null {
  try {
    const raw = sessionStorage.getItem(skey(sid));
    if (!raw) return null;
    return JSON.parse(raw) as SessionData;
  } catch {
    return null;
  }
}

export function lastSid(source: string): string | null {
  try {
    return sessionStorage.getItem(lkey(source));
  } catch {
    return null;
  }
}

export function clearSession(sid: string, source: string): void {
  try {
    sessionStorage.removeItem(skey(sid));
    if (sessionStorage.getItem(lkey(source)) === sid) {
      sessionStorage.removeItem(lkey(source));
    }
  } catch {
    /* ignore */
  }
}

export function sessionUrl(source: string, sid: string): string {
  return `#/${source}/s/${sid}`;
}

export function tabUrl(tab: string): string {
  return `#/${tab}`;
}
