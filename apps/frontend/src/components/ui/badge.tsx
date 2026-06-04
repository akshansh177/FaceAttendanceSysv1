import { cn } from "@/lib/utils";
import { HTMLAttributes } from "react";

const variants = {
  default: "bg-[var(--brand-muted)] text-[var(--brand)]",
  success: "bg-emerald-50 text-emerald-800 ring-1 ring-emerald-200/80",
  warning: "bg-amber-50 text-amber-900 ring-1 ring-amber-200/80",
  danger: "bg-red-50 text-red-800 ring-1 ring-red-200/80",
  info: "bg-[var(--brand-muted)] text-[var(--brand-dark)] ring-1 ring-[var(--border)]",
  neutral: "bg-[var(--surface-muted)] text-[var(--foreground-muted)] ring-1 ring-[var(--border)]",
} as const;

export function Badge({
  className,
  variant = "default",
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: keyof typeof variants }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}

export function statusBadgeVariant(status: string | null | undefined): keyof typeof variants {
  if (!status) return "neutral";
  const s = status.toLowerCase();
  if (s.includes("present") || s.includes("checked_in") || s.includes("success")) return "success";
  if (s.includes("late") || s.includes("warning") || s.includes("half")) return "warning";
  if (s.includes("absent") || s.includes("error") || s.includes("reject")) return "danger";
  if (s.includes("leave") || s.includes("holiday") || s.includes("weekend")) return "info";
  if (s.includes("checked_out") || s.includes("checkout")) return "neutral";
  return "default";
}
