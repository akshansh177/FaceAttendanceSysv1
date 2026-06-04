"use client";

import type { KioskAttendanceAction } from "@/lib/kiosk-api";
import type { KioskRecognizeResponse } from "@/lib/types";

export function IconCheckIn({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M15 3h4a2 2 0 012 2v14a2 2 0 01-2 2h-4M10 17l5-5-5-5M13.8 12H3" />
    </svg>
  );
}

export function IconCheckOut({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M14 7l5 5-5 5M10.2 12H21" />
    </svg>
  );
}

export function IconSuccess({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" aria-hidden>
      <circle cx="12" cy="12" r="10" />
      <path strokeLinecap="round" strokeLinejoin="round" d="M8 12l3 3 5-6" />
    </svg>
  );
}

export function IconWarning({ className }: { className?: string }) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
      <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v4m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
    </svg>
  );
}

export function CaptureProgress({ step, total }: { step: number; total: number }) {
  return (
    <div className="flex flex-col items-center gap-3" role="progressbar" aria-valuenow={step} aria-valuemin={0} aria-valuemax={total}>
      <p className="text-sm font-medium text-slate-300">Capturing face… {step}/{total}</p>
      <div className="flex gap-2">
        {Array.from({ length: total }, (_, i) => (
          <span
            key={i}
            className={`h-3 w-10 rounded-full transition-colors duration-200 ${
              i < step ? "bg-brand-500" : i === step ? "bg-brand-400 animate-pulse" : "bg-slate-600"
            }`}
          />
        ))}
      </div>
    </div>
  );
}

export function IdlePrompt({ lang }: { lang: "en" | "hi" }) {
  const en = {
    title: "Mark your attendance",
    steps: ["Center your face in the oval", "Hold still for a moment", "Tap Check In or Check Out"],
  };
  const hi = {
    title: "अपनी उपस्थिति दर्ज करें",
    steps: ["चेहरा ओवल के बीच में रखें", "थोड़ी देर स्थिर रहें", "चेक इन या चेक आउट दबाएं"],
  };
  const copy = lang === "hi" ? hi : en;
  return (
    <div className="space-y-4 text-left">
      <p className="text-xl font-semibold text-white">{copy.title}</p>
      <ol className="space-y-2 text-slate-300">
        {copy.steps.map((s, i) => (
          <li key={s} className="flex items-start gap-3 text-base">
            <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-slate-700 text-sm font-bold text-brand-400">
              {i + 1}
            </span>
            {s}
          </li>
        ))}
      </ol>
    </div>
  );
}

export function ResultPanel({
  result,
  photoSrc,
  resetSeconds,
  pendingAction,
}: {
  result: KioskRecognizeResponse | null;
  photoSrc: string | null;
  resetSeconds: number;
  pendingAction: KioskAttendanceAction | null;
}) {
  const isSuccess = result?.status === "success";
  const isWarning = result?.status === "warning";
  const isError = result && !isSuccess && !isWarning;

  const borderClass = isSuccess
    ? "border-emerald-400/50 bg-emerald-950/40"
    : isWarning
      ? "border-amber-400/50 bg-amber-950/40"
      : isError
        ? "border-red-400/50 bg-red-950/40"
        : "border-slate-600/80 bg-slate-800/60";

  return (
    <div
      className={`flex min-h-[280px] w-full max-w-lg flex-col rounded-2xl border-2 p-5 shadow-2xl backdrop-blur-sm sm:min-h-[360px] sm:rounded-3xl sm:p-8 ${borderClass}`}
      aria-live="polite"
      aria-atomic="true"
    >
      {result && (
        <div className="kiosk-success-pop flex flex-1 flex-col items-center justify-center gap-4 text-center">
          <div
            className={`flex h-16 w-16 items-center justify-center rounded-full ${
              isSuccess ? "bg-emerald-500/20 text-emerald-300" : isWarning ? "bg-amber-500/20 text-amber-300" : "bg-red-500/20 text-red-300"
            }`}
          >
            {isSuccess ? <IconSuccess className="h-10 w-10" /> : <IconWarning className="h-10 w-10" />}
          </div>
          {photoSrc && (
            <img
              src={photoSrc}
              alt=""
              className="h-28 w-28 rounded-full border-4 border-white/20 object-cover shadow-lg"
            />
          )}
              {result.full_name && <p className="text-2xl font-bold tracking-tight sm:text-3xl">{result.full_name}</p>}
          {result.employee_code && <p className="text-lg text-slate-300">{result.employee_code}</p>}
          {(result.department || result.job_role) && (
            <p className="text-sm text-slate-400">{[result.department, result.job_role].filter(Boolean).join(" · ")}</p>
          )}
              <p className="text-xl font-semibold leading-snug sm:text-2xl">{result.display_message}</p>
          {result.current_time && (
            <p className="font-mono text-lg text-slate-400">{new Date(result.current_time).toLocaleTimeString()}</p>
          )}
          {pendingAction && (
            <span className="rounded-full bg-white/10 px-3 py-1 text-xs uppercase tracking-wider text-slate-400">
              {pendingAction === "check_in" ? "Check in" : "Check out"}
            </span>
          )}
          <p className="mt-2 text-sm text-slate-500">Next person in {resetSeconds}s</p>
        </div>
      )}
    </div>
  );
}

export function ActionButton({
  action,
  disabled,
  onClick,
  lang,
}: {
  action: KioskAttendanceAction;
  disabled: boolean;
  onClick: () => void;
  lang: "en" | "hi";
}) {
  const isIn = action === "check_in";
  const label = isIn
    ? lang === "hi"
      ? { main: "चेक इन", sub: "आने का समय" }
      : { main: "Check In", sub: "Arrival" }
    : lang === "hi"
      ? { main: "चेक आउट", sub: "जाने का समय" }
      : { main: "Check Out", sub: "Departure" };

  return (
    <button
      type="button"
      disabled={disabled}
      onClick={onClick}
      aria-label={label.main}
      className={`group flex min-h-[72px] w-full flex-1 flex-col items-center justify-center gap-1 rounded-2xl px-4 py-4 text-white shadow-xl transition active:scale-[0.98] disabled:cursor-not-allowed disabled:opacity-45 disabled:active:scale-100 sm:min-h-[88px] sm:gap-2 sm:px-6 sm:py-5 ${
        isIn
          ? "bg-gradient-to-b from-emerald-500 to-emerald-700 hover:from-emerald-400 hover:to-emerald-600 focus-visible:ring-4 focus-visible:ring-emerald-400/50"
          : "bg-gradient-to-b from-orange-500 to-orange-700 hover:from-orange-400 hover:to-orange-600 focus-visible:ring-4 focus-visible:ring-orange-400/50"
      }`}
    >
      {isIn ? <IconCheckIn className="h-8 w-8 opacity-90 sm:h-10 sm:w-10" /> : <IconCheckOut className="h-8 w-8 opacity-90 sm:h-10 sm:w-10" />}
      <span className="text-xl font-bold tracking-tight sm:text-2xl">{label.main}</span>
      <span className="text-sm font-normal opacity-85">{label.sub}</span>
    </button>
  );
}
