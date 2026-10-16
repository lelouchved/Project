import React, { useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { cn } from "../../lib/utils";

export const Input = React.forwardRef(
  ({ className, type = "text", error, icon: Icon, showPasswordToggle = false, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === "password" || showPasswordToggle;
    const computedType = isPassword ? (showPassword ? "text" : "password") : type;

    return (
      <div className="relative w-full">
        {Icon && (
          <div className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3.5 text-zinc-500">
            <Icon className="h-4 w-4" />
          </div>
        )}
        <input
          type={computedType}
          ref={ref}
          className={cn(
            "flex h-11 w-full rounded-xl border bg-zinc-950/70 px-3.5 py-2 text-sm text-zinc-100 transition-all duration-200 file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-zinc-500 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500/80 focus-visible:border-indigo-500/80 disabled:cursor-not-allowed disabled:opacity-50",
            Icon ? "pl-10" : "pl-3.5",
            showPasswordToggle ? "pr-11" : "pr-3.5",
            error
              ? "border-red-500/80 focus-visible:ring-red-500/80 text-red-200"
              : "border-zinc-800 hover:border-zinc-700",
            className
          )}
          {...props}
        />
        {showPasswordToggle && (
          <button
            type="button"
            onClick={() => setShowPassword(!showPassword)}
            tabIndex={-1}
            className="absolute inset-y-0 right-0 flex items-center pr-3.5 text-zinc-400 hover:text-zinc-200 transition-colors"
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";
