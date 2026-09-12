import Link from "next/link";
import type { ReactNode } from "react";

import { MobileNav } from "@/components/navigation/mobile-nav";
import { Brand } from "@/components/ui/brand";
import { ArrowLeftIcon } from "@/components/ui/icons";
import { ThemeToggle } from "@/components/ui/theme-toggle";

export function SectionShell({ title, subtitle, action, children }: { title: string; subtitle?: string; action?: ReactNode; children: ReactNode }) {
  return (
    <main className="flex min-h-dvh flex-col bg-canvas">
      <header className="sticky top-0 z-20 border-b border-line bg-surface/95 backdrop-blur"><div className="mx-auto flex h-[72px] max-w-5xl items-center gap-3 px-4 sm:px-6"><Link href="/chat" aria-label="Retour aux discussions" className="grid h-10 w-10 place-items-center rounded-full text-muted hover:bg-brand-50 hover:text-brand-600 lg:hidden"><ArrowLeftIcon /></Link><div className="hidden lg:block"><Brand /></div><div className="min-w-0 flex-1 lg:ml-8"><h1 className="truncate text-lg font-extrabold">{title}</h1>{subtitle && <p className="truncate text-xs text-muted">{subtitle}</p>}</div>{action}<ThemeToggle /></div></header>
      <div className="mx-auto w-full max-w-5xl flex-1 px-4 py-6 sm:px-6 sm:py-8">{children}</div>
      <MobileNav />
    </main>
  );
}
