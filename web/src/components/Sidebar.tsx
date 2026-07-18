import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  Download,
  History,
  ListCollapse,
  FolderOpen,
  RefreshCw,
  Share2,
  Settings,
  ShieldAlert,
  Activity,
  Terminal,
  MessageSquare,
  HelpCircle,
  Info,
  ChevronLeft,
  ChevronRight
} from "lucide-react";
import { cn } from "../utils/cn";

interface SidebarProps {
  collapsed: boolean;
  onCollapseToggle: () => void;
  isOpenMobile: boolean;
  onCloseMobile: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  collapsed,
  onCollapseToggle,
  isOpenMobile,
  onCloseMobile
}) => {
  const menuItems = [
    { name: "Dashboard", path: "/", icon: LayoutDashboard },
    { name: "Downloads", path: "/downloads", icon: Download },
    { name: "History", path: "/history", icon: History },
    { name: "Queue", path: "/queue", icon: ListCollapse },
    { name: "Files", path: "/files", icon: FolderOpen },
    { name: "Converter", path: "/converter", icon: RefreshCw },
    { name: "Sharing", path: "/sharing", icon: Share2 },
    { name: "Settings", path: "/settings", icon: Settings },
    { name: "Updates", path: "/updates", icon: ShieldAlert },
    { name: "Diagnostics", path: "/diagnostics", icon: Activity },
    { name: "Logs", path: "/logs", icon: Terminal },
    { name: "Feedback", path: "/feedback", icon: MessageSquare },
    { name: "Help", path: "/help", icon: HelpCircle },
    { name: "About", path: "/about", icon: Info }
  ];

  const sidebarContent = (
    <div className="flex h-full flex-col justify-between bg-background border-r border-border py-4">
      <div className="space-y-4">
        {/* Navigation Items */}
        <nav className="space-y-1 px-3">
          {menuItems.map((item) => (
            <NavLink
              key={item.name}
              to={item.path}
              onClick={onCloseMobile}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors hover:bg-secondary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-primary",
                  isActive
                    ? "bg-secondary text-foreground"
                    : "text-muted-foreground hover:text-foreground",
                  collapsed && "justify-center px-0"
                )
              }
              title={collapsed ? item.name : undefined}
            >
              <item.icon className="h-4.5 w-4.5 shrink-0" />
              {!collapsed && <span>{item.name}</span>}
            </NavLink>
          ))}
        </nav>
      </div>

      {/* Collapse Toggle Button for Desktop */}
      <div className="hidden lg:flex justify-end px-3">
        <button
          onClick={onCollapseToggle}
          className="rounded-md border border-border p-1.5 hover:bg-secondary text-muted-foreground hover:text-foreground"
          aria-label={collapsed ? "Expand Sidebar" : "Collapse Sidebar"}
        >
          {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
        </button>
      </div>
    </div>
  );

  return (
    <>
      {/* Mobile Sidebar Overlay */}
      {isOpenMobile && (
        <div
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm lg:hidden"
          onClick={onCloseMobile}
        />
      )}

      {/* Mobile Drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 transform transition-transform duration-300 ease-in-out lg:hidden",
          isOpenMobile ? "translate-x-0" : "-translate-x-full"
        )}
      >
        {sidebarContent}
      </aside>

      {/* Desktop Sidebar */}
      <aside
        className={cn(
          "hidden h-[calc(100vh-3.5rem)] shrink-0 lg:block border-r border-border transition-all duration-300",
          collapsed ? "w-16" : "w-64"
        )}
      >
        {sidebarContent}
      </aside>
    </>
  );
};
