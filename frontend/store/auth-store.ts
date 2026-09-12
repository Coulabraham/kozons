import { create } from "zustand";
import { createJSONStorage, persist } from "zustand/middleware";

import type { User } from "@/lib/types";

interface AuthState {
  accessToken: string | null;
  user: User | null;
  pendingIdentifier: string | null;
  sessionChecked: boolean;
  setSession: (accessToken: string, user: User) => void;
  setAccessToken: (accessToken: string) => void;
  setSessionChecked: (checked: boolean) => void;
  setPendingIdentifier: (identifier: string | null) => void;
  updateUser: (changes: Partial<User>) => void;
  clearSession: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      accessToken: null,
      user: null,
      pendingIdentifier: null,
      sessionChecked: false,
      setSession: (accessToken, user) =>
        set({ accessToken, user, pendingIdentifier: null, sessionChecked: true }),
      setAccessToken: (accessToken) => set({ accessToken }),
      setSessionChecked: (sessionChecked) => set({ sessionChecked }),
      setPendingIdentifier: (pendingIdentifier) => set({ pendingIdentifier }),
      updateUser: (changes) => set((state) => ({ user: state.user ? { ...state.user, ...changes } : null })),
      clearSession: () => set({ accessToken: null, user: null, sessionChecked: true }),
    }),
    {
      name: "kozons-auth-flow",
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({ pendingIdentifier: state.pendingIdentifier }),
    },
  ),
);
