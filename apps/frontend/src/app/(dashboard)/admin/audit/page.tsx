"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

interface AuditLog {
  id: string;
  actor_id: string | null;
  action: string;
  resource: string;
  ip_address: string | null;
  created_at: string;
}

export default function AuditPage() {
  const [page, setPage] = useState(1);
  const pageSize = 25;

  const { data } = useQuery({
    queryKey: ["audit", page],
    queryFn: () =>
      apiFetch<{ items: AuditLog[]; total: number; pages: number }>(
        `/api/admin/audit?page=${page}&page_size=${pageSize}`
      ),
  });

  const logs = data?.items ?? [];
  const totalPages = data?.pages ?? 1;

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Audit Logs</h2>
      <Card>
        <CardHeader><CardTitle>Recent activity</CardTitle></CardHeader>
        <CardContent className="table-scroll p-0 sm:overflow-x-auto">
          <table className="data-table min-w-[640px]">
            <thead className="border-b bg-slate-50">
              <tr>
                <th className="p-3 text-left">Time</th>
                <th className="p-3 text-left">Action</th>
                <th className="p-3 text-left">Resource</th>
                <th className="p-3 text-left">IP</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((l) => (
                <tr key={l.id} className="border-b">
                  <td className="p-3">{new Date(l.created_at).toLocaleString()}</td>
                  <td className="p-3">{l.action}</td>
                  <td className="p-3">{l.resource}</td>
                  <td className="p-3">{l.ip_address || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3 text-sm">
              <span>Page {page} of {totalPages}</span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </Button>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
