import React, { useState } from "react";
import { Terminal } from "lucide-react";
import { Card, CardHeader, CardTitle, CardContent } from "../components/ui/Card";
import { Button } from "../components/ui/Button";

export const DeveloperCenter: React.FC = () => {
  const [command, setCommand] = useState("");
  const [consoleOutput, setConsoleOutput] = useState<string[]>([
    "FluxMedia Developer Console v1.0.0",
    "Type 'help' to review internal API commands."
  ]);

  const handleExecute = (e: React.FormEvent) => {
    e.preventDefault();
    if (!command) return;

    let response = `Unknown command: '${command}'. Type 'help' for instructions.`;
    const cmdClean = command.trim().toLowerCase();

    if (cmdClean === "help") {
      response = "Available Commands:\n- config: Dump system environment configurations\n- state: Inspect memory parameters\n- clear: Clear terminal output console";
    } else if (cmdClean === "config") {
      response = "System Config:\n- python: v3.12.0\n- OS: Windows 11\n- RAM: 16GB total";
    } else if (cmdClean === "state") {
      response = "Active Threads: 3\nMemory Allocated: 148MB\nDisk Buffer Status: Writable";
    } else if (cmdClean === "clear") {
      setConsoleOutput([]);
      setCommand("");
      return;
    }

    setConsoleOutput((prev) => [...prev, `> ${command}`, response]);
    setCommand("");
  };

  return (
    <div className="flex flex-col gap-8 max-w-6xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Developer Console</h1>
        <p className="text-muted-foreground mt-1">Execute internal commands, inspect state parameters, and debug extractor channels.</p>
      </div>

      <div className="grid gap-6 lg:grid-cols-3 items-start">
        {/* Core console (Left 2 columns) */}
        <div className="lg:col-span-2 space-y-6">
          <Card className="bg-neutral-950 text-neutral-200 border-neutral-800">
            <CardHeader className="border-b border-neutral-900 pb-3">
              <CardTitle className="text-xs font-semibold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                <Terminal className="h-4 w-4 text-primary" /> Interactive Developer Console
              </CardTitle>
            </CardHeader>
            <CardContent className="p-4 font-mono text-xs leading-relaxed max-h-[300px] overflow-y-auto space-y-2 select-text">
              {consoleOutput.map((out, idx) => (
                <div key={idx} className="whitespace-pre-wrap">{out}</div>
              ))}
            </CardContent>
            <div className="p-3 border-t border-neutral-900 bg-neutral-900/30">
              <form onSubmit={handleExecute} className="flex gap-2">
                <input
                  type="text"
                  placeholder="Execute developer commands here..."
                  value={command}
                  onChange={(e) => setCommand(e.target.value)}
                  className="flex-1 bg-transparent px-3 py-1.5 text-xs font-mono outline-none border border-neutral-800 rounded-md focus:border-neutral-700 text-neutral-200"
                />
                <Button variant="primary" type="submit" size="sm">Run</Button>
              </form>
            </div>
          </Card>
        </div>

        {/* Info panel (Right column) */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Specifications</CardTitle>
            </CardHeader>
            <CardContent className="text-xs text-muted-foreground space-y-3 leading-relaxed">
              <p>Execute scripts to test media conversion channels directly using local libraries.</p>
              <div className="pt-2 border-t border-border/40">
                <Button variant="outline" className="w-full text-xs h-9">Dump Environment Variables</Button>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
};
export default DeveloperCenter;
