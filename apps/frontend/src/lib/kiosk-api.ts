import { getApiBaseUrl } from "./api-base";

const API_URL = getApiBaseUrl() || (typeof window !== "undefined" ? "" : "http://localhost:6002");

export function kioskMediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  if (path.startsWith("http://") || path.startsWith("https://")) return path;
  return `${API_URL}${path.startsWith("/") ? path : `/${path}`}`;
}

export function getKioskCredentials() {
  if (typeof window === "undefined") {
    return { deviceId: "", apiKey: "" };
  }
  return {
    deviceId: localStorage.getItem("kiosk_device_id") || process.env.NEXT_PUBLIC_KIOSK_DEVICE_ID || "",
    apiKey: localStorage.getItem("kiosk_api_key") || process.env.NEXT_PUBLIC_KIOSK_API_KEY || "",
  };
}

export function setKioskCredentials(deviceId: string, apiKey: string) {
  localStorage.setItem("kiosk_device_id", deviceId);
  localStorage.setItem("kiosk_api_key", apiKey);
}

export async function kioskFetch<T>(path: string, options: RequestInit = {}): Promise<T> {
  const { deviceId, apiKey } = getKioskCredentials();
  const headers: Record<string, string> = {
    ...(options.headers as Record<string, string>),
    "X-Kiosk-Key": apiKey,
  };
  const res = await fetch(`${API_URL}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Kiosk request failed");
  }
  return res.json();
}

export type KioskAttendanceAction = "check_in" | "check_out";

export async function kioskRecognize(
  formData: FormData,
  action: KioskAttendanceAction,
  clientEventId?: string
): Promise<import("./types").KioskRecognizeResponse> {
  const { deviceId, apiKey } = getKioskCredentials();
  formData.append("device_identifier", deviceId);
  formData.append("action", action);
  if (clientEventId) {
    formData.append("client_event_id", clientEventId);
  }
  const res = await fetch(`${API_URL}/api/kiosk/recognize`, {
    method: "POST",
    headers: { "X-Kiosk-Key": apiKey },
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(typeof err.detail === "string" ? err.detail : "Recognition failed");
  }
  return res.json();
}

export async function kioskConfig() {
  return kioskFetch<import("./types").KioskConfig>("/api/kiosk/config");
}

export async function kioskHeartbeat() {
  const { deviceId } = getKioskCredentials();
  const body = new FormData();
  body.append("device_identifier", deviceId);
  return kioskFetch<{ message: string }>("/api/kiosk/heartbeat", { method: "POST", body });
}
