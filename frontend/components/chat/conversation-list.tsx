"use client";

import Link from "next/link";
import { useMemo } from "react";

import { Avatar } from "@/components/ui/avatar";
import { Brand } from "@/components/ui/brand";
import { GroupIcon, PlusIcon, SearchIcon } from "@/components/ui/icons";
import { ThemeToggle } from "@/components/ui/theme-toggle";
import { conversationPeer, conversationTitle } from "@/lib/chat-format";
import type { Conversation, GlobalSearchResults } from "@/lib/types";

import { ConversationItem } from "./conversation-item";

interface ConversationListProps {
  conversations: Conversation[];
  currentUserId: number;
  activeId: number | null;
  presence: Record<number, boolean>;
  search: string;
  searchResults?: GlobalSearchResults;
  searching: boolean;
  onSearchChange: (value: string) => void;
  onOpen: (id: number) => void;
}

export function ConversationList({ conversations, currentUserId, activeId, presence, search, searchResults, searching, onSearchChange, onOpen }: ConversationListProps) {
  const normalized = search.toLowerCase().trim();
  const localFiltered = useMemo(
    () => conversations.filter((conversation) => conversationTitle(conversation, currentUserId).toLowerCase().includes(normalized)),
    [conversations, currentUserId, normalized],
  );
  const filtered = normalized.length >= 2 && searchResults ? searchResults.conversations : localFiltered;
  const contacts = normalized.length >= 2 ? searchResults?.contacts ?? [] : [];
  return (
    <aside className="relative flex h-full w-full flex-col border-r border-line bg-surface lg:w-[380px] lg:shrink-0">
      <header className="flex h-[72px] items-center justify-between border-b border-line px-5"><Brand /><ThemeToggle /></header>
      <div className="px-4 pb-2 pt-4"><label className="flex h-11 items-center gap-2 rounded-2xl bg-elevated px-3 text-muted focus-within:ring-2 focus-within:ring-brand-400/40"><SearchIcon size={19} /><span className="sr-only">Rechercher une conversation ou un contact</span><input value={search} onChange={(event) => onSearchChange(event.target.value)} className="min-w-0 flex-1 bg-transparent text-sm text-ink outline-none placeholder:text-muted" placeholder="Conversations et contacts" /></label></div>
      <div className="scrollbar-subtle flex-1 overflow-y-auto px-2 pb-24 lg:pb-3">
        {searching && <p className="px-4 py-2 text-xs text-muted">Recherche…</p>}
        {filtered.map((conversation) => {
          const peer = conversationPeer(conversation, currentUserId);
          return <ConversationItem key={conversation.id} conversation={conversation} currentUserId={currentUserId} online={peer ? Boolean(presence[peer.id]) : false} active={conversation.id === activeId} onClick={() => onOpen(conversation.id)} />;
        })}
        {contacts.length > 0 && <div className="mt-3 border-t border-line px-2 pt-3"><p className="mb-2 px-2 text-xs font-bold uppercase tracking-wide text-muted">Contacts</p>{contacts.map((contact) => <Link key={contact.id} href="/contacts" className="flex items-center gap-3 rounded-xl p-2 hover:bg-elevated"><Avatar user={contact} size="sm" /><span className="min-w-0"><strong className="block truncate text-sm">{contact.nom_affichage}</strong><span className="text-xs text-muted">Ouvrir les contacts</span></span></Link>)}</div>}
        {!searching && filtered.length === 0 && contacts.length === 0 && <div className="mx-4 mt-16 text-center"><span className="mx-auto grid h-14 w-14 place-items-center rounded-2xl bg-brand-50 text-brand-600"><SearchIcon size={26} /></span><p className="mt-4 font-bold">Aucun résultat</p><p className="mt-1 text-sm text-muted">Essayez un autre nom.</p></div>}
      </div>
      <div className="absolute bottom-20 right-5 flex flex-col gap-2 lg:bottom-5"><Link href="/groups/new" aria-label="Créer un groupe" title="Créer un groupe" className="grid h-11 w-11 place-items-center rounded-full bg-surface text-brand-600 shadow-soft transition hover:bg-brand-50"><GroupIcon /></Link><Link href="/contacts" aria-label="Nouvelle conversation" title="Nouvelle conversation" className="grid h-14 w-14 place-items-center rounded-full bg-brand-500 text-white shadow-float transition hover:bg-brand-600"><PlusIcon size={26} /></Link></div>
    </aside>
  );
}
