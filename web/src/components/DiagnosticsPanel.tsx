import { useCallback, useEffect, useState } from "react";
import { getDiagnostics } from "../lib/api.ts";
import type { DiagCheck } from "../lib/api.ts";

export function DiagnosticsPanel(): React.JSX.Element {
  const [checks, setChecks] = useState<DiagCheck[]>([]);
  const [score, setScore] = useState<number | null>(null);
  const [platform, setPlatform] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const refresh = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const data = await getDiagnostics();
      setScore(data.score);
      setChecks(data.checks ?? []);
      const plat = (data as { platform?: string }).platform ?? "";
      setPlatform(plat);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not run diagnostics.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  return (
    <section className="panel">
      <h2>Diagnostics</h2>
      <p>
        {loading
          ? "Running system checks…"
          : score !== null
            ? `${score}% checks passing${platform ? ` · ${platform}` : ""}`
            : "System health at a glance."}
      </p>

      {error && <div className="error">{error}</div>}

      <div className="table-card">
        {checks.map((c) => (
          <div className="diag-row" key={c.name}>
            <span className={`dot ${c.status}`} />
            <span className="diag-name">{c.name}</span>
            <span className="diag-desc">{c.desc}</span>
          </div>
        ))}
        {!loading && checks.length === 0 && !error && (
          <div className="diag-row">
            <span className="diag-name">No checks returned.</span>
          </div>
        )}
      </div>
      <button className="btn btn-primary download-btn" onClick={refresh} disabled={loading}>
        {loading ? "Checking…" : "Re-run diagnostics"}
      </button>
    </section>
  );
}
