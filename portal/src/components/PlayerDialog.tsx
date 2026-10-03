import { forwardRef } from "react";
import {
  Avatar,
  Box,
  Button,
  Dialog,
  DialogContent,
  IconButton,
  Slide,
  Toolbar,
  Typography,
  useMediaQuery,
  useTheme,
} from "@mui/material";
import type { TransitionProps } from "@mui/material/transitions";
import CloseIcon from "@mui/icons-material/Close";
import DownloadIcon from "@mui/icons-material/Download";
import VideocamIcon from "@mui/icons-material/Videocam";
import AudioFileIcon from "@mui/icons-material/AudioFile";
import ImageIcon from "@mui/icons-material/Image";
import DescriptionIcon from "@mui/icons-material/Description";
import { fileUrl, formatSize, subtitlesUrl } from "../api.ts";
import type { FileType, PortalFile } from "../api.ts";

const SlideUp = forwardRef(function SlideUp(
  props: TransitionProps & { children: React.ReactElement },
  ref: React.Ref<unknown>,
) {
  return <Slide direction="up" ref={ref} {...props} />;
});

function TypeIcon({ type }: { type: FileType }): React.JSX.Element {
  if (type === "video") return <VideocamIcon fontSize="small" />;
  if (type === "audio") return <AudioFileIcon fontSize="small" />;
  if (type === "image") return <ImageIcon fontSize="small" />;
  return <DescriptionIcon fontSize="small" />;
}

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

  return (
    <Dialog
      open={file !== null}
      onClose={onClose}
      fullScreen={fullScreen}
      maxWidth="md"
      fullWidth
      slots={{ transition: SlideUp }}
    >
      <Toolbar sx={{ gap: 1.5, py: 0.5 }}>
        {file && (
          <Avatar sx={{ bgcolor: "primary.main", width: 36, height: 36 }}>
            <TypeIcon type={file.type} />
          </Avatar>
        )}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography variant="subtitle2" noWrap>
            {file?.name ?? ""}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {file ? formatSize(file.size) : ""}
          </Typography>
        </Box>
        <IconButton edge="end" onClick={onClose} aria-label="Close">
          <CloseIcon />
        </IconButton>
      </Toolbar>
      <DialogContent sx={{ p: file?.type === "audio" ? 3 : 0, pt: "0 !important" }}>
        {file?.type === "video" && (
          <Box
            component="video"
            controls
            playsInline
            autoPlay
            src={fileUrl(file.id, token)}
            sx={{ width: "100%", maxHeight: "70vh", background: "#000", display: "block" }}
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
        {file && (file.type === "video" || file.type === "document" || file.type === "other") && (
          <Box sx={{ p: 2, display: "flex", justifyContent: "flex-end" }}>
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
        {file && (file.type === "audio" || file.type === "image") && (
          <Box sx={{ pt: 2, display: "flex", justifyContent: "flex-end" }}>
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
