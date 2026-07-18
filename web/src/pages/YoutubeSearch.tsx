import React, { useState } from "react";
import { 
  Search, SlidersHorizontal, Play, Eye, Calendar, User, 
  Download, Heart, FileVideo, MessageSquare, X, RefreshCw
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";

export const YoutubeSearch: React.FC = () => {
  const [query, setQuery] = useState("");
  const [searching, setSearching] = useState(false);
  const [results, setResults] = useState<any[]>([]);
  const [selectedVideo, setSelectedVideo] = useState<any>(null);

  const handleSearch = () => {
    if (!query) return;
    setSearching(true);
    setResults([]);
    setTimeout(() => {
      setSearching(false);
      setResults([
        {
          id: "vid-1",
          title: "Building a Premium React Dashboard in 2026 (Tailwind v4)",
          channel: "Frontend Masterclass",
          duration: "18:42",
          views: "24,812",
          date: "3 days ago",
          description: "Step-by-step tutorial on building desktop-grade web applications using React, TypeScript, and Tailwind CSS v4 compiler.",
          likes: "1,248",
          comments: "148"
        },
        {
          id: "vid-2",
          title: "Introduction to Advanced Quantum Cryptography",
          channel: "Science Frontiers",
          duration: "45:10",
          views: "128,591",
          date: "1 month ago",
          description: "An in-depth look at quantum key distribution protocols, BB84, and the future of post-quantum network security.",
          likes: "9,812",
          comments: "591"
        },
        {
          id: "vid-3",
          title: "Lo-Fi Cafe Ambient Music for Coding (3 Hour Mix)",
          channel: "Study Oasis",
          duration: "3:00:00",
          views: "2,482,914",
          date: "6 months ago",
          description: "Relaxing atmospheric lo-fi beats curated specifically for concentration, studying, coding, and workflow productivity.",
          likes: "45,812",
          comments: "1,248"
        }
      ]);
    }, 1200);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">YouTube Search Engine</h1>
          <p className="text-muted-foreground mt-1">Search and filter media streams, preview metadata, and download instantly.</p>
        </div>
      </div>

      {/* Search Input Card */}
      <Card>
        <CardContent className="pt-6 space-y-4">
          <div className="flex gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-3 h-4.5 w-4.5 text-muted-foreground/60" />
              <Input
                placeholder="Search YouTube videos, channels, or playlists..."
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleSearch()}
                className="pl-10"
              />
            </div>
            <Button variant="primary" onClick={handleSearch} disabled={!query || searching}>
              {searching ? "Searching..." : "Search"}
            </Button>
          </div>

          {/* Filters */}
          <div className="flex flex-wrap items-center gap-3 pt-2 text-xs">
            <span className="flex items-center gap-1 text-muted-foreground"><SlidersHorizontal className="h-3.5 w-3.5" /> Filters:</span>
            <select className="h-8 rounded-md border border-border bg-background px-2.5 py-1 text-xs">
              <option>Duration: Any</option>
              <option>Short (&lt; 4m)</option>
              <option>Long (&gt; 20m)</option>
            </select>
            <select className="h-8 rounded-md border border-border bg-background px-2.5 py-1 text-xs">
              <option>Quality: HD / 4K</option>
              <option>HD Only</option>
              <option>4K Ultra HD</option>
            </select>
            <select className="h-8 rounded-md border border-border bg-background px-2.5 py-1 text-xs">
              <option>Sort: Relevance</option>
              <option>Upload Date</option>
              <option>View Count</option>
              <option>Rating</option>
            </select>
          </div>
        </CardContent>
      </Card>

      {/* Searching state */}
      {searching && (
        <div className="h-64 flex flex-col items-center justify-center">
          <RefreshCw className="h-8 w-8 text-primary animate-spin mb-3" />
          <span className="text-sm text-muted-foreground">Searching YouTube databases...</span>
        </div>
      )}

      {/* Results grid */}
      {!searching && results.length > 0 && (
        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {results.map((video) => (
            <Card key={video.id} className="flex flex-col justify-between overflow-hidden">
              <div className="h-40 bg-secondary/80 flex items-center justify-center border-b border-border overflow-hidden relative">
                <FileVideo className="h-10 w-10 text-muted-foreground" />
                <Badge variant="outline" className="absolute bottom-2 right-2 bg-background/90 text-foreground font-mono text-[10px]">
                  {video.duration}
                </Badge>
              </div>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-semibold leading-snug line-clamp-2">{video.title}</CardTitle>
                <CardDescription className="text-xs flex items-center gap-1.5 mt-1.5">
                  <User className="h-3.5 w-3.5 shrink-0" /> {video.channel}
                </CardDescription>
              </CardHeader>
              <CardContent className="pb-3 text-xs text-muted-foreground space-y-1.5">
                <div className="flex gap-4">
                  <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5 shrink-0" /> {video.views}</span>
                  <span className="flex items-center gap-1"><Calendar className="h-3.5 w-3.5 shrink-0" /> {video.date}</span>
                </div>
                <p className="line-clamp-2 text-[11px] leading-relaxed pt-1.5 border-t border-border/40">
                  {video.description}
                </p>
              </CardContent>
              <CardFooter className="flex gap-2 border-t border-border/40 pt-3">
                <Button variant="outline" size="sm" className="flex-1" onClick={() => setSelectedVideo(video)}>Preview</Button>
                <Button variant="primary" size="sm" className="flex-1 gap-1"><Download className="h-3.5 w-3.5" /> Download</Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}

      {/* Video Preview Modal Dialog */}
      {selectedVideo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" onClick={() => setSelectedVideo(null)} />
          <div className="z-50 w-full max-w-2xl bg-card border border-border rounded-xl overflow-hidden shadow-2xl animate-in fade-in zoom-in-95 duration-100">
            <div className="flex justify-between items-center px-4 py-3 border-b border-border bg-secondary/20">
              <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Video Stream Preview</span>
              <button onClick={() => setSelectedVideo(null)} className="p-1 rounded-md hover:bg-secondary text-muted-foreground hover:text-foreground">
                <X className="h-4 w-4" />
              </button>
            </div>
            
            <div className="p-6 space-y-6">
              {/* Fake player */}
              <div className="h-64 rounded-lg bg-neutral-950 flex flex-col items-center justify-center border border-border relative group">
                <Play className="h-12 w-12 text-primary group-hover:scale-110 transition-transform cursor-pointer" />
                <span className="text-xs text-neutral-400 mt-2">Click to preview audio/video stream</span>
              </div>

              <div className="space-y-3">
                <h3 className="text-base font-semibold leading-snug">{selectedVideo.title}</h3>
                <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                  <span className="flex items-center gap-1"><User className="h-3.5 w-3.5" /> {selectedVideo.channel}</span>
                  <span className="flex items-center gap-1"><Eye className="h-3.5 w-3.5" /> {selectedVideo.views} views</span>
                  <span className="flex items-center gap-1"><Heart className="h-3.5 w-3.5" /> {selectedVideo.likes} likes</span>
                  <span className="flex items-center gap-1"><MessageSquare className="h-3.5 w-3.5" /> {selectedVideo.comments} comments</span>
                </div>
                <p className="text-xs text-muted-foreground leading-relaxed bg-secondary/20 p-3 rounded-lg border border-border/40">
                  {selectedVideo.description}
                </p>
              </div>

              <div className="flex gap-2 justify-end">
                <Button variant="outline" onClick={() => setSelectedVideo(null)}>Close Preview</Button>
                <Button variant="primary" className="gap-1"><Download className="h-4 w-4" /> Start Download</Button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
