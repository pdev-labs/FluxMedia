import React from "react";
import { LinearProgress } from "@mui/material";
import { cn } from "../../utils/cn";

export interface ProgressBarProps extends React.HTMLAttributes<HTMLDivElement> {
  value: number; // 0 to 100
  variant?: "default" | "success" | "warning" | "danger";
  size?: "sm" | "md" | "lg";
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  className,
  value,
  variant = "default",
  size = "md",
  ...props
}) => {
  const clampedValue = Math.min(100, Math.max(0, value));
  
  let muiColor: "primary" | "secondary" | "error" | "info" | "success" | "warning" | "inherit" = "primary";
  switch (variant) {
    case "success": muiColor = "success"; break;
    case "warning": muiColor = "warning"; break;
    case "danger": muiColor = "error"; break;
  }

  let height = 12;
  if (size === "sm") height = 6;
  if (size === "lg") height = 20;

  return (
    <div className={cn("w-full", className)} {...props}>
      <LinearProgress 
        variant="determinate" 
        value={clampedValue} 
        color={muiColor} 
        sx={{ height, borderRadius: height / 2 }}
      />
    </div>
  );
};
