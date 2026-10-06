import { useEffect, useState } from "react";
import { getSettings, updateSettings } from "../lib/api.ts";

const TEXT_KEYS: { key: string; label: string }[] = [
  { key: "download_dir", label: "Download folder" },
  { key: "filename_format", label: "Filename format" },
  { key: "audio_bitrate", label: "Audio bitrate" },
];

const SELECT_KEYS: { key: string; label: string; options: string[] }[] = [
  { key: "download_speed_limit", label: "Speed limit", options: ["disabled", "1M", "5M", "10M", "50M"] },
  { key: "cookies_browser", label: "Cookies browser", options: ["none", "chrome", "firefox", "edge", "brave", "opera"] },
  { key: "update_interval", label: "Update check", options: ["daily", "weekly", "monthly", "never"] },
  { key: "audio_format", label: "Audio format", options: ["mp3", "m4a", "flac", "wav", "ogg", "opus", "aac", "default"] },
];

const BOOL_KEYS: { key: string; label: string }[] = [
  { key: "embed_metadata", label: "Embed metadata" },
  { key: "embed_thumbnail", label: "Embed thumbnail" },
  { key: "embed_subtitles", label: "Embed subtitles" },
  { key: "show_educational_notice", label: "Startup notice" },
  { key: "web_auth_enabled", label: "Password-protect web UI" },
  { key: "clean_logs_enabled", label: "Write log files" },
  { key: "auto_update", label: "Automatic update checks" },
];

function asText(v: unknown): string {
  return typeof v === "string" || typeof v === "number" ? String(v) : "";
}

function asBool(v: unknown): boolean {
  return v === true;
}

export function SettingsPanel(): React.JSX.Element {
  const [settings, setSettings] = useState<Record<string, unknown> | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState(false);

  useEffect(() => {
    getSettings()
      .then(setSettings)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load settings."));
  }, []);

  function set(key: string, value: unknown): void {
    setSettings((prev) => (prev ? { ...prev, [key]: value } : prev));
    setDone(false);
  }

  async function save(): Promise<void> {
    if (!settings || busy) return;
    setBusy(true);
    setError("");
    try {
      const updated = await updateSettings(settings);
      setSettings(updated);
      setDone(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not save settings.");
    } finally {
      setBusy(false);
    }
  }

  if (!settings) {
    return (
      <section className="panel">
        <h2>Settings</h2>
        <p>{error || "Loading settings…"}</p>
        {error && <div className="error">{error}</div>}
      </section>
    );
  }

  return (
    <section className="panel">
      <h2>Settings</h2>
      <p>Changes apply to new downloads immediately.</p>

      {error && <div className="error">{error}</div>}
      {done && <div className="success-note">Settings saved.</div>}

      <div className="table-card">
        {TEXT_KEYS.map(({ key, label }) => (
          <div className="file-row" key={key}>
            <span className="file-name">{label}</span>
            <input
              className="text-input"
              value={asText(settings[key])}
              onChange={(e) => set(key, e.target.value)}
              aria-label={label}
            />
          </div>
        ))}
        {SELECT_KEYS.map(({ key, label, options }) => (
          <div className="file-row" key={key}>
            <span className="file-name">{label}</span>
            <select
              className="select-input"
              value={asText(settings[key])}
              onChange={(e) => set(key, e.target.value)}
              aria-label={label}
            >
              {!options.includes(asText(settings[key])) && (
                <option value={asText(settings[key])}>{asText(settings[key])}</option>
              )}
              {options.map((o) => (
                <option key={o} value={o}>
                  {o}
                </option>
              ))}
            </select>
          </div>
        ))}
        {BOOL_KEYS.map(({ key, label }) => (
          <div className="file-row" key={key}>
            <span className="file-name">{label}</span>
            <input
              type="checkbox"
              checked={asBool(settings[key])}
              onChange={(e) => set(key, e.target.checked)}
              aria-label={label}
            />
          </div>
        ))}
      </div>
      <button className="btn btn-primary download-btn" onClick={save} disabled={busy}>
        {busy ? "Saving…" : "Save settings"}
      </button>
    </section>
  );
}
