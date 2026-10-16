import React from "react";
import { cn } from "../../lib/utils";

export const Card = React.forwardRef(({ className, children, glow = false, ...props }, ref) => {
  return (
    <div
      ref={ref}
      className={cn(
        "rounded-2xl border border-zinc-800/80 bg-zinc-900/60 p-6 text-zinc-100 backdrop-blur-xl shadow-xl transition-all duration-300",
        glow && "relative before:absolute before:-inset-px before:rounded-2xl before:bg-gradient-to-r before:from-indigo-500/20 before:via-purple-500/20 before:to-pink-500/20 before:-z-10",
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
});
Card.displayName = "Card";

export const CardHeader = React.forwardRef(({ className, ...props }, ref) => {
  return <div ref={ref} className={cn("flex flex-col space-y-1.5 pb-4", className)} {...props} />;
});
CardHeader.displayName = "CardHeader";

export const CardTitle = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <h3
      ref={ref}
      className={cn("text-xl font-bold tracking-tight text-white", className)}
      {...props}
    />
  );
});
CardTitle.displayName = "CardTitle";

export const CardDescription = React.forwardRef(({ className, ...props }, ref) => {
  return (
    <p
      ref={ref}
      className={cn("text-xs text-zinc-400 leading-relaxed", className)}
      {...props}
    />
  );
});
CardDescription.displayName = "CardDescription";

export const CardContent = React.forwardRef(({ className, ...props }, ref) => {
  return <div ref={ref} className={cn("pt-0", className)} {...props} />;
});
CardContent.displayName = "CardContent";

export const CardFooter = React.forwardRef(({ className, ...props }, ref) => {
  return <div ref={ref} className={cn("flex items-center pt-4", className)} {...props} />;
});
CardFooter.displayName = "CardFooter";
