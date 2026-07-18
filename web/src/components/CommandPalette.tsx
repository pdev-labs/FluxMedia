import React, { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Terminal, Search, Settings, ShieldAlert, Activity, LayoutDashboard, Share2, HelpCircle } from "lucide-react";
import { useTheme } from "../context/ThemeContext";

interface CommandPaletteProps {
  isOpen: boolean;
  onClose: () => void;
}

export const CommandPalette: React.FC<CommandPaletteProps> = ({ isOpen, onClose }) => {
  const navigate = useNavigate();
  const { setTheme } = useTheme();
  const [search, setSearch] = useState("");
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);

  const commands = [
    { name: "Go to Dashboard", category: "Navigation", icon: LayoutDashboard, action: () => navigate("/") },
    { name: "Go to Settings", category: "Navigation", icon: Settings, action: () => navigate("/settings") },
    { name: "Go to Updates", category: "Navigation", icon: ShieldAlert, action: () => navigate("/updates") },
    { name: "Go to Sharing Gateway", category: "Navigation", icon: Share2, action: () => navigate("/sharing") },
    { name: "Run Diagnostics", category: "System", icon: Activity, action: () => navigate("/diagnostics") },
    { name: "View System Help", category: "System", icon: HelpCircle, action: () => navigate("/help") },
    { name: "Switch to Dark Mode", category: "Appearance", icon: Terminal, action: () => setTheme("dark") },
    { name: "Switch to Light Mode", category: "Appearance", icon: Terminal, action: () => setTheme("light") },
    { name: "Switch to High Contrast Mode", category: "Appearance", icon: Terminal, action: () => setTheme("contrast") }
  ];

  const filteredCommands = commands.filter((cmd) =>
    cmd.name.toLowerCase().includes(search.toLowerCase()) ||
    cmd.category.toLowerCase().includes(search.toLowerCase())
  );

  useEffect(() => {
    if (isOpen) {
      setSearch("");
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [isOpen]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      } else if (e.key === "ArrowDown") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev + 1) % filteredCommands.length);
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        setSelectedIndex((prev) => (prev - 1 + filteredCommands.length) % filteredCommands.length);
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (filteredCommands[selectedIndex]) {
          filteredCommands[selectedIndex].action();
          onClose();
        }
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [isOpen, selectedIndex, filteredCommands, onClose]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh] px-4">
      {/* Overlay backdrop */}
      <div className="fixed inset-0 bg-background/80 backdrop-blur-sm" onClick={onClose} />
      
      {/* Palette dialog */}
      <div className="z-50 w-full max-w-lg overflow-hidden rounded-xl border border-border bg-card shadow-2xl animate-in fade-in zoom-in-95 duration-100">
        {/* Input area */}
        <div className="flex items-center border-b border-border px-3.5">
          <Search className="h-4 w-4 shrink-0 text-muted-foreground" />
          <input
            ref={inputRef}
            type="text"
            placeholder="Type a command or search..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setSelectedIndex(0);
            }}
            className="flex h-12 w-full bg-transparent px-3 py-3 text-sm outline-none placeholder:text-muted-foreground/60 disabled:cursor-not-allowed disabled:opacity-50"
          />
        </div>

        {/* Results Area */}
        <div className="max-h-[300px] overflow-y-auto p-2">
          {filteredCommands.length === 0 ? (
            <div className="py-6 text-center text-sm text-muted-foreground">No commands found.</div>
          ) : (
            filteredCommands.map((cmd, idx) => (
              <button
                key={cmd.name}
                onClick={() => {
                  cmd.action();
                  onClose();
                }}
                className={`flex w-full items-center justify-between rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                  idx === selectedIndex
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:bg-secondary/40 hover:text-foreground"
                }`}
              >
                <div className="flex items-center gap-3">
                  <cmd.icon className="h-4 w-4 shrink-0" />
                  <span>{cmd.name}</span>
                </div>
                <span className="text-[10px] font-semibold uppercase tracking-wider text-muted-foreground/50">
                  {cmd.category}
                </span>
              </button>
            ))
          )}
        </div>
      </div>
    </div>
  );
};
