import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { 
  Sparkles, ArrowRight, FolderOpen, Palette, ShieldCheck
} from "lucide-react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";
import { Input } from "../components/ui/Input";

export const OnboardingWizard: React.FC = () => {
  const [step, setStep] = useState(0);
  const navigate = useNavigate();

  return (
    <div className="flex items-center justify-center min-h-[calc(100vh-10rem)] animate-in fade-in zoom-in-95 duration-200">
      <Card className="w-full max-w-lg shadow-2xl border border-border/80">
        <CardHeader className="text-center pb-3 border-b border-border/40 bg-secondary/15">
          <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-lg bg-primary text-primary-foreground mb-3">
            <Sparkles className="h-5 w-5" />
          </div>
          <CardTitle className="text-xl">FluxMedia Onboarding</CardTitle>
          <CardDescription>Configure your core media environment parameters in three steps.</CardDescription>
        </CardHeader>
        <CardContent className="pt-6 text-xs leading-relaxed space-y-6">
          {step === 0 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold text-center">Step 1: Welcome to FluxMedia Web</h3>
              <p className="text-muted-foreground text-center">FluxMedia provides high-performance video extraction and transcoding capabilities powered by local yt-dlp and FFmpeg binaries.</p>
              <div className="flex justify-end pt-4">
                <Button variant="primary" className="gap-1" onClick={() => setStep(1)}>
                  Next Step <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {step === 1 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold flex items-center gap-1.5"><Palette className="h-4 w-4 text-primary" /> Step 2: Choose Interface Aesthetics</h3>
              <div className="grid gap-3 sm:grid-cols-2">
                <div className="border border-border/80 hover:border-primary p-3 rounded-lg cursor-pointer bg-neutral-900 text-neutral-200">
                  <h4 className="font-semibold text-xs">Dark Mode</h4>
                  <p className="text-[10px] text-neutral-400 mt-1">Midnight dark aesthetic.</p>
                </div>
                <div className="border border-border/80 hover:border-primary p-3 rounded-lg cursor-pointer bg-white text-neutral-900">
                  <h4 className="font-semibold text-xs">Light Mode</h4>
                  <p className="text-[10px] text-neutral-600 mt-1">Alabaster light theme.</p>
                </div>
              </div>
              <div className="flex justify-between pt-4 border-t border-border/40">
                <Button variant="outline" onClick={() => setStep(0)}>Back</Button>
                <Button variant="primary" className="gap-1" onClick={() => setStep(2)}>
                  Next Step <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
            </div>
          )}

          {step === 2 && (
            <div className="space-y-4">
              <h3 className="text-sm font-semibold flex items-center gap-1.5"><FolderOpen className="h-4 w-4 text-primary" /> Step 3: Default Output Directory</h3>
              <Input label="Download Save Folder" defaultValue="D:\Downloads\FluxMedia" />
              <div className="flex justify-between pt-4 border-t border-border/40">
                <Button variant="outline" onClick={() => setStep(1)}>Back</Button>
                <Button variant="primary" className="gap-1.5" onClick={() => navigate("/")}>
                  <ShieldCheck className="h-4 w-4" /> Finish Setup
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
export default OnboardingWizard;
