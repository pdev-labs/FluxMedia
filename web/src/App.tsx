import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sparkles } from "lucide-react";
import { ThemeProvider } from "./context/ThemeContext";
import { GlobalLayout } from "./layouts/GlobalLayout";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "./components/ui/Card";
import { Button } from "./components/ui/Button";
import { Badge } from "./components/ui/Badge";
import { Input } from "./components/ui/Input";
import { ProgressBar } from "./components/ui/ProgressBar";

// A general mockup view to represent unbuilt pages
const PagePlaceholder: React.FC<{ title: string; desc: string }> = ({ title, desc }) => (
  <div className="flex flex-col gap-6 max-w-4xl animate-in fade-in slide-in-from-bottom-4 duration-300">
    <div>
      <h1 className="text-3xl font-bold tracking-tight">{title}</h1>
      <p className="text-muted-foreground mt-1">{desc}</p>
    </div>
    
    <Card>
      <CardHeader>
        <CardTitle>Module Configuration</CardTitle>
        <CardDescription>FluxMedia CLI module is connected. Graphical interface controls will appear here.</CardDescription>
      </CardHeader>
      <CardContent className="h-64 flex flex-col items-center justify-center border border-dashed border-border rounded-lg m-6 mt-0">
        <Sparkles className="h-8 w-8 text-primary animate-pulse mb-3" />
        <span className="text-sm font-medium text-muted-foreground">Interface Pending Implementation</span>
        <span className="text-xs text-muted-foreground/60 mt-1">Use Cmd Palette (Ctrl+K) to navigate modules</span>
      </CardContent>
    </Card>
  </div>
);

// The Core Dashboard rendering the complete Design System demonstration
const DashboardDemo: React.FC = () => {
  return (
    <div className="flex flex-col gap-8 max-w-6xl animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">System Dashboard</h1>
        <p className="text-muted-foreground mt-1">Welcome to FluxMedia Web. Manage your media files and network gateways.</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* Buttons Design Card */}
        <Card>
          <CardHeader>
            <CardTitle>Buttons & Actions</CardTitle>
            <CardDescription>Interactive design system buttons.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2.5">
            <Button variant="primary">Primary Accent</Button>
            <Button variant="secondary">Secondary</Button>
            <Button variant="outline">Outline</Button>
            <Button variant="ghost">Ghost Link</Button>
            <Button variant="destructive">Destructive</Button>
            <Button variant="primary" isLoading>Processing</Button>
          </CardContent>
        </Card>

        {/* Inputs Design Card */}
        <Card>
          <CardHeader>
            <CardTitle>Data Fields</CardTitle>
            <CardDescription>Structured input text components.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Input id="input-demo" label="Download Destination" placeholder="e.g. C:\Downloads\FluxMedia" />
            <Input id="input-error" label="Media URL" placeholder="https://youtube.com/watch?v=..." error="Invalid URL structure" />
          </CardContent>
        </Card>

        {/* Status Badges Card */}
        <Card>
          <CardHeader>
            <CardTitle>Status Indicators</CardTitle>
            <CardDescription>Informative badges and state tokens.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            <Badge variant="default">Default</Badge>
            <Badge variant="secondary">Secondary</Badge>
            <Badge variant="success">Completed</Badge>
            <Badge variant="warning">In Queue</Badge>
            <Badge variant="danger">Failed</Badge>
            <Badge variant="info">Downloading</Badge>
            <Badge variant="outline">Offline</Badge>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Progress & Speed indicators */}
        <Card>
          <CardHeader>
            <CardTitle>Transcoding & Downloads</CardTitle>
            <CardDescription>Download progress tracking with custom sizes.</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-5">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span>Universal Video Downloader</span>
                <span className="text-primary">85%</span>
              </div>
              <ProgressBar value={85} size="sm" />
            </div>
            
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span>FFmpeg Audio Extraction (FLAC)</span>
                <span className="text-emerald-500">42%</span>
              </div>
              <ProgressBar value={42} variant="success" size="md" />
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs font-semibold">
                <span>Diagnostics Scan status</span>
                <span className="text-amber-500">95%</span>
              </div>
              <ProgressBar value={95} variant="warning" size="lg" />
            </div>
          </CardContent>
        </Card>

        {/* Network connection overview */}
        <Card className="flex flex-col justify-between">
          <CardHeader>
            <CardTitle>LAN QR Share Portal</CardTitle>
            <CardDescription>Local HTTP media server gateway configurations.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex justify-between text-sm py-1 border-b border-border/40">
              <span className="text-muted-foreground">HTTP File Server status</span>
              <Badge variant="success">Active</Badge>
            </div>
            <div className="flex justify-between text-sm py-1 border-b border-border/40">
              <span className="text-muted-foreground">Network Address (Local)</span>
              <span className="font-mono text-xs">192.168.1.112:8000</span>
            </div>
            <div className="flex justify-between text-sm py-1">
              <span className="text-muted-foreground">Connected Mobile clients</span>
              <span className="font-semibold text-primary">3 Active Device(s)</span>
            </div>
          </CardContent>
          <CardFooter className="flex gap-2">
            <Button variant="outline" size="sm">Censor IP Address</Button>
            <Button variant="primary" size="sm">Regenerate Access QR</Button>
          </CardFooter>
        </Card>
      </div>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <GlobalLayout>
          <Routes>
            <Route path="/" element={<DashboardDemo />} />
            <Route path="/downloads" element={<PagePlaceholder title="Downloads Core" desc="Universal extraction download queues and configurations." />} />
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
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </GlobalLayout>
      </BrowserRouter>
    </ThemeProvider>
  );
};

export default App;
