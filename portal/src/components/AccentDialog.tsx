import { useState } from "react";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  TextField,
  Typography,
} from "@mui/material";
import CheckIcon from "@mui/icons-material/Check";
import { ACCENT_PRESETS, toneMain } from "../theme.ts";

const SWATCH = 46;

function Swatch({
  color,
  label,
  selected,
  onPick,
}: {
  color: string;
  label: string;
  selected: boolean;
  onPick: () => void;
}): React.JSX.Element {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0.5 }}>
      <Box
        component="button"
        onClick={onPick}
        title={label}
        aria-label={label}
        aria-pressed={selected}
        sx={{
          width: SWATCH,
          height: SWATCH,
          borderRadius: "50%",
          bgcolor: color,
          border: 2,
          borderColor: selected ? "primary.main" : "transparent",
          outline: selected ? 2 : 0,
          outlineColor: "primary.main",
          outlineOffset: 2,
          cursor: "pointer",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          color: "#fff",
        }}
      >
        {selected && <CheckIcon />}
      </Box>
      <Typography variant="caption" color="text.secondary" noWrap sx={{ maxWidth: 64 }}>
        {label}
      </Typography>
    </Box>
  );
}

export function AccentDialog({
  open,
  serverTone,
  current,
  onPick,
  onClose,
}: {
  open: boolean;
  serverTone: string | undefined;
  current: string | null;
  onPick: (hex: string | null) => void;
  onClose: () => void;
}): React.JSX.Element {
  const isCustom = current !== null && !Object.values(ACCENT_PRESETS).includes(current);
  const [hex, setHex] = useState(current ?? "#d90429");
  const valid = /^#[0-9a-fA-F]{6}$/.test(hex);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="xs" fullWidth>
      <DialogTitle>Accent color</DialogTitle>
      <DialogContent>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          Applies instantly on this device.
        </Typography>
        <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1.5, mb: 2.5 }}>
          <Swatch
            color={toneMain(serverTone)}
            label="Server"
            selected={current === null}
            onPick={() => onPick(null)}
          />
          {Object.entries(ACCENT_PRESETS).map(([name, value]) => (
            <Swatch
              key={name}
              color={value}
              label={name.split(" ")[0]}
              selected={current === value}
              onPick={() => onPick(value)}
            />
          ))}
          <Box sx={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 0.5 }}>
            <Box
              component="label"
              title="Custom color"
              sx={{
                width: SWATCH,
                height: SWATCH,
                borderRadius: "50%",
                bgcolor: valid ? hex : "action.disabledBackground",
                border: 2,
                borderColor: isCustom ? "primary.main" : "divider",
                outline: isCustom ? 2 : 0,
                outlineColor: "primary.main",
                outlineOffset: 2,
                cursor: "pointer",
                overflow: "hidden",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                color: "#fff",
                fontSize: 20,
                fontWeight: 700,
              }}
            >
              {isCustom ? <CheckIcon /> : "+"}
              <Box
                component="input"
                type="color"
                value={valid ? hex : "#d90429"}
                onChange={(e) => {
                  setHex(e.target.value);
                  onPick(e.target.value);
                }}
                sx={{ opacity: 0, position: "absolute", width: SWATCH, height: SWATCH, cursor: "pointer" }}
                aria-label="Pick a custom color"
              />
            </Box>
            <Typography variant="caption" color="text.secondary">
              Custom
            </Typography>
          </Box>
        </Box>
        <TextField
          fullWidth
          size="small"
          label="Custom hex code"
          value={hex}
          onChange={(e) => {
            const v = e.target.value.startsWith("#") ? e.target.value : `#${e.target.value}`;
            setHex(v);
            if (/^#[0-9a-fA-F]{6}$/.test(v)) onPick(v);
          }}
          error={!valid}
          helperText={valid ? "Applies as you type" : "Use 6 hex digits, e.g. #d90429"}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Done</Button>
      </DialogActions>
    </Dialog>
  );
}
