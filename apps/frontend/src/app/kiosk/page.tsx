"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  ActionButton,
  CaptureProgress,
  IdlePrompt,
  ResultPanel,
} from "@/components/kiosk/kiosk-ui";
import {
  getKioskCredentials,
  kioskConfig,
  kioskHeartbeat,
  kioskMediaUrl,
  kioskRecognize,
  setKioskCredentials,
  type KioskAttendanceAction,
} from "@/lib/kiosk-api";
import {
  enqueueOfflineEvent,
  flushOfflineQueue,
  type OfflineKioskEvent,
} from "@/lib/kiosk-offline";
import type { KioskConfig, KioskRecognizeResponse } from "@/lib/types";
import { usePageVisible } from "@/hooks/use-page-visible";

const FRAME_COUNT = 5;
const FRAME_CAPTURE_MS = 400;
const JPEG_QUALITY = 0.82;
const HEARTBEAT_MS = 120_000;

const VOICE: Record<string, Record<string, string>> = {
  en: {
    check_in_success: "Check in successful",
    check_out_success: "Check out successful",
    already_checked_in: "Already checked in today",
    already_checked_out: "Already checked out",
    no_check_in_today: "Please check in first",
    attendance_already_recorded: "Attendance already recorded",
    face_not_recognized: "Face not recognized",
    liveness_failed: "Please look at the camera and blink",
  },
  hi: {
    check_in_success: "चेक इन सफल",
    check_out_success: "चेक आउट सफल",
    already_checked_in: "आज पहले से चेक इन",
    already_checked_out: "पहले से चेक आउट",
    no_check_in_today: "पहले चेक इन करें",
    attendance_already_recorded: "उपस्थिति पहले से दर्ज",
    face_not_recognized: "चेहरा पहचान में नहीं आया",
    liveness_failed: "कृपया कैमरे की ओर देखें और पलकें झपकाएं",
  },
};

