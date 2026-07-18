import React, { useState } from "react";
import { Download, FileText } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const SubtitleDownloader: React.FC = () => {
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [metadata, setMetadata] = useState<any>(null);
  const [selectedLangs, setSelectedLangs] = useState<Set<string>>(new Set());
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleAnalyze = () => {
    if (!url) return;
    setAnalyzing(true);
    setMetadata(null);
    setSelectedLangs(new Set());
    setTimeout(() => {
      setAnalyzing(false);
      setMetadata({
        title: "Quantum Computation Explained - Lecture 1",
        duration: "15:20",
        languages: [
          { code: "en", name: "English (Human-created)", type: "manual" },
          { code: "en-auto", name: "English (Auto-generated)", type: "auto" },
          { code: "es", name: "Spanish / Español (Human-created)", type: "manual" },
          { code: "fr", name: "French / Français (Auto-generated)", type: "auto" }
        ]
      });
      setSelectedLangs(new Set(["en"]));
    }, 1200);
  };

  const handleToggleLang = (code: string) => {
    setSelectedLangs((prev) => {
      const next = new Set(prev);
      if (next.has(code)) next.delete(code);
      else next.add(code);
      return next;
    });
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
        return prev + 20;
      });
    }, 300);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Subtitle Extractor</h1>
        <p className="text-muted-foreground mt-1">Download human-written or auto-generated subtitle tracks in custom formats (SRT, VTT).</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Video URL & Langs list (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* URL Input */}
          <Card>
            <CardHeader>
              <CardTitle>Video URL</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Input
                placeholder="https://www.youtube.com/watch?v=..."
                value={url}
                onChange={(e) => setUrl(e.target.value)}
                className="font-mono text-sm"
              />
              <Button variant="primary" onClick={handleAnalyze} disabled={!url || analyzing}>
                {analyzing ? "Analyzing..." : "Analyze"}
              </Button>
            </CardContent>
          </Card>

          {/* Languages Selector */}
          {metadata && (
            <Card>
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base">Available Captions Tracks</CardTitle>
                    <CardDescription>{metadata.title} ({metadata.duration})</CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="p-0">
                <div className="divide-y divide-border/40">
                  {metadata.languages.map((lang: any) => (
                    <div 
                      key={lang.code} 
                      onClick={() => handleToggleLang(lang.code)}
                      className="flex items-center justify-between p-3.5 hover:bg-secondary/40 cursor-pointer select-none"
                    >
                      <div className="flex items-center gap-3">
                        <input 
                          type="checkbox" 
                          checked={selectedLangs.has(lang.code)}
                          onChange={() => {}}
                          className="rounded border-border text-primary focus:ring-primary h-4 w-4"
                        />
                        <FileText className="h-4.5 w-4.5 text-muted-foreground shrink-0" />
                        <span className="text-sm font-medium leading-tight">{lang.name}</span>
                      </div>
                      <Badge variant={lang.type === "manual" ? "success" : "secondary"} className="text-[10px]">
                        {lang.type === "manual" ? "Human" : "Auto-Gen"}
                      </Badge>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action & Format settings (Right column) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Subtitle Formats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Subtitle File Format</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>SRT (SubRip)</option>
                  <option>VTT (WebVTT)</option>
                  <option>ASS (Advanced SubStation)</option>
                  <option>TXT (Raw text description)</option>
                </select>
              </div>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Embed directly inside video</span>
              </label>

              <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                <span>Save as separate files</span>
              </label>
            </CardContent>
          </Card>

          {downloading || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Extracting Captions</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Downloading subtitle tracks...</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
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
                  disabled={selectedLangs.size === 0 || downloading}
                  onClick={handleDownload}
                >
                  <Download className="h-4.5 w-4.5" /> Download Selected Subtitles
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
