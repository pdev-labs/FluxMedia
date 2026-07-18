import React, { useState } from "react";
import { 
  RefreshCw, FileVideo, Music, Layers, Sliders, Scissors, Trash2
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const MediaConverter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"video" | "audio" | "batch">("video");
  const [conversionType, setConversionType] = useState("mp4");
  const [converting, setConverting] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleConvert = () => {
    setConverting(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setConverting(false);
          return 100;
        }
        return prev + 10;
      });
    }, 350);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">FFmpeg Media Converter</h1>
          <p className="text-muted-foreground mt-1">Transcode video formats, convert audio bitrates, crop resolution boundaries, and batch process files.</p>
        </div>
      </div>

      {/* Tab controls */}
      <div className="flex gap-2 border-b border-border/80 pb-1">
        <button
          onClick={() => { setActiveTab("video"); setProgress(0); }}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "video" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <FileVideo className="h-4 w-4" /> Video Converter
        </button>
        <button
          onClick={() => { setActiveTab("audio"); setProgress(0); }}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "audio" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Music className="h-4 w-4" /> Audio Converter
        </button>
        <button
          onClick={() => { setActiveTab("batch"); setProgress(0); }}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "batch" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Layers className="h-4 w-4" /> Batch Transcode
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Converter configuration options (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === "video" && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Video File Input</CardTitle>
                </CardHeader>
                <CardContent className="flex gap-2">
                  <Input placeholder="D:\Downloads\FluxMedia\input_video.mkv" className="font-mono text-xs" />
                  <Button variant="outline">Browse</Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Sliders className="h-4.5 w-4.5 text-primary" /> Encoding Settings</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Target Format</label>
                    <select 
                      value={conversionType}
                      onChange={(e) => setConversionType(e.target.value)}
                      className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm"
                    >
                      <option value="mp4">MP4 (H.264 / AAC)</option>
                      <option value="mkv">MKV (HEVC / Lossless)</option>
                      <option value="webm">WebM (VP9 / Opus)</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Quality Profile (CRF)</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option>Medium (CRF 23)</option>
                      <option>High (CRF 18)</option>
                      <option>Highest (CRF 16)</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Resolution Override</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option>No Override (Same Source)</option>
                      <option>1080p (FHD)</option>
                      <option>720p (HD)</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Preset Speed</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option>medium (Balanced)</option>
                      <option>fast (Speedy)</option>
                      <option>slow (High Compression)</option>
                    </select>
                  </div>
                </CardContent>
              </Card>

              {/* Crop & Trim card */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Scissors className="h-4.5 w-4.5 text-primary" /> Crop & Trim Timeline</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 sm:grid-cols-2">
                  <Input label="Start Time (hh:mm:ss)" placeholder="e.g. 00:01:10" />
                  <Input label="End Time (hh:mm:ss)" placeholder="e.g. 00:04:45" />
                </CardContent>
              </Card>
            </>
          )}

          {activeTab === "audio" && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>Audio File Input</CardTitle>
                </CardHeader>
                <CardContent className="flex gap-2">
                  <Input placeholder="D:\Downloads\FluxMedia\input_song.wav" className="font-mono text-xs" />
                  <Button variant="outline">Browse</Button>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2"><Sliders className="h-4.5 w-4.5 text-primary" /> Audio Codec Settings</CardTitle>
                </CardHeader>
                <CardContent className="grid gap-6 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Target Format</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option>MP3 (Lame)</option>
                      <option>FLAC (Lossless)</option>
                      <option>M4A (AAC)</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Audio Bitrate</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option>320 kbps (High)</option>
                      <option>192 kbps (Medium)</option>
                      <option>128 kbps (Low)</option>
                    </select>
                  </div>

                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                    <span>Normalize audio volume levels</span>
                  </label>

                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                    <span>Fade In (2 seconds)</span>
                  </label>
                </CardContent>
              </Card>
            </>
          )}

          {activeTab === "batch" && (
            <Card>
              <CardHeader>
                <CardTitle>Batch Processing queue</CardTitle>
                <CardDescription>Drag and drop multiple media files below to queue them for batch encoding.</CardDescription>
              </CardHeader>
              <CardContent className="divide-y divide-border/40 p-0">
                <div className="flex items-center justify-between p-3.5">
                  <span className="text-xs font-semibold">lecture_01.mkv</span>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">MKV to MP4</Badge>
                    <Trash2 className="h-4 w-4 text-muted-foreground cursor-pointer hover:text-destructive" />
                  </div>
                </div>

                <div className="flex items-center justify-between p-3.5">
                  <span className="text-xs font-semibold">audio_track.wav</span>
                  <div className="flex items-center gap-3">
                    <Badge variant="outline">WAV to FLAC</Badge>
                    <Trash2 className="h-4 w-4 text-muted-foreground cursor-pointer hover:text-destructive" />
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action Panel (Right column) */}
        <div>
          {converting || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Converting Media</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>FFmpeg processing...</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
                <div className="text-xs text-muted-foreground text-center pt-2 border-t border-border/40">
                  {progress === 100 ? "Done" : "Re-encoding segments using libx264..."}
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Action Center</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="primary" className="w-full gap-2" onClick={handleConvert}>
                  <RefreshCw className="h-4.5 w-4.5" /> Start Transcoding
                </Button>
                <p className="text-[10px] text-center text-muted-foreground">The media will be saved inside the same input directory by default.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
