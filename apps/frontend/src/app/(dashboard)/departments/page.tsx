"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { Department } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function DepartmentsPage() {
  const qc = useQueryClient();
  const [name, setName] = useState("");

  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: () => apiFetch<Department[]>("/api/departments"),
  });

  const createMutation = useMutation({
    mutationFn: () => apiFetch<Department>("/api/departments", { method: "POST", body: JSON.stringify({ name }) }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["departments"] });
      setName("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/departments/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["departments"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Departments</h2>
      <Card>
        <CardHeader><CardTitle>Add Department</CardTitle></CardHeader>
        <CardContent className="flex gap-2">
          <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Department name" />
          <Button onClick={() => createMutation.mutate()} disabled={!name}>Add</Button>
        </CardContent>
      </Card>
      <Card>
        <CardContent className="divide-y p-0">
          {departments.map((d) => (
            <div key={d.id} className="flex items-center justify-between p-4">
              <span>{d.name}</span>
              <Button variant="destructive" size="sm" onClick={() => deleteMutation.mutate(d.id)}>Delete</Button>
            </div>
          ))}
        </CardContent>
      </Card>
    </div>
  );
}
