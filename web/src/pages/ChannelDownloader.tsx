import React, { useState } from "react";
import { FolderGit, CheckCircle } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const ChannelDownloader: React.FC = () => {
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [channel, setChannel] = useState<any>(null);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleAnalyze = () => {
    if (!url) return;
    setAnalyzing(true);
    setChannel(null);
    setTimeout(() => {
      setAnalyzing(false);
      setChannel({
        name: "DevFrontiers - Coding Tutorials",
        subscribers: "128.4K subscribers",
        videosCount: 148,
        description: "Official channel for advanced React, Tailwind, and Vite tutorials. Weekly live builds."
      });
    }, 1500);
  };

  const handleDownload = () => {
    setDownloading(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setDownloading(false);
          return 100;
        }
        return prev + 5;
      });
    }, 450);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Channel Downloader</h1>
        <p className="text-muted-foreground mt-1">Download creator videos, live streams, shorts, or playlists with custom limiters.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* URL and Channel details (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* URL Card */}
          <Card>
            <CardHeader>
              <CardTitle>Channel URL</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Input
                placeholder="https://www.youtube.com/@channelname"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="font-mono text-sm"
              />
              <Button variant="primary" onClick={handleAnalyze} disabled={!url || analyzing}>
                {analyzing ? "Analyzing..." : "Analyze"}
              </Button>
            </CardContent>
          </Card>

          {/* Channel Info Card */}
          {channel && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><CheckCircle className="h-4.5 w-4.5 text-emerald-500" /> Channel Profile</CardTitle>
              </CardHeader>
              <CardContent className="flex flex-col sm:flex-row gap-6">
                <div className="h-24 w-24 shrink-0 rounded-full bg-secondary/80 border border-border flex items-center justify-center font-bold text-lg text-primary">
                  {channel.name[0]}
                </div>
                <div className="space-y-2 flex-1">
                  <h3 className="text-base font-semibold leading-tight">{channel.name}</h3>
                  <div className="flex gap-4 text-xs text-muted-foreground">
                    <span>{channel.subscribers}</span>
                    <span>{channel.videosCount} Video(s)</span>
                  </div>
                  <p className="text-xs text-muted-foreground leading-relaxed pt-1.5 border-t border-border/40">
                    {channel.description}
                  </p>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Filters Card */}
          <Card>
            <CardHeader>
              <CardTitle>Download Filters</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Filter Videos By</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>Latest Uploads</option>
                  <option>Most Popular (Views)</option>
                  <option>Oldest Videos</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Content Categories</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>Full Videos Only</option>
                  <option>Shorts Only</option>
                  <option>Live Stream archives</option>
                  <option>All Uploads</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Input label="Max Video Download Limit" type="number" defaultValue="20" placeholder="e.g. 50" />
              </div>

              <div className="space-y-1.5">
                <Input label="Date Range Filter" placeholder="e.g. Last 30 Days" />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Action Panel (Right column) */}
        <div>
          {downloading || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Syncing Channel</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Batch download progress</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
                <div className="text-xs text-muted-foreground text-center">
                  {progress === 100 ? "Synced" : `Extracting video index...`}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Action Center</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  variant="primary" 
                  className="w-full gap-2" 
                  disabled={!channel || downloading}
                  onClick={handleDownload}
                >
                  <FolderGit className="h-4.5 w-4.5" /> Start Channel Sync
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
