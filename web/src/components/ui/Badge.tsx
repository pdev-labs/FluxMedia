import React from "react";
import { Chip } from "@mui/material";
import { cn } from "../../utils/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "success" | "warning" | "danger" | "info" | "outline";
}

export const Badge: React.FC<BadgeProps> = ({ className, variant = "default", children, ...props }) => {
  let muiColor: "primary" | "secondary" | "success" | "warning" | "error" | "info" | "default" = "primary";
  let muiVariant: "filled" | "outlined" = "filled";

  switch (variant) {
    case "default":
      muiColor = "primary";
      break;
    case "secondary":
      muiColor = "secondary";
      break;
    case "success":
      muiColor = "success";
      break;
    case "warning":
      muiColor = "warning";
      break;
    case "danger":
      muiColor = "error";
      break;
    case "info":
      muiColor = "info";
      break;
    case "outline":
      muiColor = "default";
      muiVariant = "outlined";
      break;
  }

  return (
    <Chip
      label={children}
      color={muiColor}
      variant={muiVariant}
      size="small"
      className={cn("font-semibold", className)}
      {...(props as any)}
    />
  );
};
