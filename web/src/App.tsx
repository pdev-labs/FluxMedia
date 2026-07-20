import React from "react";
import { BrowserRouter, Routes, Route, Navigate, useLocation } from "react-router-dom";
import { AnimatePresence, motion } from "framer-motion";
import { Sparkles } from "lucide-react";
import { ThemeProvider } from "./context/ThemeContext";
import { GlobalLayout } from "./layouts/GlobalLayout";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "./components/ui/Card";

// Import all subpages
const Dashboard = React.lazy(() => import("./pages/Dashboard").then(m => ({ default: m.Dashboard })));
const DownloadCenter = React.lazy(() => import("./pages/DownloadCenter").then(m => ({ default: m.DownloadCenter })));
const VideoDownloader = React.lazy(() => import("./pages/VideoDownloader").then(m => ({ default: m.VideoDownloader })));
const YoutubeSearch = React.lazy(() => import("./pages/YoutubeSearch").then(m => ({ default: m.YoutubeSearch })));
const AudioDownloader = React.lazy(() => import("./pages/AudioDownloader").then(m => ({ default: m.AudioDownloader })));
const PlaylistDownloader = React.lazy(() => import("./pages/PlaylistDownloader").then(m => ({ default: m.PlaylistDownloader })));
const ChannelDownloader = React.lazy(() => import("./pages/ChannelDownloader").then(m => ({ default: m.ChannelDownloader })));
const SubtitleDownloader = React.lazy(() => import("./pages/SubtitleDownloader").then(m => ({ default: m.SubtitleDownloader })));
const TrimDownloader = React.lazy(() => import("./pages/TrimDownloader").then(m => ({ default: m.TrimDownloader })));
const InstagramDownloader = React.lazy(() => import("./pages/InstagramDownloader").then(m => ({ default: m.InstagramDownloader })));

// Media management & converter imports
const DownloadQueue = React.lazy(() => import("./pages/DownloadQueue").then(m => ({ default: m.DownloadQueue })));
const DownloadHistory = React.lazy(() => import("./pages/DownloadHistory").then(m => ({ default: m.DownloadHistory })));
const FileManager = React.lazy(() => import("./pages/FileManager").then(m => ({ default: m.FileManager })));
const MediaConverter = React.lazy(() => import("./pages/MediaConverter").then(m => ({ default: m.MediaConverter })));
const SystemStats = React.lazy(() => import("./pages/SystemStats").then(m => ({ default: m.SystemStats })));

// Settings, updates, sharing, and diagnostics imports
const SettingsPage = React.lazy(() => import("./pages/Settings").then(m => ({ default: m.SettingsPage })));
const UpdatesManager = React.lazy(() => import("./pages/UpdatesManager").then(m => ({ default: m.UpdatesManager })));
const SharingGateway = React.lazy(() => import("./pages/SharingGateway").then(m => ({ default: m.SharingGateway })));
const SystemDiagnostics = React.lazy(() => import("./pages/SystemDiagnostics").then(m => ({ default: m.SystemDiagnostics })));

// Extensibility, support, logs, developer, and onboarding imports
const HelpCenter = React.lazy(() => import("./pages/HelpCenter").then(m => ({ default: m.HelpCenter })));
const FeedbackCenter = React.lazy(() => import("./pages/FeedbackCenter").then(m => ({ default: m.FeedbackCenter })));
const LogCenter = React.lazy(() => import("./pages/LogCenter").then(m => ({ default: m.LogCenter })));
const PluginManager = React.lazy(() => import("./pages/PluginManager").then(m => ({ default: m.PluginManager })));
const DeveloperCenter = React.lazy(() => import("./pages/DeveloperCenter").then(m => ({ default: m.DeveloperCenter })));
const OnboardingWizard = React.lazy(() => import("./pages/OnboardingWizard").then(m => ({ default: m.OnboardingWizard })));

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


const PageTransition: React.FC<{ children: React.ReactNode }> = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.2 }}
  >
    {children}
  </motion.div>
);

