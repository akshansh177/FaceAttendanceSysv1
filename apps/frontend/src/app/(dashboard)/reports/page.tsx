"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileSpreadsheet, FileText, RefreshCw } from "lucide-react";
import { apiDownload, apiFetch } from "@/lib/api";
import { canAccessHR } from "@/lib/auth";
import { REFERENCE_STALE_MS, REPORT_STALE_MS } from "@/lib/react-query";
import type { Department, ReportRow } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/layout/page-header";
import { Badge, statusBadgeVariant } from "@/components/ui/badge";

type ReportType = "daily" | "weekly" | "monthly" | "late" | "overtime" | "absent";

function buildReportPath(
  reportType: ReportType,
  opts: {
    reportDate: string;
    start: string;
    end: string;
    weekStart: string;
    year: number;
    month: number;
    departmentId: string;
  }
): string {
  const dept = opts.departmentId ? `&department_id=${opts.departmentId}` : "";
  switch (reportType) {
    case "daily":
      return `/api/reports/daily?report_date=${opts.reportDate}${dept}`;
    case "weekly":
      return `/api/reports/weekly?week_start=${opts.weekStart}${dept}`;
    case "monthly":
      return `/api/reports/monthly?year=${opts.year}&month=${opts.month}${dept}`;
    case "late":
      return `/api/reports/late?start=${opts.start}&end=${opts.end}${dept}`;
    case "overtime":
      return `/api/reports/overtime?start=${opts.start}&end=${opts.end}${dept}`;
    case "absent":
      return `/api/reports/absent?start=${opts.start}&end=${opts.end}${dept}`;
  }
}

function exportFilename(reportType: ReportType, format: string, opts: { reportDate: string; start: string; end: string; weekStart: string; year: number; month: number }) {
  const ext = format === "xlsx" ? "xlsx" : format === "pdf" ? "pdf" : "csv";
  const base =
    reportType === "daily"
      ? `daily_${opts.reportDate}`
      : reportType === "weekly"
        ? `weekly_${opts.weekStart}`
        : reportType === "monthly"
          ? `monthly_${opts.year}_${String(opts.month).padStart(2, "0")}`
          : `${reportType}_${opts.start}_${opts.end}`;
  return `${base}.${ext}`;
}

