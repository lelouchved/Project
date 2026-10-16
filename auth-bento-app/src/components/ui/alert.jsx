import React from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { cn } from "../../lib/utils";

export const Alert = React.forwardRef(({ className, variant = "default", children, ...props }, ref) => {
  const variants = {
    default: "border-zinc-800 bg-zinc-900/80 text-zinc-300",
    destructive: "border-red-500/40 bg-red-950/30 text-red-300",
    success: "border-emerald-500/40 bg-emerald-950/30 text-emerald-300",
  };

  const icons = {
    default: <Info className="h-4 w-4 shrink-0 text-zinc-400" />,
    destructive: <AlertCircle className="h-4 w-4 shrink-0 text-red-400" />,
    success: <CheckCircle2 className="h-4 w-4 shrink-0 text-emerald-400" />,
  };

  return (
    <div
      ref={ref}
      role="alert"
      className={cn(
        "relative w-full rounded-xl border p-3.5 text-xs flex items-start gap-3 backdrop-blur-md animate-fade-in",
        variants[variant],
        className
      )}
      {...props}
    >
      {icons[variant]}
      <div className="flex-1 space-y-0.5">{children}</div>
    </div>
  );
});
Alert.displayName = "Alert";

export const AlertTitle = React.forwardRef(({ className, ...props }, ref) => (
  <h5 ref={ref} className={cn("font-bold tracking-tight text-current leading-none", className)} {...props} />
));
AlertTitle.displayName = "AlertTitle";

export const AlertDescription = React.forwardRef(({ className, ...props }, ref) => (
  <div ref={ref} className={cn("text-[11px] leading-relaxed opacity-90", className)} {...props} />
));
AlertDescription.displayName = "AlertDescription";
