"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ScanFace, ShieldCheck, Camera } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent } from "@/components/ui/card";
import { apiFetch, clearTokens, setTokens } from "@/lib/api";
import { setRole } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [mounted, setMounted] = useState(false);
  const [email, setEmail] = useState("");
  const [employeeCode, setEmployeeCode] = useState("");
  const [useCode, setUseCode] = useState(false);
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    setMounted(true);
    clearTokens();
  }, []);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const data = await apiFetch<{
        access_token: string;
        refresh_token: string;
        role: string;
      }>("/api/auth/login", {
        method: "POST",
        body: JSON.stringify(
          useCode ? { employee_code: employeeCode, password } : { email, password }
        ),
      });
      setTokens(data.access_token, data.refresh_token);
      setRole(data.role);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-[var(--background)]">
      <section className="relative hidden w-[42%] flex-col justify-between overflow-hidden bg-gradient-to-br from-[var(--brand)] via-[var(--brand-light)] to-[var(--brand-dark)] p-10 text-white lg:flex">
        <div className="relative z-10">
          <div className="mb-8 flex h-12 w-12 items-center justify-center rounded-2xl bg-white/15 backdrop-blur">
            <ScanFace className="h-7 w-7" aria-hidden />
          </div>
          <h1 className="text-3xl font-bold leading-tight">Face Attendance</h1>
          <p className="mt-3 max-w-sm text-lg text-blue-100">
            Secure check-in, real-time dashboards, and workforce insights in one place.
          </p>
        </div>
        <ul className="relative z-10 space-y-4 text-sm text-blue-100">
          <li className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-300" />
            Face recognition kiosk with liveness detection
          </li>
          <li className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-300" />
            Role-based HR, manager, and employee portals
          </li>
          <li className="flex items-start gap-3">
            <ShieldCheck className="mt-0.5 h-5 w-5 shrink-0 text-emerald-300" />
            Attendance policies, corrections, and live feed
          </li>
        </ul>
        <div className="pointer-events-none absolute -right-20 -top-20 h-80 w-80 rounded-full bg-white/10 blur-3xl" />
      </section>

      <section className="flex flex-1 items-center justify-center p-6 md:p-10">
        <div className="w-full max-w-md">
          <div className="mb-8 lg:hidden">
            <div className="mb-3 flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--brand)] text-white shadow-lg">
              <ScanFace className="h-6 w-6" />
            </div>
            <h1 className="text-2xl font-bold text-[var(--foreground)]">Sign in</h1>
            <p className="text-[var(--foreground-muted)]">Face Attendance Management</p>
          </div>

          <Card className="shadow-panel">
            <CardContent className="p-8">
              <div className="mb-6 hidden lg:block">
                <h2 className="text-xl font-bold text-[var(--foreground)]">Welcome back</h2>
                <p className="text-sm text-[var(--foreground-muted)]">Sign in to your account</p>
              </div>

              {!mounted ? (
                <div className="space-y-4" aria-hidden="true">
                  <div className="h-11 rounded-lg bg-slate-100" />
                  <div className="h-11 rounded-lg bg-slate-100" />
                  <div className="h-11 rounded-lg bg-slate-200" />
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-5" suppressHydrationWarning>
                  <div className="flex rounded-full bg-[var(--brand-muted)] p-1">
                    <button
                      type="button"
                      className={`flex-1 rounded-md py-2 text-sm font-medium transition ${
                        !useCode ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                      }`}
                      onClick={() => setUseCode(false)}
                    >
                      Email
                    </button>
                    <button
                      type="button"
                      className={`flex-1 rounded-md py-2 text-sm font-medium transition ${
                        useCode ? "bg-white text-slate-900 shadow-sm" : "text-slate-600"
                      }`}
                      onClick={() => setUseCode(true)}
                    >
                      Employee code
                    </button>
                  </div>

                  {useCode ? (
                    <div>
                      <label className="mb-1.5 block text-sm font-medium text-slate-700">Employee code</label>
                      <Input
                        value={employeeCode}
                        onChange={(e) => setEmployeeCode(e.target.value)}
                        required
                        placeholder="EMP001"
                        className="h-11"
                        suppressHydrationWarning
                      />
                    </div>
                  ) : (
                    <div>
                      <label className="mb-1.5 block text-sm font-medium text-slate-700">Email</label>
                      <Input
                        type="email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        autoComplete="email"
                        className="h-11"
                        suppressHydrationWarning
                      />
                    </div>
                  )}
                  <div>
                    <label className="mb-1.5 block text-sm font-medium text-slate-700">Password</label>
                    <Input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      required
                      autoComplete="current-password"
                      className="h-11"
                      suppressHydrationWarning
                    />
                  </div>
                  {error && (
                    <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-700 ring-1 ring-red-100" role="alert">
                      {error}
                    </p>
                  )}
                  <Button type="submit" className="h-11 w-full text-base" disabled={loading}>
                    {loading ? "Signing in…" : "Sign in"}
                  </Button>
                </form>
              )}
            </CardContent>
          </Card>

          <Link
            href="/kiosk"
            className="theme-btn-primary mt-6 flex w-full items-center justify-center gap-2.5 py-3.5 text-base font-semibold shadow-panel"
          >
            <Camera className="h-5 w-5 shrink-0" aria-hidden />
            Click for Attendance
          </Link>
        </div>
      </section>
    </div>
  );
}
