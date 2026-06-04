"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { Bell, ExternalLink, Menu, PanelLeftClose, PanelLeftOpen, Search } from "lucide-react";
import { getRole } from "@/lib/auth";
import { Badge } from "@/components/ui/badge";

const roleLabels: Record<string, string> = {
  super_admin: "Super Admin",
  hr_manager: "HR Manager",
  team_manager: "Team Manager",
  employee: "Employee",
};

type DashboardTopbarProps = {
  onMobileMenuClick?: () => void;
  onSidebarToggle?: () => void;
  sidebarHidden?: boolean;
};

export function DashboardTopbar({
  onMobileMenuClick,
  onSidebarToggle,
  sidebarHidden = false,
}: DashboardTopbarProps) {
  const router = useRouter();
  const role = getRole();
  const label = role ? roleLabels[role] ?? role : "Admin";

  return (
    <header className="mb-4 flex flex-col gap-4 border-b border-[var(--border)]/80 pb-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 flex-1 items-center gap-3">
        <button
          type="button"
          className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[var(--border)] bg-white text-[var(--foreground)] shadow-sm lg:hidden"
          onClick={onMobileMenuClick}
          aria-label="Open menu"
        >
          <Menu className="h-5 w-5" />
        </button>
        <button
          type="button"
          className="hidden h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-[var(--border)] bg-white text-[var(--foreground)] shadow-sm transition hover:bg-[var(--brand-muted)] lg:inline-flex"
          onClick={onSidebarToggle}
          aria-label={sidebarHidden ? "Show sidebar" : "Hide sidebar"}
          title={sidebarHidden ? "Show sidebar" : "Hide sidebar"}
        >
          {sidebarHidden ? (
            <PanelLeftOpen className="h-5 w-5" />
          ) : (
            <PanelLeftClose className="h-5 w-5" />
          )}
        </button>
        <div className="relative hidden min-w-0 flex-1 sm:block sm:max-w-md">
          <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-[var(--foreground-muted)]" />
          <input
            type="search"
            placeholder="Search employees, reports…"
            className="theme-input w-full pl-11"
            onKeyDown={(e) => {
              if (e.key === "Enter") router.push("/employees");
            }}
          />
        </div>
      </div>

      <div className="flex shrink-0 items-center justify-end gap-2 sm:gap-4">
        <Link
          href="/kiosk"
          target="_blank"
          rel="noopener noreferrer"
          className="theme-btn-outline hidden items-center gap-1.5 px-3 py-2 text-xs sm:inline-flex sm:text-sm"
        >
          Kiosk
          <ExternalLink className="h-3.5 w-3.5" />
        </Link>
        <button
          type="button"
          className="relative flex h-10 w-10 items-center justify-center rounded-full border border-[var(--border)] bg-white shadow-sm"
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4 text-[var(--foreground-muted)]" />
          <span className="absolute right-2 top-2 h-2 w-2 rounded-full bg-red-500 ring-2 ring-white" />
        </button>
        <div className="flex items-center gap-2 rounded-full border border-[var(--border)] bg-white py-1 pl-1 pr-3 shadow-sm">
          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-gradient-to-br from-brand-500 to-brand-700 text-sm font-bold text-white">
            {label.charAt(0)}
          </div>
          <div className="hidden text-left sm:block">
            <p className="text-sm font-semibold text-[var(--foreground)]">{label}</p>
            <p className="text-[10px] text-[var(--foreground-muted)]">Admin</p>
          </div>
        </div>
      </div>
    </header>
  );
}
