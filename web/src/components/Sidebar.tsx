import React from "react";
import { NavLink } from "react-router-dom";
import {
  LayoutDashboard, Download, History, ListCollapse, FolderOpen, RefreshCw,
  Share2, Settings, ShieldAlert, Terminal, MessageSquare, HelpCircle,
  Info, ChevronLeft, ChevronRight, BarChart4
} from "lucide-react";
import { 
  Drawer, List, ListItem, ListItemButton, ListItemIcon, ListItemText, 
  IconButton, Box, useTheme, useMediaQuery
} from "@mui/material";

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
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('lg'));

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
    { name: "Analytics", path: "/stats", icon: BarChart4 },
    { name: "Logs", path: "/logs", icon: Terminal },
    { name: "Feedback", path: "/feedback", icon: MessageSquare },
    { name: "Help", path: "/help", icon: HelpCircle },
    { name: "About", path: "/about", icon: Info }
  ];

  const sidebarContent = (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between', py: 2 }}>
      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.name} disablePadding sx={{ mb: 0.5 }}>
            <ListItemButton
              component={NavLink}
              to={item.path}
              onClick={isMobile ? onCloseMobile : undefined}
              sx={{
                borderRadius: 2,
                minHeight: 44,
                justifyContent: collapsed && !isMobile ? 'center' : 'initial',
                px: 2.5,
                '&.active': {
                  bgcolor: 'action.selected',
                  color: 'primary.main',
                  '& .MuiListItemIcon-root': {
                    color: 'primary.main',
                  }
                }
              }}
              title={collapsed && !isMobile ? item.name : undefined}
            >
              <ListItemIcon
                sx={{
                  minWidth: 0,
                  mr: collapsed && !isMobile ? 0 : 2,
                  justifyContent: 'center',
                }}
              >
                <item.icon className="h-5 w-5" />
              </ListItemIcon>
              {(!collapsed || isMobile) && <ListItemText primary={item.name} primaryTypographyProps={{ fontSize: 14, fontWeight: 500 }} />}
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      {!isMobile && (
        <Box sx={{ display: 'flex', justifyContent: 'flex-end', px: 2 }}>
          <IconButton onClick={onCollapseToggle} size="small" sx={{ border: 1, borderColor: 'divider' }}>
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </IconButton>
        </Box>
      )}
    </Box>
  );

  return (
    <>
      {/* Mobile Drawer */}
      <Drawer
        variant="temporary"
        open={isOpenMobile}
        onClose={onCloseMobile}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: 'block', lg: 'none' },
          '& .MuiDrawer-paper': { boxSizing: 'border-box', width: 256 },
        }}
      >
        {sidebarContent}
      </Drawer>

      {/* Desktop Sidebar Container (mimics the layout) */}
      <Box
        component="aside"
        sx={{
          display: { xs: 'none', lg: 'block' },
          width: collapsed ? 72 : 256,
          flexShrink: 0,
          borderRight: 1,
          borderColor: 'divider',
          transition: theme.transitions.create('width', {
            easing: theme.transitions.easing.sharp,
            duration: theme.transitions.duration.enteringScreen,
          }),
          bgcolor: 'background.paper'
        }}
      >
        {sidebarContent}
      </Box>
    </>
  );
};
