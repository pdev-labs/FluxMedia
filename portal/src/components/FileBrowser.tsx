import { useMemo, useState } from "react";
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Chip,
  Grid,
  Skeleton,
  TextField,
  Typography,
} from "@mui/material";
import VideocamIcon from "@mui/icons-material/Videocam";
import AudioFileIcon from "@mui/icons-material/AudioFile";
import ImageIcon from "@mui/icons-material/Image";
import DescriptionIcon from "@mui/icons-material/Description";
import FolderOffIcon from "@mui/icons-material/FolderOff";
import { formatDuration, formatSize, thumbnailUrl } from "../api.ts";
import type { FileType, PortalFile } from "../api.ts";

const FILTERS: ("all" | FileType)[] = ["all", "video", "audio", "image", "document", "other"];

function TypeIcon({ type }: { type: FileType }): React.JSX.Element {
  if (type === "video") return <VideocamIcon />;
  if (type === "audio") return <AudioFileIcon />;
  if (type === "image") return <ImageIcon />;
  return <DescriptionIcon />;
}

function LoadingGrid(): React.JSX.Element {
  return (
    <Grid container spacing={1.5}>
      {Array.from({ length: 6 }).map((_, i) => (
        <Grid key={i} size={{ xs: 6, sm: 4, md: 3 }}>
          <Skeleton variant="rounded" sx={{ aspectRatio: "16/10", borderRadius: 4 }} />
          <Skeleton width="80%" sx={{ mt: 1 }} />
          <Skeleton width="50%" />
        </Grid>
      ))}
    </Grid>
  );
}

export function FileBrowser({
  files,
  token,
  loading,
  onOpen,
}: {
  files: PortalFile[];
  token: string;
  loading: boolean;
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
        type="search"
        placeholder="Search this library…"
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
      {loading ? (
        <LoadingGrid />
      ) : visible.length === 0 ? (
        <Box
          sx={{
            py: 7,
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: 1,
            color: "text.secondary",
          }}
        >
          <FolderOffIcon sx={{ fontSize: 44, mb: 0.5 }} />
          <Typography variant="h6" color="text.primary">
            {files.length === 0 ? "Nothing shared yet" : "No matches"}
          </Typography>
          <Typography variant="body1" align="center" sx={{ maxWidth: 300 }}>
            {files.length === 0
              ? "Downloaded videos will appear here for streaming."
              : "Try a different search or filter."}
          </Typography>
        </Box>
      ) : (
        <Grid container spacing={1.5}>
          {visible.map((f) => {
            const thumb = thumbnailUrl(f, token);
            const dur = formatDuration(f.duration);
            return (
              <Grid key={f.id} size={{ xs: 6, sm: 4, md: 3 }}>
                <Card
                  sx={{
                    height: "100%",
                    transition: "transform 120ms ease, box-shadow 120ms ease",
                    "&:hover": { transform: "translateY(-2px)" },
                    "&:active": { transform: "translateY(0)" },
                  }}
                >
                  <CardActionArea onClick={() => onOpen(f)} sx={{ height: "100%" }}>
                    <Box sx={{ position: "relative" }}>
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
                          sx={(t) => ({
                            aspectRatio: "16/10",
                            display: "flex",
                            alignItems: "center",
                            justifyContent: "center",
                            bgcolor: `${t.palette.primary.main}14`,
                            color: "primary.main",
                            "& .MuiSvgIcon-root": { fontSize: 34 },
                          })}
                        >
                          <TypeIcon type={f.type} />
                        </Box>
                      )}
                      {dur && (
                        <Typography
                          variant="caption"
                          sx={{
                            fontWeight: 700,
                            position: "absolute",
                            right: 8,
                            bottom: 8,
                            bgcolor: "rgba(0,0,0,0.72)",
                            color: "#fff",
                            px: 1,
                            py: 0.25,
                            borderRadius: 1.5,
                          }}
                        >
                          {dur}
                        </Typography>
                      )}
                    </Box>
                    <CardContent sx={{ p: 1.5, "&:last-child": { pb: 1.5 } }}>
                      <Typography
                        variant="subtitle2"
                        title={f.name}
                        sx={{
                          display: "-webkit-box",
                          WebkitLineClamp: 2,
                          WebkitBoxOrient: "vertical",
                          overflow: "hidden",
                        }}
                      >
                        {f.name}
                      </Typography>
                      <Typography variant="body2" color="text.secondary" sx={{ mt: 0.25 }}>
                        {formatSize(f.size)}
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
