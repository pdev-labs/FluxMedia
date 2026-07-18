import React from "react";
import { 
  ArrowUpRight, ArrowDownRight, History, Database, Cpu, 
  Wifi, FileVideo, Music, Image, FileText
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Badge } from "../components/ui/Badge";
import { ProgressBar } from "../components/ui/ProgressBar";

export const SystemStats: React.FC = () => {
  const statMetrics = [
    { title: "Total Downloads", value: "148 files", change: "+12.4% vs last month", isUp: true, icon: History, color: "text-indigo-500", bg: "bg-indigo-500/10" },
    { title: "Storage Space Used", value: "32.4 GB", change: "42.8 GB total limit", isUp: false, icon: Database, color: "text-amber-500", bg: "bg-amber-500/10" },
    { title: "Bandwidth Saved", value: "12.6 GB", change: "Via local caches", isUp: true, icon: Wifi, color: "text-emerald-500", bg: "bg-emerald-500/10" },
    { title: "Average Speed", value: "4.8 MB/s", change: "Broadband network link", isUp: true, icon: Cpu, color: "text-blue-500", bg: "bg-blue-500/10" }
  ];

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Statistics & Analytics</h1>
        <p className="text-muted-foreground mt-1">Review download historical volumes, bandwidth limits, storage usage logs, and formats allocations.</p>
      </div>

      {/* Grid numbers */}
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {statMetrics.map((stat) => (
          <Card key={stat.title}>
            <CardContent className="pt-6">
              <div className="flex justify-between items-start">
                <div className={`p-2 rounded-lg ${stat.bg} ${stat.color}`}>
                  <stat.icon className="h-5 w-5" />
                </div>
                {stat.isUp ? (
                  <Badge variant="success" className="gap-0.5"><ArrowUpRight className="h-3 w-3" /> Up</Badge>
                ) : (
                  <Badge variant="secondary" className="gap-0.5"><ArrowDownRight className="h-3 w-3" /> Safe</Badge>
                )}
              </div>
              <h3 className="text-2xl font-bold mt-4">{stat.value}</h3>
              <p className="text-xs font-semibold text-foreground mt-1">{stat.title}</p>
              <p className="text-[11px] text-muted-foreground mt-0.5">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Weekly download speed interactive SVG Graph */}
        <Card>
          <CardHeader>
            <CardTitle>Speed Trends (Last 7 Days)</CardTitle>
            <CardDescription>Average network download speeds over the past week.</CardDescription>
          </CardHeader>
          <CardContent className="h-64 flex flex-col justify-between pt-4">
            {/* Custom SVG line chart */}
            <div className="flex-1 w-full relative">
              <svg className="w-full h-full" viewBox="0 0 500 200" preserveAspectRatio="none">
                {/* Grid lines */}
                <line x1="0" y1="50" x2="500" y2="50" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <line x1="0" y1="100" x2="500" y2="100" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <line x1="0" y1="150" x2="500" y2="150" stroke="rgba(255,255,255,0.05)" strokeWidth="1" />

                {/* Line path */}
                <path
                  d="M 10 150 L 80 120 L 160 170 L 240 80 L 320 130 L 400 60 L 480 40"
                  fill="none"
                  stroke="hsl(var(--primary))"
                  strokeWidth="3"
                  strokeLinecap="round"
                />

                {/* Data points */}
                <circle cx="10" cy="150" r="4" fill="hsl(var(--primary))" />
                <circle cx="80" cy="120" r="4" fill="hsl(var(--primary))" />
                <circle cx="160" cy="170" r="4" fill="hsl(var(--primary))" />
                <circle cx="240" cy="80" r="4" fill="hsl(var(--primary))" />
                <circle cx="320" cy="130" r="4" fill="hsl(var(--primary))" />
                <circle cx="400" cy="60" r="4" fill="hsl(var(--primary))" />
                <circle cx="480" cy="40" r="4" fill="hsl(var(--primary))" />
              </svg>
            </div>
            
            {/* Days label */}
            <div className="flex justify-between text-[10px] text-muted-foreground pt-4 border-t border-border/40 font-mono">
              <span>Mon</span>
              <span>Tue</span>
              <span>Wed</span>
              <span>Thu</span>
              <span>Fri</span>
              <span>Sat</span>
              <span>Sun</span>
            </div>
          </CardContent>
        </Card>

        {/* Media Formats Allocation */}
        <Card>
          <CardHeader>
            <CardTitle>Storage Ratio by Media Type</CardTitle>
            <CardDescription>Percentage distribution of files in the download directories.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4 pt-4">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5"><FileVideo className="h-4 w-4 text-blue-500" /> MP4 Video Streams</span>
                <span className="font-mono">75% (24.3 GB)</span>
              </div>
              <ProgressBar value={75} size="sm" />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5"><Music className="h-4 w-4 text-emerald-500" /> FLAC/MP3 Audio Tracks</span>
                <span className="font-mono">15% (4.8 GB)</span>
              </div>
              <ProgressBar value={15} size="sm" />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5"><Image className="h-4 w-4 text-pink-500" /> Album Cover Images</span>
                <span className="font-mono">5% (1.6 GB)</span>
              </div>
              <ProgressBar value={5} size="sm" />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span className="flex items-center gap-1.5"><FileText className="h-4 w-4 text-neutral-400" /> SRT/VTT Subtitle Logs</span>
                <span className="font-mono">5% (1.6 GB)</span>
              </div>
              <ProgressBar value={5} size="sm" />
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};
