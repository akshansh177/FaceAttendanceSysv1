import { cn } from "@/lib/utils";
import type { LucideIcon } from "lucide-react";

const accents = {
  green: "border-emerald-200/80 bg-white",
  red: "border-red-200/80 bg-white",
  amber: "border-amber-200/80 bg-white",
  orange: "border-orange-200/80 bg-white",
  blue: "border-[var(--brand)]/30 bg-[var(--brand-muted)]",
  slate: "border-[var(--border)] bg-white",
} as const;

const iconColors = {
  green: "text-emerald-600 bg-emerald-100",
  red: "text-red-600 bg-red-100",
  amber: "text-amber-600 bg-amber-100",
  orange: "text-orange-600 bg-orange-100",
  blue: "text-white bg-[var(--brand)]",
  slate: "text-[var(--brand)] bg-[var(--brand-muted)]",
} as const;

const valueColors = {
  green: "text-emerald-700",
  red: "text-red-700",
  amber: "text-amber-700",
  orange: "text-orange-700",
  blue: "text-[var(--brand)]",
  slate: "text-[var(--foreground)]",
} as const;

export function StatCard({
  label,
  value,
  accent = "slate",
  icon: Icon,
  hint,
}: {
  label: string;
  value: string | number;
  accent?: keyof typeof accents;
  icon?: LucideIcon;
  hint?: string;
}) {
  return (
    <div className={cn("rounded-2xl border p-5 shadow-card transition hover:shadow-md", accents[accent])}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium text-[var(--foreground-muted)]">{label}</p>
          <p className={cn("mt-1 text-3xl font-bold tabular-nums tracking-tight", valueColors[accent])}>
            {value}
          </p>
          {hint && <p className="mt-1 text-xs text-[var(--foreground-muted)]">{hint}</p>}
        </div>
        {Icon && (
          <div
            className={cn(
              "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl shadow-sm",
              iconColors[accent]
            )}
          >
            <Icon className="h-5 w-5" aria-hidden />
          </div>
        )}
      </div>
    </div>
  );
}
