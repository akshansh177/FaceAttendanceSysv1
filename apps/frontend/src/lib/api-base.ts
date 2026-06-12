/** API base URL. Empty string = same-origin relative paths (aaPanel /api proxy). */
export function getApiBaseUrl(): string {
  const raw = (process.env.NEXT_PUBLIC_API_URL ?? "").trim();
  if (!raw || raw.includes(",")) return "";
  return raw.replace(/\/$/, "");
}
