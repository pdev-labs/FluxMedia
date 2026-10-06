import { useEffect, useRef, useState } from "react";
import {
  analyze,
  startDownload,
  getJob,
  formatViews,
  formatSpeed,
  formatEta,
} from "../lib/api.ts";
import type { MediaMeta, DownloadStart } from "../lib/api.ts";
import {
  newSid,
  saveSession,
  loadSession,
  lastSid,
  clearSession,
  sessionUrl,
  tabUrl,
} from "../lib/session.ts";

type Phase = "idle" | "analyzing" | "ready" | "downloading" | "done";

const PLACEHOLDERS: Record<string, { hint: string; example: string }> = {
  youtube: {
    hint: "Paste a YouTube link to fetch available qualities.",
    example: "https://www.youtube.com/watch?v=...",
  },
  tiktok: {
    hint: "Paste a TikTok link to fetch download options.",
    example: "https://www.tiktok.com/@user/video/...",
  },
};

export function Downloader({
  source,
  initialSid,
}: {
  source: string;
  initialSid?: string | null;
}): React.JSX.Element {
  const [url, setUrl] = useState("");
  const [phase, setPhase] = useState<Phase>("idle");
  const [meta, setMeta] = useState<MediaMeta | null>(null);
  const [quality, setQuality] = useState("720p");
  const [viaBrowser, setViaBrowser] = useState(false);
  const [subLangs, setSubLangs] = useState("en");
  const [downloadUrl, setDownloadUrl] = useState("");
  const [downloadName, setDownloadName] = useState("");
  const [progress, setProgress] = useState(0);
  const [speed, setSpeed] = useState(0);
  const [eta, setEta] = useState(0);
  const [status, setStatus] = useState("");
  const [duplicate, setDuplicate] = useState<DownloadStart | null>(null);
  const [termLogs, setTermLogs] = useState<string[]>([]);
  const [showTerm, setShowTerm] = useState(false);
  const termRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState("");
  const pollRef = useRef<number | null>(null);
  // Session id for this paste. Resolved once on mount so later prop
  // changes (from our own hash updates) don't disturb the flow.
  const sidRef = useRef<string | null>(initialSid ?? lastSid(source));
  const restoredRef = useRef(false);

  const copy = PLACEHOLDERS[source] ?? PLACEHOLDERS.youtube;

  function persist(patch: {
    url?: string;
    quality?: string;
    browser?: boolean;
    jobId?: string | null;
  }): string | null {
    const sid = sidRef.current;
    if (!sid) return null;
    const prev = loadSession(sid);
    saveSession(sid, {
      source,
      url: patch.url ?? prev?.url ?? url,
      quality: patch.quality ?? prev?.quality ?? quality,
      browser: patch.browser ?? prev?.browser ?? viaBrowser,
      jobId: patch.jobId !== undefined ? patch.jobId : (prev?.jobId ?? null),
    });
    return sid;
  }

  function stopPolling(): void {
    if (pollRef.current !== null) {
      window.clearInterval(pollRef.current);
      pollRef.current = null;
    }
  }

  useEffect(() => {
    return () => stopPolling();
  }, []);

  // Auto-scroll the terminal view as new lines arrive.
  useEffect(() => {
    const el = termRef.current;
    if (el && showTerm) el.scrollTop = el.scrollHeight;
  }, [termLogs, showTerm]);

  function attachPoll(jobId: string, wantBrowser: boolean): void {
    stopPolling();
    pollRef.current = window.setInterval(async () => {
      try {
        const job = await getJob(jobId);
        setProgress(job.progress ?? 0);
        setSpeed(job.speed ?? 0);
        setEta(job.eta ?? 0);
        const last = job.logs?.[job.logs.length - 1] ?? "";
        if (last)
          setStatus(last.replace(/^\[(info|debug|warning|error|success)\]\s*/, ""));
        if (job.logs) setTermLogs([...job.logs]);
        if (job.status === "completed") {
          stopPolling();
          setProgress(100);
          if (wantBrowser && job.file_url) {
            setDownloadUrl(job.file_url);
            setDownloadName(job.file ?? "download");
            // Trigger the browser's own download manager.
            const a = document.createElement("a");
            a.href = job.file_url;
            a.download = job.file ?? "";
            document.body.appendChild(a);
            a.click();
            a.remove();
          }
          setPhase("done");
        } else if (job.status === "failed") {
          stopPolling();
          const tail = job.logs?.filter((l) => l.startsWith("[error]")).pop();
          setError(tail ? tail.replace(/^\[error\]\s*/, "") : "Download failed.");
          persist({ jobId: null });
          setPhase("ready");
        }
      } catch {
        /* keep polling on transient errors */
      }
    }, 800);
  }

  async function runAnalyze(clean: string): Promise<void> {
    setError("");
    setDuplicate(null);
    setPhase("analyzing");
    try {
      const data = await analyze(clean);
      setMeta(data);
      const ids = (data.qualities ?? []).map((q) => q.id);
      const q = ids.includes("720p") ? "720p" : (ids[0] ?? "720p");
      setQuality(q);
      // Mint the temporary URL for this paste.
      if (!sidRef.current) sidRef.current = newSid();
      persist({ url: clean, quality: q, jobId: null });
      window.location.hash = sessionUrl(source, sidRef.current);
      setPhase("ready");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Analysis failed.");
      setPhase("idle");
    }
  }

  // Restore a session on mount (refresh, shared link, or last session).
  useEffect(() => {
    if (restoredRef.current) return;
    restoredRef.current = true;
    const sid = sidRef.current;
    if (!sid) return;
    const sess = loadSession(sid);
    if (!sess?.url) return;
    setUrl(sess.url);
    setQuality(sess.quality || "720p");
    setViaBrowser(sess.browser);
    void runAnalyze(sess.url).then(() => {
      if (sess.jobId) {
        setStatus("Reconnected — resuming progress…");
        setShowTerm(true);
        setPhase("downloading");
        attachPoll(sess.jobId, sess.browser);
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handleAnalyze(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    const clean = url.trim();
    if (!clean || phase === "analyzing" || phase === "downloading") return;
    await runAnalyze(clean);
  }

  async function handleDownload(force = false): Promise<void> {
    if (!meta || phase === "downloading") return;
    setError("");
    setDuplicate(null);
    setProgress(0);
    setSpeed(0);
    setEta(0);
    setDownloadUrl("");
    setDownloadName("");
    setTermLogs([]);
    setShowTerm(true);
    setStatus("Starting download…");
    setPhase("downloading");
    try {
      const started = await startDownload(url.trim(), quality, viaBrowser, force, subLangs);
      if (!started.jobId) {
        setPhase("ready");
        setShowTerm(false);
        setDuplicate(started);
        return;
      }
      persist({ jobId: started.jobId });
      attachPoll(started.jobId, viaBrowser);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start download.");
      setPhase("ready");
    }
  }

  function pickQuality(id: string): void {
    setQuality(id);
    persist({ quality: id });
  }

  function toggleBrowser(v: boolean): void {
    setViaBrowser(v);
    persist({ browser: v });
  }

  function reset(): void {
    stopPolling();
    if (sidRef.current) {
      clearSession(sidRef.current, source);
      sidRef.current = null;
    }
    window.location.hash = tabUrl(source);
    setUrl("");
    setMeta(null);
    setPhase("idle");
    setProgress(0);
    setError("");
    setDuplicate(null);
    setStatus("");
    setTermLogs([]);
    setShowTerm(false);
  }

  const showHero = phase === "idle" || phase === "analyzing";

  return (
    <div>
      {showHero && (
        <section className="hero">
          <h1>
            Flux <span>Media</span>
          </h1>
          <p>{copy.hint}</p>
        </section>
      )}

      {(phase === "idle" || phase === "analyzing" || !meta) && (
        <form className="url-form" onSubmit={handleAnalyze}>
          <input
            type="url"
            required
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder={copy.example}
            aria-label="Video URL"
          />
          <button
            className="btn btn-primary"
            type="submit"
            disabled={phase === "analyzing"}
          >
            {phase === "analyzing" ? "Checking…" : "Continue"}
          </button>
        </form>
      )}

      {(phase === "idle" || phase === "analyzing") && !error && (
        <p className="hint">Supports YouTube, TikTok and 1000+ sites via yt-dlp.</p>
      )}

      {error && <div className="error">{error}</div>}

      {meta && (phase === "ready" || phase === "downloading" || phase === "done") && (
        <article className="card">
          {meta.thumbnail && (
            <img className="card-thumb" src={meta.thumbnail} alt="" />
          )}
          <div className="card-body">
            <h2 className="video-title">{meta.title}</h2>
            <p className="video-meta">
              {meta.uploader} · {meta.duration} · {formatViews(meta.views)}
            </p>

            <h3 className="section-label">VIDEO QUALITY</h3>
            <p className="section-sub">APPROXIMATE SIZES</p>

            <div className="quality-list">
              {(meta.qualities ?? []).map((q) => (
                <button
                  key={q.id}
                  type="button"
                  className={quality === q.id ? "quality-row selected" : "quality-row"}
                  onClick={() => phase === "ready" && pickQuality(q.id)}
                  disabled={phase !== "ready"}
                >
                  <span className="quality-check">✓</span>
                  <span className="quality-main">
                    <div className="quality-label">{q.label}</div>
                    <div className="quality-tag">{q.tag}</div>
                  </span>
                  {q.size && <span className="quality-size">{q.size}</span>}
                </button>
              ))}
            </div>

            {(phase === "ready" || phase === "downloading" || phase === "done") && (
              <div className="progress">
                {phase === "ready" && (
                  <label className="save-row">
                    <span>
                      Subtitles
                      <small>
                        <input
                          value={subLangs}
                          onChange={(e) => setSubLangs(e.target.value)}
                          placeholder="en"
                          aria-label="Subtitle languages"
                          style={{ width: 90 }}
                        />{" "}
                        comma-separated, e.g. en,es
                      </small>
                    </span>
                  </label>
                )}
                {phase === "ready" && (
                  <label className="save-row">
                    <input
                      type="checkbox"
                      checked={viaBrowser}
                      onChange={(e) => toggleBrowser(e.target.checked)}
                    />
                    <span>
                      Download via browser
                      <small>Save to this device's download folder</small>
                    </span>
                  </label>
                )}
                {phase === "downloading" && (
                  <>
                    <div className="progress-track">
                      <div
                        className="progress-fill"
                        style={{ width: `${progress}%` }}
                      />
                    </div>
                    <div className="progress-row">
                      <span className="progress-pct">{progress}%</span>
                      <span>
                        {[formatSpeed(speed), formatEta(eta), status]
                          .filter(Boolean)
                          .join(" · ")}
                      </span>
                    </div>
                  </>
                )}
                <button
                  className="btn btn-primary download-btn"
                  onClick={() => void handleDownload(false)}
                  disabled={phase === "downloading"}
                >
                  {phase === "downloading"
                    ? `Downloading… ${progress}%`
                    : "⬇ Download now"}
                </button>
              </div>
            )}

            {duplicate && (
              <div className="success-note">
                Already {duplicate.duplicate?.where ?? "downloaded"}
                {duplicate.duplicate?.title ? `: ${duplicate.duplicate.title}` : ""}.{" "}
                <button className="reset-link" onClick={() => void handleDownload(true)}>
                  Download again anyway
                </button>
              </div>
            )}

            {phase === "done" && (
              <div className="success-note">
                {downloadUrl ? (
                  <>
                    Download complete — saved via your browser.{" "}
                    <a href={downloadUrl} download={downloadName}>
                      Download again
                    </a>
                  </>
                ) : (
                  <>Download complete — check your FluxMedia folder.</>
                )}
              </div>
            )}

            {(phase === "downloading" || phase === "done") &&
              termLogs.length > 0 && (
                <div className="term">
                  <button
                    className="term-toggle"
                    onClick={() => setShowTerm((v) => !v)}
                    aria-expanded={showTerm}
                  >
                    <span className="term-dot" />
                    Terminal log
                    <span className="term-caret">{showTerm ? "▾" : "▸"}</span>
                  </button>
                  {showTerm && (
                    <div className="log-box" ref={termRef}>
                      {termLogs.join("\n")}
                    </div>
                  )}
                </div>
              )}
          </div>
        </article>
      )}

      {meta && (
        <div className="reset-wrap">
          <button className="reset-link" onClick={reset}>
            ← FETCH A NEW LINK
          </button>
        </div>
      )}
    </div>
  );
}