const AppRoutes: React.FC = () => {
  const location = useLocation();
  return (
    <AnimatePresence mode="wait">
      <React.Suspense fallback={<div className="flex items-center justify-center h-full min-h-[400px]"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div></div>}>
        <Routes location={location} key={location.pathname}>
            {/* Core Dashboard */}
            <Route path="/" element={<PageTransition><Dashboard /></PageTransition>} />
            
            {/* Download Hub & Extractor Engines */}
            <Route path="/downloads" element={<PageTransition><DownloadCenter /></PageTransition>} />
            <Route path="/download/video" element={<PageTransition><VideoDownloader /></PageTransition>} />
            <Route path="/download/search" element={<PageTransition><YoutubeSearch /></PageTransition>} />
            <Route path="/download/audio" element={<PageTransition><AudioDownloader /></PageTransition>} />
            <Route path="/download/playlist" element={<PageTransition><PlaylistDownloader /></PageTransition>} />
            <Route path="/download/channel" element={<PageTransition><ChannelDownloader /></PageTransition>} />
            <Route path="/download/subtitles" element={<PageTransition><SubtitleDownloader /></PageTransition>} />
            <Route path="/download/trimmer" element={<PageTransition><TrimDownloader /></PageTransition>} />
            <Route path="/download/instagram" element={<PageTransition><InstagramDownloader /></PageTransition>} />

            {/* Download Queue & Manager */}
            <Route path="/queue" element={<PageTransition><DownloadQueue /></PageTransition>} />

            {/* History logs & sub-routes */}
            <Route path="/history" element={<PageTransition><DownloadHistory /></PageTransition>} />
            <Route path="/history/downloads" element={<PageTransition><DownloadHistory /></PageTransition>} />
            <Route path="/history/search" element={<PageTransition><DownloadHistory /></PageTransition>} />
            <Route path="/history/errors" element={<PageTransition><DownloadHistory /></PageTransition>} />

            {/* File manager & categories */}
            <Route path="/files" element={<PageTransition><FileManager /></PageTransition>} />
            <Route path="/files/videos" element={<PageTransition><FileManager /></PageTransition>} />
            <Route path="/files/audio" element={<PageTransition><FileManager /></PageTransition>} />
            <Route path="/files/playlists" element={<PageTransition><FileManager /></PageTransition>} />
            <Route path="/files/images" element={<PageTransition><FileManager /></PageTransition>} />
            <Route path="/files/documents" element={<PageTransition><FileManager /></PageTransition>} />
            <Route path="/files/trash" element={<PageTransition><FileManager /></PageTransition>} />

            {/* Converter Options */}
            <Route path="/converter" element={<PageTransition><MediaConverter /></PageTransition>} />
            <Route path="/converter/video" element={<PageTransition><MediaConverter /></PageTransition>} />
            <Route path="/converter/audio" element={<PageTransition><MediaConverter /></PageTransition>} />
            <Route path="/converter/batch" element={<PageTransition><MediaConverter /></PageTransition>} />

            {/* Statistics */}
            <Route path="/stats" element={<PageTransition><SystemStats /></PageTransition>} />

            {/* LAN Sharing Gateway */}
            <Route path="/sharing" element={<PageTransition><SharingGateway /></PageTransition>} />
            <Route path="/share" element={<PageTransition><SharingGateway /></PageTransition>} />
            <Route path="/share/send" element={<PageTransition><SharingGateway /></PageTransition>} />
            <Route path="/share/receive" element={<PageTransition><SharingGateway /></PageTransition>} />
            <Route path="/share/history" element={<PageTransition><SharingGateway /></PageTransition>} />
            <Route path="/share/devices" element={<PageTransition><SharingGateway /></PageTransition>} />

            {/* System Settings */}
            <Route path="/settings" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/general" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/downloads" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/network" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/appearance" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/advanced" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/privacy" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/storage" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/integrations" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/keyboard" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/accessibility" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/import-export" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/experimental" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/about" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/licenses" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/system" element={<PageTransition><SettingsPage /></PageTransition>} />
            <Route path="/settings/logs" element={<PageTransition><SettingsPage /></PageTransition>} />

            {/* Updates Center */}
            <Route path="/updates" element={<PageTransition><UpdatesManager /></PageTransition>} />
            <Route path="/updates/releases" element={<PageTransition><UpdatesManager /></PageTransition>} />
            <Route path="/updates/changelog" element={<PageTransition><UpdatesManager /></PageTransition>} />

            {/* Diagnostics Scans */}
            <Route path="/diagnostics" element={<PageTransition><SystemDiagnostics /></PageTransition>} />
            <Route path="/diagnostics/system" element={<PageTransition><SystemDiagnostics /></PageTransition>} />
            <Route path="/diagnostics/network" element={<PageTransition><SystemDiagnostics /></PageTransition>} />
            <Route path="/diagnostics/download" element={<PageTransition><SystemDiagnostics /></PageTransition>} />
            <Route path="/diagnostics/storage" element={<PageTransition><SystemDiagnostics /></PageTransition>} />
            <Route path="/diagnostics/report" element={<PageTransition><SystemDiagnostics /></PageTransition>} />

            {/* Extensibility & Support modules */}
            <Route path="/help" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/getting-started" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/tutorials" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/faq" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/commands" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/troubleshooting" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/releases" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/keyboard-shortcuts" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/search" element={<PageTransition><HelpCenter /></PageTransition>} />
            <Route path="/help/contact" element={<PageTransition><HelpCenter /></PageTransition>} />

            <Route path="/feedback" element={<PageTransition><FeedbackCenter /></PageTransition>} />
            <Route path="/feedback/bug" element={<PageTransition><FeedbackCenter /></PageTransition>} />
            <Route path="/feedback/feature" element={<PageTransition><FeedbackCenter /></PageTransition>} />
            <Route path="/feedback/general" element={<PageTransition><FeedbackCenter /></PageTransition>} />

            <Route path="/logs" element={<PageTransition><LogCenter /></PageTransition>} />
            <Route path="/logs/application" element={<PageTransition><LogCenter /></PageTransition>} />
            <Route path="/logs/downloads" element={<PageTransition><LogCenter /></PageTransition>} />
            <Route path="/logs/network" element={<PageTransition><LogCenter /></PageTransition>} />
            <Route path="/logs/system" element={<PageTransition><LogCenter /></PageTransition>} />
            <Route path="/logs/debug" element={<PageTransition><LogCenter /></PageTransition>} />

            <Route path="/plugins" element={<PageTransition><PluginManager /></PageTransition>} />
            <Route path="/plugins/installed" element={<PageTransition><PluginManager /></PageTransition>} />
            <Route path="/plugins/store" element={<PageTransition><PluginManager /></PageTransition>} />
            <Route path="/plugins/developer" element={<PageTransition><PluginManager /></PageTransition>} />
            <Route path="/plugins/settings" element={<PageTransition><PluginManager /></PageTransition>} />

            <Route path="/developer" element={<PageTransition><DeveloperCenter /></PageTransition>} />
            <Route path="/developer/console" element={<PageTransition><DeveloperCenter /></PageTransition>} />
            <Route path="/developer/api" element={<PageTransition><DeveloperCenter /></PageTransition>} />
            <Route path="/developer/system" element={<PageTransition><DeveloperCenter /></PageTransition>} />
            <Route path="/developer/debug" element={<PageTransition><DeveloperCenter /></PageTransition>} />

            <Route path="/onboarding" element={<PageTransition><OnboardingWizard /></PageTransition>} />

            {/* Other System Areas (Placeholders) */}
            <Route path="/about" element={<PagePlaceholder title="About Project" desc="Learn about the authors and technology credits." />} />
            
            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
      </React.Suspense>
    </AnimatePresence>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <GlobalLayout>
          <AppRoutes />
        </GlobalLayout>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
