import React, { useState, useEffect, useCallback } from "react";
import { 
  FolderOpen, FileVideo, Music, Play, 
  Image, FileText, Trash2, LayoutGrid, List, Search, 
  AlertTriangle, RotateCcw, FolderSymlink, HardDrive
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { cn } from "../utils/cn";

interface MediaFile {
  id: string;
  name: string;
  path: string;
  relative_path: string;
  type: string;
  ext: string;
  size: string;
  size_bytes: number;
  date: string;
}

const categoryIcons: Record<string, React.ElementType> = {
  all: FolderOpen,
  videos: FileVideo,
  audio: Music,
  images: Image,
  documents: FileText,
  trash: Trash2,
};

const fileIcon = (type: string, className = "h-7 w-7") => {
  const colors: Record<string, string> = {
    videos: "text-blue-500",
    audio: "text-emerald-500",
    images: "text-pink-500",
    documents: "text-neutral-400",
    other: "text-muted-foreground",
  };
  const icons: Record<string, React.ElementType> = {
    videos: FileVideo,
    audio: Music,
    images: Image,
    documents: FileText,
    other: FileText,
  };
  const Icon = icons[type] ?? FileText;
  return <Icon className={`${className} ${colors[type] ?? "text-muted-foreground"}`} />;
};

export const FileManager: React.FC = () => {
  const [category, setCategory] = useState("all");
  const [layout, setLayout] = useState<"grid" | "list">("grid");
  const [search, setSearch] = useState("");
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);
  const [files, setFiles] = useState<MediaFile[]>([]);
  const [downloadDir, setDownloadDir] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [deleting, setDeleting] = useState<string | null>(null);

  const categories = [
    { id: "all", name: "All Files" },
    { id: "videos", name: "Videos" },
    { id: "audio", name: "Audio" },
    { id: "images", name: "Images" },
    { id: "documents", name: "Logs & Subs" },
  ];

  const fetchFiles = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch(`/api/files?category=${category}`);
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setFiles(data.files ?? []);
      setDownloadDir(data.download_dir ?? "");
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [category]);

  useEffect(() => {
    fetchFiles();
    setSelectedFile(null);
  }, [fetchFiles]);

  const handleDelete = async (file: MediaFile) => {
    if (!window.confirm(`Delete "${file.name}"? This cannot be undone.`)) return;
    try {
      setDeleting(file.id);
      const res = await fetch(`/api/files?path=${encodeURIComponent(file.path)}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete file");
      setFiles((prev) => prev.filter((f) => f.id !== file.id));
      if (selectedFile?.id === file.id) setSelectedFile(null);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setDeleting(null);
    }
  };

  const filteredFiles = files.filter((file) =>
    file.name.toLowerCase().includes(search.toLowerCase())
  );

  const totalSize = files.reduce((acc, f) => acc + f.size_bytes, 0);
  const humanTotal = totalSize < 1024 ** 3
    ? `${(totalSize / (1024 ** 2)).toFixed(1)} MB`
    : `${(totalSize / (1024 ** 3)).toFixed(2)} GB`;

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Media File Manager</h1>
          <p className="text-muted-foreground mt-1">Browse, search, and manage your local download directory.</p>
        </div>
        <Button variant="outline" size="sm" onClick={fetchFiles} disabled={loading}>
          <RotateCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </Button>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Storage summary bar */}
      {downloadDir && (
        <Card>
          <CardContent className="pt-5 pb-4">
            <div className="flex items-center gap-3 text-xs text-muted-foreground">
              <HardDrive className="h-4 w-4 shrink-0 text-primary" />
              <span className="font-mono truncate">{downloadDir}</span>
              <span className="ml-auto shrink-0 font-semibold text-foreground">{files.length} files · {humanTotal}</span>
            </div>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-4 items-start">
        {/* Left Category panel */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">Categories</CardTitle>
            </CardHeader>
            <CardContent className="p-2 space-y-1">
              {categories.map((cat) => {
                const Icon = categoryIcons[cat.id] ?? FolderOpen;
                const count = cat.id === "all" ? files.length : files.filter(f => f.type === cat.id).length;
                return (
                  <button
                    key={cat.id}
                    onClick={() => { setCategory(cat.id); setSelectedFile(null); }}
                    className={cn(
                      "flex w-full items-center justify-between gap-3 rounded-lg px-3 py-2 text-left text-xs font-semibold transition-colors hover:bg-secondary/40",
                      category === cat.id ? "bg-secondary text-primary" : "text-muted-foreground"
                    )}
                  >
                    <span className="flex items-center gap-2">
                      <Icon className="h-4 w-4 shrink-0" />
                      {cat.name}
                    </span>
                    <span className="text-[10px] font-mono opacity-60">{count}</span>
                  </button>
                );
              })}
            </CardContent>
          </Card>
        </div>

        {/* Files Explorer */}
        <div className="lg:col-span-2 space-y-4">
          <Card>
            <CardHeader className="pb-3 border-b border-border/40">
              <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
                <div className="relative flex-1 w-full">
                  <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground/60" />
                  <Input
                    placeholder="Search files..."
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    className="pl-9 h-9"
                  />
                </div>
                <div className="flex gap-1 bg-secondary/50 border border-border p-1 rounded-lg">
                  <Button variant={layout === "grid" ? "secondary" : "ghost"} size="icon" className="h-8 w-8" onClick={() => setLayout("grid")}>
                    <LayoutGrid className="h-4 w-4" />
                  </Button>
                  <Button variant={layout === "list" ? "secondary" : "ghost"} size="icon" className="h-8 w-8" onClick={() => setLayout("list")}>
                    <List className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-0 max-h-[520px] overflow-y-auto">
              {loading ? (
                <div className="h-48 flex items-center justify-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                </div>
              ) : filteredFiles.length === 0 ? (
                <div className="h-48 flex flex-col items-center justify-center text-muted-foreground gap-3">
                  <FolderOpen className="h-10 w-10 opacity-20" />
                  <p className="text-xs">
                    {files.length === 0
                      ? "No files found in your download directory."
                      : "No files match your search."}
                  </p>
                </div>
              ) : layout === "grid" ? (
                <div className="grid gap-3 p-4 grid-cols-2">
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
                        {fileIcon(file.type, "h-7 w-7")}
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
                        {fileIcon(file.type, "h-4.5 w-4.5")}
                        <span className="font-medium truncate max-w-[180px]">{file.name}</span>
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

        {/* File Preview / Properties panel */}
        <div className="lg:col-span-1 space-y-4">
          {selectedFile ? (
            <Card>
              <CardHeader className="pb-3 border-b border-border/40">
                <CardTitle className="text-sm font-semibold uppercase tracking-wider text-muted-foreground">File Properties</CardTitle>
              </CardHeader>
              <CardContent className="pt-4 space-y-4 text-xs">
                {selectedFile.type === "videos" && (
                  <div className="h-28 bg-neutral-950 rounded-lg flex items-center justify-center border border-border group cursor-pointer">
                    <Play className="h-8 w-8 text-primary group-hover:scale-110 transition-transform" />
                  </div>
                )}
                {selectedFile.type === "audio" && (
                  <div className="h-20 bg-secondary/85 rounded-lg border border-border flex flex-col justify-center px-4 space-y-1">
                    <span className="text-[9px] uppercase font-bold text-muted-foreground">Audio Track</span>
                    <div className="h-6 flex items-end gap-0.5">
                      {[4, 2, 5, 3, 1, 4, 2, 3, 5, 2].map((h, i) => (
                        <div key={i} className="w-1 bg-primary rounded-full transition-all" style={{ height: `${h * 4}px`, opacity: 0.7 + (i % 3) * 0.1 }} />
                      ))}
                    </div>
                  </div>
                )}

                <div className="space-y-1">
                  <h4 className="text-xs font-semibold leading-tight break-all">{selectedFile.name}</h4>
                  <p className="text-[10px] text-muted-foreground font-mono break-all">{selectedFile.path}</p>
                </div>

                <div className="grid grid-cols-2 gap-2 text-muted-foreground pt-2 border-t border-border/40">
                  <div>Size: <span className="text-foreground font-semibold">{selectedFile.size}</span></div>
                  <div>Date: <span className="text-foreground font-semibold">{selectedFile.date}</span></div>
                  <div>Type: <span className="text-foreground font-semibold capitalize">{selectedFile.type}</span></div>
                  <div>Ext: <span className="text-foreground font-semibold font-mono">{selectedFile.ext}</span></div>
                </div>

                <div className="flex flex-col gap-2 pt-2 border-t border-border/40">
                  <Button variant="outline" className="w-full justify-start gap-2 h-9 text-xs">
                    <FolderSymlink className="h-4 w-4" /> Open Location
                  </Button>
                  <Button
                    variant="destructive"
                    className="w-full justify-start gap-2 h-9 text-xs"
                    onClick={() => handleDelete(selectedFile)}
                    disabled={deleting === selectedFile.id}
                  >
                    <Trash2 className="h-4 w-4" />
                    {deleting === selectedFile.id ? "Deleting..." : "Delete File"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="h-48 flex items-center justify-center text-muted-foreground text-xs">
                Select a file to view its properties.
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default FileManager;
