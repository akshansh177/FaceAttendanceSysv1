"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiFetch } from "@/lib/api";
import type { AttendanceSettings } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { useEffect, useState } from "react";

const METHODS = [
  { value: "kiosk_only", label: "Kiosk only" },
  { value: "portal_only", label: "Employee portal only" },
  { value: "kiosk_portal", label: "Kiosk + portal" },
  { value: "mobile_app", label: "Mobile app (API placeholder)" },
  { value: "any", label: "Any method" },
];

const MODES = [
  { value: "face_only", label: "Face only" },
  { value: "face_gps", label: "Face + GPS" },
  { value: "face_network", label: "Face + office network" },
  { value: "face_gps_device", label: "Face + GPS + registered device" },
];

export default function AttendanceSettingsPage() {
  const qc = useQueryClient();
  const { data } = useQuery({
    queryKey: ["attendance-settings"],
    queryFn: () => apiFetch<AttendanceSettings>("/api/settings/attendance"),
  });

  const [form, setForm] = useState({
    attendance_mode: "face_only",
    attendance_method: "kiosk_portal",
    gps_enforcement_enabled: false,
    device_enforcement_enabled: false,
    allowed_ip_cidrs: "",
    kiosk_checkout_after_checkout: "ignore",
    kiosk_screen_reset_seconds: 5,
    voice_feedback_enabled: true,
    voice_language: "en",
    match_threshold_preset: "balanced",
    match_threshold: "" as string | number,
  });

  useEffect(() => {
    if (data) {
      setForm({
        attendance_mode: data.attendance_mode,
        attendance_method: data.attendance_method,
        gps_enforcement_enabled: data.gps_enforcement_enabled,
        device_enforcement_enabled: data.device_enforcement_enabled,
        allowed_ip_cidrs: (data.allowed_ip_cidrs ?? []).join("\n"),
        kiosk_checkout_after_checkout: data.kiosk_checkout_after_checkout,
        kiosk_screen_reset_seconds: data.kiosk_screen_reset_seconds,
        voice_feedback_enabled: data.voice_feedback_enabled,
        voice_language: data.voice_language,
        match_threshold_preset: data.match_threshold_preset ?? "balanced",
        match_threshold: data.match_threshold ?? "",
      });
    }
  }, [data]);

  const saveMutation = useMutation({
    mutationFn: () =>
      apiFetch<AttendanceSettings>("/api/settings/attendance", {
        method: "PUT",
        body: JSON.stringify({
          ...form,
          match_threshold: form.match_threshold === "" ? null : Number(form.match_threshold),
          allowed_ip_cidrs: form.allowed_ip_cidrs
            .split("\n")
            .map((s) => s.trim())
            .filter(Boolean),
        }),
      }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["attendance-settings"] }),
  });

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">Attendance Settings</h2>
      <Card>
        <CardHeader><CardTitle>Face match threshold</CardTitle></CardHeader>
        <CardContent className="max-w-xl space-y-4">
          <div>
            <p className="mb-1 text-sm font-medium">Security preset</p>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              value={form.match_threshold_preset}
              onChange={(e) => setForm({ ...form, match_threshold_preset: e.target.value })}
            >
              <option value="high_security">High security (0.80)</option>
              <option value="balanced">Balanced (0.70)</option>
              <option value="convenience">Convenience (0.65)</option>
            </select>
          </div>
          <div>
            <p className="mb-1 text-sm font-medium">Custom threshold (optional, overrides preset)</p>
            <Input
              type="number"
              step="0.01"
              min={0.5}
              max={0.95}
              placeholder="e.g. 0.75"
              value={form.match_threshold}
              onChange={(e) => setForm({ ...form, match_threshold: e.target.value })}
            />
          </div>
          {data?.effective_match_threshold != null && (
            <p className="text-sm text-slate-500">
              Effective threshold: <strong>{data.effective_match_threshold}</strong>
            </p>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle>Validation Mode</CardTitle></CardHeader>
        <CardContent className="max-w-xl space-y-4">
          <div>
            <p className="mb-1 text-sm font-medium">Attendance method</p>
            <select
              className="w-full rounded-md border border-slate-300 px-3 py-2"
              value={form.attendance_method}
              onChange={(e) => setForm({ ...form, attendance_method: e.target.value })}
            >
              {METHODS.map((m) => (
                <option key={m.value} value={m.value}>{m.label}</option>
              ))}
            </select>
          </div>
          <select
            className="w-full rounded-md border border-slate-300 px-3 py-2"
            value={form.attendance_mode}
            onChange={(e) => setForm({ ...form, attendance_mode: e.target.value })}
          >
            {MODES.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.gps_enforcement_enabled}
              onChange={(e) => setForm({ ...form, gps_enforcement_enabled: e.target.checked })}
            />
            Enforce GPS (within assigned location radius)
          </label>
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.device_enforcement_enabled}
              onChange={(e) => setForm({ ...form, device_enforcement_enabled: e.target.checked })}
            />
            Enforce registered device
          </label>
          <div>
            <p className="mb-1 text-sm text-slate-600">After checkout (kiosk rescan)</p>
            <select
              className="w-full rounded-md border px-3 py-2 text-sm"
              value={form.kiosk_checkout_after_checkout}
              onChange={(e) => setForm({ ...form, kiosk_checkout_after_checkout: e.target.value })}
            >
              <option value="ignore">Ignore (show already checked out)</option>
              <option value="update">Update checkout time</option>
            </select>
          </div>
          <Input
            type="number"
            placeholder="Screen reset seconds"
            value={form.kiosk_screen_reset_seconds}
            onChange={(e) => setForm({ ...form, kiosk_screen_reset_seconds: parseInt(e.target.value, 10) || 5 })}
          />
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={form.voice_feedback_enabled}
              onChange={(e) => setForm({ ...form, voice_feedback_enabled: e.target.checked })}
            />
            Voice feedback on kiosk
          </label>
          <select
            className="w-full rounded-md border px-3 py-2 text-sm"
            value={form.voice_language}
            onChange={(e) => setForm({ ...form, voice_language: e.target.value })}
          >
            <option value="en">English</option>
            <option value="hi">Hindi</option>
          </select>
          <div>
            <p className="mb-1 text-sm text-slate-600">Allowed office IP CIDRs (one per line)</p>
            <textarea
              className="w-full rounded-md border border-slate-300 p-2 text-sm"
              rows={4}
              value={form.allowed_ip_cidrs}
              onChange={(e) => setForm({ ...form, allowed_ip_cidrs: e.target.value })}
              placeholder="10.0.0.0/8&#10;192.168.1.0/24"
            />
          </div>
          <Button onClick={() => saveMutation.mutate()} disabled={saveMutation.isPending}>
            {saveMutation.isPending ? "Saving..." : "Save Settings"}
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
