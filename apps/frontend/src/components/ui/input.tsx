import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef } from "react";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, suppressHydrationWarning, ...props }, ref) => (
    <input
      ref={ref}
      suppressHydrationWarning={suppressHydrationWarning}
      className={cn(
        "flex h-10 w-full rounded-xl border border-[var(--border)] bg-white px-4 py-2 text-sm text-[var(--foreground)] shadow-sm placeholder:text-[var(--foreground-muted)] focus:border-[var(--brand)] focus:outline-none focus:ring-2 focus:ring-[var(--brand)]/20",
        className
      )}
      {...props}
    />
  )
);
Input.displayName = "Input";
