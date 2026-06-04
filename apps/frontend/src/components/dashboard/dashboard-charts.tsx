"use client";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import type { DashboardMetrics, DashboardTrends } from "@/lib/types";

const COLORS = ["#2563eb", "#059669", "#d97706", "#dc2626"];

type DashboardChartsProps = {
  metrics?: DashboardMetrics;
  trends?: DashboardTrends;
};

export function DashboardCharts({ metrics, trends }: DashboardChartsProps) {
  if (!trends) return null;

  const trendData =
    trends.dates.map((d, i) => ({
      date: d.slice(5),
      present: trends.present[i],
      absent: trends.absent[i],
      late: trends.late[i],
    })) ?? [];

  const pieData =
    metrics?.department_breakdown.map((d) => ({
      name: d.department,
      value: d.present,
    })) ?? [];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Attendance trend (30 days)</CardTitle>
        </CardHeader>
        <CardContent className="min-w-0">
          <div className="h-[220px] w-full min-w-0 sm:h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #e2e8f0" }} />
                <Legend />
                <Line type="monotone" dataKey="present" stroke="#2563eb" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="absent" stroke="#dc2626" strokeWidth={2} dot={false} isAnimationActive={false} />
                <Line type="monotone" dataKey="late" stroke="#d97706" strokeWidth={2} dot={false} isAnimationActive={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>

      {pieData.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Department attendance</CardTitle>
          </CardHeader>
          <CardContent className="min-w-0">
            <div className="h-[220px] w-full min-w-0 sm:h-[280px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={pieData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius="70%" label isAnimationActive={false}>
                    {pieData.map((_, i) => (
                      <Cell key={i} fill={COLORS[i % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: 8 }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}

      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Weekly present count</CardTitle>
        </CardHeader>
        <CardContent className="min-w-0">
          <div className="h-[200px] w-full min-w-0 sm:h-[240px]">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={trendData.slice(-7)}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                <XAxis dataKey="date" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} width={32} />
                <Tooltip contentStyle={{ borderRadius: 8 }} />
                <Bar dataKey="present" fill="#2563eb" radius={[6, 6, 0, 0]} isAnimationActive={false} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
