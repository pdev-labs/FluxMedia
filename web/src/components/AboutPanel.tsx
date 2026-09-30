import { useEffect, useState } from "react";
import { getDiagnostics, getStats } from "../lib/api.ts";
import type { DiagCheck } from "../lib/api.ts";

export function AboutPanel(): React.JSX.Element {
  const [checks, setChecks] = useState<DiagCheck[]>([]);
  const [score, setScore] = useState(0);
  const [stats, setStats] = useState<{
    total_downloads: number;
    completed: number;
    failed: number;
    total_size: string;
  } | null>(null);

  useEffect(() => {
    getDiagnostics()
      .then((d) => {
        setScore(d.score);
        setChecks(d.checks);
      })
      .catch(() => {});
    getStats()
      .then(setStats)
      .catch(() => {});
  }, []);

  return (
    <section className="panel">
      <h2>About FluxMedia</h2>
      <p>
        A local video downloader. Paste a link, pick a quality, save the file
        to your machine. Powered by yt-dlp — no account, no uploads.
      </p>

      {stats && (
        <div className="stat-grid">
          <div className="stat">
            <div className="stat-value">{stats.total_downloads}</div>
            <div className="stat-label">Total downloads</div>
          </div>
          <div className="stat">
            <div className="stat-value">{stats.completed}</div>
            <div className="stat-label">Completed</div>
          </div>
          <div className="stat">
            <div className="stat-value">{stats.total_size}</div>
            <div className="stat-label">Library size</div>
          </div>
        </div>
      )}

      <div className="table-card">
        <div className="diag-row">
          <span className="dot pass" />
          <span className="diag-name">System status</span>
          <span className="diag-desc">{score}% checks passing</span>
        </div>
        {checks.map((c) => (
          <div className="diag-row" key={c.name}>
            <span className={`dot ${c.status}`} />
            <span className="diag-name">{c.name}</span>
            <span className="diag-desc">{c.desc}</span>
          </div>
        ))}
      </div>

      <p className="hint" style={{ marginTop: 20 }}>
        Supported: YouTube, TikTok, Instagram and 1000+ sites supported by
        yt-dlp. For best YouTube quality, keep FFmpeg installed.
      </p>
    </section>
  );
}
