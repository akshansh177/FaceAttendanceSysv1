import { apiFetch } from "@/lib/api";
import type { Employee } from "@/lib/types";

type PaginatedEmployees = {
  items: Employee[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
};

/** Load all employees (paginated API, max 100 per page). */
export async function fetchAllEmployees(): Promise<Employee[]> {
  const pageSize = 100;
  const first = await apiFetch<PaginatedEmployees>(
    `/api/employees?page=1&page_size=${pageSize}`
  );
  const items = [...first.items];
  for (let p = 2; p <= first.pages; p++) {
    const next = await apiFetch<PaginatedEmployees>(
      `/api/employees?page=${p}&page_size=${pageSize}`
    );
    items.push(...next.items);
  }
  return items;
}
