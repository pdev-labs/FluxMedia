import React from "react";
import { Skeleton as MuiSkeleton } from "@mui/material";
import { cn } from "../../utils/cn";

export const Skeleton: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => {
  return (
    <MuiSkeleton
      animation="pulse"
      variant="rectangular"
      className={cn("rounded-md", className)}
      {...(props as any)}
    />
  );
};
