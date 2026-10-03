import {
  AppBar,
  Box,
  Button,
  Dialog,
  DialogContent,
  IconButton,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import DownloadIcon from "@mui/icons-material/Download";
import { fileUrl, formatSize, subtitlesUrl } from "../api.ts";
import type { PortalFile } from "../api.ts";

export function PlayerDialog({
  file,
  token,
  onClose,
}: {
  file: PortalFile | null;
  token: string;
  onClose: () => void;
}): React.JSX.Element {
  const theme = useTheme();
  const fullScreen = useMediaQuery(theme.breakpoints.down("sm"));
  const open = file !== null;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
    >
      <AppBar position="relative" color="default" elevation={0}>
        <Toolbar>
          <Typography variant="subtitle1" noWrap sx={{ flex: 1 }}>
            {file?.name ?? ""}
          </Typography>
          <IconButton edge="end" onClick={onClose} aria-label="Close">
            <CloseIcon />
          </IconButton>
        </Toolbar>
      </AppBar>
      <DialogContent sx={{ p: file?.type === "audio" ? 3 : 0 }}>
        {file?.type === "video" && (
          <Box
            component="video"
            controls
            playsInline
            autoPlay
            src={fileUrl(file.id, token)}
            sx={{ width: "100%", maxHeight: "70vh", background: "#000" }}
          >
            <track
              kind="subtitles"
              srcLang="en"
              label="Subtitles"
              src={subtitlesUrl(file.id, token)}
            />
          </Box>
        )}
        {file?.type === "audio" && (
          <Box
            component="audio"
            controls
            autoPlay
            src={file ? fileUrl(file.id, token) : ""}
            sx={{ width: "100%" }}
          />
        )}
        {file?.type === "image" && (
          <Box
            component="img"
            src={file ? fileUrl(file.id, token) : ""}
            alt={file?.name ?? ""}
            sx={{ width: "100%", display: "block" }}
          />
        )}
        {file && (
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 2,
              p: file.type === "audio" || file.type === "image" ? 0 : 2,
              pt: file.type === "video" || file.type === "document" || file.type === "other" ? 2 : 0,
            }}
          >
            <Typography variant="body2" color="text.secondary" sx={{ flex: 1 }}>
              {formatSize(file.size)}
            </Typography>
            <Button
              variant="contained"
              startIcon={<DownloadIcon />}
              href={fileUrl(file.id, token)}
              download={file.name}
            >
              Download
            </Button>
          </Box>
        )}
      </DialogContent>
    </Dialog>
  );
}
