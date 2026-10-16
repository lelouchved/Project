import React from "react";
import { cn } from "../../lib/utils";

export function Badge({ className, variant = "default", children, ...props }) {
  const variants = {
    default: "border-transparent bg-zinc-100 text-zinc-900 shadow hover:bg-zinc-100/80",
    secondary: "border-transparent bg-zinc-800 text-zinc-300 hover:bg-zinc-800/80",
    outline: "text-zinc-300 border-zinc-700 bg-zinc-900/40",
    success: "border-emerald-500/30 bg-emerald-500/10 text-emerald-400 font-mono",
    warning: "border-amber-500/30 bg-amber-500/10 text-amber-400 font-mono",
  };

  return (
    <div
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 text-[10px] font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-zinc-400",
        variants[variant],
        className
      )}
      {...props}
    >
      {children}
    </div>
  );
}
