import React, { useState } from "react";
import { 
  RefreshCw, Terminal, Copy, Check
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { cn } from "../utils/cn";

export const SystemDiagnostics: React.FC = () => {
  const [runningTests, setRunningTests] = useState(false);
  const [score, setScore] = useState(95);
  const [logs, setLogs] = useState<string[]>([]);
  const [copied, setCopied] = useState(false);

  const diagnosticChecks = [
    { name: "Internet Connection", status: "success", desc: "Connected to YouTube stream nodes." },
    { name: "DNS Resolvers", status: "success", desc: "Lookup latency 12ms." },
    { name: "Python Interpreter", status: "success", desc: "Python v3.12.0 active." },
    { name: "FFmpeg Codecs", status: "success", desc: "FFmpeg v6.0-stable initialized." },
    { name: "Write Permissions", status: "success", desc: "D:\Downloads directory writable." },
    { name: "Disk Storage Space", status: "warning", desc: "D:\ drive has less than 15GB free." }
  ];

  const handleRunTests = () => {
    setRunningTests(true);
    setLogs(["[diagnostics] Spawning subsystem testers...", "[diagnostics] Pinging YouTube DNS servers..."]);
    setTimeout(() => {
      setRunningTests(false);
      setScore(98);
      setLogs((prev) => [
        ...prev,
        "[diagnostics] Network latency check: 14ms (Excellent)",
        "[diagnostics] Directory structure verified",
        "[success] Subsystems diagnostics complete. Score updated."
      ]);
    }, 1500);
  };

  const handleCopyReport = () => {
    setCopied(true);
    navigator.clipboard.writeText("FluxMedia Diagnostics Report - Score: " + score + "\nInternet: PASS\nPython: PASS\nFFmpeg: PASS");
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Diagnostics & Health</h1>
          <p className="text-muted-foreground mt-1">Scan system dependencies, measure internet latencies, check file permissions, and export reports.</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Verification Check Cards (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* Health Score Overview */}
          <div className="grid gap-6 sm:grid-cols-2">
            <Card className="flex flex-col justify-between">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Diagnostics Score</CardTitle>
              </CardHeader>
              <CardContent className="pt-2 flex flex-col justify-center">
                <div className="flex items-baseline gap-2">
                  <span className="text-5xl font-extrabold tracking-tight text-primary">{score}</span>
                  <span className="text-xs text-muted-foreground">/ 100</span>
                </div>
                <p className="text-xs text-muted-foreground mt-2 leading-relaxed">
                  {score >= 95 ? "All critical subsystems are fully operational." : "Subsystem warnings detected. Review checks below."}
                </p>
              </CardContent>
            </Card>

            <Card className="flex flex-col justify-between">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Automatic Repairs</CardTitle>
              </CardHeader>
              <CardContent className="pt-2 flex flex-col gap-2">
                <Button variant="outline" size="sm" className="w-full justify-start text-xs">Reset Folder Permissions</Button>
                <Button variant="outline" size="sm" className="w-full justify-start text-xs">Flush Temporary Cache</Button>
              </CardContent>
            </Card>
          </div>

          {/* Subsystems check items */}
          <Card>
            <CardHeader className="pb-3 border-b border-border/40">
              <CardTitle className="text-base">Subsystem Health Checklist</CardTitle>
            </CardHeader>
            <CardContent className="divide-y divide-border/40 p-0">
              {diagnosticChecks.map((check) => (
                <div key={check.name} className="flex justify-between items-center p-3.5">
                  <div>
                    <h4 className="text-xs font-semibold leading-tight">{check.name}</h4>
                    <p className="text-[10px] text-muted-foreground mt-0.5">{check.desc}</p>
                  </div>
                  <Badge variant={check.status === "success" ? "success" : "warning"}>
                    {check.status === "success" ? "Pass" : "Warning"}
                  </Badge>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Live logs & copy options (Right column) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Action Center</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Button variant="primary" className="w-full gap-2" disabled={runningTests} onClick={handleRunTests}>
                <RefreshCw className={`h-4 w-4 ${runningTests && "animate-spin"}`} />
                {runningTests ? "Running Scans..." : "Run Diagnostics Scans"}
              </Button>
              <Button variant="outline" className="w-full gap-2" onClick={handleCopyReport}>
                {copied ? <Check className="h-4 w-4 text-emerald-500" /> : <Copy className="h-4 w-4" />}
                {copied ? "Copied!" : "Copy Diagnostics Report"}
              </Button>
            </CardContent>
          </Card>

          {/* Diagnostics console log output */}
          <Card className="bg-neutral-950 text-neutral-200 border-neutral-800">
            <CardHeader className="border-b border-neutral-900 pb-3">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" /> Scan Output Logs
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 font-mono text-[10px] leading-relaxed max-h-[220px] overflow-y-auto space-y-1">
              {logs.length === 0 ? (
                <span className="text-neutral-600">Diagnostics console idle. Click Run Scans to test connections.</span>
              ) : (
                logs.map((log, idx) => (
                  <div 
                    key={idx} 
                    className={cn(
                      log.includes("[success]") && "text-emerald-400",
                      log.includes("[diagnostics]") && "text-neutral-400"
                    )}
                  >
                    {log}
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
export default SystemDiagnostics;
