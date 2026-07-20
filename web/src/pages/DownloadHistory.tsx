import React, { useState, useEffect, useCallback } from "react";
import { 
  History, Search, LayoutGrid, List, FileVideo, Music, RefreshCw, 
  SlidersHorizontal, Database, X, AlertTriangle, RotateCcw, Trash2
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";

interface HistoryEntry {
  timestamp: string;
  url: string;
  title: string;
  status: string;
  type: string;
  file_path: string;
}

export const DownloadHistory: React.FC = () => {
  const [layout, setLayout] = useState<"grid" | "table">("grid");
  const [search, setSearch] = useState("");
  const [selectedItem, setSelectedItem] = useState<HistoryEntry | null>(null);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [clearing, setClearing] = useState(false);

  const fetchHistory = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/history?limit=100");
      if (!res.ok) throw new Error(`Server error: ${res.status}`);
      const data = await res.json();
      setHistory(data.history ?? []);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  const handleClearAll = async () => {
    if (!window.confirm("Clear all download history? This cannot be undone.")) return;
    try {
      setClearing(true);
      const res = await fetch("/api/history", { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to clear history");
      setHistory([]);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setClearing(false);
    }
  };

  const handleDeleteItem = async (index: number) => {
    try {
      const res = await fetch(`/api/history/${index}`, { method: "DELETE" });
      if (!res.ok) throw new Error("Failed to delete entry");
      setHistory((prev) => prev.filter((_, i) => i !== index));
      if (selectedItem === history[index]) setSelectedItem(null);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const filteredItems = history.filter((item) => {
    const query = search.toLowerCase();
    if (!query) return true;
    return (
      item.title.toLowerCase().includes(query) ||
      item.url.toLowerCase().includes(query) ||
      item.type.toLowerCase().includes(query) ||
      item.status.toLowerCase().includes(query)
    );
  });

  const statusBadge = (status: string): "default" | "warning" | "success" | "danger" => {
    switch(status.toLowerCase()) {
      case "completed": case "success": return "success";
      case "failed": case "error": return "danger";
      case "paused": return "warning";
      default: return "default";
    }
  };

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Download History</h1>
          <p className="text-muted-foreground mt-1">Browse all previously downloaded media from your local history log.</p>
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={fetchHistory} disabled={loading}>
            <RotateCcw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
          <Button variant="destructive" size="sm" onClick={handleClearAll} disabled={clearing || history.length === 0}>
            <Trash2 className="h-4 w-4 mr-1.5" /> Clear All
          </Button>
          <div className="flex gap-1 bg-secondary/50 border border-border p-1 rounded-lg">
            <Button variant={layout === "grid" ? "secondary" : "ghost"} size="icon" className="h-8 w-8" onClick={() => setLayout("grid")}>
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button variant={layout === "table" ? "secondary" : "ghost"} size="icon" className="h-8 w-8" onClick={() => setLayout("table")}>
              <List className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5 shrink-0" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      {/* Search panel */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4.5 w-4.5 text-muted-foreground/60" />
              <Input
                placeholder="Search by title, URL, type, or status..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="pl-10"
              />
            </div>
            {search && <Button variant="ghost" onClick={() => setSearch("")}>Reset</Button>}
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1"><SlidersHorizontal className="h-3.5 w-3.5" /> Quick:</span>
            {["video", "audio", "completed", "failed"].map((q) => (
              <Badge key={q} variant="outline" className="cursor-pointer hover:bg-secondary capitalize" onClick={() => setSearch(q)}>{q}</Badge>
            ))}
          </div>
        </CardContent>
      </Card>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
        </div>
      ) : filteredItems.length === 0 ? (
        <Card>
          <CardContent className="h-48 flex flex-col items-center justify-center text-muted-foreground gap-3">
            <History className="h-10 w-10 opacity-20" />
            <p className="text-sm">{search ? "No results match your search." : "No download history yet. Start a download to see it here."}</p>
          </CardContent>
        </Card>
      ) : layout === "grid" ? (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {filteredItems.map((item, idx) => (
            <Card key={idx} className="flex flex-col justify-between overflow-hidden">
              <div className="h-36 bg-secondary/80 flex items-center justify-center border-b border-border relative">
                {item.type === "audio" ? <Music className="h-10 w-10 text-muted-foreground" /> : <FileVideo className="h-10 w-10 text-muted-foreground" />}
                <Badge variant={statusBadge(item.status)} className="absolute top-2 right-2 text-[10px] capitalize">{item.status}</Badge>
              </div>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold leading-snug line-clamp-2">{item.title || "Unknown Title"}</CardTitle>
                <CardDescription className="text-xs mt-1 font-mono truncate">{item.url}</CardDescription>
              </CardHeader>
              <CardContent className="pb-3 text-xs text-muted-foreground flex gap-3">
                <span className="flex items-center gap-1"><Database className="h-3.5 w-3.5 shrink-0" /> {item.type}</span>
                <span className="flex items-center gap-1"><History className="h-3.5 w-3.5 shrink-0" /> {item.timestamp}</span>
              </CardContent>
              <CardFooter className="flex gap-2 border-t border-border/40 pt-3">
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setSelectedItem(item)}>Details</Button>
                <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive hover:text-destructive" onClick={() => handleDeleteItem(history.indexOf(item))}>
                  <Trash2 className="h-4 w-4" />
                </Button>
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
                    <th className="p-4">Type</th>
                    <th className="p-4">Status</th>
                    <th className="p-4">Timestamp</th>
                    <th className="p-4 text-right">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {filteredItems.map((item, idx) => (
                    <tr key={idx} className="hover:bg-secondary/20">
                      <td className="p-4 font-medium leading-tight max-w-xs truncate">{item.title || "Unknown"}</td>
                      <td className="p-4 text-muted-foreground capitalize">{item.type}</td>
                      <td className="p-4">
                        <Badge variant={statusBadge(item.status)} className="text-[10px] capitalize">{item.status}</Badge>
                      </td>
                      <td className="p-4 text-muted-foreground font-mono text-xs">{item.timestamp}</td>
                      <td className="p-4 text-right">
                        <div className="flex gap-1 justify-end">
                          <Button variant="ghost" size="sm" onClick={() => setSelectedItem(item)}>View</Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive" onClick={() => handleDeleteItem(history.indexOf(item))}>
                            <Trash2 className="h-3.5 w-3.5" />
                          </Button>
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

      {/* Item Details Modal */}
      {selectedItem && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setSelectedItem(null)} />
          <div className="z-50 w-full max-w-2xl bg-card border border-border rounded-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-100">
            <div className="flex justify-between items-center px-4 py-3 border-b border-border bg-secondary/20">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Download Entry Details</span>
              <button onClick={() => setSelectedItem(null)} className="p-1 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            <div className="p-6 space-y-4">
              <div className="flex flex-col sm:flex-row gap-6">
                <div className="h-32 w-48 bg-secondary/80 border border-border rounded-lg flex items-center justify-center shrink-0">
                  {selectedItem.type === "audio" ? <Music className="h-8 w-8 text-muted-foreground" /> : <FileVideo className="h-8 w-8 text-muted-foreground" />}
                </div>
                <div className="space-y-2 flex-1 text-sm">
                  <h3 className="text-base font-semibold leading-snug">{selectedItem.title || "Unknown Title"}</h3>
                  <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-xs text-muted-foreground">
                    <span>Type: <span className="text-foreground capitalize">{selectedItem.type}</span></span>
                    <span>Status: <span className="text-foreground capitalize">{selectedItem.status}</span></span>
                    <span>Downloaded: <span className="text-foreground">{selectedItem.timestamp}</span></span>
                    <span className="col-span-2 break-all">URL: <span className="text-primary font-mono">{selectedItem.url}</span></span>
                    {selectedItem.file_path && selectedItem.file_path !== "N/A" && (
                      <span className="col-span-2 break-all">File: <span className="text-foreground font-mono">{selectedItem.file_path}</span></span>
                    )}
                  </div>
                </div>
              </div>
              <div className="flex gap-2 justify-end pt-4 border-t border-border/40">
                <Button variant="outline" className="gap-1" onClick={() => setSelectedItem(null)}>
                  <X className="h-4 w-4" /> Close
                </Button>
                <Button variant="outline" className="gap-1">
                  <RefreshCw className="h-4 w-4" /> Re-Download
                </Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DownloadHistory;
