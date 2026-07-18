import React, { useState } from "react";
import { 
  Puzzle, Download, Star, Trash2, Cpu, Settings
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";

export const PluginManager: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"installed" | "store" | "developer">("installed");
  const [plugins, setPlugins] = useState([
    { id: "p1", name: "YouTube Cookie Sync", desc: "Syncs authenticated YouTube browser cookies to local yt-dlp to bypass age boundaries.", author: "DevLabs", version: "1.2.0", enabled: true },
    { id: "p2", name: "Soundcloud Batch Extractor", desc: "Extracted audio tracks from any Soundcloud playlist URL.", author: "Lofi Team", version: "0.9.5", enabled: false }
  ]);
  const [templateName, setTemplateName] = useState("");

  const handleToggle = (id: string) => {
    setPlugins((prev) => 
      prev.map((p) => p.id === id ? { ...p, enabled: !p.enabled } : p)
    );
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Plugin Extensibility</h1>
        <p className="text-muted-foreground mt-1">Install or build custom extractor APIs, conversion formats, or interface themes.</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-border/80 pb-1">
        <button
          onClick={() => setActiveTab("installed")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "installed" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Puzzle className="h-4 w-4" /> Installed Plugins
        </button>
        <button
          onClick={() => setActiveTab("store")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "store" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Download className="h-4 w-4" /> Plugin Store
        </button>
        <button
          onClick={() => setActiveTab("developer")}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "developer" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Cpu className="h-4 w-4" /> Developer Mode
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Core settings (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === "installed" && (
            <Card>
              <CardHeader>
                <CardTitle>Installed Components</CardTitle>
                <CardDescription>Plugins actively loaded by the FluxCore engine.</CardDescription>
              </CardHeader>
              <CardContent className="divide-y divide-border/40 p-0">
                {plugins.map((pl) => (
                  <div key={pl.id} className="p-4 flex justify-between items-start gap-4">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h4 className="text-xs font-semibold leading-tight">{pl.name}</h4>
                        <Badge variant="outline" className="text-[9px]">{pl.version}</Badge>
                      </div>
                      <p className="text-[11px] text-muted-foreground leading-normal">{pl.desc}</p>
                      <p className="text-[10px] text-muted-foreground/60">Author: {pl.author}</p>
                    </div>
                    <div className="flex gap-2 shrink-0">
                      <Button 
                        variant={pl.enabled ? "primary" : "outline"} 
                        size="sm" 
                        className="h-8"
                        onClick={() => handleToggle(pl.id)}
                      >
                        {pl.enabled ? "Disable" : "Enable"}
                      </Button>
                      <Button variant="ghost" size="icon" className="h-8 w-8 text-destructive"><Trash2 className="h-4 w-4" /></Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {activeTab === "store" && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground px-1">Trending Extensibility Plugins</h3>
              
              <Card>
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <div>
                      <CardTitle className="text-sm font-semibold">Twitch Clip Extractor</CardTitle>
                      <CardDescription className="text-xs">Extract clip segments using timeline markers.</CardDescription>
                    </div>
                    <Badge variant="outline">Store Featured</Badge>
                  </div>
                </CardHeader>
                <CardContent className="text-xs text-muted-foreground space-y-2">
                  <div className="flex gap-3 font-semibold text-[10px] text-foreground">
                    <span>1,248 downloads</span>
                    <span className="flex items-center gap-0.5"><Star className="h-3.5 w-3.5 text-amber-500 fill-amber-500" /> 4.8</span>
                  </div>
                </CardContent>
                <CardFooter className="border-t border-border/40 pt-3 flex justify-end">
                  <Button variant="primary" size="sm">Install Plugin</Button>
                </CardFooter>
              </Card>
            </div>
          )}

          {activeTab === "developer" && (
            <Card>
              <CardHeader>
                <CardTitle>Create Plugin Extension</CardTitle>
                <CardDescription>Generate a plugin template repository configured with routing APIs.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <Input 
                  label="Plugin Package Name" 
                  placeholder="e.g. flux-my-extractor" 
                  value={templateName}
                  onChange={(e) => setTemplateName(e.target.value)}
                />
                <Button variant="primary" className="w-full" disabled={!templateName}>Generate Template</Button>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Info panel (Right column) */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Plugin Safety</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground leading-relaxed space-y-3">
              <p>Plugins run locally outside browser isolation and have full filesystem access to output directories. Ensure you only install plugins from trusted authors.</p>
              <div className="pt-2 border-t border-border/40">
                <Button variant="outline" className="w-full gap-1.5 h-9"><Settings className="h-4 w-4" /> Plugin Settings</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
export default PluginManager;
