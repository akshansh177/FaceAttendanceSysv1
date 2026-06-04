"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Holiday } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function HolidaysPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", date: "", scope: "global" });

  const { data: holidays = [] } = useQuery({
    queryKey: ["holidays"],
    queryFn: () => apiFetch<Holiday[]>("/api/holidays"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<Holiday>("/api/holidays", { method: "POST", body: JSON.stringify(form) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/holidays/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["holidays"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Holidays</h2>
      <Card>
        <CardHeader><CardTitle>Add Holiday</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input type="date" value={form.date} onChange={(e) => setForm({ ...form, date: e.target.value })} />
          <Button onClick={() => createMutation.mutate()}>Add</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {holidays.map((h) => (
            <div key={h.id} className="flex justify-between p-4">
              <span>{h.name} — {h.date} ({h.scope})</span>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(h.id)}>Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
