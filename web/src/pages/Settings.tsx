import React, { useState, useEffect } from "react";
import { 
  Settings, Globe, Palette, Shield, HardDrive, 
  FolderOpen, Save, Search, Sparkles, AlertTriangle
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export const SettingsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState("general");
  const [searchQuery, setSearchQuery] = useState("");
  const [unsaved, setUnsaved] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  const [settings, setSettings] = useState<any>({});
  const [originalSettings, setOriginalSettings] = useState<any>({});

  const categories = [
    { id: "general", name: "General Settings", icon: Settings },
    { id: "downloads", name: "Downloads", icon: FolderOpen },
    { id: "network", name: "Network & Proxy", icon: Globe },
    { id: "appearance", name: "Appearance", icon: Palette },
    { id: "privacy", name: "Privacy & Logs", icon: Shield },
    { id: "storage", name: "Storage & Cache", icon: HardDrive }
  ];

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await fetch("/api/settings");
      if (!res.ok) throw new Error("Failed to fetch settings");
      const data = await res.json();
      setSettings(data.settings);
      setOriginalSettings(data.settings);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ settings })
      });
      if (!res.ok) throw new Error("Failed to save settings");
      const data = await res.json();
      setSettings(data.settings);
      setOriginalSettings(data.settings);
      setUnsaved(false);
    } catch (err: any) {
      setError(err.message);
    }
  };

  const handleDiscard = () => {
    setSettings(originalSettings);
    setUnsaved(false);
  };

  const updateSetting = (key: string, value: any) => {
    setSettings((prev: any) => ({ ...prev, [key]: value }));
    setUnsaved(true);
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 max-w-7xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300 pb-16">
      <div className="flex justify-between items-start">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
          <p className="text-muted-foreground mt-1">Configure language interfaces, proxy tunnels, themes, and default path overrides.</p>
        </div>
      </div>

      {error && (
        <div className="bg-destructive/10 border border-destructive/20 text-destructive px-4 py-3 rounded-lg flex items-center gap-2">
          <AlertTriangle className="h-5 w-5" />
          <p className="text-sm font-medium">{error}</p>
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-4 items-start">
        {/* Left Settings Sidebar */}
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

        {/* Right Settings Configuration viewport */}
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
                    <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                      <option>English (United States)</option>
                    </select>
                  </div>
                </div>

                <div className="space-y-4 pt-4 border-t border-border/40">
                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input 
                      type="checkbox" 
                      checked={settings.show_educational_notice ?? true} 
                      className="rounded border-border text-primary focus:ring-primary h-4 w-4" 
                      onChange={(e) => updateSetting("show_educational_notice", e.target.checked)} 
                    />
                    <span>Show Educational Notice</span>
                  </label>
                  
                  <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                    <input 
                      type="checkbox" 
                      checked={settings.web_auth_enabled ?? true} 
                      className="rounded border-border text-primary focus:ring-primary h-4 w-4" 
                      onChange={(e) => updateSetting("web_auth_enabled", e.target.checked)} 
                    />
                    <span>Web Authentication Enabled</span>
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
                  <Input 
                    label="Default Download Directory" 
                    value={settings.download_dir || ""} 
                    onChange={(e) => updateSetting("download_dir", e.target.value)} 
                  />
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Default Quality Preset</label>
                    <select 
                      className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" 
                      value={settings.default_quality || "best"}
                      onChange={(e) => updateSetting("default_quality", e.target.value)}
                    >
                      <option value="best">Best Available</option>
                      <option value="1080p">1080p</option>
                      <option value="720p">720p</option>
                      <option value="worst">Lowest Quality</option>
                    </select>
                  </div>
                  
                  <Input 
                    label="Filename Format" 
                    value={settings.filename_format || ""} 
                    onChange={(e) => updateSetting("filename_format", e.target.value)} 
                  />
                </div>

                <div className="grid gap-4 sm:grid-cols-2 pt-4 border-t border-border/40">
                  <div className="space-y-4">
                    <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                      <input 
                        type="checkbox" 
                        checked={settings.embed_metadata ?? true} 
                        className="rounded border-border text-primary focus:ring-primary h-4 w-4" 
                        onChange={(e) => updateSetting("embed_metadata", e.target.checked)} 
                      />
                      <span>Embed Metadata</span>
                    </label>
                    <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                      <input 
                        type="checkbox" 
                        checked={settings.embed_thumbnail ?? true} 
                        className="rounded border-border text-primary focus:ring-primary h-4 w-4" 
                        onChange={(e) => updateSetting("embed_thumbnail", e.target.checked)} 
                      />
                      <span>Embed Thumbnail</span>
                    </label>
                    <label className="flex items-center gap-3 text-sm cursor-pointer select-none">
                      <input 
                        type="checkbox" 
                        checked={settings.embed_subtitles ?? false} 
                        className="rounded border-border text-primary focus:ring-primary h-4 w-4" 
                        onChange={(e) => updateSetting("embed_subtitles", e.target.checked)} 
                      />
                      <span>Embed Subtitles</span>
                    </label>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "network" && (
            <Card>
              <CardHeader>
                <CardTitle>Network Settings</CardTitle>
                <CardDescription>Manage browser cookies and download limits.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Cookies from Browser</label>
                    <select 
                      className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" 
                      value={settings.cookies_browser || "none"}
                      onChange={(e) => updateSetting("cookies_browser", e.target.value)}
                    >
                      <option value="none">None</option>
                      <option value="chrome">Chrome</option>
                      <option value="firefox">Firefox</option>
                      <option value="edge">Edge</option>
                      <option value="safari">Safari</option>
                      <option value="brave">Brave</option>
                      <option value="opera">Opera</option>
                    </select>
                  </div>
                  
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Download Speed Limit</label>
                    <select 
                      className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" 
                      value={settings.download_speed_limit || "disabled"}
                      onChange={(e) => updateSetting("download_speed_limit", e.target.value)}
                    >
                      <option value="disabled">Disabled</option>
                      <option value="1M">1 MB/s</option>
                      <option value="5M">5 MB/s</option>
                      <option value="10M">10 MB/s</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {activeTab === "appearance" && (
            <Card>
              <CardHeader>
                <CardTitle>Aesthetics & Layout</CardTitle>
                <CardDescription>Alter layouts and accent coloring.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                <div className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Theme presets</label>
                    <select 
                      className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm" 
                      value={settings.theme || "dark"}
                      onChange={(e) => updateSetting("theme", e.target.value)}
                    >
                      <option value="dark">Dark Mode</option>
                      <option value="light">Light Mode</option>
                    </select>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}
          
          {(activeTab === "privacy" || activeTab === "storage") && (
            <Card>
              <CardHeader>
                <CardTitle>Not Applicable</CardTitle>
                <CardDescription>These settings are not managed through this interface.</CardDescription>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">Please use the general and downloads tabs to configure FluxMedia.</p>
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
            <Button variant="ghost" size="sm" onClick={handleDiscard}>Discard</Button>
            <Button variant="primary" size="sm" className="gap-1" onClick={handleSave}><Save className="h-3.5 w-3.5" /> Save Changes</Button>
          </div>
        </div>
      )}
    </div>
  );
};
export default SettingsPage;