export default function ReportsPage() {
  const today = new Date().toISOString().slice(0, 10);
  const [reportType, setReportType] = useState<ReportType>("daily");
  const [reportDate, setReportDate] = useState(today);
  const [weekStart, setWeekStart] = useState(today);
  const [start, setStart] = useState(today);
  const [end, setEnd] = useState(today);
  const [departmentId, setDepartmentId] = useState("");
  const [exporting, setExporting] = useState<string | null>(null);
  const [exportError, setExportError] = useState<string | null>(null);

  const year = parseInt(reportDate.slice(0, 4), 10);
  const month = parseInt(reportDate.slice(5, 7), 10);

  const queryPath = useMemo(
    () =>
      buildReportPath(reportType, {
        reportDate,
        start,
        end,
        weekStart,
        year,
        month,
        departmentId,
      }),
    [reportType, reportDate, start, end, weekStart, year, month, departmentId]
  );

  const { data: rows = [], isLoading, isError, error, refetch, isFetching } = useQuery({
    queryKey: ["reports", queryPath],
    queryFn: () => apiFetch<ReportRow[]>(queryPath),
    staleTime: REPORT_STALE_MS,
  });

  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: () => apiFetch<Department[]>("/api/departments"),
    enabled: canAccessHR(),
    staleTime: REFERENCE_STALE_MS,
  });

  async function download(format: "csv" | "xlsx" | "pdf") {
    setExporting(format);
    setExportError(null);
    try {
      if ((reportType === "daily" || reportType === "monthly") && format !== "csv") {
        const jobType = reportType === "daily" ? "daily" : "monthly";
        const params = new URLSearchParams({ report_type: jobType, format });
        if (reportType === "daily") params.set("report_date", reportDate);
        else {
          params.set("year", String(year));
          params.set("month", String(month));
        }
        if (departmentId) params.set("department_id", departmentId);
        const { job_id } = await apiFetch<{ job_id: string }>(`/api/reports/jobs?${params}`, { method: "POST" });
        for (let i = 0; i < 60; i++) {
          await new Promise((r) => setTimeout(r, 2000));
          const job = await apiFetch<{
            status: string;
            content_b64?: string;
            filename?: string;
            media_type?: string;
            error?: string;
          }>(`/api/reports/jobs/${job_id}`);
          if (job.status === "completed" && job.content_b64) {
            const bin = atob(job.content_b64);
            const bytes = new Uint8Array(bin.length);
            for (let j = 0; j < bin.length; j++) bytes[j] = bin.charCodeAt(j);
            const blob = new Blob([bytes], { type: job.media_type || "application/octet-stream" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = job.filename || exportFilename(reportType, format, { reportDate, start, end, weekStart, year, month });
            a.click();
            URL.revokeObjectURL(url);
            return;
          }
          if (job.status === "failed") throw new Error(job.error || "Export failed");
        }
        throw new Error("Export timed out");
      }
      const sep = queryPath.includes("?") ? "&" : "?";
      await apiDownload(
        `${queryPath}${sep}format=${format}`,
        exportFilename(reportType, format, { reportDate, start, end, weekStart, year, month })
      );
    } catch (e) {
      setExportError(e instanceof Error ? e.message : "Export failed");
    } finally {
      setExporting(null);
    }
  }

  const showRange = ["late", "overtime", "absent", "weekly"].includes(reportType);
  const showSingleDate = reportType === "daily";
  const showMonth = reportType === "monthly";

  return (
    <div className="app-page">
      <PageHeader
        title="Reports"
        description="Generate attendance reports and export to CSV, Excel, or PDF."
        actions={
          <Button variant="outline" size="sm" onClick={() => refetch()} disabled={isFetching}>
            <RefreshCw className={`mr-2 h-4 w-4 ${isFetching ? "animate-spin" : ""}`} />
            Refresh
          </Button>
        }
      />

      <Card>
        <CardHeader>
          <CardTitle>Report builder</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <label className="flex min-w-[160px] flex-col gap-1 text-sm">
              <span className="font-medium text-slate-600">Report type</span>
              <select
                className="h-10 rounded-lg border border-slate-200 bg-white px-3 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/25"
                value={reportType}
                onChange={(e) => setReportType(e.target.value as ReportType)}
              >
                <option value="daily">Daily attendance</option>
                <option value="weekly">Weekly summary</option>
                <option value="monthly">Monthly summary</option>
                <option value="late">Late arrivals</option>
                <option value="overtime">Overtime</option>
                <option value="absent">Absent</option>
              </select>
            </label>

            {showSingleDate && (
              <label className="flex flex-col gap-1 text-sm">
                <span className="font-medium text-slate-600">Date</span>
                <Input type="date" value={reportDate} onChange={(e) => setReportDate(e.target.value)} />
              </label>
            )}

            {reportType === "weekly" && (
              <label className="flex flex-col gap-1 text-sm">
                <span className="font-medium text-slate-600">Week starting</span>
                <Input type="date" value={weekStart} onChange={(e) => setWeekStart(e.target.value)} />
              </label>
            )}

            {showMonth && (
              <label className="flex flex-col gap-1 text-sm">
                <span className="font-medium text-slate-600">Month</span>
                <Input type="month" value={reportDate.slice(0, 7)} onChange={(e) => setReportDate(`${e.target.value}-01`)} />
              </label>
            )}

            {showRange && reportType !== "weekly" && (
              <>
                <label className="flex flex-col gap-1 text-sm">
                  <span className="font-medium text-slate-600">From</span>
                  <Input type="date" value={start} onChange={(e) => setStart(e.target.value)} />
                </label>
                <label className="flex flex-col gap-1 text-sm">
                  <span className="font-medium text-slate-600">To</span>
                  <Input type="date" value={end} onChange={(e) => setEnd(e.target.value)} />
                </label>
              </>
            )}

            {canAccessHR() && departments.length > 0 && (
              <label className="flex min-w-[180px] flex-col gap-1 text-sm">
                <span className="font-medium text-slate-600">Department</span>
                <select
                  className="h-10 rounded-lg border border-slate-200 bg-white px-3 shadow-sm"
                  value={departmentId}
                  onChange={(e) => setDepartmentId(e.target.value)}
                >
                  <option value="">All departments</option>
                  {departments.map((d) => (
                    <option key={d.id} value={d.id}>
                      {d.name}
                    </option>
                  ))}
                </select>
              </label>
            )}
          </div>

          <div className="flex flex-wrap items-center gap-2 border-t border-slate-100 pt-4">
            <span className="mr-2 text-sm font-medium text-slate-600">Export</span>
            <Button variant="outline" size="sm" disabled={!!exporting} onClick={() => download("csv")}>
              <FileText className="mr-2 h-4 w-4" />
              {exporting === "csv" ? "Exporting…" : "CSV"}
            </Button>
            <Button variant="outline" size="sm" disabled={!!exporting} onClick={() => download("xlsx")}>
              <FileSpreadsheet className="mr-2 h-4 w-4" />
              {exporting === "xlsx" ? "Exporting…" : "Excel"}
            </Button>
            <Button variant="outline" size="sm" disabled={!!exporting} onClick={() => download("pdf")}>
              <Download className="mr-2 h-4 w-4" />
              {exporting === "pdf" ? "Exporting…" : "PDF"}
            </Button>
            <span className="text-sm text-slate-500">
              {rows.length} row{rows.length === 1 ? "" : "s"}
            </span>
          </div>
          {exportError && (
            <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700" role="alert">
              {exportError}
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between">
          <CardTitle>Preview</CardTitle>
          {isError && (
            <p className="text-sm text-red-600">{error instanceof Error ? error.message : "Failed to load"}</p>
          )}
        </CardHeader>
        <CardContent className="table-scroll p-0 sm:overflow-x-auto">
          <table className="data-table min-w-[720px]">
            <thead>
              <tr>
                <th>Date</th>
                <th>Code</th>
                <th>Name</th>
                <th>Department</th>
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
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    Generating preview…
                  </td>
                </tr>
              ) : rows.length === 0 ? (
                <tr>
                  <td colSpan={9} className="py-12 text-center text-slate-500">
                    No records for this report. Try another date range or department.
                  </td>
                </tr>
              ) : (
                rows.map((r, i) => (
                  <tr key={`${r.employee_code}-${r.date ?? ""}-${i}`}>
                    <td className="font-medium">{r.date ?? "—"}</td>
                    <td>{r.employee_code}</td>
                    <td>{r.full_name}</td>
                    <td>{r.department || "—"}</td>
                    <td className="font-mono text-xs">
                      {r.check_in ? new Date(r.check_in).toLocaleTimeString() : "—"}
                    </td>
                    <td className="font-mono text-xs">
                      {r.check_out ? new Date(r.check_out).toLocaleTimeString() : "—"}
                    </td>
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
