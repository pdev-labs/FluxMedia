import { useEffect, useRef, useState } from "react";
import { getLogs } from "../lib/api.ts";
import type { LogLine } from "../lib/api.ts";

const FILTERS = ["all", "info", "warning", "error", "debug"] as const;
type Filter = (typeof FILTERS)[number];

export function LogsPanel(): React.JSX.Element {
  const [lines, setLines] = useState<LogLine[]>([]);
  const [filter, setFilter] = useState<Filter>("all");
  const [auto, setAuto] = useState(true);
  const [error, setError] = useState("");
  const boxRef = useRef<HTMLDivElement | null>(null);

  async function refresh(): Promise<void> {
    try {
      const data = await getLogs(300);
      setLines(data);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load logs.");
    }
  }

  useEffect(() => {
    void refresh();
    if (!auto) return;
    const id = window.setInterval(() => void refresh(), 3000);
    return () => window.clearInterval(id);
  }, [auto]);

  useEffect(() => {
    const el = boxRef.current;
    if (el && auto) el.scrollTop = el.scrollHeight;
  }, [lines, auto]);

  const visible =
    filter === "all" ? lines : lines.filter((l) => l.severity === filter);

  return (
    <section className="panel">
      <h2>Console logs</h2>
      <p>Real server output — newest entries at the bottom.</p>

      <div className="log-bar">
        <div className="log-filters">
          {FILTERS.map((f) => (
            <button
              key={f}
              className={filter === f ? "chip active" : "chip"}
              onClick={() => setFilter(f)}
            >
              {f}
            </button>
          ))}
        </div>
        <div className="log-actions">
          <label className="mini-check">
            <input
              type="checkbox"
              checked={auto}
              onChange={(e) => setAuto(e.target.checked)}
            />
            Auto-refresh
          </label>
          <button className="file-del" onClick={() => void refresh()}>
            Refresh
          </button>
        </div>
      </div>

      {error && <div className="error">{error}</div>}

      {visible.length === 0 ? (
        <div className="empty">No log entries yet.</div>
      ) : (
        <div className="log-box log-tall" ref={boxRef}>
          {visible.map((l, i) => (
            <div key={i} className={`log-line sev-${l.severity}`}>
              {l.timestamp && <span className="log-ts">{l.timestamp} </span>}
              <span className="log-sev">[{l.severity}] </span>
              {l.component !== "system" && (
                <span className="log-comp">{l.component}: </span>
              )}
              {l.message}
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
