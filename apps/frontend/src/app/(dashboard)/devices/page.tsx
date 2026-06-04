"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Device, Location } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function DevicesPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    device_id: "",
    name: "",
    mac_address: "",
    device_type: "kiosk",
    status: "pending",
    location_id: "",
  });

  const { data: devices = [] } = useQuery({
    queryKey: ["devices"],
    queryFn: () => apiFetch<Device[]>("/api/devices"),
  });

  const { data: locations = [] } = useQuery({
    queryKey: ["locations"],
    queryFn: () => apiFetch<Location[]>("/api/locations"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<Device>("/api/devices", {
        method: "POST",
        body: JSON.stringify({
          device_id: form.device_id,
          name: form.name,
          mac_address: form.mac_address || null,
          device_type: form.device_type,
          status: form.status,
          location_id: form.location_id || null,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["devices"] });
      setForm({ device_id: "", name: "", mac_address: "", device_type: "kiosk", status: "pending", location_id: "" });
    },
  });

  const approveMutation = useMutation({
    mutationFn: (id: string) =>
      apiFetch<Device>(`/api/devices/${id}`, {
        method: "PUT",
        body: JSON.stringify({ status: "approved" }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["devices"] }),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/devices/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["devices"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Devices</h2>
      <Card>
        <CardHeader><CardTitle>Register Device</CardTitle></CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <Input placeholder="Device ID" value={form.device_id} onChange={(e) => setForm({ ...form, device_id: e.target.value })} />
          <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="MAC (optional)" value={form.mac_address} onChange={(e) => setForm({ ...form, mac_address: e.target.value })} />
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.device_type}
            onChange={(e) => setForm({ ...form, device_type: e.target.value })}
          >
            <option value="kiosk">Kiosk</option>
            <option value="mobile">Mobile</option>
            <option value="tablet">Tablet</option>
          </select>
          <select
            className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            value={form.location_id}
            onChange={(e) => setForm({ ...form, location_id: e.target.value })}
          >
            <option value="">No location</option>
            {locations.map((l) => (
              <option key={l.id} value={l.id}>{l.name}</option>
            ))}
          </select>
          <Button onClick={() => createMutation.mutate()} disabled={!form.device_id || !form.name}>Add</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {devices.map((d) => (
            <div key={d.id} className="flex flex-wrap items-center justify-between gap-2 p-4">
              <div>
                <p className="font-medium">{d.name} ({d.device_id})</p>
                <p className="text-sm text-slate-500 capitalize">
                  {d.device_type} · {d.status}
                  {d.mac_address && ` · ${d.mac_address}`}
                </p>
              </div>
              <div className="flex gap-2">
                {d.status !== "approved" && (
                  <Button size="sm" onClick={() => approveMutation.mutate(d.id)}>Approve</Button>
                )}
                <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(d.id)}>Delete</Button>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
