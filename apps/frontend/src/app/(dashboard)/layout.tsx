"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { DashboardTopbar } from "@/components/layout/dashboard-topbar";
import { getTokens } from "@/lib/api";
import { useSidebarMode } from "@/hooks/use-sidebar-mode";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  const { mode, setMode, toggleHidden, toggleCollapsed } = useSidebarMode();
  const closeMobileNav = useCallback(() => setMobileNavOpen(false), []);

  useEffect(() => {
    const { access } = getTokens();
    if (!access) router.replace("/login");
  }, [router]);

  return (
    <div className="flex min-h-[100dvh] gap-0 bg-[var(--background)] p-2 sm:gap-0 sm:p-3 lg:gap-4 lg:p-4">
      <Sidebar
        mode={mode}
        onModeChange={setMode}
        onToggleCollapsed={toggleCollapsed}
        mobileOpen={mobileNavOpen}
        onMobileClose={closeMobileNav}
      />
      <div className="flex min-w-0 flex-1 flex-col">
        <main className="app-shell-panel flex flex-1 flex-col overflow-auto">
          <div className="min-w-0 flex-1 p-4 sm:p-6 lg:p-8">
            <DashboardTopbar
              sidebarHidden={mode === "hidden"}
              onMobileMenuClick={() => setMobileNavOpen(true)}
              onSidebarToggle={toggleHidden}
            />
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
