import React from "react";
import { 
  Card as MuiCard, 
  CardHeader as MuiCardHeader, 
  CardContent as MuiCardContent, 
  CardActions as MuiCardActions,
  Typography
} from "@mui/material";
import { cn } from "../../utils/cn";

export const Card: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <MuiCard className={cn("flex flex-col h-full", className)} {...(props as any)} />
);

export const CardHeader: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <MuiCardHeader 
    className={cn("p-4 sm:p-6 pb-0", className)} 
    sx={{ '& .MuiCardHeader-content': { display: 'flex', flexDirection: 'column', gap: 1 } }}
    {...(props as any)} 
  />
);

export const CardTitle: React.FC<React.HTMLAttributes<HTMLHeadingElement>> = ({ className, children, ...props }) => (
  <Typography variant="h6" component="h3" className={cn("font-semibold leading-none tracking-tight", className)} {...(props as any)}>
    {children}
  </Typography>
);

export const CardDescription: React.FC<React.HTMLAttributes<HTMLParagraphElement>> = ({ className, children, ...props }) => (
  <Typography variant="body2" color="text.secondary" className={className} {...(props as any)}>
    {children}
  </Typography>
);

export const CardContent: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <MuiCardContent className={cn("p-4 sm:p-6 flex-grow", className)} {...(props as any)} />
);

export const CardFooter: React.FC<React.HTMLAttributes<HTMLDivElement>> = ({ className, ...props }) => (
  <MuiCardActions className={cn("p-4 sm:p-6 pt-0 border-t border-divider mt-4 sm:mt-6", className)} {...(props as any)} />
);
