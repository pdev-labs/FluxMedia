import React, { useState } from "react";
import { 
  Play, Pause, X, RotateCcw, FolderOpen, Copy, FileVideo
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";
import { cn } from "../utils/cn";

export const DownloadQueue: React.FC = () => {
  const [activeQueue, setActiveQueue] = useState([
    { id: "q1", title: "Study Lofi Chill Beats Mix 2026.mp4", status: "downloading", progress: 65, speed: "4.8 MB/s", eta: "0m 18s", size: "320 MB", url: "https://youtube.com/watch?v=1" },
    { id: "q2", title: "React Router Navigation Masterclass.mp4", status: "paused", progress: 42, speed: "0 KB/s", eta: "Paused", size: "128 MB", url: "https://youtube.com/watch?v=2" },
    { id: "q3", title: "Advanced Quantum Computing Lecture 1.mkv", status: "queued", progress: 0, speed: "Queued", eta: "Waiting", size: "1.2 GB", url: "https://youtube.com/watch?v=3" },
    { id: "q4", title: "Profile Highlight Story Reel.mp4", status: "failed", progress: 15, speed: "Failed", eta: "Error", size: "18 MB", url: "https://instagram.com/reel/4" }
  ]);
  const [selectedJob, setSelectedJob] = useState<any>(activeQueue[0]);

  const handleAction = (id: string, action: "play" | "pause" | "delete" | "retry") => {
    setActiveQueue((prev) => 
      prev.map((item) => {
        if (item.id !== id) return item;
        if (action === "play") return { ...item, status: "downloading", speed: "4.5 MB/s" };
        if (action === "pause") return { ...item, status: "paused", speed: "0 KB/s" };
        if (action === "retry") return { ...item, status: "downloading", progress: 0, speed: "Connecting..." };
        return item;
      }).filter((item) => !(action === "delete" && item.id === id))
    );
  };

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Active Queue Manager</h1>
          <p className="text-muted-foreground mt-1">Manage active downloads, pause threads, prioritize streams, and control bandwidth allocation.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={() => setActiveQueue((prev) => prev.map(q => ({ ...q, status: "paused", speed: "0 KB/s" })))}>Pause All</Button>
          <Button variant="primary" size="sm" onClick={() => setActiveQueue((prev) => prev.map(q => q.status === "paused" ? { ...q, status: "downloading", speed: "4.5 MB/s" } : q))}>Resume All</Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Active downloads list (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-border/40">
              <div className="flex justify-between items-center">
                <CardTitle className="text-base">Jobs Pipeline</CardTitle>
                <Badge variant="info">{activeQueue.length} Active Job(s)</Badge>
              </div>
            </CardHeader>
            <CardContent className="p-0 divide-y divide-border/40">
              {activeQueue.length === 0 ? (
                <div className="h-48 flex items-center justify-center text-muted-foreground text-sm">Download queue is empty.</div>
              ) : (
                activeQueue.map((job) => (
                  <div 
                    key={job.id} 
                    onClick={() => setSelectedJob(job)}
                    className={cn(
                      "p-4 hover:bg-secondary/30 cursor-pointer transition-colors flex flex-col gap-3",
                      selectedJob?.id === job.id && "bg-secondary/45"
                    )}
                  >
                    <div className="flex justify-between items-start gap-4">
                      <div className="flex items-center gap-3 min-w-0">
                        <FileVideo className="h-5 w-5 text-muted-foreground shrink-0" />
                        <span className="text-sm font-semibold truncate leading-tight">{job.title}</span>
                      </div>
                      <div className="flex items-center gap-1.5 shrink-0">
                        {job.status === "downloading" && <Badge variant="info">Active</Badge>}
                        {job.status === "paused" && <Badge variant="secondary">Paused</Badge>}
                        {job.status === "queued" && <Badge variant="outline">Queued</Badge>}
                        {job.status === "failed" && <Badge variant="danger">Failed</Badge>}
                      </div>
                    </div>

                    <div className="flex items-center justify-between text-xs text-muted-foreground">
                      <div className="flex gap-4">
                        <span>Speed: <span className="text-foreground font-medium">{job.speed}</span></span>
                        <span>ETA: <span className="text-foreground font-medium">{job.eta}</span></span>
                        <span>Size: <span className="text-foreground font-medium">{job.size}</span></span>
                      </div>
                      <div className="flex items-center gap-1">
                        {job.status === "paused" && (
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={(e) => { e.stopPropagation(); handleAction(job.id, "play"); }}><Play className="h-3 w-3" /></Button>
                        )}
                        {job.status === "downloading" && (
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={(e) => { e.stopPropagation(); handleAction(job.id, "pause"); }}><Pause className="h-3 w-3" /></Button>
                        )}
                        {job.status === "failed" && (
                          <Button variant="ghost" size="icon" className="h-7 w-7" onClick={(e) => { e.stopPropagation(); handleAction(job.id, "retry"); }}><RotateCcw className="h-3 w-3" /></Button>
                        )}
                        <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={(e) => { e.stopPropagation(); handleAction(job.id, "delete"); }}><X className="h-3 w-3" /></Button>
                      </div>
                    </div>

                    {job.status === "downloading" && (
                      <ProgressBar value={job.progress} size="sm" />
                    )}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>

        {/* Selected job details side panel (Right column) */}
        <div className="space-y-6">
          {selectedJob ? (
            <Card>
              <CardHeader className="pb-3 border-b border-border/40">
                <CardTitle className="text-base">Selected Job Details</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4 text-xs">
                <div className="h-32 bg-secondary/80 border border-border rounded-lg flex items-center justify-center">
                  <FileVideo className="h-8 w-8 text-muted-foreground" />
                </div>
                
                <div className="space-y-2">
                  <h4 className="text-sm font-semibold leading-tight">{selectedJob.title}</h4>
                  <p className="text-muted-foreground break-all font-mono text-[10px] bg-secondary/20 p-2 rounded">{selectedJob.url}</p>
                </div>

                <div className="grid grid-cols-2 gap-x-4 gap-y-2.5 pt-2 border-t border-border/40 text-muted-foreground">
                  <div>Size: <span className="text-foreground font-semibold">{selectedJob.size}</span></div>
                  <div>Resolution: <span className="text-foreground font-semibold">1080p</span></div>
                  <div>Output: <span className="text-foreground font-semibold">MP4</span></div>
                  <div>Priority: <span className="text-foreground font-semibold">Medium</span></div>
                </div>

                <div className="flex gap-2 pt-2 border-t border-border/40">
                  <Button variant="outline" size="sm" className="flex-1 gap-1"><FolderOpen className="h-3.5 w-3.5" /> Reveal</Button>
                  <Button variant="outline" size="sm" className="flex-1 gap-1"><Copy className="h-3.5 w-3.5" /> Copy URL</Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="h-48 flex items-center justify-center text-muted-foreground text-sm">Select a job to view details.</CardContent>
            </Card>
          )}

          {/* Core concurrency limits */}
          <Card>
            <CardHeader>
              <CardTitle>Bandwidth Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Concurrency limit</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>3 Parallel Streams</option>
                  <option>5 Parallel Streams</option>
                  <option>1 (Sequential)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Input label="Max Bandwidth Limit" placeholder="e.g. 5 MB/s" defaultValue="No Limit" />
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
