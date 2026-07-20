import React, { useEffect, useState } from "react";
import { Header } from "../components/Header";
import { Sidebar } from "../components/Sidebar";
import { Footer } from "../components/Footer";
import { CommandPalette } from "../components/CommandPalette";
import { SyncPlayer } from "../components/SyncPlayer";

interface GlobalLayoutProps {
  children: React.ReactNode;
}

export const GlobalLayout: React.FC<GlobalLayoutProps> = ({ children }) => {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    return localStorage.getItem("flux-sidebar-collapsed") === "true";
  });
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => {
      const next = !prev;
      localStorage.setItem("flux-sidebar-collapsed", String(next));
      return next;
    });
  };

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key === "k") {
        e.preventDefault();
        setCommandPaletteOpen((prev) => !prev);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <div className="flex h-screen w-screen flex-col overflow-hidden bg-background text-foreground font-sans bg-gradient-to-br from-background via-background to-primary/5">
      {/* Top Header */}
      <Header
        onMenuToggle={() => setMobileMenuOpen(true)}
        onCommandPaletteToggle={() => setCommandPaletteOpen(true)}
      />

      {/* Center Layout Shell */}
      <div className="flex flex-1 overflow-hidden">
        {/* Navigation Sidebar */}
        <Sidebar
          collapsed={sidebarCollapsed}
          onCollapseToggle={toggleSidebar}
          isOpenMobile={mobileMenuOpen}
          onCloseMobile={() => setMobileMenuOpen(false)}
        />

        {/* Core Main Viewport */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 md:p-8 relative">
          {children}
        </main>
      </div>

      {/* Bottom Footer Status Bar */}
      <Footer />

      {/* Global Command Palette overlay */}
      <CommandPalette
        isOpen={commandPaletteOpen}
        onClose={() => setCommandPaletteOpen(false)}
      />
      <SyncPlayer />
    </div>
  );
};
