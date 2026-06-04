"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Location } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function LocationsPage() {
  const qc = useQueryClient();
  const [form, setForm] = useState({
    name: "",
    address: "",
    latitude: "",
    longitude: "",
    radius_meters: "200",
  });

  const { data: locations = [] } = useQuery({
    queryKey: ["locations"],
    queryFn: () => apiFetch<Location[]>("/api/locations"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<Location>("/api/locations", {
        method: "POST",
        body: JSON.stringify({
          name: form.name,
          address: form.address || null,
          latitude: parseFloat(form.latitude),
          longitude: parseFloat(form.longitude),
          radius_meters: parseInt(form.radius_meters, 10),
          is_active: true,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["locations"] });
      setForm({ name: "", address: "", latitude: "", longitude: "", radius_meters: "200" });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/locations/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["locations"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Locations</h2>
      <Card>
        <CardHeader><CardTitle>Add Location</CardTitle></CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
          <Input placeholder="Name" value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} />
          <Input placeholder="Address" value={form.address} onChange={(e) => setForm({ ...form, address: e.target.value })} />
          <Input placeholder="Latitude" value={form.latitude} onChange={(e) => setForm({ ...form, latitude: e.target.value })} />
          <Input placeholder="Longitude" value={form.longitude} onChange={(e) => setForm({ ...form, longitude: e.target.value })} />
          <Input placeholder="Radius (m)" value={form.radius_meters} onChange={(e) => setForm({ ...form, radius_meters: e.target.value })} />
          <Button onClick={() => createMutation.mutate()} disabled={!form.name || !form.latitude || !form.longitude}>Add</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {locations.map((loc) => (
            <div key={loc.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{loc.name}</p>
                <p className="text-sm text-slate-500">
                  {loc.latitude}, {loc.longitude} · {loc.radius_meters}m radius
                </p>
              </div>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(loc.id)}>Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
