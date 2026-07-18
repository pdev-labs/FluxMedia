import React from "react";
import { cn } from "../../utils/cn";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "secondary" | "success" | "warning" | "danger" | "info" | "outline";
}

export const Badge: React.FC<BadgeProps> = ({ className, variant = "default", ...props }) => {
  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2",
        variant === "default" && "border-transparent bg-primary text-primary-foreground",
        variant === "secondary" && "border-transparent bg-secondary text-secondary-foreground",
        variant === "success" && "border-transparent bg-emerald-500/15 text-emerald-500 border border-emerald-500/20",
        variant === "warning" && "border-transparent bg-amber-500/15 text-amber-500 border border-amber-500/20",
        variant === "danger" && "border-transparent bg-red-500/15 text-red-500 border border-red-500/20",
        variant === "info" && "border-transparent bg-blue-500/15 text-blue-500 border border-blue-500/20",
        variant === "outline" && "text-foreground border-border",
        className
      )}
      {...props}
    />
  );
};
