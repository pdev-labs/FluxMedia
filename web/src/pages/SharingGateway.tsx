import React, { useState } from "react";
import { 
  Share2, ArrowUpRight, ArrowDownRight, QrCode, Smartphone, Laptop
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Badge } from "../components/ui/Badge";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const SharingGateway: React.FC = () => {
  const [activeTab, setActiveTab] = useState<"send" | "receive" | "devices">("send");
  const [sharingFile, setSharingFile] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleShare = () => {
    setSharingFile(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setSharingFile(false);
          return 100;
        }
        return prev + 10;
      });
    }, 450);
  };

  const nearbyDevices = [
    { name: "Pixel 8 Pro Smartphone", type: "mobile", status: "trusted", ip: "192.168.1.115", ping: "8ms" },
    { name: "Developer MacBook Air", type: "laptop", status: "trusted", ip: "192.168.1.120", ping: "15ms" },
    { name: "Unknown Network Client", type: "laptop", status: "unknown", ip: "192.168.1.182", ping: "142ms" }
  ];

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">LAN Sharing Gateway</h1>
        <p className="text-muted-foreground mt-1">Broadcast media files to nearby local network clients using secure QR codes or device pipelines.</p>
      </div>

      {/* Tab controls */}
      <div className="flex gap-2 border-b border-border/80 pb-1">
        <button
          onClick={() => { setActiveTab("send"); setProgress(0); }}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "send" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <ArrowUpRight className="h-4 w-4" /> Send Media File
        </button>
        <button
          onClick={() => { setActiveTab("receive"); setProgress(0); }}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "receive" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <ArrowDownRight className="h-4 w-4" /> Receive Media File
        </button>
        <button
          onClick={() => { setActiveTab("devices"); setProgress(0); }}
          className={`flex items-center gap-2 px-4 py-2 text-sm font-semibold border-b-2 transition-colors ${
            activeTab === "devices" ? "border-primary text-foreground" : "border-transparent text-muted-foreground hover:text-foreground"
          }`}
        >
          <Smartphone className="h-4 w-4" /> Nearby Devices
        </button>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Core Settings / Device listings (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {activeTab === "send" && (
            <>
              <Card>
                <CardHeader>
                  <CardTitle>File Broadcast Configuration</CardTitle>
                </CardHeader>
                <CardContent className="flex gap-2">
                  <Input placeholder="D:\Downloads\FluxMedia\input_lecture.mp4" className="font-mono text-xs" />
                  <Button variant="outline">Browse</Button>
                </CardContent>
              </Card>

              {/* QR share panel */}
              <Card>
                <CardHeader>
                  <CardTitle>LAN QR Share Portal</CardTitle>
                  <CardDescription>Generate an access QR code that clients can scan to download the file directly from their browser.</CardDescription>
                </CardHeader>
                <CardContent className="flex flex-col sm:flex-row gap-6 items-center">
                  <div className="h-40 w-40 bg-neutral-900 border border-border rounded-lg flex items-center justify-center relative">
                    <QrCode className="h-28 w-28 text-primary" />
                  </div>
                  <div className="space-y-3 flex-1 text-xs">
                    <h4 className="font-semibold text-sm">HTTP Share Server: Active</h4>
                    <p className="text-muted-foreground">Local IP: <strong>192.168.1.112:8000</strong></p>
                    <p className="text-muted-foreground">Your client device must be connected to the same Wi-Fi router network.</p>
                  </div>
                </CardContent>
              </Card>
            </>
          )}

          {activeTab === "receive" && (
            <Card>
              <CardHeader>
                <CardTitle>Receive Gateway configuration</CardTitle>
                <CardDescription>Start the local listener server to receive media files from nearby devices.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid gap-4 sm:grid-cols-2">
                  <Input label="Server Port" defaultValue="8080" />
                  <Input label="Save Path Directory" defaultValue="D:\Downloads\FluxMedia\Incoming" />
                </div>
                <Button variant="primary" className="w-full">Start Listener Gateway</Button>
              </CardContent>
            </Card>
          )}

          {activeTab === "devices" && (
            <Card>
              <CardHeader>
                <CardTitle>Nearby LAN Discovery</CardTitle>
                <CardDescription>Discovered network clients running FluxCore client servers.</CardDescription>
              </CardHeader>
              <CardContent className="divide-y divide-border/40 p-0">
                {nearbyDevices.map((dev) => (
                  <div key={dev.name} className="flex justify-between items-center p-3.5">
                    <div className="flex items-center gap-3">
                      {dev.type === "mobile" ? <Smartphone className="h-5 w-5 text-muted-foreground" /> : <Laptop className="h-5 w-5 text-muted-foreground" />}
                      <div>
                        <h4 className="text-xs font-semibold leading-tight">{dev.name}</h4>
                        <p className="text-[10px] text-muted-foreground">IP: {dev.ip} • latency: {dev.ping}</p>
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Badge variant={dev.status === "trusted" ? "success" : "secondary"}>
                        {dev.status}
                      </Badge>
                      <Button variant="outline" size="sm" className="h-7 text-[10px]">Pair</Button>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action center / transfer speeds (Right column) */}
        <div>
          {sharingFile || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Active File Transfer</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Transfer progress...</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
                <div className="grid grid-cols-2 gap-2 text-xs text-muted-foreground pt-2 border-t border-border/40 font-mono">
                  <div>Speed: <span className="text-foreground font-semibold">12.4 MB/s</span></div>
                  <div>ETA: <span className="text-foreground font-semibold">0m 08s</span></div>
                </div>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Action Center</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button variant="primary" className="w-full gap-2" disabled={activeTab !== "send"} onClick={handleShare}>
                  <Share2 className="h-4.5 w-4.5" /> Start Transmission
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
export default SharingGateway;
