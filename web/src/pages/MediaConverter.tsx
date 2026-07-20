import React, { useState, useEffect } from "react";
import {
  RefreshCw, FileVideo, Music, Layers, Sliders, Scissors,
  Terminal, AlertTriangle, CheckCircle2, XCircle
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";
import { cn } from "../utils/cn";

interface FFmpegStatus {
  available: boolean;
  version: string | null;
  path: string | null;
}

interface ConvertJob {
  job_id: string;
  message: string;
  output_path: string;
}

export const MediaConverter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"video" | "audio" | "batch">("video");
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState(0);
  const [ffmpeg, setFfmpeg] = useState<FFmpegStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [lastJob, setLastJob] = useState<ConvertJob | null>(null);
  const [logs, setLogs] = useState<string[]>([]);

  // Video settings
  const [videoInput, setVideoInput] = useState("");
  const [videoFormat, setVideoFormat] = useState("mp4");
  const [videoQuality, setVideoQuality] = useState("medium");
  const [videoResolution, setVideoResolution] = useState("");
  const [startTime, setStartTime] = useState("");
  const [endTime, setEndTime] = useState("");

  // Audio settings
  const [audioInput, setAudioInput] = useState("");
  const [audioFormat, setAudioFormat] = useState("mp3");
  const [audioBitrate, setAudioBitrate] = useState("192k");
  const [normalize, setNormalize] = useState(true);

  useEffect(() => {
    fetch("/api/convert/check")
      .then((r) => r.json())
      .then(setFfmpeg)
      .catch(() => setFfmpeg({ available: false, version: null, path: null }));
  }, []);

  const handleConvert = async () => {
    setError(null);
    setLastJob(null);
    const isVideo = activeTab === "video";
    const inputPath = isVideo ? videoInput : audioInput;

    if (!inputPath.trim()) {
      setError("Please specify an input file path.");
      return;
    }

    setConverting(true);
    setProgress(0);
    setLogs(["[converter] Sending conversion request to API..."]);

    try {
      const body: any = {
        input_path: inputPath,
        output_format: isVideo ? videoFormat : audioFormat,
        quality: videoQuality,
        audio_bitrate: audioBitrate,
        normalize,
      };
      if (startTime) body.start_time = startTime;
      if (endTime) body.end_time = endTime;
      if (videoResolution) body.resolution = videoResolution;

      const res = await fetch("/api/convert", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "Conversion failed");
      }

      setLastJob(data);
      setLogs((p) => [
        ...p,
        `[converter] Job ${data.job_id} started`,
        `[converter] ${data.message}`,
        "[converter] FFmpeg is processing in the background...",
        `[converter] Output will be saved to: ${data.output_path}`,
      ]);

      // Simulate progress while the background job runs
      const interval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 95) {
            clearInterval(interval);
            setConverting(false);
            setProgress(100);
            setLogs((p) => [...p, "[success] Conversion job dispatched successfully!"]);
            return 100;
          }
          return prev + 5;
        });
      }, 300);
    } catch (err: any) {
      setError(err.message);
      setLogs((p) => [...p, `[error] ${err.message}`]);
      setConverting(false);
    }
  };

  const tabs = [
    { id: "video" as const, label: "Video Converter", icon: FileVideo },
    { id: "audio" as const, label: "Audio Converter", icon: Music },
    { id: "batch" as const, label: "Batch Transcode", icon: Layers },
  ];

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">FFmpeg Media Converter</h1>
          <p className="text-muted-foreground mt-1">Transcode video formats, convert audio bitrates, crop resolution boundaries, and batch process files.</p>
        </div>
      </div>

      {/* FFmpeg status banner */}
      {ffmpeg && (
        <div className={cn(
          "flex items-center gap-3 px-4 py-3 rounded-lg border text-sm",
          ffmpeg.available
            ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
            : "bg-destructive/10 border-destructive/20 text-destructive"
        )}>
          {ffmpeg.available ? <CheckCircle2 className="h-5 w-5 shrink-0" /> : <XCircle className="h-5 w-5 shrink-0" />}
          <span className="font-medium">
            {ffmpeg.available
              ? `FFmpeg available — ${ffmpeg.version ?? "Ready"}`
              : "FFmpeg not found. Install FFmpeg to enable conversion features."}
          </span>
        </div>
      )}

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Tab controls */}
      <div className="flex gap-2 border-b border-border/80 pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => { setActiveTab(tab.id); setProgress(0); setError(null); setLastJob(null); }}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
              activeTab === tab.id ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            <tab.icon className="h-4 w-4" /> {tab.label}
          </button>
        ))}
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Left: Config */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === "video" && (
            <>
              <Card>
                <CardHeader><CardTitle>Video File Input</CardTitle></CardHeader>
                <CardContent>
                  <Input
                    placeholder="e.g. C:\Users\Admin\Downloads\video.mkv"
                    className="font-mono text-xs"
                    value={videoInput}
                    onChange={(e) => setVideoInput(e.target.value)}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Sliders className="h-4.5 w-4.5 text-primary" /> Encoding Settings</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Target Format</label>
                    <select value={videoFormat} onChange={(e) => setVideoFormat(e.target.value)} className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option value="mp4">MP4 (H.264 / AAC)</option>
                      <option value="mkv">MKV (HEVC / Lossless)</option>
                      <option value="webm">WebM (VP9 / Opus)</option>
                      <option value="mov">MOV (QuickTime)</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Quality Profile (CRF)</label>
                    <select value={videoQuality} onChange={(e) => setVideoQuality(e.target.value)} className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option value="high">High (CRF 18)</option>
                      <option value="medium">Medium (CRF 23)</option>
                      <option value="low">Low (CRF 28)</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Resolution Override</label>
                    <select value={videoResolution} onChange={(e) => setVideoResolution(e.target.value)} className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option value="">No Override (Same Source)</option>
                      <option value="1080p">1080p (FHD)</option>
                      <option value="720p">720p (HD)</option>
                      <option value="480p">480p (SD)</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Scissors className="h-4.5 w-4.5 text-primary" /> Trim Timeline</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 sm:grid-cols-2">
                  <Input label="Start Time (hh:mm:ss)" placeholder="e.g. 00:01:10" value={startTime} onChange={(e) => setStartTime(e.target.value)} />
                  <Input label="End Time (hh:mm:ss)" placeholder="e.g. 00:04:45" value={endTime} onChange={(e) => setEndTime(e.target.value)} />
                </CardContent>
              </Card>
            </>
          )}

          {activeTab === "audio" && (
            <>
              <Card>
                <CardHeader><CardTitle>Audio File Input</CardTitle></CardHeader>
                <CardContent>
                  <Input
                    placeholder="e.g. C:\Users\Admin\Downloads\song.wav"
                    className="font-mono text-xs"
                    value={audioInput}
                    onChange={(e) => setAudioInput(e.target.value)}
                  />
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Sliders className="h-4.5 w-4.5 text-primary" /> Audio Codec Settings</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Target Format</label>
                    <select value={audioFormat} onChange={(e) => setAudioFormat(e.target.value)} className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option value="mp3">MP3 (Lame)</option>
                      <option value="flac">FLAC (Lossless)</option>
                      <option value="m4a">M4A (AAC)</option>
                      <option value="wav">WAV (Uncompressed)</option>
                      <option value="ogg">OGG (Vorbis)</option>
                    </select>
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Audio Bitrate</label>
                    <select value={audioBitrate} onChange={(e) => setAudioBitrate(e.target.value)} className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option value="320k">320 kbps (High)</option>
                      <option value="192k">192 kbps (Medium)</option>
                      <option value="128k">128 kbps (Low)</option>
                    </select>
                  </div>
                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none col-span-2">
                    <input type="checkbox" checked={normalize} onChange={(e) => setNormalize(e.target.checked)} className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                    <span>Normalize audio volume levels (loudnorm)</span>
                  </label>
                </CardContent>
              </Card>
            </>
          )}

          {activeTab === "batch" && (
            <Card>
              <CardHeader>
                <CardTitle>Batch Processing Queue</CardTitle>
                <CardDescription>Individual file conversion with full settings is available in the Video and Audio tabs.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">Batch transcoding support coming in a future release. Use the Video or Audio tabs to convert files one at a time.</p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Right: Action Panel */}
        <div className="space-y-6">
          {converting || progress > 0 ? (
            <Card>
              <CardHeader><CardTitle>Conversion Status</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>FFmpeg processing...</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
                {lastJob && (
                  <p className="text-[10px] text-muted-foreground font-mono break-all">{lastJob.output_path}</p>
                )}
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader><CardTitle>Action Center</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                <Button
                  variant="primary"
                  className="w-full gap-2"
                  onClick={handleConvert}
                  disabled={!ffmpeg?.available || activeTab === "batch"}
                >
                  <RefreshCw className="h-4.5 w-4.5" /> Start Transcoding
                </Button>
                {!ffmpeg?.available && (
                  <p className="text-[10px] text-center text-destructive">FFmpeg must be installed to use this feature.</p>
                )}
                <p className="text-[10px] text-center text-muted-foreground">Output is saved next to the input file with a `_converted` suffix.</p>
              </CardContent>
            </Card>
          )}

          {/* Console output */}
          {logs.length > 0 && (
            <Card className="bg-neutral-950 text-neutral-200 border-neutral-800">
              <CardHeader className="border-b border-neutral-900 pb-3">
                <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                  <Terminal className="h-4 w-4 text-primary" /> Conversion Log
                </CardTitle>
              </CardHeader>
              <CardContent className="p-3 font-mono text-[10px] leading-relaxed max-h-[200px] overflow-y-auto space-y-1 select-text">
                {logs.map((log, idx) => (
                  <div key={idx} className={cn(
                    log.includes("[success]") && "text-emerald-400",
                    log.includes("[error]") && "text-red-400",
                    !log.includes("[success]") && !log.includes("[error]") && "text-neutral-400"
                  )}>{log}</div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default MediaConverter;
