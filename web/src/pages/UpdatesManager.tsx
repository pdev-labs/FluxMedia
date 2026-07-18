import React, { useState } from "react";
import { 
  RefreshCw, ShieldCheck, Download, ArrowUpCircle
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";

export const UpdatesManager: React.FC = () => {
  const [checking, setChecking] = useState(false);
  const [updateAvailable, setUpdateAvailable] = useState(false);
  const [updating, setUpdating] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleCheck = () => {
    setChecking(true);
    setUpdateAvailable(false);
    setTimeout(() => {
      setChecking(false);
      setUpdateAvailable(true);
    }, 1500);
  };

  const handleUpdate = () => {
    setUpdating(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setUpdating(false);
          setUpdateAvailable(false);
          return 100;
        }
        return prev + 10;
      });
    }, 450);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Updates Manager</h1>
        <p className="text-muted-foreground mt-1">Keep the yt-dlp binary, FFmpeg codecs, and FluxMedia Core engine up to date.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Release Status & details (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Core Version Information</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex justify-between items-center pb-3 border-b border-border/40">
                <div>
                  <h4 className="text-xs font-semibold">FluxMedia Web Core</h4>
                  <p className="text-[10px] text-muted-foreground">Main application interface wrapper.</p>
                </div>
                <Badge variant="outline">v1.6.33</Badge>
              </div>

              <div className="flex justify-between items-center pb-3 border-b border-border/40">
                <div>
                  <h4 className="text-xs font-semibold">yt-dlp Extractor Engine</h4>
                  <p className="text-[10px] text-muted-foreground">Universal stream extractor binary.</p>
                </div>
                <div className="flex gap-2">
                  <Badge variant="outline">v2026.06.12</Badge>
                  <Badge variant="success">Latest</Badge>
                </div>
              </div>

              <div className="flex justify-between items-center">
                <div>
                  <h4 className="text-xs font-semibold">FFmpeg Transcoder Library</h4>
                  <p className="text-[10px] text-muted-foreground">Multiplexer and format conversion codecs.</p>
                </div>
                <div className="flex gap-2">
                  <Badge variant="outline">v6.0-stable</Badge>
                  <Badge variant="success">Latest</Badge>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Release history / Timeline cards */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground px-1">Changelog & Releases Timeline</h3>
            
            <Card>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-sm font-semibold">v1.6.33 - Media Management Release</CardTitle>
                  <span className="text-[10px] text-muted-foreground">2026-07-18</span>
                </div>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground space-y-2">
                <p>Features added in this version include active download queues, folder browsers, converters, and performance diagnostics graphs.</p>
                <div className="flex gap-1.5 pt-1">
                  <Badge variant="secondary" className="text-[9px]">Features</Badge>
                  <Badge variant="secondary" className="text-[9px]">FFmpeg</Badge>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <div className="flex justify-between items-start">
                  <CardTitle className="text-sm font-semibold">v1.6.32 - Downloader Engine Release</CardTitle>
                  <span className="text-[10px] text-muted-foreground">2026-07-18</span>
                </div>
              </CardHeader>
              <CardContent className="text-xs text-muted-foreground space-y-2">
                <p>Scaffolded downloader submodules for Video, Audio, Playlist, Channel, Subtitles, Trimming, and Instagram extractors.</p>
                <div className="flex gap-1.5 pt-1">
                  <Badge variant="secondary" className="text-[9px]">Engines</Badge>
                  <Badge variant="secondary" className="text-[9px]">Extractor</Badge>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Update checks triggers (Right column) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Update Channel Settings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Update Release Channel</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>Stable (Highly Recommended)</option>
                  <option>Beta (Experimental Features)</option>
                  <option>Nightly (Development Builds)</option>
                </select>
              </div>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Auto-download updates</span>
              </label>
            </CardContent>
          </Card>

          {updating ? (
            <Card>
              <CardHeader>
                <CardTitle>Installing Update</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Downloading package segments...</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant="default" />
              </CardContent>
            </Card>
          ) : updateAvailable ? (
            <Card className="border-primary bg-primary/5">
              <CardHeader>
                <CardTitle className="text-base text-primary flex items-center gap-2"><ArrowUpCircle className="h-5 w-5" /> Update Available!</CardTitle>
                <CardDescription>FluxMedia Core v1.6.34 is ready for download.</CardDescription>
              </CardHeader>
              <CardContent>
                <Button variant="primary" className="w-full gap-2" onClick={handleUpdate}>
                  <Download className="h-4 w-4" /> Download and Install
                </Button>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Action Center</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="outline" className="w-full gap-2" disabled={checking} onClick={handleCheck}>
                  {checking ? <RefreshCw className="h-4 w-4 animate-spin" /> : <ShieldCheck className="h-4 w-4" />}
                  {checking ? "Checking..." : "Check for Updates"}
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
export default UpdatesManager;
