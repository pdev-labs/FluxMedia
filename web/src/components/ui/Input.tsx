import React, { forwardRef } from "react";
import { TextField } from "@mui/material";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  error?: string;
  label?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, type = "text", error, label, id, disabled, ...props }, ref) => {
    return (
      <TextField
        id={id}
        type={type}
        inputRef={ref}
        label={label}
        error={!!error}
        helperText={error}
        disabled={disabled}
        variant="outlined"
        fullWidth
        className={className}
        size="small"
        InputProps={{
          ...(props as any)
        }}
        inputProps={{
          ...props
        }}
      />
    );
  }
);

Input.displayName = "Input";
