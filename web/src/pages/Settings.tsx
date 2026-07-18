import React, { useState } from "react";
import { 
  Settings, Globe, Palette, Shield, HardDrive, 
  FolderOpen, Save, Search, Sparkles
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("general");
  const [searchQuery, setSearchQuery] = useState("");
  const [unsaved, setUnsaved] = useState(false);

  const categories = [
    { id: "general", name: "General Settings", icon: Settings },
    { id: "downloads", name: "Downloads", icon: FolderOpen },
    { id: "network", name: "Network & Proxy", icon: Globe },
    { id: "appearance", name: "Appearance", icon: Palette },
    { id: "privacy", name: "Privacy & Logs", icon: Shield },
    { id: "storage", name: "Storage & Cache", icon: HardDrive }
  ];

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300 pb-16">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
          <p className="text-muted-foreground mt-1">Configure language interfaces, proxy tunnels, themes, and default path overrides.</p>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-4 items-start">
        {/* Left Settings Sidebar (1 column) */}
        <div className="lg:col-span-1 space-y-4">
          <Card>
            <CardHeader className="pb-3 border-b border-border/40">
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground/60" />
                <Input
                  placeholder="Search settings..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-8 h-9 text-xs"
                />
              </div>
            </CardHeader>
            <CardContent className="p-2 space-y-1">
              {categories.map((cat) => (
                <button
                  key={cat.id}
                  onClick={() => setActiveTab(cat.id)}
                  className={`flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-xs font-semibold transition-colors hover:bg-secondary/40 ${
                    activeTab === cat.id ? "bg-secondary text-primary" : "text-muted-foreground"
                  }`}
                >
                  <cat.icon className="h-4 w-4 shrink-0" />
                  <span>{cat.name}</span>
                </button>
              ))}
            </CardContent>
          </Card>
        </div>

        {/* Right Settings Configuration viewport (3 columns) */}
        <div className="lg:col-span-3 space-y-6">
          {activeTab === "general" && (
            <Card>
              <CardHeader>
                <CardTitle>General Configurations</CardTitle>
                <CardDescription>Configure system boot-ups, language localization, and telemetry logs.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Default Interface Language</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" onChange={() => setUnsaved(true)}>
                      <option>English (United States)</option>
                      <option>Español (España)</option>
                      <option>Deutsch (Deutschland)</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Time Format</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" onChange={() => setUnsaved(true)}>
                      <option>24-Hour (HH:MM)</option>
                      <option>12-Hour (AM/PM)</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-border/40">
                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" onChange={() => setUnsaved(true)} />
                    <span>Auto Start on OS launch</span>
                  </label>

                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" onChange={() => setUnsaved(true)} />
                    <span>Close to system tray instead of exiting</span>
                  </label>

                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" onChange={() => setUnsaved(true)} />
                    <span>Anonymous telemetry transmission</span>
                  </label>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "downloads" && (
            <Card>
              <CardHeader>
                <CardTitle>Download Targets & Queues</CardTitle>
                <CardDescription>Setup default paths, parallel limits, and cookie managers.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="space-y-4">
                  <Input label="Default Download Directory" defaultValue="D:\Downloads\FluxMedia" onChange={() => setUnsaved(true)} />
                  <Input label="Default Quality Preset" defaultValue="Best Available Quality (1080p+)" onChange={() => setUnsaved(true)} />
                </div>

                <div className="grid gap-4 sm:grid-cols-2 pt-4 border-t border-border/40">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Retry Count on Failures</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" onChange={() => setUnsaved(true)}>
                      <option>3 attempts</option>
                      <option>5 attempts</option>
                      <option>No Retries</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Auto-resume downloads</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" onChange={() => setUnsaved(true)}>
                      <option>Enabled (Recommended)</option>
                      <option>Disabled</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "network" && (
            <Card>
              <CardHeader>
                <CardTitle>Proxy & DNS Tunnels</CardTitle>
                <CardDescription>Redirect network requests through custom proxy servers.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Proxy Tunnel Protocol</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" onChange={() => setUnsaved(true)}>
                      <option>None (Direct Link)</option>
                      <option>SOCKS5 Proxy</option>
                      <option>HTTP/HTTPS Proxy</option>
                    </select>
                  </div>
                  
                  <Input label="Proxy Server Address" placeholder="127.0.0.1:1080" onChange={() => setUnsaved(true)} />
                </div>

                <div className="space-y-4 pt-4 border-t border-border/40">
                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" onChange={() => setUnsaved(true)} />
                    <span>Perform SSL/TLS peer certificate validation</span>
                  </label>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "appearance" && (
            <Card>
              <CardHeader>
                <CardTitle>Aesthetics & Layout</CardTitle>
                <CardDescription>Alter layouts, accent coloring, animations, and typography variables.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Theme presets</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" onChange={() => setUnsaved(true)}>
                      <option>Dark Mode (Midnight)</option>
                      <option>Light Mode (Alabaster)</option>
                      <option>High Contrast Mode</option>
                    </select>
                  </div>

                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Display Density</label>
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" onChange={() => setUnsaved(true)}>
                      <option>Comfortable spacing</option>
                      <option>Compact spacing</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-border/40">
                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" onChange={() => setUnsaved(true)} />
                    <span>Enable layout animations</span>
                  </label>

                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input type="checkbox" className="rounded border-border text-primary focus:ring-primary h-4 w-4" onChange={() => setUnsaved(true)} />
                    <span>Reduce motion scale defaults</span>
                  </label>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "privacy" && (
            <Card>
              <CardHeader>
                <CardTitle>History & Temporary Caches</CardTitle>
                <CardDescription>Censor active search buffers, logs, and cookie caches.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between items-center pb-3 border-b border-border/40">
                  <div>
                    <h5 className="text-xs font-semibold">Clear Search History</h5>
                    <p className="text-[10px] text-muted-foreground">Wipes all cached query lookups.</p>
                  </div>
                  <Button variant="destructive" size="sm">Clear</Button>
                </div>

                <div className="flex justify-between items-center pb-3 border-b border-border/40">
                  <div>
                    <h5 className="text-xs font-semibold">Delete Local Cookies Cache</h5>
                    <p className="text-[10px] text-muted-foreground">Forces logout of authenticated modules.</p>
                  </div>
                  <Button variant="destructive" size="sm">Clear</Button>
                </div>

                <div className="flex justify-between items-center">
                  <div>
                    <h5 className="text-xs font-semibold">Wipe System Logs</h5>
                    <p className="text-[10px] text-muted-foreground">Clears terminal output files from core directories.</p>
                  </div>
                  <Button variant="destructive" size="sm">Clear</Button>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "storage" && (
            <Card>
              <CardHeader>
                <CardTitle>Storage Allocation</CardTitle>
                <CardDescription>Scan folder directory weights and release cached memory.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-1.5">
                  <div className="flex justify-between text-xs font-semibold">
                    <span>Cache Limit Capacity</span>
                    <span>1.2 GB / 5.0 GB Max</span>
                  </div>
                  <ProgressBar value={24} size="sm" />
                </div>

                <div className="flex justify-between items-center pt-3 border-t border-border/40">
                  <span className="text-xs text-muted-foreground">Cleanup Recommendations: <strong>Remove 248MB of temp logs</strong></span>
                  <Button variant="outline" size="sm">Run Cleanup</Button>
                </div>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Unsaved Changes Banner */}
      {unsaved && (
        <div className="fixed bottom-10 left-1/2 transform -translate-x-1/2 z-50 flex items-center justify-between gap-6 bg-card border border-primary/50 shadow-2xl rounded-xl px-5 py-3.5 animate-in fade-in slide-in-from-bottom-5 duration-200">
          <div className="flex items-center gap-2.5">
            <Sparkles className="h-4.5 w-4.5 text-primary animate-pulse" />
            <span className="text-xs font-semibold">Unsaved configuration changes detected.</span>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="sm" onClick={() => setUnsaved(false)}>Discard</Button>
            <Button variant="primary" size="sm" className="gap-1" onClick={() => setUnsaved(false)}><Save className="h-3.5 w-3.5" /> Save Changes</Button>
          </div>
        </div>
      )}
    </div>
  );
};
export default SettingsPage;
