import { useMemo, useState } from "react";
import {
  Alert,
  Avatar,
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Chip,
  Grid,
  TextField,
  Typography,
} from "@mui/material";
import VideocamIcon from "@mui/icons-material/Videocam";
import AudioFileIcon from "@mui/icons-material/AudioFile";
import ImageIcon from "@mui/icons-material/Image";
import DescriptionIcon from "@mui/icons-material/Description";
import { formatDuration, formatSize, thumbnailUrl } from "../api.ts";
import type { FileType, PortalFile } from "../api.ts";

const FILTERS: ("all" | FileType)[] = ["all", "video", "audio", "image", "document", "other"];

function TypeIcon({ type }: { type: FileType }): React.JSX.Element {
  if (type === "video") return <VideocamIcon />;
  if (type === "audio") return <AudioFileIcon />;
  if (type === "image") return <ImageIcon />;
  return <DescriptionIcon />;
}

export function FileBrowser({
  files,
  token,
  onOpen,
}: {
  files: PortalFile[];
  token: string;
  onOpen: (f: PortalFile) => void;
}): React.JSX.Element {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [query, setQuery] = useState("");

  const visible = useMemo(
    () =>
      files.filter(
        (f) =>
          (filter === "all" || f.type === filter) &&
          f.name.toLowerCase().includes(query.toLowerCase()),
      ),
    [files, filter, query],
  );

  return (
    <Box>
      <TextField
        fullWidth
        size="small"
        type="search"
        placeholder="Search files…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        sx={{ mb: 1.5 }}
      />
      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 2 }}>
        {FILTERS.map((f) => (
          <Chip
            key={f}
            label={f}
            clickable
            color={filter === f ? "primary" : "default"}
            variant={filter === f ? "filled" : "outlined"}
            onClick={() => setFilter(f)}
            sx={{ textTransform: "capitalize" }}
          />
        ))}
      </Box>
      {visible.length === 0 ? (
        <Alert severity="info">No files match.</Alert>
      ) : (
        <Grid container spacing={1.5}>
          {visible.map((f) => {
            const thumb = thumbnailUrl(f, token);
            const dur = formatDuration(f.duration);
            return (
              <Grid key={f.id} size={{ xs: 6, sm: 4, md: 3 }}>
                <Card sx={{ height: "100%" }}>
                  <CardActionArea onClick={() => onOpen(f)} sx={{ height: "100%" }}>
                    {thumb ? (
                      <CardMedia
                        component="img"
                        image={thumb}
                        alt=""
                        loading="lazy"
                        sx={{ aspectRatio: "16/10", objectFit: "cover" }}
                      />
                    ) : (
                      <Box
                        sx={{
                          aspectRatio: "16/10",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          bgcolor: "action.hover",
                        }}
                      >
                        <Avatar sx={{ bgcolor: "primary.main" }}>
                          <TypeIcon type={f.type} />
                        </Avatar>
                      </Box>
                    )}
                    <CardContent sx={{ p: 1.5 }}>
                      <Typography
                        variant="body2"
                        sx={{ fontWeight: 600 }}
                        noWrap
                        title={f.name}
                      >
                        {f.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {[dur, formatSize(f.size)].filter(Boolean).join(" · ")}
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}
