"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { JobRole } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function JobRolesPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const { data: roles = [] } = useQuery({
    queryKey: ["job-roles"],
    queryFn: () => apiFetch<JobRole[]>("/api/job-roles"),
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<JobRole>("/api/job-roles", {
        method: "POST",
        body: JSON.stringify({ name, description: description || null }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["job-roles"] });
      setName("");
      setDescription("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/job-roles/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["job-roles"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Job Roles</h2>
      <Card>
        <CardHeader><CardTitle>Add Job Role</CardTitle></CardHeader>
        <CardContent className="grid gap-2 sm:grid-cols-3">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Role name" />
          <Input value={description} onChange={(e) => setDescription(e.target.value)} placeholder="Description" />
          <Button onClick={() => createMutation.mutate()} disabled={!name}>Add</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {roles.map((r) => (
            <div key={r.id} className="flex items-center justify-between p-4">
              <div>
                <p className="font-medium">{r.name}</p>
                {r.description && <p className="text-sm text-slate-500">{r.description}</p>}
              </div>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(r.id)}>Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
