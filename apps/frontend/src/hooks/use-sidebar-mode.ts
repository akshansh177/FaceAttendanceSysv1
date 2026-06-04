"use client";

import { useCallback, useEffect, useState } from "react";

export type SidebarMode = "expanded" | "collapsed" | "hidden";

const STORAGE_KEY = "fas-sidebar-mode";

function readStoredMode(): SidebarMode {
  if (typeof window === "undefined") return "expanded";
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored === "expanded" || stored === "collapsed" || stored === "hidden") {
    return stored;
  }
  return "expanded";
}

export function useSidebarMode() {
  const [mode, setModeState] = useState<SidebarMode>("expanded");
  const [hydrated, setHydrated] = useState(false);

  useEffect(() => {
    setModeState(readStoredMode());
    setHydrated(true);
  }, []);

  const setMode = useCallback((next: SidebarMode | ((prev: SidebarMode) => SidebarMode)) => {
    setModeState((prev) => {
      const value = typeof next === "function" ? next(prev) : next;
      if (hydrated) {
        localStorage.setItem(STORAGE_KEY, value);
      }
      return value;
    });
  }, [hydrated]);

  useEffect(() => {
    if (hydrated) {
      localStorage.setItem(STORAGE_KEY, mode);
    }
  }, [mode, hydrated]);

  const toggleHidden = useCallback(() => {
    setMode((m) => (m === "hidden" ? "expanded" : "hidden"));
  }, [setMode]);

  const toggleCollapsed = useCallback(() => {
    setMode((m) => {
      if (m === "hidden") return "expanded";
      return m === "expanded" ? "collapsed" : "expanded";
    });
  }, [setMode]);

  return { mode, setMode, toggleHidden, toggleCollapsed, hydrated };
}
