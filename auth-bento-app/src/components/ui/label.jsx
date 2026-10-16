import React from "react";
import { cn } from "../../lib/utils";

export const Label = React.forwardRef(({ className, children, required, ...props }, ref) => {
  return (
    <label
      ref={ref}
      className={cn(
        "text-xs font-semibold tracking-wide text-zinc-300 flex items-center justify-between",
        className
      )}
      {...props}
    >
      <span>
        {children}
        {required && <span className="ml-1 text-red-400">*</span>}
      </span>
    </label>
  );
});

Label.displayName = "Label";
