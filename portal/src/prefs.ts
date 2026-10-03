/* Viewer preferences, persisted locally. Server tone stays the default
   accent; anything the viewer picks here overrides it on their device. */

export type SortKey = "newest" | "name" | "size";
export type ViewMode = "grid" | "list";

export interface Prefs {
  accent: string | null;
  sort: SortKey;
  view: ViewMode;
}

const KEY = "flux.portal.prefs";

const DEFAULTS: Prefs = { accent: null, sort: "newest", view: "grid" };

export function loadPrefs(): Prefs {
  try {
    const raw = window.localStorage.getItem(KEY);
    if (!raw) return { ...DEFAULTS };
    const p = JSON.parse(raw) as Partial<Prefs>;
    return {
      accent: typeof p.accent === "string" ? p.accent : null,
      sort: p.sort === "name" || p.sort === "size" ? p.sort : "newest",
      view: p.view === "list" ? "list" : "grid",
    };
  } catch {
    return { ...DEFAULTS };
  }
}

export function savePrefs(p: Prefs): void {
  try {
    window.localStorage.setItem(KEY, JSON.stringify(p));
  } catch {
    /* private mode */
  }
}

/* Playback resume positions, keyed by stable file identity. */

function posKey(name: string, size: number): string {
  return `flux.pos.${size}::${name}`;
}

export function loadPosition(name: string, size: number): number {
  try {
    const v = window.localStorage.getItem(posKey(name, size));
    const n = v === null ? 0 : Number(v);
    return Number.isFinite(n) && n > 0 ? n : 0;
  } catch {
    return 0;
  }
}

export function savePosition(name: string, size: number, seconds: number): void {
  try {
    if (seconds < 5) {
      window.localStorage.removeItem(posKey(name, size));
      return;
    }
    window.localStorage.setItem(posKey(name, size), String(Math.floor(seconds)));
  } catch {
    /* ignore */
  }
}

export function clearPosition(name: string, size: number): void {
  try {
    window.localStorage.removeItem(posKey(name, size));
  } catch {
    /* ignore */
  }
}
