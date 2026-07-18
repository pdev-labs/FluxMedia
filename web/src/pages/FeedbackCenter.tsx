import React, { useState } from "react";
import { Check, FileCode } from "lucide-react";
import { Card, CardHeader, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export const FeedbackCenter: React.FC = () => {
  const [feedbackType, setFeedbackType] = useState<"bug" | "feature" | "general">("bug");
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setTimeout(() => {
      setSubmitting(false);
      setSuccess(true);
    }, 1500);
  };

  return (
    <div className="flex flex-col gap-8 max-w-4xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Feedback & Bug Reporting</h1>
        <p className="text-muted-foreground mt-1">Submit issues directly to the developers or suggest experimental feature plugins.</p>
      </div>

      {success ? (
        <Card className="border-emerald-500 bg-emerald-500/5">
          <CardContent className="pt-6 flex flex-col items-center justify-center text-center space-y-3">
            <Check className="h-10 w-10 text-emerald-500 bg-emerald-500/10 p-2 rounded-full" />
            <h3 className="font-semibold text-base">Feedback Successfully Transmitted!</h3>
            <p className="text-xs text-muted-foreground max-w-sm">Thank you for helping improve FluxMedia. Developers will inspect the attached logs and tracebacks.</p>
            <Button variant="outline" size="sm" onClick={() => setSuccess(false)}>Submit another ticket</Button>
          </CardContent>
        </Card>
      ) : (
        <Card>
          <CardHeader className="pb-3 border-b border-border/40">
            {/* Feedback category switches */}
            <div className="flex gap-2">
              <Button 
                variant={feedbackType === "bug" ? "primary" : "outline"} 
                size="sm"
                onClick={() => setFeedbackType("bug")}
              >
                Report Bug
              </Button>
              <Button 
                variant={feedbackType === "feature" ? "primary" : "outline"} 
                size="sm"
                onClick={() => setFeedbackType("feature")}
              >
                Request Feature
              </Button>
              <Button 
                variant={feedbackType === "general" ? "primary" : "outline"} 
                size="sm"
                onClick={() => setFeedbackType("general")}
              >
                General Feedback
              </Button>
            </div>
          </CardHeader>
          <CardContent className="pt-6">
            <form onSubmit={handleSubmit} className="space-y-6">
              {feedbackType === "bug" && (
                <div className="space-y-4">
                  <Input label="Short Summary of the bug" placeholder="e.g. Video downloader crashes at 99% FFmpeg merge" required />
                  
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Steps to Reproduce</label>
                    <textarea 
                      placeholder="1. Paste URL...\n2. Configure output to MKV...\n3. Click download..."
                      className="min-h-[100px] w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary disabled:cursor-not-allowed disabled:opacity-50"
                      required
                    />
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <Input label="Expected Behaviour" placeholder="The files should merge and save as MP4." />
                    <Input label="Actual Behaviour" placeholder="Vite terminal logs trace code 1 FFmpeg fail." />
                  </div>
                </div>
              )}

              {feedbackType === "feature" && (
                <div className="space-y-4">
                  <Input label="Feature Proposal Title" placeholder="e.g. Integrate soundcloud playlists bulk extractor" required />
                  
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">Detailed Use Case & Proposed Solution</label>
                    <textarea 
                      placeholder="Provide details about why this feature is important and how you imagine it working..."
                      className="min-h-[120px] w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      required
                    />
                  </div>
                </div>
              )}

              {feedbackType === "general" && (
                <div className="space-y-4">
                  <div className="space-y-1.5">
                    <label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">General Comments / Rating</label>
                    <textarea 
                      placeholder="Share your experience using FluxMedia Web..."
                      className="min-h-[120px] w-full rounded-md border border-border bg-transparent px-3 py-2 text-sm placeholder:text-muted-foreground/60 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-primary"
                      required
                    />
                  </div>
                </div>
              )}

              {/* Attachments & logs */}
              <div className="p-4 rounded-lg bg-secondary/15 border border-border/80 space-y-3">
                <h4 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground flex items-center gap-1.5">
                  <FileCode className="h-4 w-4" /> Diagnosis Attachments
                </h4>
                
                <div className="flex flex-wrap gap-4 text-xs">
                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                    <span>Attach system performance logs</span>
                  </label>

                  <label className="flex items-center gap-2 cursor-pointer select-none">
                    <input type="checkbox" defaultChecked className="rounded border-border text-primary focus:ring-primary h-4 w-4" />
                    <span>Attach diagnostic checklist report</span>
                  </label>
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button variant="ghost" type="button">Cancel</Button>
                <Button variant="primary" type="submit" disabled={submitting}>
                  {submitting ? "Submitting Ticket..." : "Submit Feedback"}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      )}
    </div>
  );
};
export default FeedbackCenter;
