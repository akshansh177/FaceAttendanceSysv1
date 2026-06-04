import { cn } from "@/lib/utils";
import { ButtonHTMLAttributes, forwardRef } from "react";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "outline" | "destructive" | "ghost";
  size?: "sm" | "md" | "lg";
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    const variants = {
      default:
        "bg-[var(--brand)] text-white shadow-md hover:bg-[var(--brand-dark)] active:scale-[0.98]",
      outline:
        "border-2 border-[var(--brand)] bg-white text-[var(--brand)] hover:bg-[var(--brand-muted)]",
      destructive: "bg-red-600 text-white hover:bg-red-700",
      ghost: "text-[var(--foreground)] hover:bg-[var(--brand-muted)]",
    };
    const sizes = {
      sm: "rounded-full px-4 py-1.5 text-xs",
      md: "rounded-xl px-4 py-2.5 text-sm",
      lg: "rounded-xl px-6 py-3 text-base",
    };
    return (
      <button
        ref={ref}
        className={cn(
          "inline-flex items-center justify-center font-semibold transition disabled:opacity-50",
          variants[variant],
          sizes[size],
          className
        )}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
