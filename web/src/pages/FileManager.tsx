import React, { useState } from "react";
import { 
  FolderOpen, Download, FileVideo, Music, Play, 
  Image, FileText, Trash2, LayoutGrid, List, Search, FolderSymlink
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { cn } from "../utils/cn";

export const FileManager: React.FC = () => {
  const [category, setCategory] = useState("all");
  const [layout, setLayout] = useState<"grid" | "list">("grid");
  const [search, setSearch] = useState("");
  const [selectedFile, setSelectedFile] = useState<any>(null);

  const categories = [
    { id: "all", name: "All Downloads", icon: Download },
    { id: "videos", name: "Videos Only", icon: FileVideo },
    { id: "audio", name: "Audio Files", icon: Music },
    { id: "playlists", name: "Playlists Sync", icon: FolderOpen },
    { id: "images", name: "Images / Album Art", icon: Image },
    { id: "documents", name: "Logs & Subtitles", icon: FileText },
    { id: "trash", name: "Trash Bin", icon: Trash2 }
  ];

  const files = [
    { id: "f1", name: "Quantum Physics Explained - Lecture 1.mp4", type: "videos", size: "320 MB", date: "2026-07-17", duration: "12:15" },
    { id: "f2", name: "Study Lofi Chill Beats Mix 2026.mp3", type: "audio", size: "45 MB", date: "2026-07-16", duration: "45:00" },
    { id: "f3", name: "Travel Vlog - Italy Cinematic.mp4", type: "videos", size: "128 MB", date: "2026-07-15", duration: "08:30" },
    { id: "f4", name: "Album Cover Art.png", type: "images", size: "1.2 MB", date: "2026-07-14" },
    { id: "f5", name: "Intro Transcript.txt", type: "documents", size: "12 KB", date: "2026-07-14" }
  ];

  const filteredFiles = files.filter((file) => {
    if (category !== "all" && file.type !== category) return false;
    return file.name.toLowerCase().includes(search.toLowerCase());
  });

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Media File Manager</h1>
        <p className="text-muted-foreground mt-1">Browse, search, stream, and manage your local download directory files.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-4 items-start">
        {/* Left Categories panel (1 column) */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Directories</CardTitle>
            </CardHeader>
            <CardContent className="p-2 space-y-1">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => { setCategory(cat.id); setSelectedFile(null); }}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-xs font-semibold transition-colors hover:bg-secondary/40",
                    category === cat.id ? "bg-secondary text-primary" : "text-muted-foreground"
                  )}
                >
                  <cat.icon className="h-4 w-4 shrink-0" />
                  <span>{cat.name}</span>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Center Files Explorer viewport (2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card>
            <CardHeader className="pb-3 border-b border-border/40">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                <div className="relative flex-1 w-full">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground/60" />
                  <Input
                    placeholder="Search folder files..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 h-9"
                  />
                </div>
                
                <div className="flex gap-1 bg-secondary/50 border border-border p-1 rounded-lg">
                  <Button 
                    variant={layout === "grid" ? "secondary" : "ghost"} 
                    size="icon" 
                    className="h-8 w-8"
                    onClick={() => setLayout("grid")}
                  >
                    <LayoutGrid className="h-4 w-4" />
                  </Button>
                  <Button 
                    variant={layout === "list" ? "secondary" : "ghost"} 
                    size="icon" 
                    className="h-8 w-8"
                    onClick={() => setLayout("list")}
                  >
                    <List className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0 max-h-[500px] overflow-y-auto">
              {filteredFiles.length === 0 ? (
                <div className="h-64 flex items-center justify-center text-muted-foreground text-xs">No matching files found.</div>
              ) : layout === "grid" ? (
                <div className="grid gap-4 p-4 grid-cols-2">
                  {filteredFiles.map((file) => (
                    <div
                      key={file.id}
                      onClick={() => setSelectedFile(file)}
                      className={cn(
                        "border border-border/80 hover:border-primary/50 transition-all rounded-lg p-3 cursor-pointer flex flex-col justify-between h-32 bg-secondary/15",
                        selectedFile?.id === file.id && "border-primary bg-secondary/30"
                      )}
                    >
                      <div className="flex justify-between items-start">
                        {file.type === "videos" && <FileVideo className="h-7 w-7 text-blue-500" />}
                        {file.type === "audio" && <Music className="h-7 w-7 text-emerald-500" />}
                        {file.type === "images" && <Image className="h-7 w-7 text-pink-500" />}
                        {file.type === "documents" && <FileText className="h-7 w-7 text-neutral-400" />}
                        <span className="text-[9px] font-mono text-muted-foreground/60">{file.size}</span>
                      </div>
                      <span className="text-[11px] font-semibold leading-snug line-clamp-2 mt-3 select-none">{file.name}</span>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="divide-y divide-border/40">
                  {filteredFiles.map((file) => (
                    <div
                      key={file.id}
                      onClick={() => setSelectedFile(file)}
                      className={cn(
                        "flex items-center justify-between p-3.5 hover:bg-secondary/40 cursor-pointer select-none text-xs",
                        selectedFile?.id === file.id && "bg-secondary/45"
                      )}
                    >
                      <div className="flex items-center gap-3">
                        {file.type === "videos" && <FileVideo className="h-4.5 w-4.5 text-blue-500 shrink-0" />}
                        {file.type === "audio" && <Music className="h-4.5 w-4.5 text-emerald-500 shrink-0" />}
                        {file.type === "images" && <Image className="h-4.5 w-4.5 text-pink-500 shrink-0" />}
                        {file.type === "documents" && <FileText className="h-4.5 w-4.5 text-neutral-400 shrink-0" />}
                        <span className="font-medium truncate">{file.name}</span>
                      </div>
                      <div className="flex gap-4 text-muted-foreground font-mono text-[10px]">
                        <span>{file.size}</span>
                        <span>{file.date}</span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Right Preview panel (1 column) */}
        <div className="lg:col-span-1 space-y-4">
          {selectedFile ? (
            <Card>
              <CardHeader className="pb-3 border-b border-border/40">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">File Preview</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4 text-xs">
                {/* Media preview player mock */}
                {selectedFile.type === "videos" && (
                  <div className="h-32 bg-neutral-950 rounded-lg flex items-center justify-center border border-border group cursor-pointer">
                    <Play className="h-8 w-8 text-primary group-hover:scale-110 transition-transform" />
                  </div>
                )}
                {selectedFile.type === "audio" && (
                  <div className="h-20 bg-secondary/85 rounded-lg border border-border flex flex-col justify-center px-4 space-y-1">
                    <span className="text-[9px] uppercase font-bold text-muted-foreground">Waveform Spectrum</span>
                    <div className="h-6 flex items-center gap-0.5">
                      <div className="h-4 w-1 bg-primary rounded-full" />
                      <div className="h-2 w-1 bg-primary/60 rounded-full" />
                      <div className="h-5 w-1 bg-primary rounded-full" />
                      <div className="h-3 w-1 bg-primary/60 rounded-full" />
                      <div className="h-1 w-1 bg-primary/45 rounded-full" />
                    </div>
                  </div>
                )}

                <div className="space-y-1">
                  <h4 className="text-xs font-semibold leading-tight break-all">{selectedFile.name}</h4>
                  <p className="text-[10px] text-muted-foreground">Path: D:\Downloads\FluxMedia\{selectedFile.name}</p>
                </div>

                <div className="grid grid-cols-2 gap-2 text-muted-foreground pt-2 border-t border-border/40">
                  <div>Size: <span className="text-foreground font-semibold">{selectedFile.size}</span></div>
                  <div>Date: <span className="text-foreground font-semibold">{selectedFile.date}</span></div>
                </div>

                <div className="flex flex-col gap-2 pt-2 border-t border-border/40">
                  <Button variant="outline" className="w-full justify-start gap-2 h-9 text-xs"><FolderSymlink className="h-4 w-4" /> Move File</Button>
                  <Button variant="destructive" className="w-full justify-start gap-2 h-9 text-xs"><Trash2 className="h-4 w-4" /> Move to Trash</Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="h-48 flex items-center justify-center text-muted-foreground text-xs">Select a file to open properties panel.</CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
