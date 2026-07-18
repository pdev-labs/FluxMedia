import React, { useState, useEffect, useCallback, useRef } from "react";
import {
  RefreshCw, Terminal, Copy, Check, AlertTriangle, RotateCcw,
  CheckCircle2, XCircle, AlertCircle, Wifi, Cpu, HardDrive, Package
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { cn } from "../utils/cn";

interface DiagCheck {
  name: string;
  status: "pass" | "fail" | "warning";
  desc: string;
}

interface DiagResult {
  score: number;
  checks: DiagCheck[];
  platform: string;
  python_version: string;
}

const checkIcon = (status: string) => {
  if (status === "pass") return <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />;
  if (status === "fail") return <XCircle className="h-4 w-4 text-red-500 shrink-0" />;
  return <AlertCircle className="h-4 w-4 text-amber-500 shrink-0" />;
};

const checkIcons: Record<string, React.ElementType> = {
  "Internet Connection": Wifi,
  "Python Interpreter": Cpu,
  "yt-dlp": Package,
  "FFmpeg": RefreshCw,
  "Write Permissions": HardDrive,
  "Disk Space": HardDrive,
};

export const SystemDiagnostics: React.FC = () => {
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState<DiagResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const logEndRef = useRef<HTMLDivElement>(null);

  const runDiagnostics = useCallback(async () => {
    setRunning(true);
    setError(null);
    setLogs([
      "[diagnostics] Spawning subsystem testers...",
      "[diagnostics] Checking internet connectivity...",
      "[diagnostics] Verifying Python interpreter...",
      "[diagnostics] Probing yt-dlp installation...",
      "[diagnostics] Checking FFmpeg availability...",
      "[diagnostics] Verifying write permissions...",
      "[diagnostics] Scanning disk space...",
    ]);

    try {
      const res = await fetch("/api/diagnostics");
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setResult(data);

      const newLogs: string[] = [];
      data.checks.forEach((c: DiagCheck) => {
        const icon = c.status === "pass" ? "[pass]" : c.status === "fail" ? "[fail]" : "[warn]";
        newLogs.push(`${icon} ${c.name}: ${c.desc}`);
      });
      newLogs.push(`[success] Diagnostics complete. Health score: ${data.score}/100`);
      setLogs((p) => [...p, ...newLogs]);
    } catch (err: any) {
      setError(err.message);
      setLogs((p) => [...p, `[error] Failed to run diagnostics: ${err.message}`]);
    } finally {
      setRunning(false);
    }
  }, []);

  // Run on mount
  useEffect(() => { runDiagnostics(); }, [runDiagnostics]);

  useEffect(() => {
    logEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [logs]);

  const handleCopyReport = () => {
    if (!result) return;
    const lines = [
      `FluxMedia Diagnostics Report`,
      `Health Score: ${result.score}/100`,
      `Platform: ${result.platform}`,
      `Python: ${result.python_version}`,
      "",
      ...result.checks.map((c) => `[${c.status.toUpperCase()}] ${c.name}: ${c.desc}`)
    ].join("\n");
    navigator.clipboard.writeText(lines);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const scoreColor = (score: number) => {
    if (score >= 90) return "text-emerald-500";
    if (score >= 70) return "text-amber-500";
    return "text-red-500";
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Diagnostics & Health</h1>
          <p className="text-muted-foreground mt-1">Scan system dependencies, measure internet latencies, check file permissions, and export reports.</p>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{error} — Make sure the API server is running.</p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Left 2 columns */}
        <div className="lg:col-span-2 space-y-6">
          {/* Score + summary */}
          <div className="grid gap-6 sm:grid-cols-2">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Diagnostics Score</CardTitle>
              </CardHeader>
              <CardContent className="pt-2">
                {running ? (
                  <div className="flex items-center gap-3">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    <span className="text-sm text-muted-foreground">Scanning...</span>
                  </div>
                ) : result ? (
                  <>
                    <div className="flex items-baseline gap-2">
                      <span className={`text-5xl font-extrabold tracking-tight ${scoreColor(result.score)}`}>{result.score}</span>
                      <span className="text-xs text-muted-foreground">/ 100</span>
                    </div>
                    <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                      {result.score >= 90 ? "All critical subsystems are fully operational." :
                        result.score >= 70 ? "Minor warnings detected. Review checks below." :
                        "Critical issues detected. Action required."}
                    </p>
                  </>
                ) : (
                  <p className="text-sm text-muted-foreground">Not yet scanned.</p>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">System Info</CardTitle>
              </CardHeader>
              <CardContent className="pt-2 text-xs text-muted-foreground space-y-1.5">
                {result ? (
                  <>
                    <p className="break-all"><span className="font-semibold text-foreground">Platform:</span> {result.platform}</p>
                    <p className="break-all"><span className="font-semibold text-foreground">Python:</span> {result.python_version.split(" ")[0]}</p>
                  </>
                ) : (
                  <p className="italic">Run diagnostics to see system info.</p>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Subsystem health checks */}
          <Card>
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base">Subsystem Health Checklist</CardTitle>
            </CardHeader>
            <CardContent className="divide-y divide-border/40 p-0">
              {running ? (
                <div className="h-48 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : result ? (
                result.checks.map((check) => {
                  const Icon = checkIcons[check.name] ?? Cpu;
                  return (
                    <div key={check.name} className="flex justify-between items-center p-4">
                      <div className="flex items-center gap-3">
                        <Icon className="h-4 w-4 text-muted-foreground shrink-0" />
                        <div>
                          <h4 className="text-xs font-semibold leading-tight">{check.name}</h4>
                          <p className="text-[10px] text-muted-foreground mt-0.5">{check.desc}</p>
                        </div>
                      </div>
                      <div className="flex items-center gap-2 shrink-0 ml-4">
                        {checkIcon(check.status)}
                        <Badge variant={check.status === "pass" ? "success" : check.status === "fail" ? "destructive" : "warning"} className="capitalize text-[10px]">
                          {check.status === "pass" ? "Pass" : check.status === "fail" ? "Fail" : "Warning"}
                        </Badge>
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="h-48 flex items-center justify-center text-muted-foreground text-xs">Click "Run Diagnostics" to start.</div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right column */}
        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Action Center</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              <Button variant="primary" className="w-full gap-2" disabled={running} onClick={runDiagnostics}>
                <RotateCcw className={`h-4 w-4 ${running ? "animate-spin" : ""}`} />
                {running ? "Running Scans..." : "Run Diagnostics"}
              </Button>
              <Button variant="outline" className="w-full gap-2" onClick={handleCopyReport} disabled={!result}>
                {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                {copied ? "Copied!" : "Copy Diagnostics Report"}
              </Button>
            </CardContent>
          </Card>

          {/* Console output */}
          <Card className="bg-neutral-950 text-neutral-200 border-neutral-800">
            <CardHeader className="border-b border-neutral-900 pb-3">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" /> Scan Output
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 font-mono text-[10px] leading-relaxed max-h-[280px] overflow-y-auto space-y-1 select-text">
              {logs.length === 0 ? (
                <span className="text-neutral-600">Diagnostics console idle.</span>
              ) : (
                logs.map((log, idx) => (
                  <div key={idx} className={cn(
                    log.includes("[success]") && "text-emerald-400",
                    log.includes("[pass]") && "text-emerald-400",
                    log.includes("[fail]") && "text-red-400",
                    log.includes("[warn]") && "text-amber-400",
                    log.includes("[error]") && "text-red-400",
                    log.includes("[diagnostics]") && "text-neutral-500",
                  )}>{log}</div>
                ))
              )}
              <div ref={logEndRef} />
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default SystemDiagnostics;
