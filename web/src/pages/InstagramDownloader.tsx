import React, { useState } from "react";
import { Camera, Grid, FileVideo, Heart, MessageSquare } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";
import { ProgressBar } from "../components/ui/ProgressBar";

export const InstagramDownloader: React.FC = () => {
  const [username, setUsername] = useState("");
  const [analyzing, setAnalyzing] = useState(false);
  const [profile, setProfile] = useState<any>(null);
  const [downloading, setDownloading] = useState(false);
  const [progress, setProgress] = useState(0);

  const handleAnalyze = () => {
    if (!username) return;
    setAnalyzing(true);
    setProfile(null);
    setTimeout(() => {
      setAnalyzing(false);
      setProfile({
        username: username.replace("@", ""),
        fullName: "Nature Explorer",
        followers: "42.8K followers",
        following: "591 following",
        bio: "Documenting local mountains, landscapes, and wildlife. Weekly reels updates.",
        postsCount: 148,
        posts: [
          { id: "post-1", type: "reel", views: "128K", likes: "12K", comments: "148" },
          { id: "post-2", type: "image", views: "N/A", likes: "8K", comments: "95" },
          { id: "post-3", type: "carousel", views: "N/A", likes: "15K", comments: "210" }
        ]
      });
    }, 1500);
  };

  const handleDownload = () => {
    setDownloading(true);
    setProgress(0);
    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 100) {
          clearInterval(interval);
          setDownloading(false);
          return 100;
        }
        return prev + 10;
      });
    }, 350);
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Instagram Extractor</h1>
        <p className="text-muted-foreground mt-1">Download stories, profile photos, reels, tagged photos, and bulk user posts.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Username input & profile viewer (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          {/* URL Input */}
          <Card>
            <CardHeader>
              <CardTitle>Username or Profile Link</CardTitle>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Input
                placeholder="e.g. @nature_explorer or profile URL"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="font-mono text-sm"
              />
              <Button variant="primary" onClick={handleAnalyze} disabled={!username || analyzing}>
                {analyzing ? "Analyzing..." : "Analyze"}
              </Button>
            </CardContent>
          </Card>

          {/* Profile Book Card */}
          {profile && (
            <Card>
              <CardHeader>
                <div className="flex flex-col sm:flex-row gap-6 items-start sm:items-center">
                  <div className="h-20 w-20 rounded-full bg-secondary/80 border border-border flex items-center justify-center font-bold text-lg text-primary shrink-0">
                    {profile.fullName[0]}
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-base font-semibold leading-tight">{profile.fullName}</h3>
                    <p className="text-xs text-muted-foreground">@{profile.username}</p>
                    <div className="flex gap-4 text-xs text-muted-foreground pt-1">
                      <span>{profile.followers}</span>
                      <span>{profile.following}</span>
                      <span>{profile.postsCount} Post(s)</span>
                    </div>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                <p className="text-xs text-muted-foreground leading-relaxed bg-secondary/20 p-3 rounded-lg border border-border/40">
                  {profile.bio}
                </p>

                {/* Posts preview grid */}
                <div className="grid gap-4 sm:grid-cols-3 pt-2">
                  {profile.posts.map((post: any) => (
                    <div key={post.id} className="border border-border/80 rounded-lg overflow-hidden flex flex-col justify-between h-36 bg-secondary/20">
                      <div className="flex-1 flex items-center justify-center bg-secondary/50">
                        {post.type === "reel" ? <FileVideo className="h-6 w-6 text-primary" /> : <Grid className="h-6 w-6 text-muted-foreground" />}
                      </div>
                      <div className="flex items-center justify-between px-2.5 py-1.5 bg-background border-t border-border/40 text-[10px] text-muted-foreground">
                        <span className="flex items-center gap-0.5"><Heart className="h-3 w-3 shrink-0" /> {post.likes}</span>
                        <span className="flex items-center gap-0.5"><MessageSquare className="h-3 w-3 shrink-0" /> {post.comments}</span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Action Panel (Right column) */}
        <div className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Bulk Extract Options</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-1.5">
                <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Media Type</label>
                <select className="h-10 w-full rounded-md border border-border bg-background px-3 py-2 text-sm">
                  <option>Download Reels Only</option>
                  <option>Download Profile Photo</option>
                  <option>Download Stories Only</option>
                  <option>Download All Media Posts</option>
                </select>
              </div>

              <div className="space-y-1.5">
                <Input label="Max Post Limit" type="number" defaultValue="15" />
              </div>
            </CardContent>
          </Card>

          {downloading || progress > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle>Downloading Profile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex justify-between text-xs font-semibold">
                  <span>Batch download progress</span>
                  <span>{progress}%</span>
                </div>
                <ProgressBar value={progress} size="md" variant={progress === 100 ? "success" : "default"} />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle>Action Center</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Button 
                  variant="primary" 
                  className="w-full gap-2" 
                  disabled={!profile || downloading}
                  onClick={handleDownload}
                >
                  <Camera className="h-4.5 w-4.5" /> Start Bulk Downloader
                </Button>
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};
