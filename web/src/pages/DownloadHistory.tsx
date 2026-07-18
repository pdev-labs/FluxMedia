import React, { useState } from "react";
import { 
  History, Search, LayoutGrid, List, FileVideo, FolderOpen, RefreshCw, 
  QrCode, SlidersHorizontal, Database, X
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";

export const DownloadHistory: React.FC = () => {
  const [layout, setLayout] = useState<"grid" | "table">("grid");
  const [search, setSearch] = useState("");
  const [selectedItem, setSelectedItem] = useState<any>(null);
  const [showQr, setShowQr] = useState<string | null>(null);

  const historyItems = [
    { id: "h1", title: "Introduction to Quantum Physics.mp4", size: "320 MB", date: "Yesterday", uploader: "Physics Hub", duration: "12:15", platform: "youtube", resolution: "1080p", tags: ["education", "science"] },
    { id: "h2", title: "Lo-Fi Beats Study Session Mix.mp3", size: "45 MB", date: "2 days ago", uploader: "Lofi Collective", duration: "45:00", platform: "soundcloud", resolution: "320kbps", tags: ["music", "chill"] },
    { id: "h3", title: "Travel Vlog - Italy Cinematic.mp4", size: "128 MB", date: "Last week", uploader: "Wanderlust", duration: "08:30", platform: "instagram", resolution: "1080p", tags: ["lifestyle", "travel"] }
  ];

  // Natural language query matches
  const filteredItems = historyItems.filter((item) => {
    const query = search.toLowerCase();
    if (!query) return true;
    
    // Natural Language Search patterns
    if (query === "videos downloaded yesterday") {
      return item.date === "Yesterday" && item.title.endsWith(".mp4");
    }
    if (query.includes("mp3") || query.includes("audio")) {
      return item.title.endsWith(".mp3");
    }
    if (query.includes("youtube")) {
      return item.platform === "youtube";
    }
    if (query.includes("instagram")) {
      return item.platform === "instagram";
    }

    return (
      item.title.toLowerCase().includes(query) ||
      item.uploader.toLowerCase().includes(query) ||
      item.tags.some((t) => t.toLowerCase().includes(query))
    );
  });

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Download History</h1>
          <p className="text-muted-foreground mt-1">Browse, stream, or re-extract previously completed media files.</p>
        </div>
        
        {/* Layout controls */}
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
            variant={layout === "table" ? "secondary" : "ghost"} 
            size="icon" 
            className="h-8 w-8"
            onClick={() => setLayout("table")}
          >
            <List className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Advanced search panel */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4.5 w-4.5 text-muted-foreground/60" />
              <Input
                placeholder="Try: 'mp3 files', 'youtube downloads', 'videos downloaded yesterday'..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            {search && (
              <Button variant="ghost" onClick={() => setSearch("")}>Reset</Button>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><SlidersHorizontal className="h-3.5 w-3.5" /> Filters:</span>
            <Badge variant="outline" className="cursor-pointer hover:bg-secondary">Platform</Badge>
            <Badge variant="outline" className="cursor-pointer hover:bg-secondary">Date Range</Badge>
            <Badge variant="outline" className="cursor-pointer hover:bg-secondary">Tags</Badge>
          </div>
        </CardContent>
      </Card>

      {/* Results viewport */}
      {layout === "grid" ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredItems.map((item) => (
            <Card key={item.id} className="flex flex-col justify-between overflow-hidden">
              <div className="h-40 bg-secondary/80 flex items-center justify-center border-b border-border relative">
                <FileVideo className="h-10 w-10 text-muted-foreground" />
                <Badge variant="outline" className="absolute top-2 right-2 bg-background/90 text-foreground font-mono text-[10px]">
                  {item.duration}
                </Badge>
              </div>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold leading-snug line-clamp-2">{item.title}</CardTitle>
                <CardDescription className="text-xs mt-1">{item.uploader} • {item.date}</CardDescription>
              </CardHeader>
              <CardContent className="pb-3 text-xs text-muted-foreground flex gap-3">
                <span className="flex items-center gap-1"><Database className="h-3.5 w-3.5 shrink-0" /> {item.size}</span>
                <span className="flex items-center gap-1"><History className="h-3.5 w-3.5 shrink-0" /> {item.resolution}</span>
              </CardContent>
              <CardFooter className="flex gap-2 border-t border-border/40 pt-3">
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setSelectedItem(item)}>Details</Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground" onClick={() => setShowQr(item.id)}><QrCode className="h-4 w-4" /></Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      ) : (
        <Card>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full text-sm text-left">
                <thead className="bg-secondary/40 border-b border-border/60 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  <tr>
                    <th className="p-4">Title</th>
                    <th className="p-4">Size</th>
                    <th className="p-4">Duration</th>
                    <th className="p-4">Source</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {filteredItems.map((item) => (
                    <tr key={item.id} className="hover:bg-secondary/20">
                      <td className="p-4 font-medium leading-tight">{item.title}</td>
                      <td className="p-4 text-muted-foreground">{item.size}</td>
                      <td className="p-4 text-muted-foreground font-mono">{item.duration}</td>
                      <td className="p-4 capitalize">{item.platform}</td>
                      <td className="p-4 text-right">
                        <div className="flex gap-1 justify-end">
                          <Button variant="ghost" size="sm" onClick={() => setSelectedItem(item)}>View</Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-muted-foreground hover:text-foreground" onClick={() => setShowQr(item.id)}><QrCode className="h-4 w-4" /></Button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Item Details Overlay Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setSelectedItem(null)} />
          <div className="z-50 w-full max-w-2xl bg-card border border-border rounded-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-100">
            <div className="flex justify-between items-center px-4 py-3 border-b border-border bg-secondary/20">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Media Metadata Detail</span>
              <button onClick={() => setSelectedItem(null)} className="p-1 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              <div className="flex flex-col sm:flex-row gap-6">
                <div className="h-32 w-48 bg-secondary/80 border border-border rounded-lg flex items-center justify-center shrink-0">
                  <FileVideo className="h-8 w-8 text-muted-foreground" />
                </div>
                <div className="space-y-3 flex-1">
                  <h3 className="text-base font-semibold leading-snug">{selectedItem.title}</h3>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-muted-foreground">
                    <span>Uploader: <span className="text-foreground">{selectedItem.uploader}</span></span>
                    <span>Duration: <span className="text-foreground">{selectedItem.duration}</span></span>
                    <span>File size: <span className="text-foreground">{selectedItem.size}</span></span>
                    <span>Platform: <span className="text-foreground capitalize">{selectedItem.platform}</span></span>
                  </div>
                  <div className="flex flex-wrap gap-1.5 pt-1">
                    {selectedItem.tags.map((tag: string) => (
                      <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                    ))}
                  </div>
                </div>
              </div>

              <div className="flex gap-2 justify-end pt-4 border-t border-border/40">
                <Button variant="outline" className="gap-1"><FolderOpen className="h-4 w-4" /> Reveal Folder</Button>
                <Button variant="outline" className="gap-1"><RefreshCw className="h-4 w-4" /> Re-Download</Button>
                <Button variant="primary">Play Media</Button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Share QR Modal */}
      {showQr && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setShowQr(null)} />
          <div className="z-50 w-full max-w-sm bg-card border border-border rounded-xl overflow-hidden shadow-2xl p-6 text-center animate-in fade-in zoom-in-95 duration-100">
            <div className="flex justify-end">
              <button onClick={() => setShowQr(null)} className="p-1 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <h3 className="text-sm font-semibold mb-2">LAN Sharing Gateway QR Code</h3>
            <p className="text-xs text-muted-foreground mb-6">Scan the code with any device on your local network to stream or download this media file.</p>
            
            {/* Fake QR Graphic */}
            <div className="h-48 w-48 mx-auto bg-neutral-900 border border-border rounded-lg flex items-center justify-center mb-6">
              <QrCode className="h-32 w-32 text-primary" />
            </div>

            <Button variant="outline" className="w-full" onClick={() => setShowQr(null)}>Close</Button>
          </div>
        </div>
      )}
    </div>
  );
};
