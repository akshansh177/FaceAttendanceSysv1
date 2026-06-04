"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Shift } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function ShiftsPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    name: "Morning Shift",
    start_time: "09:00",
    end_time: "18:00",
    grace_minutes: "15",
    shift_type: "fixed",
  });

  const { data: shifts = [] } = useQuery({
    queryKey: ["shifts"],
    queryFn: () => apiFetch<Shift[]>("/api/shifts"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<Shift>("/api/shifts", {
        method: "POST",
        body: JSON.stringify({
          ...form,
          grace_minutes: parseInt(form.grace_minutes),
        }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shifts"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/shifts/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["shifts"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Shifts</h2>
      <Card>
        <CardHeader><CardTitle>Create Shift</CardTitle></CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Input value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} placeholder="Name" />
          <Input type="time" value={form.start_time} onChange={(e) => setForm({ ...form, start_time: e.target.value })} />
          <Input type="time" value={form.end_time} onChange={(e) => setForm({ ...form, end_time: e.target.value })} />
          <Input value={form.grace_minutes} onChange={(e) => setForm({ ...form, grace_minutes: e.target.value })} placeholder="Grace (min)" />
          <select
            className="h-10 rounded-lg border border-slate-300 px-3"
            value={form.shift_type}
            onChange={(e) => setForm({ ...form, shift_type: e.target.value })}
          >
            <option value="fixed">Fixed</option>
            <option value="rotational">Rotational</option>
            <option value="night">Night</option>
            <option value="flexible">Flexible</option>
          </select>
          <Button onClick={() => createMutation.mutate()}>Create</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {shifts.map((s) => (
            <div key={s.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{s.name}</p>
                <p className="text-sm text-slate-500">
                  {s.start_time} – {s.end_time} · {s.shift_type} · grace {s.grace_minutes}m
                </p>
              </div>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(s.id)}>Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
