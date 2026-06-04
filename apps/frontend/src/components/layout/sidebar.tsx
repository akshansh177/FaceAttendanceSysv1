"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import {
  LayoutDashboard,
  Users,
  Building2,
  Clock,
  Camera,
  FileText,
  Calendar,
  Shield,
  LogOut,
  MapPin,
  Briefcase,
  Monitor,
  Settings,
  ClipboardList,
  ExternalLink,
  X,
  ChevronLeft,
  ChevronRight,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { canAccessHR, canAccessManager, isAdmin } from "@/lib/auth";
import { clearTokens } from "@/lib/api";
import type { SidebarMode } from "@/hooks/use-sidebar-mode";

type NavItem = {
  href: string;
  label: string;
  icon: typeof LayoutDashboard;
  hr?: boolean;
  manager?: boolean;
  admin?: boolean;
  external?: boolean;
};

type NavGroup = { title: string; items: NavItem[] };

const groups: NavGroup[] = [
  {
    title: "Overview",
    items: [{ href: "/dashboard", label: "Dashboard", icon: LayoutDashboard, manager: true }],
  },
  {
    title: "Attendance",
    items: [
      { href: "/kiosk", label: "Kiosk", icon: Camera, external: true },
      { href: "/attendance/me", label: "My Attendance", icon: Calendar },
      { href: "/attendance/calendar", label: "Calendar", icon: Calendar },
      { href: "/corrections", label: "Corrections", icon: ClipboardList },
    ],
  },
  {
    title: "People & org",
    items: [
      { href: "/employees", label: "Employees", icon: Users, hr: true },
      { href: "/departments", label: "Departments", icon: Building2, hr: true },
      { href: "/job-roles", label: "Job Roles", icon: Briefcase, hr: true },
      { href: "/locations", label: "Locations", icon: MapPin, hr: true },
      { href: "/shifts", label: "Shifts", icon: Clock, hr: true },
    ],
  },
  {
    title: "Operations",
    items: [
      { href: "/kiosks", label: "Kiosks", icon: Monitor, hr: true },
      { href: "/policies", label: "Policies", icon: Shield, hr: true },
      { href: "/settings/attendance", label: "Settings", icon: Settings, hr: true },
    ],
  },
  {
    title: "Time off",
    items: [
      { href: "/holidays", label: "Holidays", icon: Calendar, hr: true },
      { href: "/leaves", label: "Leaves", icon: Calendar },
    ],
  },
  {
    title: "Insights",
    items: [{ href: "/reports", label: "Reports", icon: FileText, manager: true }],
  },
  {
    title: "Account",
    items: [{ href: "/profile", label: "Profile", icon: Users }],
  },
  {
    title: "Admin",
    items: [{ href: "/admin/audit", label: "Audit Logs", icon: Shield, admin: true }],
  },
];

function filterItem(item: NavItem, hr: boolean, manager: boolean, admin: boolean) {
  if (item.admin && !admin) return false;
  if (item.hr && !hr) return false;
  if (item.manager && !manager) return false;
  return true;
}

type SidebarProps = {
  mode: SidebarMode;
  onModeChange?: (mode: SidebarMode) => void;
  onToggleCollapsed?: () => void;
  mobileOpen?: boolean;
  onMobileClose?: () => void;
};

