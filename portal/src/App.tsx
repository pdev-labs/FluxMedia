import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Alert,
  AppBar,
  Avatar,
  Box,
  CircularProgress,
  Container,
  IconButton,
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
import { buildTheme, toneMain } from "./theme.ts";
import {
  clearToken,
  getFiles,
  getMeta,
  getStoredToken,
} from "./api.ts";
import type { PortalFile, PortalMeta } from "./api.ts";
import { PasswordGate } from "./components/PasswordGate.tsx";
import { FileBrowser } from "./components/FileBrowser.tsx";
import { PlayerDialog } from "./components/PlayerDialog.tsx";

function ModeToggle(): React.JSX.Element {
  const { mode, setMode } = useColorScheme();
  if (!mode) return <></>;
  return (
    <Tooltip title={mode === "dark" ? "Light mode" : "Dark mode"}>
      <IconButton
        color="inherit"
        onClick={() => setMode(mode === "dark" ? "light" : "dark")}
        aria-label="Toggle color mode"
      >
        {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
      </IconButton>
    </Tooltip>
  );
}

function Shell(): React.JSX.Element {
  const [phase, setPhase] = useState<"loading" | "gate" | "ready">("loading");
  const [token, setToken] = useState("");
  const [meta, setMeta] = useState<PortalMeta | null>(null);
  const [files, setFiles] = useState<PortalFile[]>([]);
  const [error, setError] = useState("");
  const [current, setCurrent] = useState<PortalFile | null>(null);

  const enter = useCallback(async (tok: string, m: PortalMeta) => {
    setToken(tok);
    setMeta(m);
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
    () => buildTheme(toneMain(meta?.theme_tone)),
    [meta?.theme_tone],
  );

  function logout(): void {
    clearToken();
    setToken("");
    setFiles([]);
    setCurrent(null);
    setPhase("gate");
  }

  return (
    <ThemeProvider theme={theme} defaultMode="system">
      <CssBaseline />
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
                <Typography variant="subtitle1" sx={{ fontWeight: 700 }} noWrap>
                  {meta?.profile_name ?? "FluxMedia"} Share
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {files.length} {files.length === 1 ? "file" : "files"} · tap to stream
                </Typography>
              </Box>
              <ModeToggle />
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
            <FileBrowser files={files} token={token} onOpen={setCurrent} />
          </Container>
          <PlayerDialog
            file={current}
            token={token}
            onClose={() => setCurrent(null)}
          />
        </Box>
      )}
    </ThemeProvider>
  );
}

export default function App(): React.JSX.Element {
  return <Shell />;
}
