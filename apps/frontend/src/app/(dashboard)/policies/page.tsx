"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { AttendancePolicy } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function PoliciesPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    scope_type: "department",
    scope_id: "",
    rules_json: '{"allowed_kiosk_ids": []}',
  });

  const { data: policies = [] } = useQuery({
    queryKey: ["policies"],
    queryFn: () => apiFetch<AttendancePolicy[]>("/api/policies"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<AttendancePolicy>("/api/policies", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          scope_type: form.scope_type,
          scope_id: form.scope_id || null,
          rules_json: JSON.parse(form.rules_json),
          priority: 100,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["policies"] });
      setForm({ name: "", scope_type: "department", scope_id: "", rules_json: '{"allowed_kiosk_ids": []}' });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/policies/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["policies"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Attendance Policies</h2>
      <Card>
        <CardHeader><CardTitle>Add Policy</CardTitle></CardHeader>
        <CardContent className="grid gap-2">
          <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <select
            className="rounded-md border px-3 py-2 text-sm"
            value={form.scope_type}
            onChange={(e) => setForm({ ...form, scope_type: e.target.value })}
          >
            <option value="employee">Employee</option>
            <option value="department">Department</option>
            <option value="job_role">Job Role</option>
            <option value="location">Location</option>
            <option value="shift">Shift</option>
          </select>
          <Input placeholder="Scope ID (optional)" value={form.scope_id} onChange={(e) => setForm({ ...form, scope_id: e.target.value })} />
          <textarea
            className="rounded-md border p-2 font-mono text-sm"
            rows={3}
            value={form.rules_json}
            onChange={(e) => setForm({ ...form, rules_json: e.target.value })}
          />
          <Button onClick={() => createMutation.mutate()} disabled={!form.name}>Add</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {policies.map((p) => (
            <div key={p.id} className="flex justify-between p-4">
              <div>
                <p className="font-medium">{p.name}</p>
                <p className="text-sm text-slate-500">{p.scope_type} · priority {p.priority}</p>
              </div>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(p.id)}>Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
