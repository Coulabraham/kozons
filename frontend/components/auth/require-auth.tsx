"use client";

import { useRouter } from "next/navigation";
import type { ReactNode } from "react";
import { useEffect } from "react";

import { useAuthStore } from "@/store/auth-store";

export function RequireAuth({ children }: { children: ReactNode }) {
  const router = useRouter();
  const accessToken = useAuthStore((state) => state.accessToken);
  const user = useAuthStore((state) => state.user);
  const sessionChecked = useAuthStore((state) => state.sessionChecked);

  useEffect(() => {
    if (sessionChecked && (!accessToken || !user)) router.replace("/auth/login");
  }, [accessToken, router, sessionChecked, user]);

  if (!sessionChecked || !accessToken || !user) {
    return (
      <main className="grid min-h-dvh place-items-center bg-canvas text-muted" aria-live="polite">
        Ouverture de Kozons…
      </main>
    );
  }

  return children;
}
