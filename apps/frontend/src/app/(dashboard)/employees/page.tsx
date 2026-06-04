"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import Link from "next/link";
import { apiFetch } from "@/lib/api";
import { REFERENCE_STALE_MS } from "@/lib/react-query";
import type { Employee, Department, JobRole, Location, Shift } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useState } from "react";

export default function EmployeesPage() {
  const qc = useQueryClient();
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({
    employee_code: "",
    full_name: "",
    email: "",
    phone: "",
    department_id: "",
    job_role_id: "",
    shift_id: "",
    employment_type: "full_time",
    joining_date: "",
    location_ids: [] as string[],
  });

  const [page, setPage] = useState(1);
  const pageSize = 25;

  const { data: employeePage, isLoading } = useQuery({
    queryKey: ["employees", page],
    queryFn: () =>
      apiFetch<{ items: Employee[]; total: number; pages: number }>(
        `/api/employees?page=${page}&page_size=${pageSize}`
      ),
  });
  const employees = employeePage?.items ?? [];
  const totalPages = employeePage?.pages ?? 1;

  const { data: departments = [] } = useQuery({
    queryKey: ["departments"],
    queryFn: () => apiFetch<Department[]>("/api/departments"),
    staleTime: REFERENCE_STALE_MS,
  });

  const { data: jobRoles = [] } = useQuery({
    queryKey: ["job-roles"],
    queryFn: () => apiFetch<JobRole[]>("/api/job-roles"),
    staleTime: REFERENCE_STALE_MS,
  });

  const { data: shifts = [] } = useQuery({
    queryKey: ["shifts"],
    queryFn: () => apiFetch<Shift[]>("/api/shifts"),
    staleTime: REFERENCE_STALE_MS,
  });

  const { data: locations = [] } = useQuery({
    queryKey: ["locations"],
    queryFn: () => apiFetch<Location[]>("/api/locations"),
    staleTime: REFERENCE_STALE_MS,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      apiFetch<Employee>("/api/employees", {
        method: "POST",
        body: JSON.stringify({
          employee_code: form.employee_code,
          full_name: form.full_name,
          email: form.email,
          phone: form.phone || null,
          department_id: form.department_id || null,
          job_role_id: form.job_role_id || null,
          shift_id: form.shift_id || null,
          employment_type: form.employment_type,
          joining_date: form.joining_date || null,
          location_ids: form.location_ids,
        }),
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["employees"] });
      setShowForm(false);
      setForm({
        employee_code: "",
        full_name: "",
        email: "",
        phone: "",
        department_id: "",
        job_role_id: "",
        shift_id: "",
        employment_type: "full_time",
        joining_date: "",
        location_ids: [],
      });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => apiFetch(`/api/employees/${id}`, { method: "DELETE" }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["employees"] }),
  });

  const toggleLocation = (id: string) => {
    setForm((f) => ({
      ...f,
      location_ids: f.location_ids.includes(id)
        ? f.location_ids.filter((x) => x !== id)
        : [...f.location_ids, id],
    }));
  };

  return (
    <div className="app-page">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <h2 className="text-2xl font-bold tracking-tight text-slate-900 md:text-3xl">Employees</h2>
        <Button className="w-full sm:w-auto" onClick={() => setShowForm(!showForm)}>
          {showForm ? "Cancel" : "Add Employee"}
        </Button>
      </div>

      {showForm && (
        <Card>
          <CardHeader>
            <CardTitle>New Employee</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-4 sm:grid-cols-2">
            <Input placeholder="Code" value={form.employee_code} onChange={(e) => setForm({ ...form, employee_code: e.target.value })} />
            <Input placeholder="Full name" value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            <Input placeholder="Email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} />
            <Input placeholder="Phone" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })} />
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.department_id}
              onChange={(e) => setForm({ ...form, department_id: e.target.value })}
            >
              <option value="">Department</option>
              {departments.map((d) => (
                <option key={d.id} value={d.id}>{d.name}</option>
              ))}
            </select>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.job_role_id}
              onChange={(e) => setForm({ ...form, job_role_id: e.target.value })}
            >
              <option value="">Job role</option>
              {jobRoles.map((r) => (
                <option key={r.id} value={r.id}>{r.name}</option>
              ))}
            </select>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.shift_id}
              onChange={(e) => setForm({ ...form, shift_id: e.target.value })}
            >
              <option value="">Shift</option>
              {shifts.map((s) => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
            <select
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
              value={form.employment_type}
              onChange={(e) => setForm({ ...form, employment_type: e.target.value })}
            >
              <option value="full_time">Full time</option>
              <option value="part_time">Part time</option>
              <option value="contract">Contract</option>
              <option value="intern">Intern</option>
            </select>
            <Input type="date" value={form.joining_date} onChange={(e) => setForm({ ...form, joining_date: e.target.value })} />
            <div className="sm:col-span-2">
              <p className="mb-2 text-sm font-medium">Assigned locations</p>
              <div className="flex flex-wrap gap-2">
                {locations.map((loc) => (
                  <label key={loc.id} className="flex items-center gap-1 rounded border px-2 py-1 text-sm">
                    <input
                      type="checkbox"
                      checked={form.location_ids.includes(loc.id)}
                      onChange={() => toggleLocation(loc.id)}
                    />
                    {loc.name}
                  </label>
                ))}
              </div>
            </div>
            <Button onClick={() => createMutation.mutate()} disabled={createMutation.isPending}>
              Save
            </Button>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardContent className="p-0">
          <div className="table-scroll">
            <table className="data-table min-w-[800px]">
              <thead className="border-b bg-slate-50">
                <tr>
                  <th className="p-3 text-left">Code</th>
                  <th className="p-3 text-left">Name</th>
                  <th className="p-3 text-left">Type</th>
                  <th className="p-3 text-left">Status</th>
                  <th className="p-3 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                {isLoading ? (
                  <tr><td colSpan={5} className="p-4 text-center">Loading...</td></tr>
                ) : employees.map((e) => (
                  <tr key={e.id} className="border-b">
                    <td className="p-3">{e.employee_code}</td>
                    <td className="p-3">{e.full_name}</td>
                    <td className="p-3 capitalize">{e.employment_type?.replace("_", " ")}</td>
                    <td className="p-3">{e.status}</td>
                    <td className="p-3 space-x-2">
                      <Link href={`/faces/enroll/${e.id}`} className="text-brand-600 hover:underline">
                        Enroll Face
                      </Link>
                      <button
                        className="text-red-600 hover:underline"
                        onClick={() => deleteMutation.mutate(e.id)}
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t px-4 py-3 text-sm">
              <span className="text-slate-500">
                Page {page} of {totalPages} ({employeePage?.total ?? 0} employees)
              </span>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </Button>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
