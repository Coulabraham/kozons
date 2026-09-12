"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { ChatIcon, ContactsIcon, UserIcon } from "@/components/ui/icons";

const items = [
  { href: "/chat", label: "Discussions", icon: ChatIcon },
  { href: "/contacts", label: "Contacts", icon: ContactsIcon },
  { href: "/profile", label: "Profil", icon: UserIcon },
];

export function MobileNav() {
  const pathname = usePathname();
  return (
    <nav className="safe-bottom grid grid-cols-3 border-t border-line bg-surface px-2 pt-1 lg:hidden" aria-label="Navigation principale">
      {items.map(({ href, label, icon: NavIcon }) => {
        const active = pathname.startsWith(href);
        return <Link key={href} href={href} aria-current={active ? "page" : undefined} className={`flex min-h-14 flex-col items-center justify-center gap-0.5 rounded-xl text-xs font-semibold transition ${active ? "text-brand-600" : "text-muted hover:text-ink"}`}><NavIcon size={21} /><span>{label}</span></Link>;
      })}
    </nav>
  );
}