export default function PublicKioskPage() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [config, setConfig] = useState<KioskConfig | null>(null);
  const [result, setResult] = useState<KioskRecognizeResponse | null>(null);
  const [processing, setProcessing] = useState(false);
  const [captureStep, setCaptureStep] = useState(0);
  const [pendingAction, setPendingAction] = useState<KioskAttendanceAction | null>(null);
  const [resetSeconds, setResetSeconds] = useState(0);
  const [clock, setClock] = useState<Date | null>(null);
  const [setup, setSetup] = useState({ deviceId: "", apiKey: "" });
  const [hasCredentials, setHasCredentials] = useState(false);
  const [hydrated, setHydrated] = useState(false);
  const [showApiKey, setShowApiKey] = useState(false);
  const [cameraReady, setCameraReady] = useState(false);
  const [cameraError, setCameraError] = useState<string | null>(null);
  const capturingRef = useRef(false);
  const cameraBackoffRef = useRef(0);
  const pageVisible = usePageVisible();

  const lang: "en" | "hi" = config?.voice_language === "hi" ? "hi" : "en";

  useEffect(() => {
    if (!pageVisible) return;
    setClock(new Date());
    const t = setInterval(() => setClock(new Date()), 1000);
    return () => clearInterval(t);
  }, [pageVisible]);

  useEffect(() => {
    if (resetSeconds <= 0) return;
    const t = setInterval(() => setResetSeconds((s) => Math.max(0, s - 1)), 1000);
    return () => clearInterval(t);
  }, [resetSeconds]);

  useEffect(() => {
    const creds = getKioskCredentials();
    setSetup({ deviceId: creds.deviceId, apiKey: creds.apiKey });
    setHasCredentials(!!creds.apiKey.trim());
    setHydrated(true);
    if (creds.apiKey) {
      kioskConfig().then(setConfig).catch(() => null);
    }
    const hb = setInterval(() => {
      const c = getKioskCredentials();
      if (c.deviceId && c.apiKey) kioskHeartbeat().catch(() => null);
    }, HEARTBEAT_MS);
    return () => clearInterval(hb);
  }, []);

  const startCamera = useCallback(async () => {
    setCameraError(null);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: {
          facingMode: "user",
          width: { ideal: 640 },
          height: { ideal: 480 },
          frameRate: { ideal: 15, max: 24 },
        },
        audio: false,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
        setCameraReady(true);
        cameraBackoffRef.current = 0;
        stream.getVideoTracks().forEach((track) => {
          track.onended = () => {
            setCameraReady(false);
            const delay = Math.min(30_000, 1000 * 2 ** cameraBackoffRef.current);
            cameraBackoffRef.current += 1;
            setTimeout(() => startCamera(), delay);
          };
        });
      }
    } catch {
      setCameraError("Camera access denied. Allow camera permission and refresh.");
      setCameraReady(false);
      const delay = Math.min(30_000, 1000 * 2 ** cameraBackoffRef.current);
      cameraBackoffRef.current += 1;
      setTimeout(() => startCamera(), delay);
    }
  }, []);

  useEffect(() => {
    if (hasCredentials) {
      startCamera();
    }
    return () => {
      const stream = videoRef.current?.srcObject as MediaStream | null;
      stream?.getTracks().forEach((t) => t.stop());
    };
  }, [hasCredentials, startCamera]);

  useEffect(() => {
    const stream = videoRef.current?.srcObject as MediaStream | null;
    if (!stream) return;
    stream.getVideoTracks().forEach((track) => {
      track.enabled = pageVisible;
    });
  }, [pageVisible, cameraReady]);

  useEffect(() => {
    const sendOffline = async (ev: OfflineKioskEvent) => {
      const formData = new FormData();
      ev.frames.forEach((b, i) => formData.append("files", b, `frame${i}.jpg`));
      await kioskRecognize(formData, ev.action, ev.id);
      return true;
    };
    const onOnline = () => flushOfflineQueue(sendOffline).catch(() => null);
    window.addEventListener("online", onOnline);
    onOnline();
    return () => window.removeEventListener("online", onOnline);
  }, []);

  const speak = useCallback(
    (code: string) => {
      if (!config?.voice_feedback_enabled || typeof window === "undefined") return;
      const text = VOICE[lang]?.[code] || code;
      const u = new SpeechSynthesisUtterance(text);
      u.lang = lang === "hi" ? "hi-IN" : "en-US";
      speechSynthesis.speak(u);
    },
    [config, lang]
  );

  const captureBurst = useCallback(
    async (action: KioskAttendanceAction) => {
      if (!videoRef.current || !canvasRef.current || capturingRef.current) return;
      const creds = getKioskCredentials();
      if (!creds.deviceId || !creds.apiKey) return;

      capturingRef.current = true;
      setProcessing(true);
      setPendingAction(action);
      setResult(null);
      setCaptureStep(0);

      const canvas = canvasRef.current;
      const frames: Blob[] = [];
      for (let i = 0; i < FRAME_COUNT; i++) {
        canvas.width = videoRef.current.videoWidth;
        canvas.height = videoRef.current.videoHeight;
        canvas.getContext("2d")?.drawImage(videoRef.current, 0, 0);
        const blob = await new Promise<Blob | null>((r) => canvas.toBlob(r, "image/jpeg", JPEG_QUALITY));
        if (blob) frames.push(blob);
        setCaptureStep(i + 1);
        await new Promise((r) => setTimeout(r, FRAME_CAPTURE_MS));
      }

      const formData = new FormData();
      frames.forEach((b, i) => formData.append("files", b, `frame${i}.jpg`));
      const clientEventId =
        typeof crypto !== "undefined" && crypto.randomUUID
          ? crypto.randomUUID()
          : `${Date.now()}-${Math.random()}`;

      if (!navigator.onLine) {
        await enqueueOfflineEvent({
          id: clientEventId,
          deviceId: creds.deviceId,
          action,
          frames,
          ts: Date.now(),
        });
        setResult({
          matched: false,
          status: "warning",
          code: "attendance_already_recorded",
          display_message: "Offline — queued for sync when online",
        });
        setProcessing(false);
        capturingRef.current = false;
        return;
      }

      try {
        const res = await kioskRecognize(formData, action, clientEventId);
        setResult(res);
        speak(res.code);
        const resetSec = config?.screen_reset_seconds ?? 5;
        setResetSeconds(resetSec);
        setTimeout(() => {
          setResult(null);
          setPendingAction(null);
          setResetSeconds(0);
          setCaptureStep(0);
          capturingRef.current = false;
        }, resetSec * 1000);
      } catch (e) {
        if (!navigator.onLine) {
          await enqueueOfflineEvent({
            id: clientEventId,
            deviceId: creds.deviceId,
            action,
            frames,
            ts: Date.now(),
          });
        }
        setResult({
          matched: false,
          status: "error",
          code: "face_not_recognized",
          display_message: e instanceof Error ? e.message : "Failed",
        });
        setResetSeconds(5);
        setTimeout(() => {
          setResult(null);
          setPendingAction(null);
          setResetSeconds(0);
          setCaptureStep(0);
          capturingRef.current = false;
        }, 5000);
      } finally {
        setProcessing(false);
      }
    },
    [config, speak]
  );

  const photoSrc = kioskMediaUrl(result?.photo_url ?? null);
  const busy = processing || !!result;

  if (!hydrated) {
    return (
      <div className="flex min-h-[100dvh] flex-col items-center justify-center bg-gradient-to-b from-slate-950 to-slate-900 p-8 text-white">
        <div className="h-10 w-10 animate-spin rounded-full border-2 border-brand-400 border-t-transparent" aria-hidden />
        <p className="mt-4 text-slate-400">Loading kiosk…</p>
      </div>
    );
  }

  if (!hasCredentials) {
    return (
      <div className="flex min-h-[100dvh] flex-col items-center justify-center bg-gradient-to-b from-slate-950 to-slate-900 p-8 text-white">
        <div className="w-full max-w-md rounded-3xl border border-slate-700 bg-slate-800/80 p-8 shadow-2xl">
          <p className="mb-1 text-sm font-medium uppercase tracking-widest text-brand-400">Step 1 of 1</p>
          <h1 className="mb-2 text-3xl font-bold">Kiosk setup</h1>
          <p className="mb-8 text-slate-400">Enter the device ID and API key from HR Admin → Kiosks.</p>
          <div className="space-y-4">
            <label className="block">
              <span className="mb-1 block text-sm text-slate-400">Device ID</span>
              <input
                className="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-4 text-lg focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                placeholder="e.g. kiosk-main-gate"
                value={setup.deviceId}
                onChange={(e) => setSetup({ ...setup, deviceId: e.target.value })}
                autoComplete="off"
              />
            </label>
            <label className="block">
              <span className="mb-1 block text-sm text-slate-400">API key</span>
              <div className="relative">
                <input
                  className="w-full rounded-xl border border-slate-600 bg-slate-900 px-4 py-4 pr-24 text-lg focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  placeholder="Paste one-time key"
                  type={showApiKey ? "text" : "password"}
                  value={setup.apiKey}
                  onChange={(e) => setSetup({ ...setup, apiKey: e.target.value })}
                  autoComplete="off"
                />
                <button
                  type="button"
                  className="absolute right-3 top-1/2 -translate-y-1/2 rounded-lg px-2 py-1 text-sm text-slate-400 hover:text-white"
                  onClick={() => setShowApiKey((v) => !v)}
                >
                  {showApiKey ? "Hide" : "Show"}
                </button>
              </div>
            </label>
            <button
              className="w-full rounded-xl bg-brand-600 py-4 text-lg font-bold shadow-lg transition hover:bg-brand-500 active:scale-[0.99] disabled:opacity-50"
              disabled={!setup.deviceId.trim() || !setup.apiKey.trim()}
              onClick={() => {
                setKioskCredentials(setup.deviceId.trim(), setup.apiKey.trim());
                window.location.reload();
              }}
            >
              Save & start kiosk
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[100dvh] flex-col bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white">
      <header className="flex shrink-0 flex-col gap-3 border-b border-slate-800/80 px-4 py-4 sm:flex-row sm:items-center sm:justify-between sm:px-6 md:px-10">
        <div className="min-w-0">
          <h1 className="text-lg font-bold tracking-wide md:text-xl">Face Attendance</h1>
          <p className="text-sm text-slate-500">Touch a button below to continue</p>
        </div>
        <div className="text-left sm:text-right">
          <p className="font-mono text-2xl font-bold tabular-nums sm:text-3xl md:text-4xl" suppressHydrationWarning>
            {clock ? clock.toLocaleTimeString() : "—"}
          </p>
          <p className="text-sm text-slate-400" suppressHydrationWarning>
            {clock
              ? clock.toLocaleDateString(undefined, { weekday: "short", month: "short", day: "numeric" })
              : "—"}
          </p>
        </div>
      </header>

      <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col gap-6 p-4 md:p-8 lg:flex-row lg:items-center lg:justify-center">
        <section className="flex flex-1 flex-col items-center gap-5" aria-label="Camera">
          <div className="relative w-full max-w-[720px] overflow-hidden rounded-3xl bg-black shadow-2xl ring-1 ring-slate-700">
            <video
              ref={videoRef}
              className="aspect-[4/3] w-full object-cover"
              muted
              playsInline
              autoPlay
            />
            <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
              <div
                className={`relative h-[58%] w-[42%] max-h-[320px] max-w-[240px] border-2 border-dashed border-brand-400/90 kiosk-face-ring ${
                  processing ? "kiosk-pulse-ring" : ""
                }`}
              />
            </div>
            {processing && (
              <div className="pointer-events-none absolute left-[29%] right-[29%] h-0.5 bg-brand-400/80 kiosk-scan-line" />
            )}
            <canvas ref={canvasRef} className="hidden" />
            {!cameraReady && (
              <div className="absolute inset-0 flex flex-col items-center justify-center gap-4 bg-black/75 p-6 text-center">
                {cameraError ? (
                  <p className="max-w-sm text-red-300">{cameraError}</p>
                ) : (
                  <p className="text-lg">Starting camera…</p>
                )}
                <button
                  type="button"
                  onClick={startCamera}
                  className="rounded-xl bg-brand-600 px-8 py-3 font-semibold hover:bg-brand-500"
                >
                  Enable camera
                </button>
              </div>
            )}
          </div>

          <div className="flex w-full max-w-[720px] flex-col gap-3 sm:flex-row sm:gap-4 md:gap-5">
            <ActionButton
              action="check_in"
              lang={lang}
              disabled={busy || !cameraReady}
              onClick={() => captureBurst("check_in")}
            />
            <ActionButton
              action="check_out"
              lang={lang}
              disabled={busy || !cameraReady}
              onClick={() => captureBurst("check_out")}
            />
          </div>
        </section>

        <section className="flex w-full flex-col gap-4 lg:max-w-lg" aria-label="Status">
          {processing && (
            <div className="flex min-h-[240px] flex-col items-center justify-center rounded-2xl border border-slate-700 bg-slate-800/60 p-5 sm:min-h-[360px] sm:rounded-3xl sm:p-8">
              <CaptureProgress step={captureStep} total={FRAME_COUNT} />
              <p className="mt-6 text-center text-lg text-slate-300">
                {pendingAction === "check_out"
                  ? lang === "hi"
                    ? "चेक आउट हो रहा है…"
                    : "Processing check-out…"
                  : lang === "hi"
                    ? "चेक इन हो रहा है…"
                    : "Processing check-in…"}
              </p>
              <p className="mt-2 text-center text-sm text-slate-500">Look at the camera · blink naturally</p>
            </div>
          )}

          {result && !processing && (
            <ResultPanel
              result={result}
              photoSrc={photoSrc}
              resetSeconds={resetSeconds}
              pendingAction={pendingAction}
            />
          )}

          {!result && !processing && <IdlePrompt lang={lang} />}
        </section>
      </main>

      <footer className="shrink-0 border-t border-slate-800/80 px-6 py-3 text-center text-xs text-slate-600">
        {lang === "hi" ? "अगले कर्मचारी के लिए स्क्रीन स्वतः रीसेट होगी" : "Screen resets automatically for the next employee"}
      </footer>
    </div>
  );
}
