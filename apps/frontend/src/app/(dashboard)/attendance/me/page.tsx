"use client";

import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { AttendanceSummary } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { PageHeader } from "@/components/layout/page-header";
import { Badge, statusBadgeVariant } from "@/components/ui/badge";

export default function MyAttendancePage() {
  const { data: records = [], isLoading } = useQuery({
    queryKey: ["my-attendance"],
    queryFn: () => apiFetch<AttendanceSummary[]>("/api/attendance/me"),
  });

  return (
    <div className="app-page">
      <PageHeader
        title="My attendance"
        description="Your check-in, check-out, and daily status history."
      />

      <Card>
        <CardHeader>
          <CardTitle>History</CardTitle>
        </CardHeader>
        <CardContent className="table-scroll p-0 sm:overflow-x-auto">
          <table className="data-table min-w-[640px]">
            <thead>
              <tr>
                <th>Date</th>
                <th>Check in</th>
                <th>Check out</th>
                <th>Status</th>
                <th>Late</th>
                <th>OT</th>
              </tr>
            </thead>
            <tbody>
              {isLoading ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    Loading…
                  </td>
                </tr>
              ) : records.length === 0 ? (
                <tr>
                  <td colSpan={6} className="py-12 text-center text-slate-500">
                    No attendance records yet. Use the kiosk to check in.
                  </td>
                </tr>
              ) : (
                records.map((r) => (
                  <tr key={r.id}>
                    <td className="font-medium text-slate-900">{r.date}</td>
                    <td>{r.check_in ? new Date(r.check_in).toLocaleTimeString() : "—"}</td>
                    <td>{r.check_out ? new Date(r.check_out).toLocaleTimeString() : "—"}</td>
                    <td>
                      <Badge variant={statusBadgeVariant(r.status)}>{r.status}</Badge>
                    </td>
                    <td>{r.late_minutes > 0 ? `${r.late_minutes}m` : "—"}</td>
                    <td>{r.overtime_minutes > 0 ? `${r.overtime_minutes}m` : "—"}</td>
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
