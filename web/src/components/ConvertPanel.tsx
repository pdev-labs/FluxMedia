import { useEffect, useState } from "react";
import { checkFfmpeg, startConvert } from "../lib/api.ts";

const VIDEO_FORMATS = ["mp4", "mkv", "webm", "mov", "avi"];
const AUDIO_FORMATS = ["mp3", "m4a", "flac", "wav", "ogg", "opus", "aac"];

export function ConvertPanel(): React.JSX.Element {
  const [ffmpeg, setFfmpeg] = useState<string | null>(null);
  const [inputPath, setInputPath] = useState("");
  const [format, setFormat] = useState("mp4");
  const [quality, setQuality] = useState("medium");
  const [resolution, setResolution] = useState("");
  const [bitrate, setBitrate] = useState("192k");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const [done, setDone] = useState("");

  useEffect(() => {
    checkFfmpeg()
      .then((info) =>
        setFfmpeg(info.available ? (info.version ?? "available") : null),
      )
      .catch(() => setFfmpeg(null));
  }, []);

  const isAudio = AUDIO_FORMATS.includes(format);

  async function submit(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    if (!inputPath.trim() || busy) return;
    setBusy(true);
    setError("");
    setDone("");
    try {
      const res = await startConvert({
        input_path: inputPath.trim(),
        output_format: format,
        quality,
        resolution: resolution || null,
        audio_bitrate: bitrate,
      });
      setDone(`${res.message} Output: ${res.output_path}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Conversion failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="panel">
      <h2>Media converter</h2>
      <p>
        {ffmpeg
          ? `FFmpeg ready — ${ffmpeg.slice(0, 60)}`
          : "FFmpeg was not found. Install it to enable conversion."}
      </p>

      {error && <div className="error">{error}</div>}
      {done && <div className="success-note">{done}</div>}

      <form onSubmit={submit}>
        <div className="table-card">
          <div className="file-row">
            <span className="file-name">Input file path</span>
          </div>
          <div className="file-row">
            <input
              className="text-input"
              value={inputPath}
              onChange={(e) => setInputPath(e.target.value)}
              placeholder="/path/to/video.mp4"
              aria-label="Input file path"
              style={{ width: "100%" }}
            />
          </div>
          <div className="file-row">
            <span className="file-name">Output format</span>
            <select
              className="select-input"
              value={format}
              onChange={(e) => setFormat(e.target.value)}
              aria-label="Output format"
            >
              <optgroup label="Video">
                {VIDEO_FORMATS.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </optgroup>
              <optgroup label="Audio">
                {AUDIO_FORMATS.map((f) => (
                  <option key={f} value={f}>
                    {f}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>
          {!isAudio && (
            <>
              <div className="file-row">
                <span className="file-name">Quality</span>
                <select
                  className="select-input"
                  value={quality}
                  onChange={(e) => setQuality(e.target.value)}
                  aria-label="Quality"
                >
                  <option value="high">High</option>
                  <option value="medium">Medium</option>
                  <option value="low">Low</option>
                </select>
              </div>
              <div className="file-row">
                <span className="file-name">Resolution</span>
                <select
                  className="select-input"
                  value={resolution}
                  onChange={(e) => setResolution(e.target.value)}
                  aria-label="Resolution"
                >
                  <option value="">Original</option>
                  <option value="1080p">1080p</option>
                  <option value="720p">720p</option>
                  <option value="480p">480p</option>
                </select>
              </div>
            </>
          )}
          {isAudio && (
            <div className="file-row">
              <span className="file-name">Audio bitrate</span>
              <select
                className="select-input"
                value={bitrate}
                onChange={(e) => setBitrate(e.target.value)}
                aria-label="Audio bitrate"
              >
                <option value="128k">128k</option>
                <option value="192k">192k</option>
                <option value="256k">256k</option>
                <option value="320k">320k</option>
              </select>
            </div>
          )}
        </div>
        <button className="btn btn-primary download-btn" disabled={busy || !ffmpeg}>
          {busy ? "Converting…" : "Convert"}
        </button>
      </form>
    </section>
  );
}
