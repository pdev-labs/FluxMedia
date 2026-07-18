import React from "react";
import { Link } from "react-router-dom";
import { 
  FileVideo, Search, Music, ListCollapse, FolderGit, Type, Scissors, Camera, ArrowUpRight
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";

export const DownloadCenter: React.FC = () => {
  const downloadEngines = [
    {
      name: "Download Video",
      desc: "Advanced downloader supporting custom formats, codecs, qualities, and embeds.",
      path: "/download/video",
      icon: FileVideo,
      color: "text-blue-500",
      bg: "bg-blue-500/10"
    },
    {
      name: "Search YouTube",
      desc: "Search, filter, and preview media streams before download with infinite scroll.",
      path: "/download/search",
      icon: Search,
      color: "text-purple-500",
      bg: "bg-purple-500/10"
    },
    {
      name: "Download Audio",
      desc: "Extract high-quality audio streams (FLAC, MP3, M4A) with metadata extraction.",
      path: "/download/audio",
      icon: Music,
      color: "text-emerald-500",
      bg: "bg-emerald-500/10"
    },
    {
      name: "Playlist Downloader",
      desc: "Download full playlists, select specific items, skip duplicates, and batch process.",
      path: "/download/playlist",
      icon: ListCollapse,
      color: "text-amber-500",
      bg: "bg-amber-500/10"
    },
    {
      name: "Channel Downloader",
      desc: "Extract all videos, shorts, or live streams from any creator's channel home.",
      path: "/download/channel",
      icon: FolderGit,
      color: "text-indigo-500",
      bg: "bg-indigo-500/10"
    },
    {
      name: "Subtitle Downloader",
      desc: "Download human-created or auto-generated subtitles in SRT, VTT, or ASS formats.",
      path: "/download/subtitles",
      icon: Type,
      color: "text-cyan-500",
      bg: "bg-cyan-500/10"
    },
    {
      name: "Trim & Download",
      desc: "Crop specific portions of online videos using an interactive duration timeline.",
      path: "/download/trimmer",
      icon: Scissors,
      color: "text-rose-500",
      bg: "bg-rose-500/10"
    },
    {
      name: "Instagram Downloader",
      desc: "Extract posts, stories, reels, highlights, tagged media, and full profiles.",
      path: "/download/instagram",
      icon: Camera,
      color: "text-pink-500",
      bg: "bg-pink-500/10"
    }
  ];

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Download Center</h1>
        <p className="text-muted-foreground mt-1">Select an extraction engine module below to start downloading.</p>
      </div>

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {downloadEngines.map((engine) => (
          <Link key={engine.name} to={engine.path} className="group focus:outline-none">
            <Card className="h-full border border-border/80 hover:border-primary/50 transition-all hover:shadow-md cursor-pointer flex flex-col justify-between">
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className={`p-2 rounded-lg ${engine.bg} ${engine.color}`}>
                    <engine.icon className="h-5 w-5" />
                  </div>
                  <ArrowUpRight className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
                </div>
                <CardTitle className="text-base font-semibold group-hover:text-primary transition-colors mt-3">
                  {engine.name}
                </CardTitle>
                <CardDescription className="text-xs leading-relaxed mt-1">
                  {engine.desc}
                </CardDescription>
              </CardHeader>
              <CardContent className="h-4" /> {/* spacer */}
            </Card>
          </Link>
        ))}
      </div>
    </div>
  );
};
