"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { LeaveRequest } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { canAccessHR } from "@/lib/auth";

export default function LeavesPage() {
  const qc = useQueryClient();
  const hr = canAccessHR();

  const { data: leaves = [] } = useQuery({
    queryKey: ["leaves"],
    queryFn: () => apiFetch<LeaveRequest[]>("/api/leaves"),
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, status }: { id: string; status: string }) =>
      apiFetch(`/api/leaves/${id}`, {
        method: "PATCH",
        body: JSON.stringify({ status }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["leaves"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Leave Requests</h2>
      <Card>
        <CardContent className="divide-y p-0">
          {leaves.map((l) => (
            <div key={l.id} className="flex flex-wrap items-center justify-between gap-2 p-4">
              <div>
                <p className="font-medium">{l.start_date} → {l.end_date}</p>
                <p className="text-sm text-slate-500">{l.reason || "No reason"} · {l.status}</p>
              </div>
              {hr && l.status === "pending" && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => updateMutation.mutate({ id: l.id, status: "approved" })}>Approve</Button>
                  <Button size="sm" variant="destructive" onClick={() => updateMutation.mutate({ id: l.id, status: "rejected" })}>Reject</Button>
                </div>
              )}
            </div>
          ))}
          {leaves.length === 0 && <p className="p-4 text-slate-500">No leave requests</p>}
        </CardContent>
      </Card>
    </div>
  );
}
