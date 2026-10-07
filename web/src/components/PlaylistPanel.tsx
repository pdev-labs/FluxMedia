import { useRef, useState } from "react";
import { getJob, listPlaylist, startDownload } from "../lib/api.ts";
import type { PlaylistEntry } from "../lib/api.ts";

type ItemState = "queued" | "done" | "failed" | "duplicate";

export function PlaylistPanel(): React.JSX.Element {
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [title, setTitle] = useState("");
  const [truncated, setTruncated] = useState(false);
  const [entries, setEntries] = useState<PlaylistEntry[]>([]);
  const [checked, setChecked] = useState<Set<number>>(new Set());
  const [jobs, setJobs] = useState<Record<number, { state: ItemState; label: string }>>({});
  const pollers = useRef<Record<number, number>>({});

  async function lookup(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const clean = url.trim();
    if (!clean || busy) return;
    setBusy(true);
    setError("");
    setJobs({});
    try {
      const info = await listPlaylist(clean);
      setTitle(info.title);
      setTruncated(info.truncated);
      setEntries(info.entries);
      setChecked(new Set(info.entries.map((x) => x.index)));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not read playlist.");
      setEntries([]);
    } finally {
      setBusy(false);
    }
  }

  function toggleAll(): void {
    setChecked((prev) =>
      prev.size === entries.length ? new Set() : new Set(entries.map((x) => x.index)),
    );
  }

  function toggleOne(index: number): void {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(index)) next.delete(index);
      else next.add(index);
      return next;
    });
  }

  function pollJob(index: number, jobId: string, name: string): void {
    const id = window.setInterval(async () => {
      try {
        const job = await getJob(jobId);
        if (job.status === "completed" || job.status === "failed") {
          window.clearInterval(id);
          delete pollers.current[index];
          setJobs((prev) => ({
            ...prev,
            [index]: {
              state: job.status === "completed" ? "done" : "failed",
              label: job.status === "completed" ? "Downloaded" : "Failed",
            },
          }));
        }
      } catch {
        /* keep polling on transient errors */
      }
    }, 1500);
    pollers.current[index] = id;
    setJobs((prev) => ({ ...prev, [index]: { state: "queued", label: `Queued: ${name}` } }));
  }

  async function downloadSelected(): Promise<void> {
    const picked = entries.filter((e) => checked.has(e.index));
    if (picked.length === 0 || busy) return;
    setError("");
    for (const entry of picked) {
      try {
        const started = await startDownload(entry.url, "720p", false, false);
        if (!started.jobId) {
          setJobs((prev) => ({
            ...prev,
            [entry.index]: { state: "duplicate", label: "Already have it" },
          }));
          continue;
        }
        pollJob(entry.index, started.jobId, entry.title.slice(0, 30));
      } catch (err) {
        setJobs((prev) => ({
          ...prev,
          [entry.index]: {
            state: "failed",
            label: err instanceof Error ? err.message : "Failed to queue",
          },
        }));
      }
    }
  }

  return (
    <section className="panel">
      <h2>Playlist downloader</h2>
      <p>Paste a playlist or channel link, pick videos, download the batch.</p>

      <form className="url-form" onSubmit={lookup}>
        <input
          type="url"
          required
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/playlist?list=…"
          aria-label="Playlist URL"
        />
        <button className="btn btn-primary" type="submit" disabled={busy}>
          {busy ? "Reading…" : "List videos"}
        </button>
      </form>

      {error && <div className="error">{error}</div>}

      {entries.length > 0 && (
        <>
          <div className="section-label">
            {title.slice(0, 60)} — {entries.length} videos
            {truncated ? " (first 200 shown)" : ""}
          </div>
          <div className="reset-wrap" style={{ textAlign: "left", margin: "8px 0" }}>
            <button className="reset-link" onClick={toggleAll}>
              {checked.size === entries.length ? "Deselect all" : "Select all"}
            </button>
          </div>
          <div className="table-card">
            {entries.map((e) => {
              const st = jobs[e.index];
              return (
                <div className="file-row" key={e.index}>
                  <input
                    type="checkbox"
                    checked={checked.has(e.index)}
                    onChange={() => toggleOne(e.index)}
                    aria-label={`Select ${e.title}`}
                  />
                  <span className="file-name" title={e.title}>
                    {e.index + 1}. {e.title}
                  </span>
                  <span className="file-sub">
                    {st ? st.label : e.duration ? `${Math.floor(e.duration / 60)}m` : ""}
                  </span>
                </div>
              );
            })}
          </div>
          <button
            className="btn btn-primary download-btn"
            onClick={() => void downloadSelected()}
            disabled={checked.size === 0}
          >
            Download selected ({checked.size})
          </button>
        </>
      )}
    </section>
  );
}
