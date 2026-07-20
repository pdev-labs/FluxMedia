import React from "react";
import { Search, Bell, Download, Sun, Moon, Sparkles, User, Laptop } from "lucide-react";
import { useTheme } from "../context/ThemeContext";
import { AppBar, Toolbar, IconButton, Box, Typography } from "@mui/material";

interface HeaderProps {
  onMenuToggle: () => void;
  onCommandPaletteToggle: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onMenuToggle, onCommandPaletteToggle }) => {
  const { theme, setTheme } = useTheme();

  return (
    <AppBar 
      position="sticky" 
      color="inherit" 
      elevation={0} 
      sx={{ 
        borderBottom: 1, 
        borderColor: 'divider', 
        bgcolor: theme === 'light' ? 'rgba(255, 255, 255, 0.7)' : 'rgba(15, 23, 42, 0.7)',
        backdropFilter: 'blur(12px)',
        backgroundImage: 'none',
      }}
    >
      <Toolbar variant="dense" sx={{ minHeight: 56, gap: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="Toggle Navigation Menu"
            onClick={onMenuToggle}
            sx={{ display: { lg: 'none' } }}
          >
            <span className="block h-5 w-5 border-y-2 border-current" />
          </IconButton>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, fontWeight: 'bold' }}>
            <Box sx={{ display: 'flex', height: 28, width: 28, alignItems: 'center', justifyContent: 'center', borderRadius: 2, bgcolor: 'primary.main', color: 'primary.contrastText' }}>
              <Sparkles className="h-4 w-4" />
            </Box>
            <Typography variant="subtitle1" fontWeight="bold" sx={{ display: { xs: 'none', sm: 'block' }, lineHeight: 1 }}>
              FluxMedia
            </Typography>
            <Box sx={{ borderRadius: 4, bgcolor: 'primary.light', color: 'primary.dark', px: 1, py: 0.25, fontSize: '0.625rem', fontWeight: 'bold', display: { xs: 'none', sm: 'block' } }}>
              Web
            </Box>
          </Box>
        </Box>

        {/* Global Search and Shortcuts */}
        <Box sx={{ flex: 1, display: 'flex', justifyContent: 'center', px: 2 }}>
          <Box
            component="button"
            onClick={onCommandPaletteToggle}
            sx={{
              display: 'flex', height: 36, width: '100%', maxWidth: 400, alignItems: 'center', justifyContent: 'space-between',
              borderRadius: 1.5, border: 1, borderColor: 'divider', bgcolor: 'action.hover', px: 1.5,
              typography: 'caption', color: 'text.secondary', cursor: 'pointer',
              '&:hover': { bgcolor: 'action.selected' }
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Search className="h-4 w-4" />
              Search pages, commands...
            </Box>
            <Box sx={{ display: { xs: 'none', sm: 'flex' }, height: 20, alignItems: 'center', gap: 0.5, borderRadius: 1, border: 1, borderColor: 'divider', bgcolor: 'background.default', px: 0.5, fontFamily: 'monospace', fontSize: '0.625rem', fontWeight: 'medium' }}>
              <span>Ctrl</span>+<span>K</span>
            </Box>
          </Box>
        </Box>

        {/* Action Buttons */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
          <IconButton size="small" aria-label="Quick Download">
            <Download className="h-4 w-4" />
          </IconButton>
          <IconButton size="small" aria-label="Notifications">
            <Bell className="h-4 w-4" />
          </IconButton>
          
          <IconButton
            size="small"
            onClick={() => {
              if (theme === "dark") setTheme("light");
              else if (theme === "light") setTheme("contrast");
              else setTheme("dark");
            }}
            aria-label="Toggle Theme"
          >
            {theme === "dark" && <Moon className="h-4 w-4" />}
            {theme === "light" && <Sun className="h-4 w-4" />}
            {theme === "contrast" && <Laptop className="h-4 w-4" />}
          </IconButton>

          <Box sx={{ mx: 0.5, height: 16, width: 1, bgcolor: 'divider' }} />

          <IconButton size="small" sx={{ bgcolor: 'action.selected' }}>
            <User className="h-4 w-4" />
          </IconButton>
        </Box>
      </Toolbar>
    </AppBar>
  );
};
