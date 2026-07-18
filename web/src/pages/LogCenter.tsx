import React, { useState, useEffect, useCallback, useRef } from "react";
import { Terminal, Search, RefreshCw, AlertTriangle, RotateCcw } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { cn } from "../utils/cn";

interface LogEntry {
  timestamp: string;
  severity: string;
  component: string;
  message: string;
}

export const LogCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [copied, setCopied] = useState(false);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const logEndRef = useRef<HTMLDivElement>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchLogs = useCallback(async () => {
    try {
      setError(null);
      const res = await fetch("/api/logs?lines=300");
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setLogs(data.logs ?? []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  // Auto-scroll to bottom when new logs arrive
  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  // Auto-refresh every 5 seconds when enabled
  useEffect(() => {
    if (autoRefresh) {
      intervalRef.current = setInterval(fetchLogs, 5000);
    } else {
      if (intervalRef.current) clearInterval(intervalRef.current);
    }
    return () => { if (intervalRef.current) clearInterval(intervalRef.current); };
  }, [autoRefresh, fetchLogs]);

  const tabs = [
    { id: "all", label: "All" },
    { id: "api", label: "API" },
    { id: "main", label: "Core" },
    { id: "tui", label: "TUI" },
  ];

  const filteredLogs = logs.filter((log) => {
    if (activeTab !== "all" && !log.component.toLowerCase().includes(activeTab)) return false;
    return (
      log.message.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.component.toLowerCase().includes(searchQuery.toLowerCase()) ||
      log.severity.toLowerCase().includes(searchQuery.toLowerCase())
    );
  });

  const handleCopyLogs = () => {
    setCopied(true);
    const text = filteredLogs.map(l => `[${l.timestamp}] [${l.severity.toUpperCase()}] [${l.component}] ${l.message}`).join("\n");
    navigator.clipboard.writeText(text);
    setTimeout(() => setCopied(false), 2000);
  };

  const severityColor = (severity: string) => {
    const s = severity.toLowerCase();
    if (s === "error" || s === "critical") return "bg-red-950/20 text-red-500 border border-red-950/30";
    if (s === "warning" || s === "warn") return "bg-amber-950/20 text-amber-500 border border-amber-950/30";
    if (s === "debug") return "bg-purple-950/20 text-purple-400 border border-purple-950/30";
    return "bg-neutral-900 text-neutral-400";
  };

  const summaryCount = (sev: string) => logs.filter(l => l.severity.toLowerCase().includes(sev)).length;

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Logs Explorer</h1>
          <p className="text-muted-foreground mt-1">Inspect tracebacks, diagnostics, and real-time FluxMedia log output.</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Button 
            variant={autoRefresh ? "primary" : "outline"} 
            size="sm" 
            onClick={() => setAutoRefresh(!autoRefresh)}
            className="gap-1.5"
          >
            <RefreshCw className={`h-3.5 w-3.5 ${autoRefresh ? "animate-spin" : ""}`} />
            {autoRefresh ? "Live (5s)" : "Auto Refresh"}
          </Button>
          <Button variant="outline" size="sm" onClick={fetchLogs} disabled={loading}>
            <RotateCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
          <Button variant="outline" size="sm" onClick={handleCopyLogs}>
            {copied ? "Copied!" : "Copy Logs"}
          </Button>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{error} — Make sure the FluxMedia API server is running.</p>
        </div>
      )}

      {/* Stats summary */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "Total Entries", value: logs.length, color: "text-foreground" },
          { label: "Warnings", value: summaryCount("warn"), color: "text-amber-500" },
          { label: "Errors", value: summaryCount("error"), color: "text-red-500" },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-5 pb-4 text-center">
              <p className={`text-2xl font-bold ${stat.color}`}>{stat.value}</p>
              <p className="text-xs text-muted-foreground mt-0.5">{stat.label}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border/80 pb-1">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={cn(
              "px-3 py-1.5 text-xs font-semibold border-b-2 border-transparent transition-colors hover:text-foreground",
              activeTab === tab.id ? "border-primary text-foreground" : "text-muted-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filter */}
      <Card>
        <CardContent className="pt-6">
          <div className="relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground/60" />
            <Input
              placeholder="Filter by message, component, or severity..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="pl-9 h-9"
            />
          </div>
        </CardContent>
      </Card>

      {/* Log Console */}
      <Card className="bg-neutral-950 text-neutral-200 border-neutral-800">
        <CardHeader className="border-b border-neutral-900 pb-3 flex justify-between items-center">
          <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
            <Terminal className="h-4 w-4 text-primary" /> Trace Logs Console
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant="outline" className={`text-[10px] border-neutral-800 ${autoRefresh ? "text-emerald-400 border-emerald-900" : "text-neutral-400"}`}>
              {autoRefresh ? "● Live" : "Static"}
            </Badge>
            <span className="text-[10px] text-neutral-600">{filteredLogs.length} entries</span>
          </div>
        </CardHeader>
        <CardContent className="p-4 font-mono text-[10px] leading-relaxed max-h-[420px] overflow-y-auto space-y-1 select-text">
          {loading ? (
            <span className="text-neutral-600 animate-pulse">Loading logs from API...</span>
          ) : filteredLogs.length === 0 ? (
            <span className="text-neutral-600">
              {logs.length === 0
                ? "No log entries found. The FluxMedia log file may be empty or the API is unreachable."
                : "No entries match your filter criteria."}
            </span>
          ) : (
            filteredLogs.map((log, idx) => (
              <div key={idx} className="flex gap-3 items-start py-0.5 border-b border-neutral-900/30 pb-1">
                {log.timestamp && (
                  <span className="text-neutral-600 shrink-0 tabular-nums">{log.timestamp}</span>
                )}
                <span className={cn(
                  "uppercase font-bold shrink-0 text-[9px] px-1.5 py-0.5 rounded",
                  severityColor(log.severity)
                )}>
                  {log.severity}
                </span>
                <span className="text-blue-400 shrink-0 font-semibold">[{log.component}]</span>
                <span className="text-neutral-200 leading-normal break-all">{log.message}</span>
              </div>
            ))
          )}
          <div ref={logEndRef} />
        </CardContent>
      </Card>
    </div>
  );
};

export default LogCenter;
