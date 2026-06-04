"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function LegacyKioskRedirect() {
  const router = useRouter();
  useEffect(() => {
    router.replace("/kiosk");
  }, [router]);
  return <p className="p-8 text-center">Redirecting to public kiosk...</p>;
}
