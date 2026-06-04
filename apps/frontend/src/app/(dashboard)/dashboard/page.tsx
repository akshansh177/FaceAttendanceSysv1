"use client";

import dynamic from "next/dynamic";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { UserCheck, UserX, Clock3, LogOut, Timer } from "lucide-react";
import { apiFetch } from "@/lib/api";
import { getRole, canAccessHR } from "@/lib/auth";
import type { DashboardMetrics, DashboardTrends, EmployeeDashboard } from "@/lib/types";
import { Card, CardContent } from "@/components/ui/card";
import { StatCard } from "@/components/ui/stat-card";
import { PageHeader } from "@/components/layout/page-header";
import { LiveFeedPanel } from "@/components/dashboard/live-feed-panel";
import { DASHBOARD_STALE_MS, REPORT_STALE_MS } from "@/lib/react-query";

const DashboardCharts = dynamic(
  () => import("@/components/dashboard/dashboard-charts").then((m) => m.DashboardCharts),
  {
    ssr: false,
    loading: () => (
      <div className="grid gap-6 lg:grid-cols-2">
        <div className="h-[280px] animate-pulse rounded-2xl bg-slate-100 motion-reduce:animate-none" />
        <div className="h-[280px] animate-pulse rounded-2xl bg-slate-100 motion-reduce:animate-none" />
      </div>
    ),
  }
);

function MetricsDashboard({ metrics, trends, title }: { metrics?: DashboardMetrics; trends?: DashboardTrends; title: string }) {
  const stats = [
    { label: "Present today", value: metrics?.present_today ?? 0, accent: "green" as const, icon: UserCheck },
    { label: "Absent today", value: metrics?.absent_today ?? 0, accent: "red" as const, icon: UserX },
    { label: "Late today", value: metrics?.late_today ?? 0, accent: "amber" as const, icon: Clock3 },
    { label: "Missing checkout", value: metrics?.missing_checkout_today ?? 0, accent: "orange" as const, icon: LogOut },
    { label: "Overtime today", value: metrics?.overtime_today ?? 0, accent: "blue" as const, icon: Timer },
  ];

  return (
    <div className="app-page">
      <PageHeader
        title={title}
        description="Scan KPIs at a glance — trends and live kiosk events update automatically."
      />

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {stats.map((s) => (
          <StatCard key={s.label} label={s.label} value={s.value} accent={s.accent} icon={s.icon} />
        ))}
      </div>

      {canAccessHR() && <LiveFeedPanel />}

      <DashboardCharts metrics={metrics} trends={trends} />
    </div>
  );
}

function EmployeeDashboardView({ data }: { data?: EmployeeDashboard }) {
  return (
    <div className="app-page">
      <PageHeader
        title="My dashboard"
        description="Today's status and monthly attendance summary."
        actions={
          <Link
            href="/kiosk"
            target="_blank"
            className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-brand-700"
          >
            Open kiosk
          </Link>
        }
      />

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <StatCard
          label="Today status"
          value={data?.today_status ?? "—"}
          accent="blue"
          hint="Based on shift & punches"
        />
        <StatCard
          label="Workflow"
          value={data?.workflow_status?.replace(/_/g, " ") ?? "—"}
          accent="slate"
        />
        <StatCard label="Worked today" value={`${data?.worked_minutes ?? 0} min`} accent="green" icon={Timer} />
        <StatCard label="Attendance %" value={`${data?.attendance_percentage ?? 0}%`} accent="green" icon={UserCheck} />
        <StatCard label="Absent (month)" value={data?.monthly_absent ?? 0} accent="red" icon={UserX} />
      </div>

      <Card>
        <CardContent className="flex flex-col gap-4 p-6 sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="font-medium text-slate-900">Quick links</p>
            <p className="text-sm text-slate-500">Leave balance placeholder: {data?.leave_balance_placeholder ?? 0} days</p>
          </div>
          <div className="flex flex-wrap gap-2">
            <Link
              href="/attendance/me"
              className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              My attendance
            </Link>
            <Link
              href="/corrections"
              className="rounded-lg border border-slate-200 bg-white px-4 py-2 text-sm font-medium text-slate-700 hover:bg-slate-50"
            >
              Request correction
            </Link>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

export default function DashboardPage() {
  const role = getRole();

  const metricsPath =
    role === "team_manager" ? "/api/dashboard/manager" : role === "employee" ? null : "/api/dashboard/hr";

  const { data: metrics } = useQuery({
    queryKey: ["dashboard-metrics", role],
    queryFn: () => apiFetch<DashboardMetrics>(metricsPath!),
    enabled: !!metricsPath,
    staleTime: DASHBOARD_STALE_MS,
  });

  const { data: trends } = useQuery({
    queryKey: ["dashboard-trends"],
    queryFn: () => apiFetch<DashboardTrends>("/api/dashboard/trends?days=30"),
    enabled: role !== "employee",
    staleTime: REPORT_STALE_MS,
  });

  const { data: employeeData } = useQuery({
    queryKey: ["dashboard-employee"],
    queryFn: () => apiFetch<EmployeeDashboard>("/api/me/dashboard"),
    enabled: role === "employee",
    staleTime: DASHBOARD_STALE_MS,
  });

  if (role === "employee") {
    return <EmployeeDashboardView data={employeeData} />;
  }

  const title =
    role === "team_manager" ? "Team dashboard" : role === "hr_manager" ? "HR dashboard" : "Executive dashboard";

  return <MetricsDashboard metrics={metrics} trends={trends} title={title} />;
}
