import type { UserRole } from "./types";

export function getRole(): UserRole | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("user_role") as UserRole | null;
}

export function setRole(role: string) {
  localStorage.setItem("user_role", role);
  if (typeof document !== "undefined") {
    document.cookie = `user_role=${encodeURIComponent(role)}; path=/; max-age=86400; SameSite=Lax`;
  }
}

export function canAccessHR(): boolean {
  const role = getRole();
  return role === "super_admin" || role === "hr_manager";
}

export function canAccessManager(): boolean {
  const role = getRole();
  return role === "super_admin" || role === "hr_manager" || role === "team_manager";
}

export function isAdmin(): boolean {
  return getRole() === "super_admin";
}
