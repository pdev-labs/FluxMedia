import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { ThemeProvider } from "./context/ThemeContext";
import { GlobalLayout } from "./layouts/GlobalLayout";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "./components/ui/Card";

// Import all subpages
import { Dashboard } from "./pages/Dashboard";
import { DownloadCenter } from "./pages/DownloadCenter";
import { VideoDownloader } from "./pages/VideoDownloader";
import { YoutubeSearch } from "./pages/YoutubeSearch";
import { AudioDownloader } from "./pages/AudioDownloader";
import { PlaylistDownloader } from "./pages/PlaylistDownloader";
import { ChannelDownloader } from "./pages/ChannelDownloader";
import { SubtitleDownloader } from "./pages/SubtitleDownloader";
import { TrimDownloader } from "./pages/TrimDownloader";
import { InstagramDownloader } from "./pages/InstagramDownloader";

// General placeholder component for modules implemented in future phases
const PagePlaceholder: React.FC<{ title: string; desc: string }> = ({ title, desc }) => (
  <div className="flex flex-col gap-6 max-w-4xl animate-in fade-in slide-in-from-bottom-4 duration-300">
    <div>
      <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
      <p className="text-muted-foreground mt-1">{desc}</p>
    </div>
    
    <Card>
      <CardHeader>
        <CardTitle>Module Connection</CardTitle>
        <CardDescription>FluxMedia CLI module is connected. Graphical interface configurations will appear here.</CardDescription>
      </CardHeader>
      <CardContent className="h-64 flex flex-col items-center justify-center border border-dashed border-border rounded-lg m-6 mt-0">
        <Sparkles className="h-8 w-8 text-primary animate-pulse mb-3" />
        <span className="text-sm font-medium text-muted-foreground">Interface Pending Integration</span>
        <span className="text-xs text-muted-foreground/60 mt-1">Use Cmd Palette (Ctrl+K) to navigate modules</span>
      </CardContent>
    </Card>
  </div>
);

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <GlobalLayout>
          <Routes>
            {/* Core Dashboard */}
            <Route path="/" element={<Dashboard />} />
            
            {/* Download Hub & Extractor Engines */}
            <Route path="/downloads" element={<DownloadCenter />} />
            <Route path="/download/video" element={<VideoDownloader />} />
            <Route path="/download/search" element={<YoutubeSearch />} />
            <Route path="/download/audio" element={<AudioDownloader />} />
            <Route path="/download/playlist" element={<PlaylistDownloader />} />
            <Route path="/download/channel" element={<ChannelDownloader />} />
            <Route path="/download/subtitles" element={<SubtitleDownloader />} />
            <Route path="/download/trimmer" element={<TrimDownloader />} />
            <Route path="/download/instagram" element={<InstagramDownloader />} />

            {/* Other System Areas (Placeholders) */}
            <Route path="/history" element={<PagePlaceholder title="Download History" desc="Logs of all processed audio, video, and playlist downloads." />} />
            <Route path="/queue" element={<PagePlaceholder title="Active Queue" desc="Batch media downloader job management dashboard." />} />
            <Route path="/files" element={<PagePlaceholder title="Local File Manager" desc="Browse and open your download directory files directly." />} />
            <Route path="/converter" element={<PagePlaceholder title="FFmpeg Converter" desc="Transcode or extract audio from videos manually." />} />
            <Route path="/sharing" element={<PagePlaceholder title="LAN Sharing Gateway" desc="Broadcast files to your local network via QR codes." />} />
            <Route path="/settings" element={<PagePlaceholder title="System Settings" desc="Configure themes, paths, cookie syncer, and API keys." />} />
            <Route path="/updates" element={<PagePlaceholder title="Updates Manager" desc="Keep yt-dlp and FluxMedia up to date." />} />
            <Route path="/diagnostics" element={<PagePlaceholder title="Diagnostics" desc="Analyze cpu load, memory stats, and environment variables." />} />
            <Route path="/logs" element={<PagePlaceholder title="System Logs" desc="Real-time terminal traceback and application records." />} />
            <Route path="/feedback" element={<PagePlaceholder title="Send Feedback" desc="Report bugs or request new features directly to developers." />} />
            <Route path="/help" element={<PagePlaceholder title="Help Center" desc="Check FAQs and learn CLI console shortcuts." />} />
            <Route path="/about" element={<PagePlaceholder title="About Project" desc="Learn about the authors and technology credits." />} />
            
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </GlobalLayout>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
