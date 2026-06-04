import { QueryClient } from "@tanstack/react-query";

/** Default cache: fewer background refetches and less API load */
export function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 2 * 60 * 1000,
        gcTime: 10 * 60 * 1000,
        refetchOnWindowFocus: false,
        refetchOnReconnect: true,
        retry: 1,
      },
    },
  });
}

/** Reference lists (departments, shifts, etc.) change rarely */
export const REFERENCE_STALE_MS = 15 * 60 * 1000;

/** Dashboard KPIs */
export const DASHBOARD_STALE_MS = 60 * 1000;

/** Trends / reports */
export const REPORT_STALE_MS = 5 * 60 * 1000;
