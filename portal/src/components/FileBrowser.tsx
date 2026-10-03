import { useMemo, useState } from "react";
import {
  Box,
  Card,
  CardActionArea,
  CardContent,
  CardMedia,
  Chip,
  FormControl,
  Grid,
  InputLabel,
  List,
  ListItem,
  ListItemButton,
  ListItemText,
  MenuItem,
  Select,
  Skeleton,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Typography,
} from "@mui/material";
import VideocamIcon from "@mui/icons-material/Videocam";
import AudioFileIcon from "@mui/icons-material/AudioFile";
import ImageIcon from "@mui/icons-material/Image";
import DescriptionIcon from "@mui/icons-material/Description";
import FolderOffIcon from "@mui/icons-material/FolderOff";
import GridViewIcon from "@mui/icons-material/GridView";
import ViewListIcon from "@mui/icons-material/ViewList";
import { formatDuration, formatSize, thumbnailUrl } from "../api.ts";
import type { FileType, PortalFile } from "../api.ts";
import { PlayerDialog } from "./PlayerDialog.tsx";
import { loadPrefs, savePrefs } from "../prefs.ts";
import type { SortKey, ViewMode } from "../prefs.ts";

const FILTERS: ("all" | FileType)[] = ["all", "video", "audio", "image", "document", "other"];

function TypeIcon({ type }: { type: FileType }): React.JSX.Element {
  if (type === "video") return <VideocamIcon />;
  if (type === "audio") return <AudioFileIcon />;
  if (type === "image") return <ImageIcon />;
  return <DescriptionIcon />;
}

function formatDate(iso: string): string {
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "";
  return d.toLocaleDateString(undefined, { month: "short", day: "numeric" });
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
}: {
  files: PortalFile[];
  token: string;
  loading: boolean;
}): React.JSX.Element {
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [query, setQuery] = useState("");
  const [sort, setSort] = useState<SortKey>(() => loadPrefs().sort);
  const [view, setView] = useState<ViewMode>(() => loadPrefs().view);
  const [selectedId, setSelectedId] = useState<string | null>(null);

  function persistSort(s: SortKey): void {
    setSort(s);
    savePrefs({ ...loadPrefs(), sort: s });
  }

  function persistView(v: ViewMode): void {
    setView(v);
    savePrefs({ ...loadPrefs(), view: v });
  }

  const visible = useMemo(() => {
    const list = files.filter(
      (f) =>
        (filter === "all" || f.type === filter) &&
        f.name.toLowerCase().includes(query.toLowerCase()),
    );
    const sorted = [...list];
    if (sort === "name") sorted.sort((a, b) => a.name.localeCompare(b.name));
    else if (sort === "size") sorted.sort((a, b) => b.size - a.size);
    return sorted;
  }, [files, filter, query, sort]);

  const selIdx = visible.findIndex((f) => f.id === selectedId);
  const current = selIdx >= 0 ? visible[selIdx] : null;

  function step(dir: 1 | -1): void {
    const next = selIdx + dir;
    if (next >= 0 && next < visible.length) setSelectedId(visible[next].id);
  }

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
      <Box sx={{ display: "flex", gap: 1, flexWrap: "wrap", mb: 1.5 }}>
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
      <Box sx={{ display: "flex", gap: 1.5, mb: 2, alignItems: "center" }}>
        <FormControl size="small" sx={{ minWidth: 130 }}>
          <InputLabel id="sort-label">Sort</InputLabel>
          <Select
            labelId="sort-label"
            label="Sort"
            value={sort}
            onChange={(e) => persistSort(e.target.value as SortKey)}
          >
            <MenuItem value="newest">Newest</MenuItem>
            <MenuItem value="name">Name</MenuItem>
            <MenuItem value="size">Largest</MenuItem>
          </Select>
        </FormControl>
        <Box sx={{ flex: 1 }} />
        <ToggleButtonGroup
          size="small"
          exclusive
          value={view}
          onChange={(_, v: ViewMode | null) => v && persistView(v)}
          aria-label="Layout"
        >
          <ToggleButton value="grid" aria-label="Grid view">
            <GridViewIcon fontSize="small" />
          </ToggleButton>
          <ToggleButton value="list" aria-label="List view">
            <ViewListIcon fontSize="small" />
          </ToggleButton>
        </ToggleButtonGroup>
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
      ) : view === "grid" ? (
        <Grid container spacing={1.5}>
          {visible.map((f) => {
            const thumb = thumbnailUrl(f, token);
            const dur = formatDuration(f.duration);
            const date = formatDate(f.added_at);
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
                  <CardActionArea onClick={() => setSelectedId(f.id)} sx={{ height: "100%" }}>
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
                        {[formatSize(f.size), date].filter(Boolean).join(" · ")}
                      </Typography>
                    </CardContent>
                  </CardActionArea>
                </Card>
              </Grid>
            );
          })}
        </Grid>
      ) : (
        <List disablePadding>
          {visible.map((f) => {
            const thumb = thumbnailUrl(f, token);
            const dur = formatDuration(f.duration);
            return (
              <Card key={f.id} sx={{ mb: 1 }}>
                <ListItem disablePadding>
                  <ListItemButton onClick={() => setSelectedId(f.id)} sx={{ gap: 1.5, py: 1 }}>
                    {thumb ? (
                      <Box
                        component="img"
                        src={thumb}
                        alt=""
                        loading="lazy"
                        sx={{ width: 96, aspectRatio: "16/10", objectFit: "cover", borderRadius: 2 }}
                      />
                    ) : (
                      <Box
                        sx={(t) => ({
                          width: 96,
                          aspectRatio: "16/10",
                          display: "flex",
                          alignItems: "center",
                          justifyContent: "center",
                          borderRadius: 2,
                          bgcolor: `${t.palette.primary.main}14`,
                          color: "primary.main",
                        })}
                      >
                        <TypeIcon type={f.type} />
                      </Box>
                    )}
                    <ListItemText
                      primary={f.name}
                      slotProps={{ primary: { variant: "subtitle2", noWrap: true } as object }}
                      secondary={[dur, formatSize(f.size), formatDate(f.added_at)]
                        .filter(Boolean)
                        .join(" · ")}
                    />
                  </ListItemButton>
                </ListItem>
              </Card>
            );
          })}
        </List>
      )}
      <PlayerDialog
        file={current}
        token={token}
        hasPrev={selIdx > 0}
        hasNext={selIdx >= 0 && selIdx < visible.length - 1}
        onPrev={() => step(-1)}
        onNext={() => step(1)}
        onClose={() => setSelectedId(null)}
      />
    </Box>
  );
}
