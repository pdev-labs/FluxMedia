import { useState } from "react";
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  CircularProgress,
  TextField,
  Typography,
} from "@mui/material";
import LockOutlinedIcon from "@mui/icons-material/LockOutlined";
import { postAuth, storeToken } from "../api.ts";

export function PasswordGate({
  profileName,
  onAuthed,
}: {
  profileName: string;
  onAuthed: (token: string) => void;
}): React.JSX.Element {
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  async function submit(e: React.FormEvent): Promise<void> {
    e.preventDefault();
    if (!password || busy) return;
    setBusy(true);
    setError("");
    try {
      const token = await postAuth(password);
      storeToken(token);
      onAuthed(token);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Box
      sx={{
        minHeight: "100dvh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        p: 2,
      }}
    >
      <Card sx={{ width: "100%", maxWidth: 380 }}>
        <CardContent sx={{ p: 3 }}>
          <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 1 }}>
            <LockOutlinedIcon color="primary" />
            <Typography variant="h6" component="h1">
              FluxMedia Share
            </Typography>
          </Box>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {profileName}'s library is password protected.
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Box component="form" onSubmit={submit}>
            <TextField
              fullWidth
              type="password"
              label="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              autoFocus
              sx={{ mb: 2 }}
            />
            <Button
              fullWidth
              variant="contained"
              type="submit"
              disabled={busy || !password}
              startIcon={busy ? <CircularProgress size={18} /> : undefined}
            >
              {busy ? "Checking…" : "Unlock"}
            </Button>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
}
