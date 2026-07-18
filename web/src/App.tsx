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

// Media management & converter imports
import { DownloadQueue } from "./pages/DownloadQueue";
import { DownloadHistory } from "./pages/DownloadHistory";
import { FileManager } from "./pages/FileManager";
import { MediaConverter } from "./pages/MediaConverter";
import { SystemStats } from "./pages/SystemStats";

// Settings, updates, sharing, and diagnostics imports
import { SettingsPage } from "./pages/Settings";
import { UpdatesManager } from "./pages/UpdatesManager";
import { SharingGateway } from "./pages/SharingGateway";
import { SystemDiagnostics } from "./pages/SystemDiagnostics";

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

            {/* Download Queue & Manager */}
            <Route path="/queue" element={<DownloadQueue />} />

            {/* History logs & sub-routes */}
            <Route path="/history" element={<DownloadHistory />} />
            <Route path="/history/downloads" element={<DownloadHistory />} />
            <Route path="/history/search" element={<DownloadHistory />} />
            <Route path="/history/errors" element={<DownloadHistory />} />

            {/* File manager & categories */}
            <Route path="/files" element={<FileManager />} />
            <Route path="/files/videos" element={<FileManager />} />
            <Route path="/files/audio" element={<FileManager />} />
            <Route path="/files/playlists" element={<FileManager />} />
            <Route path="/files/images" element={<FileManager />} />
            <Route path="/files/documents" element={<FileManager />} />
            <Route path="/files/trash" element={<FileManager />} />

            {/* Converter Options */}
            <Route path="/converter" element={<MediaConverter />} />
            <Route path="/converter/video" element={<MediaConverter />} />
            <Route path="/converter/audio" element={<MediaConverter />} />
            <Route path="/converter/batch" element={<MediaConverter />} />

            {/* Statistics */}
            <Route path="/stats" element={<SystemStats />} />

            {/* LAN Sharing Gateway */}
            <Route path="/sharing" element={<SharingGateway />} />
            <Route path="/share" element={<SharingGateway />} />
            <Route path="/share/send" element={<SharingGateway />} />
            <Route path="/share/receive" element={<SharingGateway />} />
            <Route path="/share/history" element={<SharingGateway />} />
            <Route path="/share/devices" element={<SharingGateway />} />

            {/* System Settings */}
            <Route path="/settings" element={<SettingsPage />} />
            <Route path="/settings/general" element={<SettingsPage />} />
            <Route path="/settings/downloads" element={<SettingsPage />} />
            <Route path="/settings/network" element={<SettingsPage />} />
            <Route path="/settings/appearance" element={<SettingsPage />} />
            <Route path="/settings/advanced" element={<SettingsPage />} />
            <Route path="/settings/privacy" element={<SettingsPage />} />
            <Route path="/settings/storage" element={<SettingsPage />} />
            <Route path="/settings/integrations" element={<SettingsPage />} />
            <Route path="/settings/keyboard" element={<SettingsPage />} />
            <Route path="/settings/accessibility" element={<SettingsPage />} />
            <Route path="/settings/import-export" element={<SettingsPage />} />
            <Route path="/settings/experimental" element={<SettingsPage />} />
            <Route path="/settings/about" element={<SettingsPage />} />
            <Route path="/settings/licenses" element={<SettingsPage />} />
            <Route path="/settings/system" element={<SettingsPage />} />
            <Route path="/settings/logs" element={<SettingsPage />} />

            {/* Updates Center */}
            <Route path="/updates" element={<UpdatesManager />} />
            <Route path="/updates/releases" element={<UpdatesManager />} />
            <Route path="/updates/changelog" element={<UpdatesManager />} />

            {/* Diagnostics Scans */}
            <Route path="/diagnostics" element={<SystemDiagnostics />} />
            <Route path="/diagnostics/system" element={<SystemDiagnostics />} />
            <Route path="/diagnostics/network" element={<SystemDiagnostics />} />
            <Route path="/diagnostics/download" element={<SystemDiagnostics />} />
            <Route path="/diagnostics/storage" element={<SystemDiagnostics />} />
            <Route path="/diagnostics/report" element={<SystemDiagnostics />} />

            {/* Other System Areas (Placeholders) */}
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
