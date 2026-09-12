import type { ReactNode } from "react";

import { Brand } from "@/components/ui/brand";
import { LockIcon } from "@/components/ui/icons";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function AuthShell({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <main className="relative grid min-h-dvh place-items-center overflow-hidden bg-canvas px-5 py-10">
      <div className="absolute right-5 top-5"><ThemeToggle /></div>
      <section className="relative z-10 w-full max-w-md animate-fade-up rounded-[2rem] border border-line bg-surface p-6 shadow-soft sm:p-9">
        <Brand fullLogo />
        <div className="mt-3">
          <h1 className="text-3xl font-extrabold tracking-[-0.04em] text-ink">{title}</h1>
          <p className="mt-2 text-base text-muted">{subtitle}</p>
        </div>
        <div className="mt-7">{children}</div>
        <p className="mt-7 flex items-center justify-center gap-2 text-xs text-muted"><LockIcon size={15} /> Vos échanges restent privés.</p>
      </section>
      <div className="pointer-events-none absolute -left-24 top-[-6rem] h-72 w-72 rounded-full bg-brand-400/10 blur-3xl" />
      <div className="pointer-events-none absolute -bottom-24 right-[-4rem] h-80 w-80 rounded-full bg-brand-600/10 blur-3xl" />
    </main>
  );
}
