import React, { useState, useEffect, useRef } from "react";
import { 
  FileVideo, Download, Sliders, Settings2, Pause, X, 
  Terminal, User, Eye, Heart, Calendar, Clock
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";
import { cn } from "../utils/cn";

export const VideoDownloader: React.FC = () => {
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [metadata, setMetadata] = useState<any>(null);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [logs, setLogs] = useState<string[]>([]);

  const [jobId, setJobId] = useState<string | null>(null);
  const [speed, setSpeed] = useState(0);
  const [eta, setEta] = useState(0);
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Helper to convert bytes to readable speed
  const formatSpeed = (bytesPerSec: number) => {
    if (bytesPerSec === 0) return "0 B/s";
    const k = 1024;
    const sizes = ["B/s", "KB/s", "MB/s", "GB/s"];
    const i = Math.floor(Math.log(bytesPerSec) / Math.log(k));
    return parseFloat((bytesPerSec / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  const formatEta = (seconds: number) => {
    if (seconds === 0) return "--";
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}m ${s}s`;
  };

  useEffect(() => {
    if (jobId) {
      pollingRef.current = setInterval(async () => {
        try {
          const res = await fetch(`/api/job/${jobId}`);
          if (res.ok) {
            const data = await res.json();
            if (data.status === "success") {
              const job = data.job;
              setProgress(job.progress);
              setSpeed(job.speed);
              setEta(job.eta);
              setLogs(job.logs);
              
              if (job.status === "completed" || job.status === "failed") {
                clearInterval(pollingRef.current as ReturnType<typeof setInterval>);
                setDownloading(false);
              }
            }
          }
        } catch (e) {}
      }, 500);
    }
    
    return () => {
      if (pollingRef.current) clearInterval(pollingRef.current);
    };
  }, [jobId]);

  const handleAnalyze = async () => {
    if (!url) return;
    setAnalyzing(true);
    setMetadata(null);
    setLogs(["[info] Extractor initialized...", "[info] Contacting backend to extract metadata..."]);
    
    try {
      const res = await fetch('/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ url })
      });
      const data = await res.json();
      if (data.status === "success") {
        setMetadata(data.metadata);
        setLogs((prev) => [...prev, "[success] Metadata extracted successfully!"]);
      } else {
        setLogs((prev) => [...prev, `[error] ${data.detail}`]);
      }
    } catch (e: any) {
      setLogs((prev) => [...prev, `[error] Analysis failed: ${e.message}`]);
    } finally {
      setAnalyzing(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setProgress(0);
    setLogs(["[info] Triggering download via API..."]);
    
    try {
      const response = await fetch('/api/download', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          url: url,
          type: 'video',
        }),
      });
      
      const data = await response.json();
      if (data.status === "success") {
        setLogs((prev) => [...prev, `[info] Background job started: ${data.job_id}`]);
        setJobId(data.job_id); // This triggers the useEffect polling
      } else {
        setLogs((prev) => [...prev, `[error] API error: ${JSON.stringify(data)}`]);
        setDownloading(false);
      }
    } catch (err: any) {
      setLogs((prev) => [...prev, `[error] Download request failed: ${err.message}`]);
      setDownloading(false);
    }
  };

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Advanced Video Downloader</h1>
        <p className="text-muted-foreground mt-1">Configure format formats, network proxies, metadata tags, and concurrent threads.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Core settings & Options (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* URL Input card */}
          <Card>
            <CardHeader>
              <CardTitle>Video URL</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Input
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="font-mono"
              />
              <Button variant="outline" onClick={handleAnalyze} disabled={!url || analyzing}>
                {analyzing ? "Analyzing..." : "Analyze"}
              </Button>
            </CardContent>
          </Card>

          {/* Metadata preview card */}
          {metadata && (
            <Card>
              <CardHeader className="pb-3">
                <CardTitle>Stream Metadata Preview</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col sm:flex-row gap-6">
                <div className="h-32 w-48 shrink-0 rounded-lg bg-secondary/80 flex items-center justify-center border border-border overflow-hidden">
                  <FileVideo className="h-10 w-10 text-muted-foreground" />
                </div>
                <div className="space-y-3 flex-1">
                  <h3 className="text-base font-semibold leading-snug">{metadata.title}</h3>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-muted-foreground">
                    <span className="flex items-center gap-1.5"><User className="h-3.5 w-3.5" /> {metadata.uploader}</span>
                    <span className="flex items-center gap-1.5"><Clock className="h-3.5 w-3.5" /> {metadata.duration}</span>
                    <span className="flex items-center gap-1.5"><Eye className="h-3.5 w-3.5" /> {metadata.views} views</span>
                    <span className="flex items-center gap-1.5"><Heart className="h-3.5 w-3.5" /> {metadata.likes} likes</span>
                    <span className="flex items-center gap-1.5"><Calendar className="h-3.5 w-3.5" /> {metadata.date}</span>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Advanced Downloader options */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Sliders className="h-4.5 w-4.5 text-primary" /> Extraction Options</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Preferred Resolution</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>1080p (FHD)</option>
                  <option>720p (HD)</option>
                  <option>1440p (2K)</option>
                  <option>2160p (4K)</option>
                  <option>Best Available</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Preferred Container</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>MP4 (Highly Compatible)</option>
                  <option>MKV (Matroska)</option>
                  <option>WebM</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Preferred FPS</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>60 FPS</option>
                  <option>30 FPS</option>
                  <option>No Preference</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Input label="Filename Template" defaultValue="%(title)s.%(ext)s" />
              </div>

              <div className="space-y-1.5">
                <Input label="Download Directory" defaultValue="D:\Downloads\FluxMedia" />
              </div>

              <div className="space-y-1.5">
                <Input label="Proxy URL" placeholder="http://127.0.0.1:8888" />
              </div>
            </CardContent>
          </Card>

          {/* Embed options */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Settings2 className="h-4.5 w-4.5 text-primary" /> Post-Processing Options</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Embed Thumbnail Image</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Embed Media Metadata Tags</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Embed Video Chapters</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Embed Subtitles Track</span>
              </label>
            </CardContent>
          </Card>
        </div>

        {/* Console Logs, Live progress & Monitor (Right column) */}
        <div className="space-y-6">
          {/* Active Download Progress Card */}
          {downloading || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Download Status</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Downloader Progress</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />

                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground pt-2">
                  <div>Speed: <span className="font-semibold text-foreground">{formatSpeed(speed)}</span></div>
                  <div>ETA: <span className="font-semibold text-foreground">{progress === 100 ? "Done" : formatEta(eta)}</span></div>
                  <div>Output: <span className="font-semibold text-foreground">MP4</span></div>
                  <div>ID: <span className="font-semibold text-foreground">{jobId}</span></div>
                </div>

                <div className="flex gap-2 justify-end pt-2">
                  <Button variant="outline" size="sm"><Pause className="h-3 w-3" /> Pause</Button>
                  <Button variant="destructive" size="sm" onClick={() => { setDownloading(false); setProgress(0); }}><X className="h-3 w-3" /> Cancel</Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Action Center</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col gap-2">
                <Button variant="primary" className="w-full" disabled={!metadata || downloading} onClick={handleDownload}>
                  <Download className="h-4 w-4" /> Start Extraction
                </Button>
                <p className="text-[10px] text-center text-muted-foreground">Make sure you check your resolution configuration before extracting.</p>
              </CardContent>
            </Card>
          )}

          {/* Console Output */}
          <Card className="bg-neutral-950 text-neutral-200 border-neutral-800">
            <CardHeader className="border-b border-neutral-900 pb-3">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" /> Live Console Output
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 font-mono text-[10px] leading-relaxed max-h-[220px] overflow-y-auto space-y-1 select-text">
              {logs.length === 0 ? (
                <span className="text-neutral-600">Console idle. Analyze a video URL to generate log streams.</span>
              ) : (
                logs.map((log, idx) => (
                  <div 
                    key={idx} 
                    className={cn(
                      log.includes("[success]") && "text-emerald-400",
                      log.includes("[info]") && "text-neutral-400"
                    )}
                  >
                    {log}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
