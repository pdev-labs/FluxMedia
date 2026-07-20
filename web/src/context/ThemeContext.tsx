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
        main: theme === 'light' ? '#4f46e5' : '#6366f1', // Vibrant indigo
      },
      secondary: {
        main: theme === 'light' ? '#3b82f6' : '#60a5fa', // Bright blue
      },
      background: {
        default: theme === 'light' ? '#f8fafc' : '#020617', // Slate backgrounds
        paper: theme === 'light' ? '#ffffff' : '#0f172a',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Inter", "Helvetica", "Arial", sans-serif',
    },
    shape: {
      borderRadius: 16,
    },
    components: {
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            borderRadius: '100px', // MD3 pill buttons
            padding: '8px 24px',
            fontWeight: 600,
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: '20px',
            boxShadow: theme === 'light' 
              ? '0 4px 6px -1px rgb(0 0 0 / 0.05), 0 2px 4px -2px rgb(0 0 0 / 0.05)' 
              : '0 4px 6px -1px rgb(0 0 0 / 0.2), 0 2px 4px -2px rgb(0 0 0 / 0.2)',
            border: theme === 'light' ? '1px solid rgba(226, 232, 240, 0.8)' : '1px solid rgba(51, 65, 85, 0.5)',
            backgroundImage: 'none',
            backdropFilter: 'blur(8px)',
            backgroundColor: theme === 'light' ? 'rgba(255, 255, 255, 0.9)' : 'rgba(15, 23, 42, 0.85)',
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
