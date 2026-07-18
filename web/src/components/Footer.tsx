import React from "react";
import { CheckCircle2, Wifi, Cpu, Database } from "lucide-react";

export const Footer: React.FC = () => {
  return (
    <footer className="flex h-6 w-full items-center justify-between border-t border-border bg-secondary/30 px-3 text-[11px] text-muted-foreground select-none">
      {/* Left section: status indicators */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
          <span>FluxCore Connected</span>
        </div>
        
        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="h-3 w-3 text-emerald-500" />
          <span>Python 3.12.0</span>
        </div>

        <div className="flex items-center gap-1.5">
          <CheckCircle2 className="h-3 w-3 text-emerald-500" />
          <span>FFmpeg v6.0</span>
        </div>
      </div>

      {/* Right section: System performance and network stats */}
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <Wifi className="h-3 w-3" />
          <span>12.4 Mbps</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Cpu className="h-3 w-3" />
          <span>CPU: 4.2%</span>
        </div>

        <div className="flex items-center gap-1.5">
          <Database className="h-3 w-3" />
          <span>RAM: 148MB</span>
        </div>

        <span className="text-border">|</span>

        <span>v1.6.30</span>
      </div>
    </footer>
  );
};
