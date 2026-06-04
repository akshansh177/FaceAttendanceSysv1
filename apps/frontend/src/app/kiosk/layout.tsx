import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Attendance Kiosk",
  description: "Employee face attendance check-in and check-out",
};

export default function KioskLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-[100dvh] overscroll-none touch-manipulation">{children}</div>
  );
}
