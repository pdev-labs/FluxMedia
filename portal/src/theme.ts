import { createTheme } from "@mui/material/styles";

/** Server theme_tone values mapped to primary hues. */
const TONES: Record<string, string> = {
  "Sunset Orange": "#e8590c",
  "Royal Purple": "#7c3aed",
  "Ocean Blue": "#1971c2",
  "Forest Green": "#2f9e44",
  "Crimson Red": "#d90429",
  "Golden Yellow": "#f08c00",
};

export function toneMain(tone: string | undefined): string {
  if (!tone) return "#d90429";
  return TONES[tone] ?? "#d90429";
}

/**
 * Single createTheme call (per skill: one options object, no multi-arg
 * merging). colorSchemes drive light/dark via useColorScheme elsewhere;
 * no top-level palette so it cannot shadow the schemes.
 */
export function buildTheme(primaryMain: string) {
  return createTheme({
    cssVariables: true,
    colorSchemes: {
      light: {
        palette: {
          primary: { main: primaryMain },
          background: { default: "#f6f6f7", paper: "#ffffff" },
        },
      },
      dark: {
        palette: {
          primary: { main: primaryMain },
          background: { default: "#09090e", paper: "#101016" },
        },
      },
    },
    typography: {
      fontFamily:
        'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif',
    },
    shape: { borderRadius: 12 },
    components: {
      MuiButton: { defaultProps: { disableElevation: true } },
      MuiCard: {
        styleOverrides: {
          root: ({ theme }) => ({
            border: `1px solid ${theme.palette.divider}`,
          }),
        },
      },
    },
  });
}
