import React, { useState } from "react";
import { 
  Search, BookOpen, Terminal, HelpCircle as QuestionIcon, ShieldAlert, ChevronDown
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { cn } from "../utils/cn";

export const HelpCenter: React.FC = () => {
  const [activeSection, setActiveSection] = useState("start");
  const [search, setSearch] = useState("");
  const [troubleshootStep, setTroubleshootStep] = useState(0);

  const sections = [
    { id: "start", name: "Getting Started", icon: BookOpen },
    { id: "commands", name: "CLI Commands", icon: Terminal },
    { id: "faq", name: "FAQ Answers", icon: QuestionIcon },
    { id: "trouble", name: "Interactive Debug", icon: ShieldAlert }
  ];

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Help & Documentation Center</h1>
          <p className="text-muted-foreground mt-1">Access first launch guides, command syntaxes, troubleshooting Wizards, and FAQs.</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4 items-start">
        {/* Left Documentation Sidebar (1 column) */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader className="pb-3 border-b border-border/40">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground/60" />
                <Input
                  placeholder="Search articles..."
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  className="pl-8 h-9 text-xs"
                />
              </div>
            </CardHeader>
            <CardContent className="p-2 space-y-1">
              {sections.map((sec) => (
                <button
                  key={sec.id}
                  onClick={() => setActiveSection(sec.id)}
                  className={cn(
                    "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-xs font-semibold transition-colors hover:bg-secondary/40",
                    activeSection === sec.id ? "bg-secondary text-primary" : "text-muted-foreground"
                  )}
                >
                  <sec.icon className="h-4 w-4 shrink-0" />
                  <span>{sec.name}</span>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Content Viewport (3 columns) */}
        <div className="lg:col-span-3 space-y-6">
          {activeSection === "start" && (
            <Card>
              <CardHeader>
                <CardTitle>Getting Started Guide</CardTitle>
                <CardDescription>Step-by-step onboarding walkthroughs for first-time operators.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 text-xs leading-relaxed">
                <div className="space-y-3">
                  <h4 className="font-semibold text-sm">1. Extracting Your First Stream</h4>
                  <p className="text-muted-foreground">Navigate to the <strong>Download Video</strong> tab in the sidebar menu. Paste any YouTube, Twitch, or generic platform stream URL into the input field and click <strong>Analyze</strong>. Once analysis completes, select your output container resolution profile and trigger the extraction thread.</p>
                </div>
                
                <div className="space-y-3 pt-4 border-t border-border/40">
                  <h4 className="font-semibold text-sm">2. Synchronizing Playlists & Creator Channels</h4>
                  <p className="text-muted-foreground">For recurring creators, navigate to <strong>Playlist Downloader</strong>. Paste the target index link, and use the selection grids to download specific items while filtering duplicate files automatically.</p>
                </div>

                <div className="space-y-3 pt-4 border-t border-border/40">
                  <h4 className="font-semibold text-sm">3. Local File Hosting Sharing Gateway</h4>
                  <p className="text-muted-foreground">Navigate to <strong>LAN Sharing</strong>. Choose any downloaded audio/video file and boot up the sharing HTTP gateway. Scan the generated QR code with your mobile devices to stream instantly.</p>
                </div>
              </CardContent>
            </Card>
          )}

          {activeSection === "commands" && (
            <Card>
              <CardHeader>
                <CardTitle>CLI Command Reference</CardTitle>
                <CardDescription>Syntax structures and switches for the underlying FluxMedia console engine.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-2">
                  <h4 className="text-xs font-bold font-mono bg-secondary/80 p-2.5 rounded border border-border">fluxmedia --video [URL] --resolution 1080p</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">Downloads the target video URL and forces FFmpeg multiplexing to FHD 1080p WebM/MP4 container streams.</p>
                </div>

                <div className="space-y-2 pt-4 border-t border-border/40">
                  <h4 className="text-xs font-bold font-mono bg-secondary/80 p-2.5 rounded border border-border">fluxmedia --audio [URL] --format flac --normalize</h4>
                  <p className="text-xs text-muted-foreground leading-relaxed">Extracts the stream sound track, transcodes it to lossless FLAC format, and runs volume leveling filters.</p>
                </div>
              </CardContent>
            </Card>
          )}

          {activeSection === "faq" && (
            <Card>
              <CardHeader>
                <CardTitle>Frequently Asked Questions (FAQ)</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="pb-3 border-b border-border/40">
                  <h4 className="text-xs font-semibold flex items-center gap-2">Why does the downloader raise age-restricted errors? <ChevronDown className="h-3 w-3 text-muted-foreground" /></h4>
                  <p className="text-[11px] text-muted-foreground mt-1">Some platforms require user cookies to authenticate age boundaries. Navigate to <strong>Settings &gt; Downloads</strong> and specify a browser cookie exports file path.</p>
                </div>

                <div className="pb-3 border-b border-border/40">
                  <h4 className="text-xs font-semibold flex items-center gap-2">How do I fix missing FFmpeg codecs on Windows? <ChevronDown className="h-3 w-3 text-muted-foreground" /></h4>
                  <p className="text-[11px] text-muted-foreground mt-1">FluxMedia wraps FFmpeg dependencies automatically. If warnings persist, go to <strong>Diagnostics</strong> and execute the auto-repair script.</p>
                </div>
              </CardContent>
            </Card>
          )}

          {activeSection === "trouble" && (
            <Card>
              <CardHeader>
                <CardTitle>Interactive Troubleshooting Wizard</CardTitle>
                <CardDescription>Step-by-step diagnostic triage framework.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 text-xs">
                {troubleshootStep === 0 && (
                  <div className="space-y-4">
                    <p className="font-semibold">What is the symptoms profile of the system warning you are encountering?</p>
                    <div className="flex flex-col gap-2">
                      <Button variant="outline" className="justify-start text-xs h-9" onClick={() => setTroubleshootStep(1)}>Downloads start but crash immediately (FFmpeg Error)</Button>
                      <Button variant="outline" className="justify-start text-xs h-9" onClick={() => setTroubleshootStep(2)}>Stream URLs fail to analyze (Network / Age Limit)</Button>
                    </div>
                  </div>
                )}

                {troubleshootStep === 1 && (
                  <div className="space-y-4">
                    <h4 className="font-semibold text-emerald-500">Diagnosis: Missing or Locked FFmpeg binaries.</h4>
                    <p className="text-muted-foreground">The downloader is attempting to merge audio and video tracks but cannot execute the transcode binary.</p>
                    <div className="flex gap-2">
                      <Button variant="outline" onClick={() => setTroubleshootStep(0)}>Go Back</Button>
                      <Button variant="primary">Run Subsystems Repair</Button>
                    </div>
                  </div>
                )}

                {troubleshootStep === 2 && (
                  <div className="space-y-4">
                    <h4 className="font-semibold text-amber-500">Diagnosis: DNS Resolvers Blocked or Age Restrictions.</h4>
                    <p className="text-muted-foreground">The local extractor cannot parse stream links. Try verifying your cookie files configuration or local network proxy settings.</p>
                    <div className="flex gap-2">
                      <Button variant="outline" onClick={() => setTroubleshootStep(0)}>Go Back</Button>
                      <Button variant="primary">Open Cookie Configuration</Button>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
export default HelpCenter;
