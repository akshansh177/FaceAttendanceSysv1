"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Kiosk, KioskCreateResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function KiosksPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({ name: "", device_identifier: "" });
  const [newKey, setNewKey] = useState<string | null>(null);

  const { data: kiosks = [] } = useQuery({
    queryKey: ["kiosks"],
    queryFn: () => apiFetch<Kiosk[]>("/api/kiosks"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<KioskCreateResponse>("/api/kiosks", {
        method: "POST",
        body: JSON.stringify({ ...form, status: "active" }),
      }),
    onSuccess: (data) => {
      setNewKey(data.api_key);
      qc.invalidateQueries({ queryKey: ["kiosks"] });
      setForm({ name: "", device_identifier: "" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/kiosks/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["kiosks"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Attendance Kiosks</h2>
      {newKey && (
        <Card className="border-amber-300 bg-amber-50">
          <CardContent className="pt-6">
            <p className="font-medium text-amber-900">Save this API key now (shown once):</p>
            <code className="mt-2 block break-all rounded bg-white p-2 text-sm">{newKey}</code>
            <Button className="mt-2" size="sm" onClick={() => setNewKey(null)}>Dismiss</Button>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader><CardTitle>Register Kiosk</CardTitle></CardHeader>
        <CardContent className="flex flex-wrap gap-2">
          <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="Device ID" value={form.device_identifier} onChange={(e) => setForm({ ...form, device_identifier: e.target.value })} />
          <Button onClick={() => createMutation.mutate()} disabled={!form.name || !form.device_identifier}>Create</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {kiosks.map((k) => (
            <div key={k.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{k.name}</p>
                <p className="text-sm text-slate-500">
                  {k.device_identifier} · {k.status}
                  {k.is_online ? " · online" : " · offline"}
                </p>
              </div>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(k.id)}>Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
