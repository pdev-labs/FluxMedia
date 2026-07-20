import React, { createContext, useContext, useEffect, useState, useMemo } from "react";
import { ThemeProvider as MuiThemeProvider, createTheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";

export type Theme = "dark" | "light" | "contrast";

interface ThemeContextType {
  theme: Theme;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const ThemeProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [theme, setThemeState] = useState<Theme>(() => {
    const saved = localStorage.getItem("flux-theme");
    return (saved as Theme) || "dark";
  });

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem("flux-theme", newTheme);
  };

  useEffect(() => {
    const root = window.document.documentElement;
    root.classList.remove("light", "dark", "contrast");
    
    if (theme === "contrast") {
      root.classList.add("dark", "contrast");
    } else {
      root.classList.add(theme);
    }
  }, [theme]);

  // Generate MUI Theme based on state
  const muiTheme = useMemo(() => createTheme({
    palette: {
      mode: theme === 'light' ? 'light' : 'dark',
      primary: {
        main: theme === 'light' ? '#6d28d9' : '#8b5cf6', // Deep purple
      },
      secondary: {
        main: theme === 'light' ? '#475569' : '#94a3b8',
      },
      background: {
        default: theme === 'light' ? '#ffffff' : '#0a0a0a',
        paper: theme === 'light' ? '#f8f8f8' : '#121212',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Inter", "Helvetica", "Arial", sans-serif',
    },
    shape: {
      borderRadius: 12,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: '100px', // MD3 pill buttons
            padding: '8px 24px',
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: '16px',
            boxShadow: 'none',
            border: theme === 'light' ? '1px solid #e2e8f0' : '1px solid #27272a',
          }
        }
      }
    }
  }), [theme]);

  return (
    <ThemeContext.Provider value={{ theme, setTheme }}>
      <MuiThemeProvider theme={muiTheme}>
        <CssBaseline />
        {children}
      </MuiThemeProvider>
    </ThemeContext.Provider>
  );
};

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) {
    throw new Error("useTheme must be used within a ThemeProvider");
  }
  return context;
};
