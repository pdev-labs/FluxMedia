import React, { useState } from "react";
import { Download, FileVideo, CheckSquare, Square } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const PlaylistDownloader: React.FC = () => {
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [playlist, setPlaylist] = useState<any>(null);
  const [selectedVideos, setSelectedVideos] = useState<Set<string>>(new Set());
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleAnalyze = () => {
    if (!url) return;
    setAnalyzing(true);
    setPlaylist(null);
    setSelectedVideos(new Set());
    setTimeout(() => {
      setAnalyzing(false);
      const mockVideos = [
        { id: "v1", title: "React Router v6 - Full Navigation Guide", duration: "12:15" },
        { id: "v2", title: "State Management via React Context API", duration: "18:40" },
        { id: "v3", title: "TypeScript Integration in Vite Projects", duration: "08:12" },
        { id: "v4", title: "Tailwind CSS v4 Layout & Utility Directives", duration: "15:30" }
      ];
      setPlaylist({
        name: "Modern Frontend Web Development",
        creator: "Lofi Cafe Music",
        videosCount: mockVideos.length,
        size: "estimated 1.2 GB",
        videos: mockVideos
      });
      // Select all by default
      setSelectedVideos(new Set(mockVideos.map((v) => v.id)));
    }, 1500);
  };

  const handleToggleSelect = (id: string) => {
    setSelectedVideos((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const handleSelectAll = () => {
    if (!playlist) return;
    setSelectedVideos(new Set(playlist.videos.map((v: any) => v.id)));
  };

  const handleDeselectAll = () => {
    setSelectedVideos(new Set());
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
    }, 400);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Playlist Downloader</h1>
        <p className="text-muted-foreground mt-1">Download entire video/audio playlists, select specific segments, and sync folders.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Playlist URL & selector list (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Playlist Input card */}
          <Card>
            <CardHeader>
              <CardTitle>Playlist URL</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Input
                placeholder="https://www.youtube.com/playlist?list=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="font-mono text-sm"
              />
              <Button variant="primary" onClick={handleAnalyze} disabled={!url || analyzing}>
                {analyzing ? "Analyzing..." : "Analyze"}
              </Button>
            </CardContent>
          </Card>

          {/* Playlist Videos Selector List */}
          {playlist && (
            <Card>
              <CardHeader className="pb-3 border-b border-border/40">
                <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                  <div>
                    <CardTitle className="text-base">{playlist.name}</CardTitle>
                    <CardDescription>{playlist.creator} • {playlist.videosCount} item(s) • {playlist.size}</CardDescription>
                  </div>
                  <div className="flex gap-2">
                    <Button variant="outline" size="sm" onClick={handleSelectAll}>Select All</Button>
                    <Button variant="outline" size="sm" onClick={handleDeselectAll}>Deselect All</Button>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border/40">
                  {playlist.videos.map((video: any) => (
                    <div 
                      key={video.id} 
                      onClick={() => handleToggleSelect(video.id)}
                      className="flex items-center justify-between p-3.5 hover:bg-secondary/40 cursor-pointer select-none"
                    >
                      <div className="flex items-center gap-3">
                        <button className="text-muted-foreground hover:text-foreground">
                          {selectedVideos.has(video.id) ? (
                            <CheckSquare className="h-4.5 w-4.5 text-primary" />
                          ) : (
                            <Square className="h-4.5 w-4.5" />
                          )}
                        </button>
                        <FileVideo className="h-4.5 w-4.5 text-muted-foreground shrink-0" />
                        <span className="text-sm font-medium leading-tight">{video.title}</span>
                      </div>
                      <Badge variant="outline" className="font-mono text-[10px] shrink-0">{video.duration}</Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action Panel (Right column) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Batch Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Parallel Download Threads</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>3 concurrent downloads</option>
                  <option>5 concurrent downloads</option>
                  <option>1 (Sequential)</option>
                </select>
              </div>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Skip existing files</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Overwrite duplicates</span>
              </label>
            </CardContent>
          </Card>

          {downloading || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Downloading Playlist</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Batch download progress</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
                <div className="text-xs text-muted-foreground text-center">
                  {progress === 100 ? "Done" : `Processed ${Math.floor(progress / 25)} of 4 videos`}
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
                  disabled={selectedVideos.size === 0 || downloading}
                  onClick={handleDownload}
                >
                  <Download className="h-4.5 w-4.5" /> Download Selected ({selectedVideos.size})
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
