import React from "react";
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

  return (
    <div
      className={cn(
        "w-full bg-secondary rounded-full overflow-hidden",
        size === "sm" && "h-1.5",
        size === "md" && "h-3",
        size === "lg" && "h-5",
        className
      )}
      {...props}
    >
      <div
        style={{ width: `${clampedValue}%` }}
        className={cn(
          "h-full rounded-full transition-all duration-300 ease-out",
          variant === "default" && "bg-primary",
          variant === "success" && "bg-emerald-500",
          variant === "warning" && "bg-amber-500",
          variant === "danger" && "bg-red-500"
        )}
      />
    </div>
  );
};
