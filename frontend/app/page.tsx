"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAuthStore } from "@/store/auth-store";

export default function HomePage() {
  const router = useRouter();
  const accessToken = useAuthStore((state) => state.accessToken);
  const sessionChecked = useAuthStore((state) => state.sessionChecked);

  useEffect(() => {
    if (!sessionChecked) return;
    router.replace(accessToken ? "/chat" : "/auth/login");
  }, [accessToken, router, sessionChecked]);

  return (
    <main className="grid min-h-dvh place-items-center bg-canvas" aria-live="polite">
      <div className="flex items-center gap-3 text-muted">
        <span className="h-3 w-3 animate-soft-pulse rounded-full bg-brand-500" />
        Ouverture de Kozons…
      </div>
    </main>
  );
}
