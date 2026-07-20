import React, { forwardRef } from "react";
import { Button as MuiButton, IconButton, CircularProgress } from "@mui/material";
import { cn } from "../../utils/cn";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive" | "outline" | "ghost" | "link";
  size?: "sm" | "md" | "lg" | "icon";
  isLoading?: boolean;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "primary", size = "md", isLoading, children, disabled, ...props }, ref) => {
    // Map custom variants to MUI variants and colors
    let muiVariant: "text" | "outlined" | "contained" = "contained";
    let muiColor: "primary" | "secondary" | "error" | "inherit" | "info" = "primary";
    
    switch (variant) {
      case "primary":
        muiVariant = "contained";
        muiColor = "primary";
        break;
      case "secondary":
        muiVariant = "contained";
        muiColor = "secondary";
        break;
      case "destructive":
        muiVariant = "contained";
        muiColor = "error";
        break;
      case "outline":
        muiVariant = "outlined";
        muiColor = "inherit";
        break;
      case "ghost":
        muiVariant = "text";
        muiColor = "inherit";
        break;
      case "link":
        muiVariant = "text";
        muiColor = "primary";
        break;
    }

    // Map custom sizes to MUI sizes
    let muiSize: "small" | "medium" | "large" = "medium";
    if (size === "sm") muiSize = "small";
    if (size === "lg") muiSize = "large";

    // Handle Icon Button
    if (size === "icon") {
      return (
        <IconButton
          ref={ref as any}
          disabled={disabled || isLoading}
          color={muiColor as any}
          className={className}
          size="small"
          {...(props as any)}
        >
          {isLoading ? <CircularProgress size={20} color="inherit" /> : children}
        </IconButton>
      );
    }

    return (
      <MuiButton
        ref={ref as any}
        disabled={disabled || isLoading}
        variant={muiVariant}
        color={muiColor}
        size={muiSize}
        className={cn(variant === "link" && "underline-offset-4 hover:underline", className)}
        startIcon={isLoading ? <CircularProgress size={16} color="inherit" /> : undefined}
        {...(props as any)}
      >
        {children}
      </MuiButton>
    );
  }
);

Button.displayName = "Button";
