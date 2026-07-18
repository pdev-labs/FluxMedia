import React, { useState, useEffect, useCallback } from "react";
import {
  ArrowUpRight, ArrowDownRight, History, Database,
  FileVideo, Music, Image, FileText, RotateCcw, AlertTriangle
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { Button } from "../components/ui/Button";
import { ProgressBar } from "../components/ui/ProgressBar";

interface TypeBreakdown {
  count: number;
  size: string;
  bytes: number;
}

interface WeeklyPoint {
  date: string;
  count: number;
}

interface StatsData {
  total_downloads: number;
  completed: number;
  failed: number;
  total_size: string;
  total_size_bytes: number;
  type_breakdown: Record<string, TypeBreakdown>;
  weekly_activity: WeeklyPoint[];
  download_dir: string;
}

const typeConfig: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  videos:    { icon: FileVideo,  color: "text-blue-500",    label: "Video Files" },
  audio:     { icon: Music,      color: "text-emerald-500", label: "Audio Tracks" },
  images:    { icon: Image,      color: "text-pink-500",    label: "Images" },
  documents: { icon: FileText,   color: "text-neutral-400", label: "Docs & Subs" },
  other:     { icon: FileText,   color: "text-muted-foreground", label: "Other" },
};

export const SystemStats: React.FC = () => {
  const [stats, setStats] = useState<StatsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/stats");
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setStats(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  // Build chart points from weekly data
  const buildChartPath = (weekly: WeeklyPoint[]) => {
    const maxCount = Math.max(...weekly.map((w) => w.count), 1);
    const points = weekly.map((w, i) => {
      const x = 10 + (i / (weekly.length - 1)) * 480;
      const y = 190 - (w.count / maxCount) * 160;
      return { x, y, ...w };
    });
    const path = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ");
    return { points, path };
  };

  const topMetrics = stats
    ? [
        {
          title: "Total Downloads",
          value: `${stats.total_downloads} files`,
          change: `${stats.completed} completed · ${stats.failed} failed`,
          isUp: stats.completed > stats.failed,
          icon: History,
          color: "text-indigo-500",
          bg: "bg-indigo-500/10"
        },
        {
          title: "Storage Used",
          value: stats.total_size,
          change: "Across all file types",
          isUp: null,
          icon: Database,
          color: "text-amber-500",
          bg: "bg-amber-500/10"
        },
      ]
    : [];

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Statistics & Analytics</h1>
          <p className="text-muted-foreground mt-1">Review download volumes, storage usage, and format breakdowns from your real data.</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchStats} disabled={loading}>
          <RotateCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Top metrics */}
      {stats && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {topMetrics.map((stat) => (
            <Card key={stat.title}>
              <CardContent className="pt-6">
                <div className="flex justify-between items-start">
                  <div className={`p-2 rounded-lg ${stat.bg} ${stat.color}`}>
                    <stat.icon className="h-5 w-5" />
                  </div>
                  {stat.isUp !== null && (
                    stat.isUp
                      ? <Badge variant="success" className="gap-0.5"><ArrowUpRight className="h-3 w-3" /> Up</Badge>
                      : <Badge variant="secondary" className="gap-0.5"><ArrowDownRight className="h-3 w-3" /> Low</Badge>
                  )}
                </div>
                <h3 className="text-2xl font-bold mt-4">{stat.value}</h3>
                <p className="text-xs font-semibold text-foreground mt-1">{stat.title}</p>
                <p className="text-[11px] text-muted-foreground mt-0.5">{stat.change}</p>
              </CardContent>
            </Card>
          ))}

          {/* Type counts */}
          {(["videos", "audio"] as const).map((type) => {
            const cfg = typeConfig[type];
            const data = stats.type_breakdown[type];
            return (
              <Card key={type}>
                <CardContent className="pt-6">
                  <div className={`p-2 rounded-lg bg-secondary/40 ${cfg.color} w-fit`}>
                    <cfg.icon className="h-5 w-5" />
                  </div>
                  <h3 className="text-2xl font-bold mt-4">{data.count}</h3>
                  <p className="text-xs font-semibold text-foreground mt-1">{cfg.label}</p>
                  <p className="text-[11px] text-muted-foreground mt-0.5">{data.size}</p>
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}

      {stats && (
        <div className="grid gap-6 md:grid-cols-2">
          {/* Weekly activity chart */}
          <Card>
            <CardHeader>
              <CardTitle>Download Activity (Last 7 Days)</CardTitle>
              <CardDescription>Number of downloads recorded per day from your history.</CardDescription>
            </CardHeader>
            <CardContent className="h-64 flex flex-col justify-between pt-4">
              {(() => {
                const { points, path } = buildChartPath(stats.weekly_activity);
                const maxCount = Math.max(...stats.weekly_activity.map((w) => w.count), 1);
                return (
                  <>
                    <div className="flex-1 w-full relative">
                      <svg className="w-full h-full" viewBox="0 0 500 200" preserveAspectRatio="none">
                        {/* Grid lines */}
                        {[50, 100, 150].map((y) => (
                          <line key={y} x1="0" y1={y} x2="500" y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                        ))}
                        {/* Gradient fill */}
                        <defs>
                          <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="hsl(var(--primary))" stopOpacity="0.3" />
                            <stop offset="100%" stopColor="hsl(var(--primary))" stopOpacity="0" />
                          </linearGradient>
                        </defs>
                        <path
                          d={`${path} L ${points[points.length - 1].x} 200 L ${points[0].x} 200 Z`}
                          fill="url(#areaGrad)"
                        />
                        <path d={path} fill="none" stroke="hsl(var(--primary))" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
                        {points.map((p, i) => (
                          <g key={i}>
                            <circle cx={p.x} cy={p.y} r="4" fill="hsl(var(--primary))" />
                            {p.count > 0 && (
                              <text x={p.x} y={p.y - 10} textAnchor="middle" fill="hsl(var(--primary))" fontSize="10" fontWeight="bold">{p.count}</text>
                            )}
                          </g>
                        ))}
                      </svg>
                    </div>
                    <div className="flex justify-between text-[10px] text-muted-foreground pt-4 border-t border-border/40 font-mono">
                      {stats.weekly_activity.map((w) => (
                        <span key={w.date}>{new Date(w.date).toLocaleDateString("en", { weekday: "short" })}</span>
                      ))}
                    </div>
                  </>
                );
              })()}
            </CardContent>
          </Card>

          {/* Storage by type */}
          <Card>
            <CardHeader>
              <CardTitle>Storage Ratio by Media Type</CardTitle>
              <CardDescription>Distribution of files scanned from your download directory.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 pt-4">
              {(["videos", "audio", "images", "documents"] as const).map((type) => {
                const cfg = typeConfig[type];
                const data = stats.type_breakdown[type];
                const pct = stats.total_size_bytes > 0
                  ? Math.round((data.bytes / stats.total_size_bytes) * 100)
                  : 0;
                return (
                  <div key={type} className="space-y-1.5">
                    <div className="flex justify-between text-xs font-semibold">
                      <span className={`flex items-center gap-1.5 ${cfg.color}`}>
                        <cfg.icon className="h-4 w-4" /> {cfg.label}
                      </span>
                      <span className="font-mono text-muted-foreground">{pct}% ({data.size})</span>
                    </div>
                    <ProgressBar value={pct} size="sm" />
                  </div>
                );
              })}
              {stats.total_size_bytes === 0 && (
                <p className="text-sm text-muted-foreground text-center py-4">No files found in download directory.</p>
              )}
            </CardContent>
          </Card>
        </div>
      )}

      {!stats && !loading && (
        <Card>
          <CardContent className="h-48 flex items-center justify-center text-muted-foreground text-sm">
            No data available. Make sure the API server is running.
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default SystemStats;
