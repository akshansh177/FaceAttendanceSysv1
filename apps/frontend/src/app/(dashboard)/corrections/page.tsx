"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { canAccessHR, canAccessManager, getRole } from "@/lib/auth";
import type { Correction } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function CorrectionsPage() {
  const qc = useQueryClient();
  const role = getRole();
  const canApprove = canAccessManager() || canAccessHR();
  const isEmployee = role === "employee";

  const [form, setForm] = useState({
    date: new Date().toISOString().slice(0, 10),
    requested_check_in: "",
    requested_check_out: "",
    reason: "",
  });

  const { data: corrections = [] } = useQuery({
    queryKey: ["corrections"],
    queryFn: () => apiFetch<Correction[]>("/api/attendance/corrections"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<Correction>("/api/attendance/corrections", {
        method: "POST",
        body: JSON.stringify({
          date: form.date,
          requested_check_in: form.requested_check_in ? new Date(form.requested_check_in).toISOString() : null,
          requested_check_out: form.requested_check_out ? new Date(form.requested_check_out).toISOString() : null,
          reason: form.reason,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["corrections"] });
      setForm({ date: form.date, requested_check_in: "", requested_check_out: "", reason: "" });
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch<Correction>(`/api/attendance/corrections/${id}/approve`, { method: "PATCH" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["corrections"] }),
  });

  const rejectMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch<Correction>(`/api/attendance/corrections/${id}/reject`, { method: "PATCH" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["corrections"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Attendance Corrections</h2>

      {isEmployee && (
        <Card>
          <CardHeader><CardTitle>Request Correction</CardTitle></CardHeader>
          <CardContent className="grid gap-3 sm:grid-cols-2">
            <Input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
            <Input
              type="datetime-local"
              placeholder="Check-in"
              value={form.requested_check_in}
              onChange={(e) => setForm({ ...form, requested_check_in: e.target.value })}
            />
            <Input
              type="datetime-local"
              placeholder="Check-out"
              value={form.requested_check_out}
              onChange={(e) => setForm({ ...form, requested_check_out: e.target.value })}
            />
            <Input
              className="sm:col-span-2"
              placeholder="Reason"
              value={form.reason}
              onChange={(e) => setForm({ ...form, reason: e.target.value })}
            />
            <Button onClick={() => createMutation.mutate()} disabled={!form.reason || createMutation.isPending}>
              Submit
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader><CardTitle>Requests</CardTitle></CardHeader>
        <CardContent className="divide-y p-0">
          {corrections.length === 0 && <p className="p-4 text-slate-500">No correction requests.</p>}
          {corrections.map((c) => (
            <div key={c.id} className="flex flex-wrap items-center justify-between gap-2 p-4">
              <div>
                <p className="font-medium">{c.date} — {c.status.replace(/_/g, " ")}</p>
                <p className="text-sm text-slate-500">{c.reason}</p>
              </div>
              {canApprove && (c.status === "pending_manager" || c.status === "pending_hr") && (
                <div className="flex gap-2">
                  <Button size="sm" onClick={() => approveMutation.mutate(c.id)}>Approve</Button>
                  <Button size="sm" variant="destructive" onClick={() => rejectMutation.mutate(c.id)}>Reject</Button>
                </div>
              )}
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
