import React, { useState } from "react";
import { Music, Sliders, Settings2, Sparkles, Image } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const AudioDownloader: React.FC = () => {
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [metadata, setMetadata] = useState<any>(null);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

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
    setMetadata(null);
    setTimeout(() => {
      setAnalyzing(false);
      setMetadata({
        title: "Ambient Coding Beats - Lofi Chill Out Session",
        artist: "Chill Beats Collective",
        album: "Lofi Developers Vol 1",
        genre: "Lo-Fi / Ambient",
        duration: "03:45",
        views: "148,914",
        date: "2026-05-12"
      });
    }, 1200);
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
        return prev + 10;
      });
    }, 400);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Audio Extraction Engine</h1>
        <p className="text-muted-foreground mt-1">Extract high-quality audio formats, convert codecs, embed cover art, and inject metadata tags.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Settings options (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Input field */}
          <Card>
            <CardHeader>
              <CardTitle>Audio URL</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Input
                placeholder="https://www.youtube.com/watch?v=... or Soundcloud URL"
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="font-mono text-sm"
              />
              <Button variant="outline" onClick={handlePaste}>Paste</Button>
              <Button variant="primary" onClick={handleAnalyze} disabled={!url || analyzing}>
                {analyzing ? "Analyzing..." : "Analyze"}
              </Button>
            </CardContent>
          </Card>

          {/* Metadata preview & metadata overrides */}
          {metadata && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Sparkles className="h-4.5 w-4.5 text-primary" /> Audio Tags & Metadata Preview</CardTitle>
                <CardDescription>FluxMedia automatically extracts audio metadata. You can override tags below.</CardDescription>
              </CardHeader>
              <CardContent className="flex flex-col sm:flex-row gap-6">
                <div className="h-32 w-32 shrink-0 rounded-lg bg-secondary/85 border border-border flex items-center justify-center relative overflow-hidden">
                  <Image className="h-8 w-8 text-muted-foreground/60" />
                  <div className="absolute inset-0 bg-neutral-900/10 flex items-center justify-center hover:opacity-100 opacity-0 transition-opacity cursor-pointer">
                    <span className="text-[10px] uppercase font-bold text-white bg-black/60 px-2 py-0.5 rounded">Change Cover</span>
                  </div>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 flex-1">
                  <Input label="Track Artist" defaultValue={metadata.artist} />
                  <Input label="Track Title" defaultValue={metadata.title} />
                  <Input label="Album Name" defaultValue={metadata.album} />
                  <Input label="Genre Tag" defaultValue={metadata.genre} />
                </div>
              </CardContent>
            </Card>
          )}

          {/* Audio Codec & Bitrate Settings */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Sliders className="h-4.5 w-4.5 text-primary" /> Audio Extraction Settings</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-6 sm:grid-cols-2">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Output Audio Format</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>MP3 (Lame Encoder)</option>
                  <option>FLAC (Lossless Audio Codec)</option>
                  <option>M4A (AAC Codec)</option>
                  <option>WAV (PCM Audio)</option>
                  <option>OGG (Vorbis Codec)</option>
                  <option>AAC (Raw stream)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Audio Bitrate quality</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>320 kbps (High Quality)</option>
                  <option>256 kbps (Standard Quality)</option>
                  <option>192 kbps (Medium Quality)</option>
                  <option>128 kbps (Low Quality)</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Input label="Filename format" defaultValue="%(artist)s - %(title)s.%(ext)s" />
              </div>

              <div className="space-y-1.5">
                <Input label="Download destination" defaultValue="D:\Downloads\FluxMedia\Audio" />
              </div>
            </CardContent>
          </Card>

          {/* Tag & embedding Options */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2"><Settings2 className="h-4.5 w-4.5 text-primary" /> Audio Embed Settings</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-4 sm:grid-cols-2">
              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Embed Album Cover Art</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Inject Standard ID3v2 metadata tags</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Download & embed lyrics tracks</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Normalize volume levels (audio normalization)</span>
              </label>
            </CardContent>
          </Card>
        </div>

        {/* Action Trigger Card (Right column) */}
        <div>
          {downloading || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Active Audio Extraction</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Converting & tagging audio...</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
                
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground pt-2 border-t border-border/40">
                  <div>Format: <span className="font-semibold text-foreground">FLAC</span></div>
                  <div>Bitrate: <span className="font-semibold text-foreground">Lossless</span></div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Action Center</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="primary" className="w-full gap-2" disabled={!metadata || downloading} onClick={handleDownload}>
                  <Music className="h-4.5 w-4.5" /> Start Audio Extraction
                </Button>
                <p className="text-[10px] text-center text-muted-foreground">Make sure FFmpeg is configured correctly inside updates diagnostic settings.</p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