export function Sidebar({
  mode,
  onModeChange,
  onToggleCollapsed,
  mobileOpen = false,
  onMobileClose,
}: SidebarProps) {
  const pathname = usePathname();
  const [navReady, setNavReady] = useState(false);

  useEffect(() => {
    setNavReady(true);
  }, []);

  const hr = navReady && canAccessHR();
  const manager = navReady && canAccessManager();
  const admin = navReady && isAdmin();

  const isExpanded = mode === "expanded";
  const isCollapsed = mode === "collapsed";
  const isHidden = mode === "hidden";

  const isActive = (href: string) =>
    pathname === href || (href !== "/dashboard" && pathname.startsWith(href + "/"));

  useEffect(() => {
    onMobileClose?.();
  }, [pathname, onMobileClose]);

  useEffect(() => {
    if (!mobileOpen) return;
    const prev = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.body.style.overflow = prev;
    };
  }, [mobileOpen]);

  const showLabels = mobileOpen || isExpanded;

  return (
    <>
      <div
        role="presentation"
        aria-hidden={!mobileOpen}
        className={cn(
          "fixed inset-0 z-40 bg-slate-900/40 backdrop-blur-sm transition-opacity lg:hidden",
          mobileOpen ? "opacity-100" : "pointer-events-none opacity-0"
        )}
        onClick={onMobileClose}
      />

      <aside
        className={cn(
          "fixed inset-y-2 left-2 z-50 flex flex-col rounded-2xl bg-[var(--sidebar)] shadow-[var(--shadow-panel)] transition-[width,transform,opacity] duration-300 ease-out sm:inset-y-3 sm:left-3 lg:inset-y-4 lg:left-4",
          "max-h-[calc(100dvh-1rem)] sm:max-h-[calc(100dvh-1.5rem)] lg:max-h-[calc(100dvh-2rem)]",
          mobileOpen ? "translate-x-0" : "-translate-x-[calc(100%+1rem)] max-lg:pointer-events-none",
          "w-[min(100vw-2rem,17rem)] max-w-[85vw]",
          "lg:static lg:z-auto lg:translate-x-0",
          isHidden && "lg:pointer-events-none lg:w-0 lg:min-w-0 lg:overflow-hidden lg:opacity-0 lg:shadow-none",
          !isHidden && isCollapsed && "lg:w-[4.5rem]",
          !isHidden && isExpanded && "lg:w-64",
          mobileOpen && "lg:w-64"
        )}
        aria-label="Main navigation"
        aria-hidden={isHidden && !mobileOpen}
      >
        <div
          className={cn(
            "flex shrink-0 items-center border-b border-white/10 px-3 py-4",
            showLabels ? "justify-between gap-2" : "justify-center lg:px-2",
            !showLabels && "lg:flex-col lg:gap-2"
          )}
        >
          <div
            className={cn(
              "flex min-w-0 items-center gap-3",
              !showLabels && "lg:flex-col lg:gap-2"
            )}
          >
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-white/20 text-sm font-bold text-white backdrop-blur sm:h-11 sm:w-11 sm:rounded-2xl sm:text-lg">
              FA
            </div>
            {showLabels && (
              <div className="min-w-0">
                <h1 className="truncate text-sm font-bold text-white sm:text-base">Face Attendance</h1>
                <p className="text-[10px] text-white/70 sm:text-xs">Workforce</p>
              </div>
            )}
          </div>
          <button
            type="button"
            className="rounded-lg p-2 text-white/80 hover:bg-white/10 lg:hidden"
            onClick={onMobileClose}
            aria-label="Close menu"
          >
            <X size={20} />
          </button>
        </div>

        <nav className="flex-1 space-y-3 overflow-y-auto overscroll-contain px-2 py-3 sm:space-y-4 sm:py-4">
          {groups.map((group) => {
            const items = group.items.filter((item) => filterItem(item, hr, manager, admin));
            if (items.length === 0) return null;
            return (
              <div key={group.title}>
                {showLabels && (
                  <p className="mb-1.5 px-2 text-[10px] font-bold uppercase tracking-wider text-white/50">
                    {group.title}
                  </p>
                )}
                <ul className="space-y-0.5">
                  {items.map(({ href, label, icon: Icon, external }) => {
                    const active = isActive(href) && !external;
                    return (
                      <li key={href}>
                        <Link
                          href={href}
                          target={external ? "_blank" : undefined}
                          rel={external ? "noopener noreferrer" : undefined}
                          onClick={onMobileClose}
                          title={!showLabels ? label : undefined}
                          className={cn(
                            "flex min-h-[42px] items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition",
                            showLabels ? "justify-start" : "justify-center px-2 lg:px-2",
                            active
                              ? "bg-[var(--sidebar-active-bg)] text-[var(--sidebar-active-text)] shadow-md"
                              : "text-white/90 hover:bg-white/15"
                          )}
                        >
                          <Icon size={20} className="shrink-0" strokeWidth={active ? 2.25 : 2} />
                          {showLabels && (
                            <>
                              <span className="flex-1 truncate">{label}</span>
                              {external && (
                                <ExternalLink size={14} className="shrink-0 opacity-60" />
                              )}
                            </>
                          )}
                        </Link>
                      </li>
                    );
                  })}
                </ul>
              </div>
            );
          })}
        </nav>

        <div className="shrink-0 space-y-1 border-t border-white/10 p-2">
          <button
            type="button"
            onClick={onToggleCollapsed}
            className={cn(
              "hidden w-full min-h-[40px] items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-white/80 transition hover:bg-white/15 lg:flex",
              showLabels ? "justify-start" : "justify-center px-2"
            )}
            aria-label={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
            title={isExpanded ? "Collapse sidebar" : "Expand sidebar"}
          >
            {isExpanded ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
            {showLabels && <span>{isExpanded ? "Collapse" : "Expand"}</span>}
          </button>

          <button
            type="button"
            onClick={() => {
              clearTokens();
              window.location.href = "/login";
            }}
            className={cn(
              "flex w-full min-h-[42px] items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-white/90 transition hover:bg-white/15",
              showLabels ? "justify-start" : "justify-center px-2"
            )}
            title="Sign out"
          >
            <LogOut size={20} />
            {showLabels && <span>Sign out</span>}
          </button>
        </div>
      </aside>

      {isHidden && (
        <button
          type="button"
          onClick={() => onModeChange?.("expanded")}
          className="fixed bottom-6 left-4 z-30 hidden h-11 w-11 items-center justify-center rounded-xl bg-[var(--sidebar)] text-white shadow-lg transition hover:bg-[var(--sidebar-hover)] lg:flex"
          aria-label="Show sidebar"
          title="Show sidebar"
        >
          <ChevronRight size={22} />
        </button>
      )}
    </>
  );
}
