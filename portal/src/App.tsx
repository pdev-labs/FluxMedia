import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  AppBar,
  Avatar,
  Box,
  CircularProgress,
  Container,
  IconButton,
  ListItemText,
  Menu,
  MenuItem,
  Toolbar,
  Tooltip,
  Typography,
} from "@mui/material";
import { ThemeProvider } from "@mui/material/styles";
import { useColorScheme } from "@mui/material/styles";
import CssBaseline from "@mui/material/CssBaseline";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import LogoutIcon from "@mui/icons-material/Logout";
import PaletteIcon from "@mui/icons-material/Palette";
import CheckIcon from "@mui/icons-material/Check";
import { buildTheme, toneMain } from "./theme.ts";
import {
  clearToken,
  getFiles,
  getMeta,
  getStoredToken,
} from "./api.ts";
import type { PortalFile, PortalMeta } from "./api.ts";
import { loadPrefs, savePrefs } from "./prefs.ts";
import { PasswordGate } from "./components/PasswordGate.tsx";
import { FileBrowser } from "./components/FileBrowser.tsx";
import { AccentDialog } from "./components/AccentDialog.tsx";

function ModeToggle(): React.JSX.Element {  const { mode, setMode } = useColorScheme();
  const [anchor, setAnchor] = useState<HTMLElement | null>(null);
  const current = mode ?? "system";
  return (
    <>
      <Tooltip title="Appearance">
        <IconButton
          color="inherit"
          onClick={(e) => setAnchor(e.currentTarget)}
          aria-label="Appearance"
        >
          {current === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
        </IconButton>
      </Tooltip>
      <Menu anchorEl={anchor} open={anchor !== null} onClose={() => setAnchor(null)}>
        {(["light", "system", "dark"] as const).map((m) => (
          <MenuItem
            key={m}
            selected={current === m}
            onClick={() => {
              setMode(m);
              setAnchor(null);
            }}
          >
            <ListItemText sx={{ textTransform: "capitalize" }}>{m}</ListItemText>
            {current === m && <CheckIcon fontSize="small" />}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

function Shell(): React.JSX.Element {
  const [phase, setPhase] = useState<"loading" | "gate" | "ready">("loading");
  const [token, setToken] = useState("");
  const [meta, setMeta] = useState<PortalMeta | null>(null);
  const [files, setFiles] = useState<PortalFile[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [accent, setAccent] = useState<string | null>(() => loadPrefs().accent);
  const [accentOpen, setAccentOpen] = useState(false);
  const [error, setError] = useState("");

  const enter = useCallback(async (tok: string, m: PortalMeta) => {
    setToken(tok);
    setMeta(m);
    setLoadingFiles(true);
    try {
      setFiles(await getFiles(tok));
      setPhase("ready");
    } catch (err) {
      if (err instanceof Error && err.message === "unauthorized") {
        clearToken();
        setPhase("gate");
      } else {
        setError(err instanceof Error ? err.message : "Could not load files.");
        setPhase("ready");
      }
    } finally {
      setLoadingFiles(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const m = await getMeta();
        if (cancelled) return;
        if (!m.password_protected) {
          await enter("", m);
          return;
        }
        const stored = getStoredToken();
        if (stored) {
          await enter(stored, m);
        } else {
          setMeta(m);
          setPhase("gate");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Server unreachable.");
          setPhase("gate");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [enter]);

  const theme = useMemo(
    () => buildTheme(accent ?? toneMain(meta?.theme_tone)),
    [accent, meta?.theme_tone],
  );

  function pickAccent(hex: string | null): void {
    setAccent(hex);
    savePrefs({ ...loadPrefs(), accent: hex });
  }

  function logout(): void {
    clearToken();
    setToken("");
    setFiles([]);
    setPhase("gate");
  }

  return (
    <ThemeProvider theme={theme} defaultMode="light">
      <CssBaseline enableColorScheme />
      {phase === "loading" && (
        <Box
          sx={{
            minHeight: "100dvh",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <CircularProgress />
        </Box>
      )}
      {phase === "gate" && (
        <PasswordGate
          profileName={meta?.profile_name ?? "Shared"}
          onAuthed={(tok) => {
            if (meta) void enter(tok, meta);
          }}
        />
      )}
      {phase === "ready" && (
        <Box>
          <AppBar position="sticky" color="default" elevation={0}>
            <Toolbar>
              {meta?.profile_image_url ? (
                <Avatar src="/profile_photo" sx={{ mr: 1.5 }} />
              ) : (
                <Avatar sx={{ mr: 1.5, bgcolor: "primary.main" }}>
                  {(meta?.profile_name ?? "F").slice(0, 1)}
                </Avatar>
              )}
              <Box sx={{ flex: 1, minWidth: 0 }}>
                <Typography variant="h6" noWrap>
                  {meta?.profile_name ?? "FluxMedia"} Share
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {files.length} {files.length === 1 ? "file" : "files"} · tap to stream
                </Typography>
              </Box>
              <ModeToggle />
              <Tooltip title="Customize accent">
                <IconButton
                  color="inherit"
                  onClick={() => setAccentOpen(true)}
                  aria-label="Customize accent"
                >
                  <PaletteIcon />
                </IconButton>
              </Tooltip>
              <AccentDialog
                open={accentOpen}
                serverTone={meta?.theme_tone}
                current={accent}
                onPick={pickAccent}
                onClose={() => setAccentOpen(false)}
              />
              {meta?.password_protected && (
                <Tooltip title="Lock">
                  <IconButton color="inherit" onClick={logout} aria-label="Lock">
                    <LogoutIcon />
                  </IconButton>
                </Tooltip>
              )}
            </Toolbar>
          </AppBar>
          <Container maxWidth="md" sx={{ py: 2, pb: 6 }}>
            {error && (
              <Alert severity="warning" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            <FileBrowser files={files} token={token} loading={loadingFiles} />
          </Container>
        </Box>
      )}
    </ThemeProvider>
  );
}

export default function App(): React.JSX.Element {
  return <Shell />;
}
