"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { fetchAllEmployees } from "@/lib/employees";
import { REFERENCE_STALE_MS, REPORT_STALE_MS } from "@/lib/react-query";
import { canAccessHR } from "@/lib/auth";
import type { Employee, ReportRow } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { cn } from "@/lib/utils";

interface CalendarDay {
  date: string;
  status: string;
  check_in: string | null;
  check_out: string | null;
}

const MONTH_NAMES = [
  "January", "February", "March", "April", "May", "June",
  "July", "August", "September", "October", "November", "December",
];

export default function AttendanceCalendarPage() {
  const isHr = canAccessHR();
  const [month, setMonth] = useState(() => {
    const d = new Date();
    return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
  });
  const [year, setYear] = useState(() => String(new Date().getFullYear()));
  const [selectedEmployeeId, setSelectedEmployeeId] = useState<string | null>(null);

  const monthNum = parseInt(month.slice(5, 7), 10);
  const monthLabel = MONTH_NAMES[monthNum - 1] ?? month;

  const { data: employees = [] } = useQuery({
    queryKey: ["employees", "all"],
    queryFn: fetchAllEmployees,
    enabled: isHr,
    staleTime: REFERENCE_STALE_MS,
  });

  const { data: monthlyRows = [] } = useQuery({
    queryKey: ["calendar-monthly", year, monthNum],
    queryFn: () =>
      apiFetch<ReportRow[]>(`/api/reports/monthly?year=${year}&month=${monthNum}`),
    enabled: isHr,
    staleTime: REPORT_STALE_MS,
  });

  const { data: days = [] } = useQuery({
    queryKey: ["calendar", month],
    queryFn: () => apiFetch<CalendarDay[]>(`/api/me/attendance/calendar?month=${month}`),
    enabled: !isHr,
    staleTime: REPORT_STALE_MS,
  });

  const filteredRows = useMemo(() => {
    if (!selectedEmployeeId) return monthlyRows;
    const emp = employees.find((e) => e.id === selectedEmployeeId);
    if (!emp) return monthlyRows;
    return monthlyRows.filter((r) => r.employee_code === emp.employee_code);
  }, [monthlyRows, selectedEmployeeId, employees]);

  const uniqueEmployees = useMemo(() => {
    const seen = new Set<string>();
    return monthlyRows.filter((r) => {
      if (seen.has(r.employee_code)) return false;
      seen.add(r.employee_code);
      return true;
    });
  }, [monthlyRows]);

  return (
    <div className="app-page !p-0">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-[var(--foreground)] sm:text-3xl">
            Attendance Month — {monthLabel}
          </h1>
          <p className="mt-1 text-sm text-[var(--foreground-muted)]">
            {isHr ? "Review team attendance by month" : "Your monthly attendance log"}
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <label className="flex flex-col gap-1 text-xs font-semibold text-[var(--foreground-muted)]">
            Year
            <select
              className="theme-select min-w-[100px]"
              value={year}
              onChange={(e) => {
                setYear(e.target.value);
                setMonth(`${e.target.value}-${month.slice(5)}`);
              }}
            >
              {[2024, 2025, 2026, 2027].map((y) => (
                <option key={y} value={y}>
                  {y}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1 text-xs font-semibold text-[var(--foreground-muted)]">
            Month
            <input
              type="month"
              className="theme-select"
              value={month}
              onChange={(e) => {
                setMonth(e.target.value);
                setYear(e.target.value.slice(0, 4));
              }}
            />
          </label>
        </div>
      </div>

      {isHr && uniqueEmployees.length > 0 && (
        <div className="-mx-1 flex gap-4 overflow-x-auto pb-2 pt-1">
          <button
            type="button"
            onClick={() => setSelectedEmployeeId(null)}
            className={cn(
              "employee-chip",
              selectedEmployeeId === null && "employee-chip-active"
            )}
          >
            <div
              className={cn(
                "mb-2 flex h-14 w-14 items-center justify-center rounded-full text-lg font-bold",
                selectedEmployeeId === null
                  ? "bg-white/20 text-white"
                  : "bg-[var(--brand-muted)] text-[var(--brand)]"
              )}
            >
              All
            </div>
            <p className="text-sm font-bold">Everyone</p>
            <p className={cn("text-xs", selectedEmployeeId === null ? "text-white/80" : "text-[var(--foreground-muted)]")}>
              {uniqueEmployees.length} employees
            </p>
          </button>
          {uniqueEmployees.map((row) => {
            const emp = employees.find((e) => e.employee_code === row.employee_code);
            const active = selectedEmployeeId === emp?.id;
            return (
              <button
                key={row.employee_code}
                type="button"
                onClick={() => emp && setSelectedEmployeeId(emp.id)}
                className={cn("employee-chip text-left", active && "employee-chip-active")}
              >
                <div
                  className={cn(
                    "mb-2 flex h-14 w-14 items-center justify-center rounded-full text-lg font-bold",
                    active ? "bg-white/20 text-white" : "bg-[var(--brand-muted)] text-[var(--brand)]"
                  )}
                >
                  {row.full_name.charAt(0)}
                </div>
                <p className="max-w-[160px] truncate text-sm font-bold">{row.full_name}</p>
                <p className={cn("max-w-[160px] truncate text-xs", active ? "text-white/80" : "text-[var(--foreground-muted)]")}>
                  {row.department || "—"}
                </p>
                {emp && (
                  <span
                    className={cn(
                      "mt-2 text-xs font-semibold underline",
                      active ? "text-white" : "text-[var(--brand)]"
                    )}
                  >
                    Profile details
                  </span>
                )}
              </button>
            );
          })}
        </div>
      )}

      <Card>
        <CardContent className="table-scroll p-0 sm:overflow-x-auto sm:p-0">
          <table className="data-table min-w-[720px]">
            <thead>
              <tr>
                {isHr && <th>Employee</th>}
                {isHr && <th>Designation</th>}
                <th>Date</th>
                <th>Check-in</th>
                <th>Checkout</th>
                {!isHr && <th>Status</th>}
                <th className="text-right">Details</th>
              </tr>
            </thead>
            <tbody>
              {isHr ? (
                filteredRows.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-12 text-center text-[var(--foreground-muted)]">
                      No attendance records for this month.
                    </td>
                  </tr>
                ) : (
                  filteredRows.map((r, i) => (
                    <tr key={`${r.employee_code}-${r.date}-${i}`}>
                      <td>
                        <div className="flex items-center gap-2">
                          <div className="flex h-9 w-9 items-center justify-center rounded-full bg-[var(--brand-muted)] text-sm font-bold text-[var(--brand)]">
                            {r.full_name.charAt(0)}
                          </div>
                          <span className="font-semibold">{r.full_name}</span>
                        </div>
                      </td>
                      <td className="text-[var(--foreground-muted)]">{r.department || "—"}</td>
                      <td>{r.date ?? "—"}</td>
                      <td className="font-mono text-xs">
                        {r.check_in ? new Date(r.check_in).toLocaleTimeString() : "—"}
                      </td>
                      <td className="font-mono text-xs">
                        {r.check_out ? new Date(r.check_out).toLocaleTimeString() : "—"}
                      </td>
                      <td className="text-right">
                        <Link
                          href={`/employees`}
                          className="theme-btn-ghost-view inline-block"
                        >
                          View
                        </Link>
                      </td>
                    </tr>
                  ))
                )
              ) : days.length === 0 ? (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-[var(--foreground-muted)]">
                    No records this month.
                  </td>
                </tr>
              ) : (
                days.map((d) => (
                  <tr key={d.date}>
                    <td className="font-medium">{d.date}</td>
                    <td className="font-mono text-xs">
                      {d.check_in ? new Date(d.check_in).toLocaleTimeString() : "—"}
                    </td>
                    <td className="font-mono text-xs">
                      {d.check_out ? new Date(d.check_out).toLocaleTimeString() : "—"}
                    </td>
                    <td>{d.status}</td>
                    <td className="text-right">
                      <Link href="/attendance/me" className="theme-btn-ghost-view inline-block">
                        View
                      </Link>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
