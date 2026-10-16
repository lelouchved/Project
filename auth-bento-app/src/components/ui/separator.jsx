import React from "react";
import { cn } from "../../lib/utils";

export function Separator({ className, label, ...props }) {
  if (label) {
    return (
      <div className={cn("relative my-4 flex items-center justify-center", className)} {...props}>
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-zinc-800" />
        </div>
        <div className="relative bg-zinc-900/90 px-3 text-[11px] font-mono uppercase tracking-wider text-zinc-500">
          {label}
        </div>
      </div>
    );
  }

  return (
    <div
      className={cn("h-px w-full bg-zinc-800 my-4", className)}
      role="separator"
      {...props}
    />
  );
}
