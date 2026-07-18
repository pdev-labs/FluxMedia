import React, { useState } from "react";
import { Terminal, Search } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { cn } from "../utils/cn";

export const LogCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [copied, setCopied] = useState(false);

  const logItems = [
    { timestamp: "2026-07-18 17:10:04", component: "extractor", severity: "info", message: "Initial parse of stream completed" },
    { timestamp: "2026-07-18 17:10:06", component: "network", severity: "warning", message: "Latency packet loss detected: 2%" },
    { timestamp: "2026-07-18 17:10:12", component: "transcoder", severity: "error", message: "FFmpeg raise invalid argument multiplexing libx265 streams" },
    { timestamp: "2026-07-18 17:10:24", component: "sharing", severity: "info", message: "HTTP files server boot online on port 8000" }
  ];

  const filteredLogs = logItems.filter((log) => {
    if (activeTab !== "all" && log.component !== activeTab) return false;
    return log.message.toLowerCase().includes(searchQuery.toLowerCase()) || 
           log.component.toLowerCase().includes(searchQuery.toLowerCase());
  });

  const handleCopyLogs = () => {
    setCopied(true);
    navigator.clipboard.writeText(JSON.stringify(filteredLogs, null, 2));
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Logs Explorer</h1>
          <p className="text-muted-foreground mt-1">Inspect traceback trace files, connection diagnostics, and downloader logs.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={handleCopyLogs}>
            {copied ? "Copied!" : "Copy Active Logs"}
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border/80 pb-1">
        <button onClick={() => setActiveTab("all")} className={cn("px-3 py-1.5 text-xs font-semibold border-b-2 border-transparent hover:text-foreground", activeTab === "all" && "border-primary text-foreground")}>All Components</button>
        <button onClick={() => setActiveTab("extractor")} className={cn("px-3 py-1.5 text-xs font-semibold border-b-2 border-transparent hover:text-foreground", activeTab === "extractor" && "border-primary text-foreground")}>Extractor</button>
        <button onClick={() => setActiveTab("network")} className={cn("px-3 py-1.5 text-xs font-semibold border-b-2 border-transparent hover:text-foreground", activeTab === "network" && "border-primary text-foreground")}>Network</button>
        <button onClick={() => setActiveTab("transcoder")} className={cn("px-3 py-1.5 text-xs font-semibold border-b-2 border-transparent hover:text-foreground", activeTab === "transcoder" && "border-primary text-foreground")}>FFmpeg Converter</button>
        <button onClick={() => setActiveTab("sharing")} className={cn("px-3 py-1.5 text-xs font-semibold border-b-2 border-transparent hover:text-foreground", activeTab === "sharing" && "border-primary text-foreground")}>LAN Share</button>
      </div>

      {/* Filter panel */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground/60" />
            <Input
              placeholder="Filter console log message content..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
        </CardContent>
      </Card>

      {/* Code Log Container */}
      <Card className="bg-neutral-950 text-neutral-200 border-neutral-800">
        <CardHeader className="border-b border-neutral-900 pb-3 flex justify-between items-center">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
            <Terminal className="h-4 w-4 text-primary" /> Trace Logs Console
          </CardTitle>
          <Badge variant="outline" className="text-[10px] text-neutral-400 border-neutral-800">Live Updating</Badge>
        </CardHeader>
        <CardContent className="p-4 font-mono text-[10px] leading-relaxed max-h-[350px] overflow-y-auto space-y-2 select-text">
          {filteredLogs.length === 0 ? (
            <span className="text-neutral-600">No trace logs matched the search criteria.</span>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className="flex gap-4 items-start py-0.5 border-b border-neutral-900/40 pb-1.5">
                <span className="text-neutral-500 shrink-0">{log.timestamp}</span>
                <span className={cn(
                  "uppercase font-bold shrink-0 text-[9px] px-1.5 py-0.5 rounded",
                  log.severity === "info" && "bg-neutral-900 text-neutral-400",
                  log.severity === "warning" && "bg-amber-950/20 text-amber-500 border border-amber-950/30",
                  log.severity === "error" && "bg-red-950/20 text-red-500 border border-red-950/30"
                )}>{log.severity}</span>
                <span className="text-neutral-400 shrink-0 font-semibold">[{log.component}]</span>
                <span className="text-neutral-200 leading-normal">{log.message}</span>
              </div>
            ))
          )}
        </CardContent>
      </Card>
    </div>
  );
};
export default LogCenter;
