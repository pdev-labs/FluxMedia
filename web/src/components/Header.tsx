import React from "react";
import { Search, Bell, Download, Sun, Moon, Sparkles, User, Laptop } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { Button } from "./ui/Button";

interface HeaderProps {
  onMenuToggle: () => void;
  onCommandPaletteToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuToggle, onCommandPaletteToggle }) => {
  const { theme, setTheme } = useTheme();

  return (
    <header className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-border bg-background/95 px-4 backdrop-blur">
      <div className="flex items-center gap-3">
        <button
          onClick={onMenuToggle}
          className="rounded-md p-1.5 hover:bg-secondary lg:hidden"
          aria-label="Toggle Navigation Menu"
        >
          <span className="block h-5 w-5 border-y-2 border-current" />
        </button>
        
        <div className="flex items-center gap-2 font-bold tracking-tight">
          <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary text-primary-foreground">
            <Sparkles className="h-4 w-4" />
          </div>
          <span className="hidden sm:inline-block">FluxMedia</span>
          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold text-primary">Web</span>
        </div>
      </div>

      {/* Global Search and Shortcuts */}
      <div className="flex flex-1 items-center justify-center px-4 max-w-lg">
        <button
          onClick={onCommandPaletteToggle}
          className="flex h-9 w-full items-center justify-between rounded-md border border-border bg-secondary/50 px-3 text-xs text-muted-foreground hover:bg-secondary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary"
        >
          <span className="flex items-center gap-2">
            <Search className="h-3.5 w-3.5" />
            Search pages, commands...
          </span>
          <kbd className="hidden sm:inline-flex h-5 select-none items-center gap-0.5 rounded border border-border bg-background px-1.5 font-mono text-[10px] font-medium opacity-100">
            <span>Ctrl</span>+<span>K</span>
          </kbd>
        </button>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-1">
        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Quick Download">
          <Download className="h-4 w-4 text-muted-foreground hover:text-foreground" />
        </Button>
        <Button variant="ghost" size="icon" className="h-8 w-8" aria-label="Notifications">
          <Bell className="h-4 w-4 text-muted-foreground hover:text-foreground" />
        </Button>
        
        {/* Theme Switcher Toggle */}
        <Button
          variant="ghost"
          size="icon"
          className="h-8 w-8"
          onClick={() => {
            if (theme === "dark") setTheme("light");
            else if (theme === "light") setTheme("contrast");
            else setTheme("dark");
          }}
          aria-label="Toggle Theme"
        >
          {theme === "dark" && <Moon className="h-4 w-4 text-muted-foreground hover:text-foreground" />}
          {theme === "light" && <Sun className="h-4 w-4 text-muted-foreground hover:text-foreground" />}
          {theme === "contrast" && <Laptop className="h-4 w-4 text-muted-foreground hover:text-foreground" />}
        </Button>

        <span className="mx-1 h-4 w-[1px] bg-border" />

        <Button variant="ghost" size="icon" className="h-8 w-8 rounded-full bg-secondary">
          <User className="h-4 w-4 text-muted-foreground" />
        </Button>
      </div>
    </header>
  );
};
