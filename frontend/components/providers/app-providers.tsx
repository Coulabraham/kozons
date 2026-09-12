"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import type { ReactNode } from "react";
import { useEffect, useState } from "react";

import { refreshAccessToken } from "@/lib/api/client";
import { useAuthStore } from "@/store/auth-store";
import { useChatStore } from "@/store/chat-store";

import { ThemeProvider } from "./theme-provider";

export function AppProviders({ children }: { children: ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            gcTime: 24 * 60 * 60 * 1000,
            retry: 1,
            refetchOnWindowFocus: true,
          },
          mutations: { retry: 0 },
        },
      }),
  );
  useEffect(() => {
    if (useAuthStore.getState().sessionChecked) return;
    refreshAccessToken().catch(() => {
      useChatStore.getState().resetPrivateData();
    }).finally(() => useAuthStore.getState().setSessionChecked(true));
  }, []);

  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>{children}</ThemeProvider>
    </QueryClientProvider>
  );
}
