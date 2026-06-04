"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useEffect, useState } from "react";

interface Profile {
  id: string;
  employee_code: string;
  full_name: string;
  email: string;
  phone: string | null;
  department: string | null;
  job_role: string | null;
  shift_name: string | null;
}

export default function ProfilePage() {
  const qc = useQueryClient();
  const { data: profile } = useQuery({
    queryKey: ["profile"],
    queryFn: () => apiFetch<Profile>("/api/me/profile"),
  });
  const [phone, setPhone] = useState("");
  const [pw, setPw] = useState({ current: "", next: "" });

  const updateProfile = useMutation({
    mutationFn: () =>
      apiFetch("/api/me/profile", { method: "PUT", body: JSON.stringify({ phone }) }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["profile"] }),
  });

  const changePassword = useMutation({
    mutationFn: () =>
      apiFetch("/api/auth/change-password", {
        method: "POST",
        body: JSON.stringify({ current_password: pw.current, new_password: pw.next }),
      }),
    onSuccess: () => setPw({ current: "", next: "" }),
  });

  useEffect(() => {
    if (profile?.phone) setPhone(profile.phone);
  }, [profile]);

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">My Profile</h2>
      {profile && (
        <Card>
          <CardHeader><CardTitle>{profile.full_name}</CardTitle></CardHeader>
          <CardContent className="space-y-2 text-sm">
            <p>Code: {profile.employee_code}</p>
            <p>Email: {profile.email}</p>
            <p>Department: {profile.department ?? "—"}</p>
            <p>Role: {profile.job_role ?? "—"}</p>
            <p>Shift: {profile.shift_name ?? "—"}</p>
            <Input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="Phone" />
            <Button onClick={() => updateProfile.mutate()}>Update phone</Button>
          </CardContent>
        </Card>
      )}
      <Card>
        <CardHeader><CardTitle>Change Password</CardTitle></CardHeader>
        <CardContent className="space-y-2 max-w-md">
          <Input type="password" placeholder="Current" value={pw.current} onChange={(e) => setPw({ ...pw, current: e.target.value })} />
          <Input type="password" placeholder="New" value={pw.next} onChange={(e) => setPw({ ...pw, next: e.target.value })} />
          <Button onClick={() => changePassword.mutate()}>Change password</Button>
        </CardContent>
      </Card>
    </div>
  );
}
