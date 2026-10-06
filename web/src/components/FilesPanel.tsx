import { useEffect, useRef, useState } from "react";
import { listFiles, deleteFile } from "../lib/api.ts";
import type { FileEntry } from "../lib/api.ts";

export function FilesPanel(): React.JSX.Element {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [dir, setDir] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const firstLoad = useRef(true);

  async function refresh(q: string): Promise<void> {
    if (firstLoad.current) setLoading(true);
    setError("");
    try {
      const data = await listFiles(q);
      setFiles(data.files);
      setDir(data.download_dir);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load files.");
    } finally {
      firstLoad.current = false;
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh(query);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query]);

  async function remove(path: string, name: string): Promise<void> {
    if (!window.confirm(`Delete "${name}"?`)) return;
    try {
      await deleteFile(path);
      setFiles((prev) => prev.filter((f) => f.path !== path));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    }
  }

  return (
    <section className="panel">
      <h2>Downloaded files</h2>
      <p>{dir || "Your completed downloads appear here."}</p>

      {error && <div className="error">{error}</div>}

      <form
        className="url-form"
        style={{ margin: "0 0 16px", maxWidth: "none" }}
        onSubmit={(e) => e.preventDefault()}
      >
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search files…"
          aria-label="Search files"
        />
      </form>

      {loading ? (
        <div className="empty">Loading files…</div>
      ) : files.length === 0 ? (
        <div className="empty">
          {query ? `No files match "${query}".` : "No files yet. Download something first."}
        </div>
      ) : (
        <div className="table-card">
          {files.map((f) => (
            <div className="file-row" key={f.path}>
              <span className="file-name" title={f.name}>
                {f.name}
              </span>
              <span className="file-sub">
                {f.size} · {f.date}
              </span>
              <button
                className="file-del"
                onClick={() => void remove(f.path, f.name)}
              >
                Delete
              </button>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}
