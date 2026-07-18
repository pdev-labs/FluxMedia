import React, { useState } from "react";
import { Scissors, Clock } from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const TrimDownloader: React.FC = () => {
  const [url, setUrl] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [metadata, setMetadata] = useState<any>(null);
  const [startTime, setStartTime] = useState("00:01:00");
  const [endTime, setEndTime] = useState("00:03:00");
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleAnalyze = () => {
    if (!url) return;
    setAnalyzing(true);
    setMetadata(null);
    setTimeout(() => {
      setAnalyzing(false);
      setMetadata({
        title: "Quantum Computation explained in 10 minutes",
        duration: "00:10:00",
        uploader: "Physics Frontiers"
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
    }, 450);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Trim & Download Downloader</h1>
        <p className="text-muted-foreground mt-1">Select and extract specific segments of online videos using duration boundaries without downloading the full stream.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Settings & Timeline (Left 2 columns) */}
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

          {/* Interactive Timeline Mock */}
          {metadata && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2"><Clock className="h-4.5 w-4.5 text-primary" /> Interactive Trimming Timeline</CardTitle>
                <CardDescription>{metadata.title} ({metadata.duration})</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Timeline Graph Placeholder */}
                <div className="h-16 rounded bg-secondary/80 border border-border flex items-center justify-between relative px-6 overflow-hidden">
                  <div className="absolute top-0 bottom-0 bg-primary/20 border-x-2 border-primary" style={{ left: "20%", right: "45%" }} />
                  <span className="text-[10px] text-muted-foreground z-10">00:00:00</span>
                  <span className="text-[10px] font-bold text-primary z-10">Start: {startTime}</span>
                  <span className="text-[10px] font-bold text-primary z-10">End: {endTime}</span>
                  <span className="text-[10px] text-muted-foreground z-10">{metadata.duration}</span>
                </div>

                {/* Duration settings inputs */}
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input 
                    label="Start Time Bound (hh:mm:ss)" 
                    value={startTime}
                    onChange={(e) => setStartTime(e.target.value)} 
                  />
                  <Input 
                    label="End Time Bound (hh:mm:ss)" 
                    value={endTime}
                    onChange={(e) => setEndTime(e.target.value)} 
                  />
                </div>

                <div className="flex gap-4 text-xs text-muted-foreground">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                    <span>Snap selection boundaries to chapters</span>
                  </label>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action Panel (Right column) */}
        <div>
          {downloading || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Trimming Video Stream</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Extracting segment...</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
                <div className="text-xs text-muted-foreground text-center">
                  {progress === 100 ? "Completed" : "Extracting and merging frames..."}
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
                  disabled={!metadata || downloading}
                  onClick={handleDownload}
                >
                  <Scissors className="h-4.5 w-4.5" /> Start Trim Extraction
                </Button>
                <div className="text-[10px] text-center text-muted-foreground">
                  Estimated size: <span className="font-semibold text-foreground">approx. 45 MB</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
