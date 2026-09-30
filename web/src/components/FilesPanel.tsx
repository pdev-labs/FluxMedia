import { useEffect, useState } from "react";
import { listFiles, deleteFile } from "../lib/api.ts";
import type { FileEntry } from "../lib/api.ts";

export function FilesPanel(): React.JSX.Element {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [dir, setDir] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  async function refresh(): Promise<void> {
    setLoading(true);
    setError("");
    try {
      const data = await listFiles();
      setFiles(data.files);
      setDir(data.download_dir);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not load files.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void refresh();
  }, []);

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

      {loading ? (
        <div className="empty">Loading files…</div>
      ) : files.length === 0 ? (
        <div className="empty">No files yet. Download something first.</div>
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
