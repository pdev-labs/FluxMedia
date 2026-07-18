import React, { useState, useEffect } from "react";
import { 
  Download, RefreshCw, Cpu, Database, Wifi, Pin, CheckCircle2, History, FileVideo, HardDrive
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const Dashboard: React.FC = () => {
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [videoMeta, setVideoMeta] = useState<any>(null);

  // Keyboard shortcut listener for Ctrl+L to focus URL input
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "l") {
        e.preventDefault();
        const input = document.getElementById("quick-url-input");
        input?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const handlePaste = async () => {
    try {
      const text = await navigator.clipboard.readText();
      setUrl(text);
    } catch (e) {
      console.warn("Clipboard access blocked");
    }
  };

  const handleAnalyze = () => {
    if (!url) return;
    setAnalyzing(true);
    setVideoMeta(null);
    setTimeout(() => {
      setAnalyzing(false);
      setVideoMeta({
        title: "Lo-Fi Beats for Coding & Studying 🎧 (24/7 Live Stream)",
        uploader: "Lofi Cafe Music",
        duration: "02:45:10",
        views: "1,248,591 views",
        date: "2026-07-01",
        size: "estimated 350 MB",
        platform: "youtube"
      });
    }, 1500);
  };

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      {/* Welcome Banner */}
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">FluxMedia Web</h1>
          <p className="text-muted-foreground mt-1">High-performance graphical gateway connected to local FluxMedia CLI engine.</p>
        </div>
        <div className="flex gap-2">
          <Badge variant="success" className="h-6 gap-1"><CheckCircle2 className="h-3 w-3" /> Core Engine v1.6.30</Badge>
          <Badge variant="info" className="h-6 gap-1"><Wifi className="h-3 w-3" /> Network Gateway Online</Badge>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* Quick Download Card */}
        <Card className="lg:col-span-2 flex flex-col justify-between">
          <CardHeader>
            <div className="flex justify-between items-start">
              <div>
                <CardTitle className="flex items-center gap-2"><Download className="h-4.5 w-4.5 text-primary" /> Quick Downloader</CardTitle>
                <CardDescription>Paste any URL below. Platforms are automatically detected.</CardDescription>
              </div>
              <Badge variant="outline">Auto-detect Platform</Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                id="quick-url-input"
                placeholder="Paste video, playlist, or audio URL here..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="flex-1 font-mono text-sm"
              />
              <Button variant="outline" size="sm" onClick={handlePaste}>Paste</Button>
              {url && (
                <Button variant="ghost" size="sm" onClick={() => { setUrl(""); setVideoMeta(null); }}>Clear</Button>
              )}
            </div>

            {/* Platform detection indicator */}
            {url && (
              <div className="text-xs text-muted-foreground">
                Detected Platform: <span className="font-semibold text-primary capitalize">{url.includes("youtube.com") || url.includes("youtu.be") ? "YouTube Video/Playlist" : url.includes("instagram.com") ? "Instagram post/reel" : "Generic Link Extractor"}</span>
              </div>
            )}

            {/* Analysis details */}
            {analyzing && (
              <div className="flex items-center gap-3 py-4 text-sm text-muted-foreground">
                <RefreshCw className="h-4 w-4 animate-spin text-primary" />
                <span>Analyzing media streams and resolutions...</span>
              </div>
            )}

            {videoMeta && (
              <div className="flex flex-col sm:flex-row gap-4 border border-border/60 rounded-lg p-4 bg-secondary/20">
                <div className="h-24 w-40 shrink-0 rounded-md bg-secondary/80 flex items-center justify-center border border-border">
                  <FileVideo className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="space-y-1">
                  <h4 className="text-sm font-semibold leading-tight">{videoMeta.title}</h4>
                  <p className="text-xs text-muted-foreground">Uploader: {videoMeta.uploader} • {videoMeta.views}</p>
                  <p className="text-xs text-muted-foreground">Duration: {videoMeta.duration} • Uploaded: {videoMeta.date}</p>
                  <div className="flex gap-2 mt-2">
                    <Badge variant="info">{videoMeta.size}</Badge>
                    <Badge variant="secondary">1080p WebM</Badge>
                  </div>
                </div>
              </div>
            )}
          </CardContent>
          <CardFooter className="flex justify-between border-t border-border/40 pt-4">
            <span className="text-[10px] text-muted-foreground/60">Press <kbd className="font-mono bg-secondary px-1 rounded">Ctrl+L</kbd> to focus input field</span>
            <div className="flex gap-2">
              <Button variant="outline" onClick={handleAnalyze} disabled={!url || analyzing}>Analyze URL</Button>
              <Button variant="primary" disabled={!videoMeta}>Download Now</Button>
            </div>
          </CardFooter>
        </Card>

        {/* System Diagnostics & Health */}
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Cpu className="h-4.5 w-4.5 text-emerald-500" /> System Diagnostics</CardTitle>
            <CardDescription>FluxMedia Core resource usage overview.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="flex items-center gap-1.5"><Cpu className="h-3.5 w-3.5" /> CPU Load</span>
                <span className="font-mono">4.2%</span>
              </div>
              <ProgressBar value={4.2} variant="success" size="sm" />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="flex items-center gap-1.5"><Database className="h-3.5 w-3.5" /> RAM Allocated</span>
                <span className="font-mono">148 MB</span>
              </div>
              <ProgressBar value={14.8} variant="success" size="sm" />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="flex items-center gap-1.5"><HardDrive className="h-3.5 w-3.5" /> Storage Capacity</span>
                <span className="font-mono">12.4 GB Free</span>
              </div>
              <ProgressBar value={75} size="sm" />
            </div>

            <div className="flex justify-between text-xs pt-2 border-t border-border/40">
              <span className="text-muted-foreground">Download Engine</span>
              <Badge variant="success">Idle</Badge>
            </div>
          </CardContent>
          <CardFooter className="flex justify-between border-t border-border/40 pt-4">
            <span className="text-xs text-muted-foreground">Port: 8000</span>
            <Button variant="outline" size="sm">System Logs</Button>
          </CardFooter>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Recent Downloads & Activity */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><History className="h-4.5 w-4.5 text-indigo-500" /> Recent Downloads</CardTitle>
            <CardDescription>Latest completed or active downloads.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded bg-secondary flex items-center justify-center text-primary font-bold">YT</div>
                <div>
                  <h5 className="text-sm font-semibold">Study Session Chill beats.mp4</h5>
                  <p className="text-xs text-muted-foreground">Video • 120.4 MB • Completed</p>
                </div>
              </div>
              <Badge variant="success">Saved</Badge>
            </div>

            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded bg-secondary flex items-center justify-center text-primary font-bold">SC</div>
                <div>
                  <h5 className="text-sm font-semibold">Artist Podcast Interview Ep 2.mp3</h5>
                  <p className="text-xs text-muted-foreground">Audio • 45.2 MB • Completed</p>
                </div>
              </div>
              <Badge variant="success">Saved</Badge>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="h-8 w-8 rounded bg-secondary flex items-center justify-center text-rose-500 font-bold">IG</div>
                <div>
                  <h5 className="text-sm font-semibold">Travel Reel Vlog 2026.mp4</h5>
                  <p className="text-xs text-muted-foreground">Video • 15.6 MB • Failed</p>
                </div>
              </div>
              <Badge variant="danger">Error</Badge>
            </div>
          </CardContent>
        </Card>

        {/* Pinned Playlists & Channels */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2"><Pin className="h-4.5 w-4.5 text-amber-500" /> Pinned Playlists & Channels</CardTitle>
            <CardDescription>Shortcut bookmarks for recurring batch extraction.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <div>
                <h5 className="text-sm font-semibold">Advanced Coding Tutorials</h5>
                <p className="text-xs text-muted-foreground">Channel • 42 Videos • youtube</p>
              </div>
              <Button variant="outline" size="sm" className="h-8 gap-1">Sync <RefreshCw className="h-3 w-3" /></Button>
            </div>

            <div className="flex items-center justify-between border-b border-border/40 pb-3">
              <div>
                <h5 className="text-sm font-semibold">Chill Lo-Fi Coding Beats Playlist</h5>
                <p className="text-xs text-muted-foreground">Playlist • 148 Videos • youtube</p>
              </div>
              <Button variant="outline" size="sm" className="h-8 gap-1">Sync <RefreshCw className="h-3 w-3" /></Button>
            </div>

            <div className="flex items-center justify-between">
              <div>
                <h5 className="text-sm font-semibold">Archived Tech Lectures</h5>
                <p className="text-xs text-muted-foreground">Playlist • 18 Videos • youtube</p>
              </div>
              <Button variant="outline" size="sm" className="h-8 gap-1">Sync <RefreshCw className="h-3 w-3" /></Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
